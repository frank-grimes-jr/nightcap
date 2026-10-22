"""Pinned quest activation with zero clients, admission hold and exact recovery."""
import base64
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time

ROOT = Path('/opt/nightcap/deploy/production')
OUT = Path('/opt/nightcap/backups/waypoint-crystal-20261022')
QUEST = ROOT/'data/server/quests/global/999240.pl'
KEEPER = QUEST.parent/'Instance_Keeper.pl'
OLD_SHA = 'f8fe9a8783e28b6685104a73769cf083c17ef5c411c9bc616e9fc3a420684e65'
NEW_SHA = '4b15350087dfd4153ea2ef98e418da9696b0c7efe99cdd8fe62cb96483f764a2'
KEEPER_SHA = '903086e695615f3c8f3f3a05ca1bf3bd96c1d8a6cff4700fc7ad6858215580b1'
CHANNEL_SHA = '5b897b3577b0b01be65eaf603bbf9eb3fd64af8459213dc01ccddb820981788c'

def sha(data): return hashlib.sha256(data).hexdigest()
def command(args): return subprocess.check_output(args,cwd=ROOT,text=True,timeout=35)
def game(source,*args): return command(['docker','compose','exec','-T','game','python3','-c',source,*args])
def control(action): return json.loads(game(CONTROL,action))
def gateway(): return command(['docker','compose','ps','-aq','gateway']).strip()
def gateway_paused(): return json.loads(command(['docker','inspect','--format','{{json .State.Paused}}',gateway()]))
def pause(): command(['docker','pause',gateway()])
def unpause(): command(['docker','unpause',gateway()])

PROCESSES = r'''
import json
from pathlib import Path
rows=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   name=(p/'comm').read_text().strip()
   if name in ('world','zone'):
    rows.append([name,int(p.name),(p/'stat').read_text().rsplit(')',1)[1].split()[19]])
  except FileNotFoundError:pass
assert sum(r[0]=='world' for r in rows)==1
assert sum(r[0]=='zone' for r in rows)==12
print(json.dumps(sorted(rows)))
'''

def snapshot():
    ids=command(['docker','compose','ps','-aq']).split()
    assert len(ids)==5, 'Expected five services'
    rows=json.loads(command(['docker','inspect',*ids]))
    states=[r['State'] for r in rows]
    assert all(s['Running'] and not s.get('OOMKilled') for s in states)
    assert all(s.get('Health',{}).get('Status','healthy')=='healthy' for s in states)
    assert sha(KEEPER.read_bytes())==KEEPER_SHA, 'Keeper drift'
    assert sha((ROOT/'data/public/channel.json').read_bytes())==CHANNEL_SHA, 'Paired client not published or channel drift'
    return {'services':sorted([r['Id'],r['Image'],r['RestartCount'],r['State']['StartedAt']] for r in rows),
            'native':json.loads(game(PROCESSES)), 'keeper_sha256':KEEPER_SHA,'channel_sha256':CHANNEL_SHA}

def sync_dir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)

def install(data):
    assert not QUEST.is_symlink()
    info=QUEST.stat(); temporary=QUEST.with_suffix('.pl.waypoint-partial')
    assert not temporary.is_symlink(), 'Partial quest symlink'
    if temporary.exists():
        assert stat.S_ISREG(temporary.lstat().st_mode), 'Partial quest is not regular'
        partial=temporary.read_bytes()
        known=[data]
        for name,digest in [('original.pl',OLD_SHA),('candidate.pl',NEW_SHA)]:
            saved=(OUT/name).read_bytes(); assert sha(saved)==digest, 'Recovery payload drift'
            known.append(saved)
        assert any(payload.startswith(partial) for payload in known), 'Foreign partial quest'
        temporary.unlink()
    with temporary.open('xb') as f:
        os.fchmod(f.fileno(),info.st_mode); os.fchown(f.fileno(),info.st_uid,info.st_gid)
        f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(temporary,QUEST)
    sync_dir(QUEST.parent)

SEND = r'''
import json,socket,struct,sys,time
from pathlib import Path
cfg=json.loads(Path('/srv/nightcap/eqemu_config.json').read_text())['server']['world']
assert cfg['tcp']=={'ip':'127.0.0.1','port':'9001'}
def frame(kind,p):return struct.pack('<IB',len(p),kind)+p
def packet(op,p):return frame(5,struct.pack('<IH',len(p),op)+p)
with socket.create_connection(('127.0.0.1',9001),timeout=5) as s:
 s.sendall(frame(4,b'Zone\0'+cfg['key'].encode()+b'\0'))
 if sys.argv[1]=='reload':s.sendall(packet(0x4100,struct.pack('<i?3xqiI',22,False,0,0,0)))
 elif sys.argv[1]=='signal':s.sendall(packet(0x4506,struct.pack('<Bii64s',6,999240,int(sys.argv[2]),b'')))
 else:raise ValueError(sys.argv[1])
 time.sleep(1)
'''

def reload(): game(SEND,'reload')
def signal(value): game(SEND,'signal',str(value))
def verify_reload(since,action):
    for attempt in range(20):
        logs=command(['docker','compose','logs','--no-color','--since',since,'game'])
        if logs.count('Reloaded [Quest] (22)')>=12: break
        time.sleep(1)
    (OUT/(action+'-reload.log')).write_text(logs)
    count=logs.count('Reloaded [Quest] (22)')
    assert count>=12, f'Incomplete aggregate quest reload acknowledgments: {count}'
    assert not any(s in logs.lower() for s in ('quest error','perl error','error compiling','syntax error','failed to compile')), 'Quest error in retained log'
    return count

def execute(action,candidate,commit):
    assert sha(candidate)==NEW_SHA, 'Candidate drift'
    assert not (ROOT/'private/gm-maintenance.json').exists(), 'GM maintenance active'
    before=snapshot()
    count=control('count'); locked=control('status'); paused=gateway_paused()
    assert type(count) is int and count==0, 'Clients must fully exit before paired activation'
    if action=='check':
        assert sha(QUEST.read_bytes())==OLD_SHA and not paused, 'Preflight state drift'
        return {'status':'ready','clients':count,'locked':locked,'gateway_paused':paused,'before':before}
    if action=='apply':
        assert not paused, 'Gateway already held'
        original=QUEST.read_bytes(); assert sha(original)==OLD_SHA, 'Quest preimage drift'
        # The retained old script reverses race425 on signal20261011 and on spawn.
        assert b'$signal == 20261011' in original and b'race => 127' in original and b'gender => 0' in original
        OUT.mkdir(mode=0o700)
        for name,data in [('original.pl',original),('candidate.pl',candidate)]:
            with (OUT/name).open('xb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
        restore_locked=locked; expected=candidate; signal_id=20261022
    elif action=='rollback':
        original=(OUT/'original.pl').read_bytes(); assert sha(original)==OLD_SHA
        assert QUEST.read_bytes() in (candidate,original), 'Unrelated quest mutation'
        restore_locked=json.loads((OUT/'apply-started.json').read_text())['restore_locked']
        expected=original; signal_id=20261011
    else: raise ValueError(action)
    start=OUT/(action+'-started.json')
    start_record={'commit':commit,'before':before,'restore_locked':restore_locked,'target_sha256':sha(expected)}
    if start.exists():
        assert action=='rollback' and not start.is_symlink(), 'Operation already attempted'
        assert json.loads(start.read_text())==start_record, 'Recovery attempt drift'
    else:
        with start.open('x') as f:
            json.dump(start_record,f,indent=2);f.flush();os.fsync(f.fileno())
    wrote=False
    try:
        if not locked: control('lock')
        assert control('status') is True
        if not paused: pause()
        assert gateway_paused()
        time.sleep(2)
        assert control('count')==0, 'Client entered during admission hold'
        since=datetime.datetime.now(datetime.timezone.utc).isoformat()
        wrote=True
        install(expected); reload(); acknowledgments=verify_reload(since,action)
        assert control('count')==0
        signal(signal_id); verify_reload(since,action)
        assert QUEST.read_bytes()==expected
        inside=game("import hashlib;from pathlib import Path;print(hashlib.sha256(Path('/srv/nightcap/quests/global/999240.pl').read_bytes()).hexdigest())").strip()
        assert inside==sha(expected)
        assert snapshot()==before, 'Service, native lifetime, Keeper or channel drift'
        assert control('count')==0
        unpause()
        if not restore_locked: control('unlock')
        assert not gateway_paused() and control('status')==restore_locked
        assert snapshot()==before
    except BaseException:
        if not wrote:
            if not paused and gateway_paused(): unpause()
            if not locked and control('status'): control('unlock')
        else:
            if not control('status'): control('lock')
            if not gateway_paused(): pause()
        # After a possible write, retain admission hold and backups for explicit recovery.
        raise
    result={'action':action,'commit':commit,'quest_sha256':inside,'quest_reload_acknowledgments':acknowledgments,
            'signal_sent':signal_id,'clients_zero_during_activation':True,'admissions_restored':True,
            'native_services_keeper_channel_unchanged':True,'rendered_acceptance':False,'before':before,'after':snapshot()}
    (OUT/(action+'-result.json')).write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    os.umask(0o077)
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        for f in (lock,gm):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        print(json.dumps(execute(ACTION,base64.b64decode(PAYLOAD),COMMIT)))

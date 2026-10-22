"""Guarded quest-only activation. No database or process lifecycle writes."""
import base64
import datetime
import fcntl
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path('/opt/nightcap/deploy/production')
OUT = Path('/opt/nightcap/backups/dungeon-keeper-visibility-20261022')
QUEST = ROOT / 'data/server/quests/global/Instance_Keeper.pl'
WAYPOINT = QUEST.parent / '999240.pl'
OLD_SHA = '3c22ca3d3e4a1b39b56c018ea97c5daea5abf735b633bf8a389ebb6ae7e8da4d'
WAYPOINT_SHA = 'f8fe9a8783e28b6685104a73769cf083c17ef5c411c9bc616e9fc3a420684e65'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def command(args):
    return subprocess.check_output(args, cwd=ROOT, text=True)

def game(code, *args):
    return command(['docker','compose','exec','-T','game','python3','-c',code,*args])

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
    ids=command(['docker','compose','ps','-q']).split()
    assert len(ids)==5, 'Expected five running services'
    states=[json.loads(line) for line in command(['docker','inspect','--format',
        '{{json .State}}',*ids]).splitlines()]
    assert all(s['Running'] for s in states)
    assert all(s.get('Health',{}).get('Status','healthy')=='healthy' for s in states)
    return {'services': sorted([i,s['StartedAt']] for i,s in zip(ids,states)),
            'native':json.loads(game(PROCESSES)), 'waypoint_sha256':sha(WAYPOINT.read_bytes())}

def install(data):
    info=QUEST.stat()
    temporary=QUEST.with_suffix('.pl.befallen-tmp')
    with temporary.open('xb') as f:
        os.fchmod(f.fileno(),info.st_mode)
        os.fchown(f.fileno(),info.st_uid,info.st_gid)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary,QUEST)

SEND = r'''
import json,socket,struct,sys,time
from pathlib import Path
cfg=json.loads(Path('/srv/nightcap/eqemu_config.json').read_text())['server']['world']
assert cfg['tcp']=={'ip':'127.0.0.1','port':'9001'}
def frame(kind,p):return struct.pack('<IB',len(p),kind)+p
def packet(op,p):return frame(5,struct.pack('<IH',len(p),op)+p)
with socket.create_connection(('127.0.0.1',9001),timeout=5) as s:
 s.sendall(frame(4,b'Zone\0'+cfg['key'].encode()+b'\0'))
 if sys.argv[1]=='reload':
  s.sendall(packet(0x4100,struct.pack('<i?3xqiI',22,False,0,0,0)))
 elif sys.argv[1]=='signal':
  for npc_id in (999228,999230,999232,999233):
   s.sendall(packet(0x4506,struct.pack('<Bii64s',6,npc_id,20261022,b'')))
 else:raise ValueError(sys.argv[1])
 time.sleep(1)
'''

def reload():
    game(SEND,'reload')

def signal():
    game(SEND,'signal')

def verify_reload(since):
    for attempt in range(20):
        logs=command(['docker','compose','logs','--no-color','--since',since,'game'])
        if logs.count('Reloaded [Quest] (22)')>=12:
            break
        time.sleep(1)
    (OUT / 'reload.log').write_text(logs)
    count=logs.count('Reloaded [Quest] (22)')
    assert count>=12, f'Incomplete quest reload acknowledgments: {count}'
    errors=[line for line in logs.splitlines() if any(s in line.lower() for s in
        ('quest error','perl error','error compiling','syntax error','failed to compile'))]
    assert not errors, 'Quest errors found; inspect private reload.log'
    return count

def execute(action,candidate,recovery,commit):
    before=snapshot()
    assert before['waypoint_sha256']==WAYPOINT_SHA, 'Waypoint drift'
    current=QUEST.read_bytes()
    if action=='apply':
        assert sha(current)==OLD_SHA, 'Keeper drift'
        OUT.mkdir(mode=0o700)
        for name,data in [('original.pl',current),('candidate.pl',candidate),('recovery.pl',recovery)]:
            (OUT/name).write_bytes(data)
        expected=candidate
    elif action=='rollback':
        assert sha((OUT/'original.pl').read_bytes())==OLD_SHA
        assert current==(OUT/'candidate.pl').read_bytes(), 'Not the retained candidate'
        assert recovery==(OUT/'recovery.pl').read_bytes(), 'Recovery drift'
        expected=recovery
    else:
        raise ValueError(action)
    start=OUT/(action+'-started.json')
    with start.open('x') as f:
        json.dump({'commit':commit,'before':before,'target_sha256':sha(expected)},f,indent=2)
    since=datetime.datetime.now(datetime.timezone.utc).isoformat()
    install(expected)
    reload()
    acknowledgments=verify_reload(since)
    signal()
    verify_reload(since)
    assert QUEST.read_bytes()==expected
    inside=game("import hashlib;from pathlib import Path;print(hashlib.sha256(Path('/srv/nightcap/quests/global/Instance_Keeper.pl').read_bytes()).hexdigest())").strip()
    assert inside==sha(expected), 'Container quest differs'
    after=snapshot()
    assert before==after, 'Service, process lifetime or waypoint changed'
    result={'action':action,'commit':commit,'quest_sha256':inside,
            'quest_reload_acknowledgments':acknowledgments,'signal_sent':20261022,
            'native_lifetimes_services_waypoint_unchanged':True,
            'rendered_acceptance':False,'before':before,'after':after}
    (OUT/(action+'-result.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return result

if __name__=='__main__':
    os.umask(0o077)
    with (ROOT/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock','a') as gm:
        for f in (lock,gm):
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        execute(ACTION,base64.b64decode(PAYLOAD),base64.b64decode(RECOVERY),COMMIT)

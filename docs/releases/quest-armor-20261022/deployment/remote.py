"""Pinned eleven-file deployment and authorized offline three-piece repair."""
import base64
import datetime
import hashlib
import fcntl
import json
import mmap
import os
import stat
import struct
import subprocess
import time
from pathlib import Path

ROOT = Path('/opt/nightcap/deploy/production')
QUESTS = ROOT/'data/server/quests'
OUT = Path('/opt/nightcap/backups/quest-armor-20261022')
PAIRS = {7: (4176,604176),17: (4174,604174),19: (4180,604180)}


def command(args):
    return subprocess.check_output(args,cwd=ROOT,text=True,timeout=40)


def game(code,*args):
    return command(['docker','compose','exec','-T','game','python3','-c',code,*args])


def control(action):
    return json.loads(game(CONTROL,action))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sql(query):
    return subprocess.check_output(['docker','compose','exec','-T','db','mariadb',
        '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw',
        '--skip-column-names','--default-character-set=utf8mb4','peq'],
        cwd=ROOT,input=query,text=True,timeout=40)


def save(name,data):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())


def gateway_paused():
    return json.loads(command(['docker','inspect','--format','{{json .State.Paused}}',
        command(['docker','compose','ps','-aq','gateway']).strip()]))


def pause(value):
    command(['docker','pause' if value else 'unpause',
             command(['docker','compose','ps','-aq','gateway']).strip()])


PROCESSES = r'''
import json
from pathlib import Path
rows=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   name=(p/'comm').read_text().strip()
   if name in ('world','zone'):
    assert (p/'cwd').resolve()==Path('/srv/nightcap'), 'Unexpected native cwd'
    rows.append([name,int(p.name),(p/'stat').read_text().rsplit(')',1)[1].split()[19]])
  except FileNotFoundError:pass
assert sum(r[0]=='world' for r in rows)==1
assert sum(r[0]=='zone' for r in rows)==12
print(json.dumps(sorted(rows)))
'''


def snapshot():
    ids=command(['docker','compose','ps','-aq']).split()
    assert len(ids)==5
    rows=json.loads(command(['docker','inspect',*ids]))
    assert all(r['State']['Running'] and not r['State'].get('OOMKilled') for r in rows)
    assert all(r['State'].get('Health',{}).get('Status','healthy')=='healthy' for r in rows)
    return {'services':sorted([r['Id'],r['Image'],r['RestartCount'],r['State']['StartedAt']] for r in rows),
            'native':json.loads(game(PROCESSES)),
            'cache_sha256':sha((ROOT/'data/server/shared/items').read_bytes()),
            'channel_sha256':sha((ROOT/'data/public/channel.json').read_bytes())}


def probe():
    config=json.loads(game("import json;from pathlib import Path;c=json.loads(Path('/srv/nightcap/eqemu_config.json').read_text())['server'];print(json.dumps({'directories':c.get('directories',{}),'paths':c.get('paths',{}),'quest_paths':c.get('quest_paths',[])}))"))
    directories=config['directories']
    assert directories.get('quests','quests/').rstrip('/')=='quests'
    assert not directories.get('quest_paths'), 'Additional configured quest roots'
    cache=ROOT/'data/server/shared/items'
    rows=[]
    with cache.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as b:
        payload,count,maximum,current=struct.unpack_from('<IIII',b)
        assert maximum==current and len(b)==payload+8==20+4*count+1332*current, 'Cache layout drift'
        for target in DATA['targets']:
            item=target['id']; assert item<count
            index=struct.unpack_from('<I',b,16+4*item)[0]; assert index<current
            start=16+4*count+1332*index
            assert struct.unpack_from('<I',b,start+440)[0]==item, 'Cache identity drift'
            name=bytes(b[start+265:start+329]).split(b'\0',1)[0].decode()
            assert name==target['Name'], (item,name,'Cache name mismatch')
            rows.append({'id':item,'name':name})
        cache_sha=sha(b)
    scripts={}
    precedence={}
    for entry in DATA['scripts']:
        path=QUESTS/entry['path']
        assert not path.is_symlink() and stat.S_ISREG(path.stat().st_mode)
        candidate=base64.b64decode(entry['payload'])
        assert sha(candidate)==entry['after_sha256'], 'Candidate drift'
        scripts[entry['path']]=sha(path.read_bytes())
        assert scripts[entry['path']] in (entry['before_sha256'],entry['after_sha256']), 'Quest drift'
        # Check every existing version directory, so an active version cannot hide an override.
        zone=path.parent; stem=path.stem
        stems={stem}
        for npc in DATA['npcs']:
            if npc['name']==stem: stems.update((str(npc['id']),stem+'_'+str(npc['id'])))
        found={str(p.relative_to(QUESTS)) for directory in [zone,QUESTS/'global',*zone.glob('v*')]
               if directory.is_dir() for name in stems for ext in ('.pl','.lua')
               if (p:=directory/(name+ext)).is_file()}
        assert found=={entry['path']}, ('Quest precedence drift',sorted(found))
        precedence[entry['path']]=sorted(found)
    inside=json.loads(game("import hashlib,json,sys;from pathlib import Path;print(json.dumps({p:hashlib.sha256((Path('/srv/nightcap/quests')/p).read_bytes()).hexdigest() for p in json.loads(sys.argv[1])}))",json.dumps(list(scripts))))
    assert inside==scripts, 'Container quest mount drift'
    return {'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'clients':control('count'),'world_locked':control('status'),'config':config,
            'cache_sha256':cache_sha,'cache_targets':rows,'scripts':scripts,'precedence':precedence}


def install(entry,data):
    path=QUESTS/entry['path']; info=path.stat()
    temporary=path.with_name(path.name+'.quest-armor-partial')
    assert not path.is_symlink() and not temporary.is_symlink()
    if temporary.exists():
        assert stat.S_ISREG(temporary.stat().st_mode)
        partial=temporary.read_bytes()
        original=(OUT/'originals'/entry['path']).read_bytes()
        candidate=base64.b64decode(entry['payload'])
        assert sha(original)==entry['before_sha256']
        assert original.startswith(partial) or candidate.startswith(partial), 'Foreign partial'
        temporary.unlink()
    with temporary.open('xb') as f:
        os.fchmod(f.fileno(),info.st_mode);os.fchown(f.fileno(),info.st_uid,info.st_gid)
        f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(temporary,path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


SEND = r'''
import json,socket,struct,time
from pathlib import Path
cfg=json.loads(Path('/srv/nightcap/eqemu_config.json').read_text())['server']['world']
assert cfg['tcp']=={'ip':'127.0.0.1','port':'9001'}
def frame(kind,p):return struct.pack('<IB',len(p),kind)+p
with socket.create_connection(('127.0.0.1',9001),timeout=5) as s:
 s.sendall(frame(4,b'Zone\0'+cfg['key'].encode()+b'\0'))
 p=struct.pack('<i?3xqiI',22,False,0,0,0)
 s.sendall(frame(5,struct.pack('<IH',len(p),0x4100)+p))
 time.sleep(1)
'''


def reload_quests(action):
    since=datetime.datetime.now(datetime.timezone.utc).isoformat()
    game(SEND)
    for attempt in range(20):
        logs=command(['docker','compose','logs','--no-color','--since',since,'game'])
        if logs.count('Reloaded [Quest] (22)')>=12:break
        time.sleep(1)
    (OUT/(action+'-reload.log')).write_text(logs)
    lines=[line for line in logs.splitlines() if 'Reloaded [Quest] (22)' in line]
    assert len(lines)==12, 'Need twelve quest reload acknowledgments'
    assert not any(s in logs.lower() for s in ('quest error','perl error','error compiling','syntax error','failed to compile'))
    return {'acknowledgments':len(lines),'lines':lines}


def inventory():
    columns=[line.split('\t')[0] for line in sql('SHOW COLUMNS FROM inventory;').splitlines()]
    assert {'character_id','slot_id','item_id'}.issubset(columns)
    expression='JSON_OBJECT('+','.join("'%s',`%s`"%(c,c) for c in columns)+')'
    rows=[json.loads(line) for line in sql('SELECT '+expression+' FROM inventory WHERE character_id=29 ORDER BY slot_id;').splitlines()]
    return columns,rows


def literal(value):
    if value is None:return 'NULL'
    if isinstance(value,(int,float)):return str(value)
    assert isinstance(value,str)
    return "CONVERT(0x"+value.encode('utf-8').hex()+" USING utf8mb4)" if value else "''"


def equal_field(name,value):
    column='`'+name+'`'
    if isinstance(value,str):return 'BINARY '+column+' <=> BINARY '+literal(value)
    return column+' <=> '+literal(value)


def repair():
    assert control('count')==0 and gateway_paused() and control('status') is True
    character=sql("SELECT id,name FROM character_data WHERE id=29 AND BINARY name='Palwar';").strip()
    assert character=='29\tPalwar', 'Character identity drift'
    assert sql("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='inventory';").strip()=='InnoDB'
    columns,before=inventory()
    time.sleep(2)
    assert inventory()==(columns,before), 'Inventory still saving'
    selected={r['slot_id']:r for r in before if r['slot_id'] in PAIRS}
    assert set(selected)==set(PAIRS)
    for slot,(old,new) in PAIRS.items():assert selected[slot]['item_id']==old, 'Piece moved/replaced/already repaired'
    save('palwar-before-private.json',{'columns':columns,'rows':before})
    expected=[{**r,'item_id':PAIRS[r['slot_id']][1]} if r['slot_id'] in PAIRS else r for r in before]
    conditions=[]
    for row in selected.values():
        conditions.append('('+' AND '.join(equal_field(c,row[c]) for c in columns)+')')
    guard=' OR '.join(conditions)
    cases=' '.join('WHEN '+str(slot)+' THEN '+str(new) for slot,(old,new) in PAIRS.items())
    query='''DELIMITER //
BEGIN NOT ATOMIC
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 UPDATE inventory SET item_id=CASE slot_id '''+cases+''' END WHERE '''+guard+''';
 IF ROW_COUNT() <> 3 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Palwar full-row preimage mismatch'; END IF;
 COMMIT;
END//
DELIMITER ;
'''
    assert control('count')==0
    save('palwar-write-started.json',{'before_sha256':sha(json.dumps(before,sort_keys=True).encode()),'slots':sorted(PAIRS)})
    try:
        sql(query)
    except BaseException as error:
        # A killed docker/SSH client does not prove its MariaDB session ended.
        # Never reopen from a stale pre-commit read while that session may finish.
        save('palwar-sql-uncertain.json',{'error_type':type(error).__name__,
            'requires':'Verify the original DB session is terminal before any admission release.'})
        raise
    save('palwar-sql-returned.json',{'client_exited_successfully':True})
    after_columns,after=inventory()
    assert after_columns==columns and after==expected, 'Inventory afterimage mismatch; inspect, never replay'
    assert control('count')==0
    save('palwar-after-private.json',{'columns':columns,'rows':after})
    report={'character':'Palwar','character_id':29,'offline_clients':0,'rows_changed':3,
            'only_item_id_changed':True,'all_other_inventory_rows_unchanged':True,
            'items':[{'slot':slot,'before':old,'after':new} for slot,(old,new) in PAIRS.items()]}
    save('palwar-result.json',report)
    return report


def reconcile_repair():
    """Resolve an uncertain commit without restoring any saved player state."""
    if not (OUT/'palwar-write-started.json').exists():
        return {'state':'no inventory write attempted','player_state_restored':False}
    assert not (OUT/'palwar-sql-uncertain.json').exists(), 'SQL session termination unproven; retain admission hold'
    assert (OUT/'palwar-sql-returned.json').exists(), 'SQL completion marker missing; retain admission hold'
    retained=json.loads((OUT/'palwar-before-private.json').read_text())
    started=json.loads((OUT/'palwar-write-started.json').read_text())
    assert sha(json.dumps(retained['rows'],sort_keys=True).encode())==started['before_sha256'], 'Private inventory preimage drift'
    expected=[{**r,'item_id':PAIRS[r['slot_id']][1]} if r['slot_id'] in PAIRS else r for r in retained['rows']]
    columns,current=inventory()
    assert columns==retained['columns'], 'Inventory schema changed during hold'
    assert current in (retained['rows'],expected), 'Unresolved inventory attempt; retain admission hold'
    report={'state':'committed exactly' if current==expected else 'not committed',
            'player_state_restored':False,'only_expected_inventory_state':True}
    # A recovery retry may repeat this read-only classification.
    (OUT/'palwar-reconciliation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def retain_hold():
    """Hold ingress first, even if the world control endpoint has failed."""
    report={}
    for name,action in [('gateway',lambda:pause(True)),('world',lambda:control('lock'))]:
        try:action()
        except BaseException as error:report[name+'_error']=str(error)[:500]
    for name,read in [('gateway_paused',gateway_paused),('world_locked',lambda:control('status'))]:
        try:report[name]=read()
        except BaseException:report[name]='unknown'
    try:(OUT/'held-after-error.json').write_text(json.dumps(report,indent=2)+'\n')
    except BaseException:pass
    return report


def execute(action):
    assert not (ROOT/'private/gm-maintenance.json').exists(), 'GM maintenance active'
    before=snapshot();preflight=probe()
    if action=='verify':return {'snapshot':before,'probe':preflight}
    assert preflight['clients']==0, 'Clients must fully exit'
    paused=gateway_paused();locked=preflight['world_locked']
    assert action in ('apply','rollback')
    if action=='apply':
        assert not paused, 'Existing admission hold'
        assert all(preflight['scripts'][e['path']]==e['before_sha256'] for e in DATA['scripts'])
        OUT.mkdir(mode=0o700)
        for e in DATA['scripts']:
            p=OUT/'originals'/e['path'];p.parent.mkdir(parents=True,exist_ok=True)
            original=(QUESTS/e['path']).read_bytes()
            assert sha(original)==e['before_sha256'], 'Backup preimage drift'
            with p.open('xb') as f:f.write(original);f.flush();os.fsync(f.fileno())
            assert sha(p.read_bytes())==e['before_sha256']
        save('apply-started.json',{'commit':DATA['commit'],'before':before,'restore_locked':locked})
        restore_locked=locked
    else:
        started=json.loads((OUT/'apply-started.json').read_text())
        assert before==started['before'], 'Recovery runtime differs from original admission hold'
        restore_locked=started['restore_locked']
        for e in DATA['scripts']:assert sha((OUT/'originals'/e['path']).read_bytes())==e['before_sha256']
    wrote=False
    try:
        if not locked:control('lock')
        assert control('status') is True
        if not paused:pause(True)
        assert gateway_paused()
        time.sleep(2)
        assert control('count')==0, 'Client entered during hold'
        wrote=True
        for e in DATA['scripts']:
            data=base64.b64decode(e['payload']) if action=='apply' else (OUT/'originals'/e['path']).read_bytes()
            install(e,data)
        reload_report=reload_quests(action)
        assert control('count')==0
        after_probe=probe()
        assert all(after_probe['scripts'][e['path']]==e['after_sha256' if action=='apply' else 'before_sha256'] for e in DATA['scripts'])
        assert snapshot()==before, 'Runtime/service/cache/client drift'
        repair_report=repair() if action=='apply' else reconcile_repair()
        assert snapshot()==before and control('count')==0
        save(action+'-verified.json',{'reload':reload_report,'palwar':repair_report})
        pause(False)
        if not restore_locked:control('unlock')
        assert not gateway_paused() and control('status')==restore_locked
        assert snapshot()==before
    except BaseException:
        if not wrote:
            if not paused and gateway_paused():pause(False)
            if not locked and control('status'):control('unlock')
        else:
            retain_hold()
        raise
    report={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'action':action,'commit':DATA['commit'],'scripts':after_probe['scripts'],
            'targets_in_cache':len(after_probe['cache_targets']),'reload':reload_report,
            'palwar':repair_report,'admissions_restored':True,'before':before,'after':snapshot()}
    save(action+'-result.json',report)
    return report


if __name__=='__main__':
    os.umask(0o077)
    if ACTION=='probe':print(json.dumps(probe()))
    else:
        with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
            for f in (lock,gm):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
            print(json.dumps(execute(ACTION)))

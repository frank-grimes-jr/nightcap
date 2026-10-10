"""Run via SSH on OVH. SQL, read-only status helper and commit supplied by runner."""
import copy
import atexit
import datetime
import fcntl
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT=Path('/opt/nightcap/deploy/production')
OUT=Path('/opt/nightcap/backups/crushbone-waypoint-entrance-20261009')
COMPOSE=['docker','compose']
DB=COMPOSE+['exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq']
SCOPES={'nightcap_waypoints':'1=1','spawn2':"zone='crushbone'",'zone_state_spawns':'zone_id=58'}
maintenance=False
writes_started=False
before=None
expected=None

def run(args,**kw):
    return subprocess.run(args,cwd=ROOT,check=True,capture_output=True,text=True,**kw).stdout
def sql(query):return run(DB,input=query)
def save(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2)+'\n')
def status():
    source="ACTION='status'\n"+STATUS_SOURCE
    return json.loads(run(COMPOSE+['exec','-T','game','python3','-'],input=source))['after']
def services():
    return [{k:r.get(k) for k in ('Service','State','Health')} for r in map(json.loads,run(COMPOSE+['ps','--all','--format','json']).splitlines())]
def restore_services(expected_state):
    run(COMPOSE+['start','game'])
    for _ in range(55):
        health=services()
        if all(s['Health']=='healthy' for s in health if s['Service'] in ('game','db')):break
        time.sleep(1)
    else:raise RuntimeError('Game health not ready; gateway kept closed')
    assert len([r for r in status() if r['pid']])==12,'Expected 12 native zone workers'
    if expected_state is not None:
        assert canonical(snapshot(queries))==expected_state,'Post-recovery-start database drift; keep gateway closed'
    run(COMPOSE+['start','gateway'])
def recover_on_exit():
    if not maintenance:return
    try:
        current=canonical(snapshot(queries)) if writes_started else None
        known=not writes_started or current==before or current==expected
        if not known:
            print('Database outcome differs from both complete snapshots; gateway remains closed.',flush=True)
            return
        restore_services(current)
        save('failure-recovery.json',{'services_restored':True,'database':'original' if not writes_started or current==before else 'relocated','services':services()})
        print('Known complete database state verified; services recovered after failed operation.',flush=True)
    except Exception as error:
        print('Recovery requires inspection: '+str(error),flush=True)
atexit.register(recover_on_exit)
def json_query(table,where):
    columns=[line.split('\t')[0] for line in sql('SHOW COLUMNS FROM '+table+';').splitlines()]
    pairs=','.join("'%s',`%s`"%(c,c) for c in columns)
    return 'SELECT JSON_OBJECT('+pairs+') FROM '+table+' WHERE '+where+' ORDER BY 1;'
def snapshot(queries):
    return {t:[json.loads(line) for line in sql(q).splitlines()] for t,q in queries.items()}
def canonical(data):
    return {t:sorted(rows,key=lambda r:json.dumps(r,sort_keys=True)) for t,rows in data.items()}
def marker(r):
    return r['zone_id']==58 and r['instance_id']==0 and r['is_corpse']==0 and r['is_zone']==0 and r['npc_id'] in (0,999240) and r['spawn2_id']==3266061 and r['spawngroup_id']==999240
def guard():
    return '''CREATE TEMPORARY TABLE waypoint_guard(ok INT NOT NULL CHECK(ok=1)) ENGINE=MEMORY;
START TRANSACTION;
SELECT id FROM spawn2 WHERE zone='crushbone' FOR UPDATE;
SELECT zone FROM nightcap_waypoints FOR UPDATE;
SELECT id FROM zone_state_spawns WHERE zone_id=58 FOR UPDATE;
INSERT INTO waypoint_guard SELECT COUNT(*)=1 FROM nightcap_waypoints
 WHERE zone='crushbone' AND zone_id=58 AND x=610 AND y=292 AND z=2 AND heading=0 AND is_dungeon=0;
INSERT INTO waypoint_guard SELECT COUNT(*)=1 FROM spawn2
 WHERE id=3266061 AND spawngroupID=999240 AND zone='crushbone' AND version=0 AND x=610 AND y=292 AND z=2 AND heading=0;
INSERT INTO waypoint_guard SELECT COUNT(*)=1 FROM zone
 WHERE short_name='crushbone' AND version=0 AND safe_x=158 AND safe_y=-644 AND safe_z=4 AND safe_heading=0;
'''
def read_snapshot_output(output):
    rows=[json.loads(line) for line in output.splitlines() if line.startswith('{')]
    result={t:[] for t in SCOPES}
    for row in rows:result[row['table']].append(row['row'])
    return canonical(result)
def emit_snapshot(queries):
    result=[]
    for t,q in queries.items():
        expr=q.split('SELECT ',1)[1].split(' FROM ',1)[0]
        result.append(q.replace('SELECT '+expr,"SELECT JSON_OBJECT('table','"+t+"','row',"+expr+")",1))
    return '\n'.join(result)

os.umask(0o077)
# Keep the flock handle alive through atexit recovery on every failure path.
lock = (ROOT/'.deployment.lock').open('a')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not OUT.exists(),'Existing evidence: inspect result before retrying'
assert all(r['players']==0 for r in status()),'Players are online; abort before maintenance'
assert all(s['State']=='running' for s in services()),'Unexpected initial service state'
OUT.mkdir(mode=0o700)
save('services-before.json',services())
for name,value in [('forward.sql',FORWARD),('rollback-durable.sql',ROLLBACK),('world-status.py',STATUS_SOURCE)]:
    (OUT/name).write_text(value)
for table in SCOPES:
    assert sql("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='"+table+"';").strip()=='InnoDB'
maintenance=True
run(COMPOSE+['stop','-t','15','gateway'])
if any(r['players'] for r in status()):
    run(COMPOSE+['start','gateway'])
    raise RuntimeError('Player arrived during gate closure; aborted')
shutdown_status=status()
since=datetime.datetime.now(datetime.timezone.utc).isoformat()
stop_started=time.monotonic()
run(COMPOSE+['stop','-t','90','game'])
stop_elapsed=time.monotonic()-stop_started
assert next(s for s in services() if s['Service']=='game')['State']=='exited'
game_id=run(COMPOSE+['ps','--all','-q','game']).strip()
stopped=json.loads(run(['docker','inspect','--format','{{json .State}}',game_id]))
save('game-stopped.json',stopped)
assert stopped['ExitCode']==0 and not stopped['OOMKilled'] and not stopped['Error'],'Game did not stop cleanly; do not migrate'
# start.py force-kills remaining children only after 75 seconds. Refuse that path.
assert stop_elapsed<70,'Native children approached supervisor kill deadline; do not migrate'
shutdown_logs=run(COMPOSE+['logs','--no-color','--since',since,'game'])
(OUT/'shutdown.log').write_text(shutdown_logs)
for row in shutdown_status:
    if row['pid'] and row['zone']:
        zone_name=row['zone'].split(' (',1)[0]
        assert 'Zone ['+zone_name+'] zone_id [' in shutdown_logs,'Missing native unload log for '+zone_name
save('shutdown-verification.json',{'seconds':stop_elapsed,'clean_exit':True,'native_unload_logs_verified':True})
print('Game and gateway stopped cleanly; database remains online.',flush=True)
dump=COMPOSE+['exec','-T','db','mariadb-dump','--defaults-extra-file=/run/secrets/db_backup_config','--single-transaction','--routines','--triggers','--events','--hex-blob','peq']
with (OUT/'peq-before.sql.gz').open('xb') as dest:
    p=subprocess.Popen(dump,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    with gzip.GzipFile(fileobj=dest,mode='wb') as zipped:shutil.copyfileobj(p.stdout,zipped)
    p.stdout.close()
    error=p.stderr.read()
    assert p.wait()==0,error.decode()
with gzip.open(OUT/'peq-before.sql.gz','rb') as src:
    size=sum(len(c) for c in iter(lambda:src.read(1024*1024),b''))
assert size>100_000_000
with (OUT/'peq-before.sql.gz').open('rb') as src:backup_sha=hashlib.file_digest(src,'sha256').hexdigest()
print('Full PEQ backup verified.',flush=True)
queries={t:json_query(t,w) for t,w in SCOPES.items()}
before=canonical(snapshot(queries))
save('before.json',before)
expected=copy.deepcopy(before)
wp=[r for r in expected['nightcap_waypoints'] if r['zone']=='crushbone']
spawn=[r for r in expected['spawn2'] if r['id']==3266061]
assert len(wp)==len(spawn)==1
for r in wp+spawn:
    assert (r['x'],r['y'],r['z'],r['heading'])==(610,292,2,0)
    r.update(x=158,y=-644,z=4,heading=0)
assert wp[0]['is_dungeon']==0
wp[0]['is_dungeon']=1
states=[r for r in expected['zone_state_spawns'] if marker(r)]
assert len(states)<=2,'Unexpected duplicate saved marker states'
state_restore=[]
for r in states:
    state_restore.append('UPDATE zone_state_spawns SET x={x},y={y},z={z},heading={heading} WHERE id={id} AND zone_id=58 AND instance_id=0 AND is_corpse=0 AND spawn2_id=3266061;'.format(**r))
    r.update(x=158,y=-644,z=4,heading=0)
inverse_guards='''INSERT INTO waypoint_guard SELECT COUNT(*)=1 FROM nightcap_waypoints WHERE zone='crushbone' AND zone_id=58 AND x=158 AND y=-644 AND z=4 AND heading=0 AND is_dungeon=1;
INSERT INTO waypoint_guard SELECT COUNT(*)=1 FROM spawn2 WHERE id=3266061 AND spawngroupID=999240 AND zone='crushbone' AND version=0 AND x=158 AND y=-644 AND z=4 AND heading=0;
'''
for r in states:
    inverse_guards+='INSERT INTO waypoint_guard SELECT COUNT(*)=1 FROM zone_state_spawns WHERE id={id} AND zone_id=58 AND instance_id=0 AND is_corpse=0 AND is_zone=0 AND npc_id={npc_id} AND spawn2_id=3266061 AND spawngroup_id=999240 AND x=158 AND y=-644 AND z=4 AND heading=0;\n'.format(**r)
inverse=inverse_guards+ROLLBACK+'\n'+'\n'.join(state_restore)
inverse_start=guard().split('INSERT INTO waypoint_guard',1)[0]
(OUT/'rollback-exact.sql').write_text(inverse_start+inverse+'COMMIT;\n')
expected=canonical(expected)
emits=emit_snapshot(queries)
writes_started=True
forward_output=sql(guard()+FORWARD+emits+'ROLLBACK;')
assert read_snapshot_output(forward_output)==expected,'Forward rehearsal mismatch'
assert canonical(snapshot(queries))==before,'Forward rehearsal persisted changes'
inverse_output=sql(guard()+FORWARD+inverse+emits+'ROLLBACK;')
assert read_snapshot_output(inverse_output)==before,'Inverse rehearsal mismatch'
assert canonical(snapshot(queries))==before
# Prove the SQL guard aborts and rolls back the connection on a stale row.
try:
    sql(guard().replace('INSERT INTO waypoint_guard SELECT COUNT(*)=1 FROM nightcap_waypoints',"UPDATE nightcap_waypoints SET x=611 WHERE zone='crushbone';\nINSERT INTO waypoint_guard SELECT COUNT(*)=1 FROM nightcap_waypoints",1)+FORWARD+'COMMIT;')
except subprocess.CalledProcessError as e:
    assert 'CONSTRAINT' in e.stderr.upper(),e.stderr
else:raise AssertionError('Stale preimage guard failed')
assert canonical(snapshot(queries))==before
print('Forward, exact inverse and stale-preimage rollback rehearsals passed.',flush=True)
result={'commit':COMMIT,'backup_directory':str(OUT),'backup_sha256':backup_sha,'uncompressed_bytes':size,'rehearsals_passed':3,'saved_marker_rows':len(states),'state':'ready'}
save('result.json',result)
sql(guard()+FORWARD+'COMMIT;')
after=canonical(snapshot(queries))
assert after==expected,'Committed snapshot mismatch; keep gateway closed'
save('after.json',after)
result['state']='database_committed'
save('result.json',result)
run(COMPOSE+['start','game'])
for _ in range(55):
    health=services()
    if all(s['Health']=='healthy' for s in health if s['Service'] in ('game','db')):break
    time.sleep(1)
else:raise RuntimeError('Game health not ready; gateway kept closed')
runtime=status()
assert len([r for r in runtime if r['pid']])==12,'Expected 12 native zone workers'
assert canonical(snapshot(queries))==expected,'Post-start placement/state mismatch'
run(COMPOSE+['start','gateway'])
maintenance=False
result.update(state='deployed',services=services(),zone_workers=12,all_scoped_rows_match=True)
save('result.json',result)
print(json.dumps(result),flush=True)

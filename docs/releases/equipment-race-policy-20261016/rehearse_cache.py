"""Exercise old/new/rollback native loaders against a disposable local content DB."""
import json
from pathlib import Path
import secrets
import subprocess
import uuid

HERE=Path(__file__).resolve().parent
DB='nightcap_race_'+uuid.uuid4().hex[:12]
USER='nr_'+uuid.uuid4().hex[:12]
PASSWORD=secrets.token_hex(24)
CONTAINER='akk-stack-eqemu-server-1'
BASE='/tmp/nightcap-divine-summons-build-20261013'
BUILD='/tmp/nightcap-equipment-race-build-20261016-r3'
RUNTIME='/tmp/'+DB
MYSQL=['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
       'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb --user=root --batch --raw --skip-column-names']

def sql(statement):
    p=subprocess.run(MYSQL,input=statement,text=True,capture_output=True,timeout=240)
    if p.returncode:raise RuntimeError('Disposable DB operation failed; credentials withheld')
    return p.stdout

def remote(script):
    p=subprocess.run(['docker','exec','-i',CONTAINER,'python3','-'],input=script,text=True,capture_output=True,timeout=240)
    if p.returncode:raise RuntimeError(p.stderr)
    return p.stdout

created=user_created=False
try:
    sql('CREATE DATABASE '+DB+';');created=True
    for table in ('items','rule_sets','rule_values','variables','logsys_categories','content_flags','zone'):
        sql(f'CREATE TABLE {DB}.{table} LIKE peq.{table}; INSERT INTO {DB}.{table} SELECT * FROM peq.{table};')
    sql(f'CREATE TABLE {DB}.instance_list LIKE peq.instance_list;')
    sql(f"CREATE USER '{USER}'@'%' IDENTIFIED BY '{PASSWORD}';");user_created=True
    sql(f"GRANT ALL ON {DB}.* TO '{USER}'@'%';")
    sql(f"UPDATE {DB}.rule_values SET rule_value='true' WHERE ruleset_id=1 AND rule_name='Items:FreeTrade';")
    print('Disposable content snapshot ready.',flush=True)
    prelude=f'RUNTIME={RUNTIME!r}\nBUILD={BUILD!r}\nBASE={BASE!r}\nDB={DB!r}\nUSER={USER!r}\nPASSWORD={PASSWORD!r}\n'
    remote(prelude+'''
import json
from pathlib import Path
r=Path(RUNTIME);r.mkdir(mode=0o700);(r/'shared').mkdir();(r/'logs').mkdir()
cfg=json.loads(Path('/home/eqemu/server/eqemu_config.json').read_text())
db=cfg['server']['database'];db.update(db=DB,username=USER,password=PASSWORD)
cfg['server']['content_database']=dict(db)
cfg['server'].setdefault('directories',{}).update(shared_memory=str(r/'shared')+'/',logs=str(r/'logs')+'/')
p=r/'eqemu_config.json';p.write_text(json.dumps(cfg));p.chmod(0o600)
''')
    subprocess.run(['docker','cp',str(HERE/'cache_check.py'),CONTAINER+':'+RUNTIME+'/cache_check.py'],check=True)
    results=[]
    for enabled in (False,True,False):
        script='''
import hashlib,json,os,subprocess,sys
from pathlib import Path
r=Path(RUNTIME);sys.path.insert(0,str(r));import cache_check
loader=Path(BUILD+'/shared_memory' if ENABLED else BASE+'/shared_memory')
m=json.loads(Path(BUILD+'/manifest.json').read_text())
assert hashlib.sha256(loader.read_bytes()).hexdigest()==m['loader_sha256' if ENABLED else 'base_loader_sha256']
with (r/'loader.log').open('w') as log:
 p=subprocess.run([str(loader),'items'],cwd=r,stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0,'Native loader failed; private log retained'
log=(r/'loader.log').read_text()
assert not any(x in log for x in ('Unknown column','SQL syntax','Unable to connect',"doesn't exist"))
cfg=json.loads((r/'eqemu_config.json').read_text())['server']['database']
env=dict(os.environ,MYSQL_PWD=cfg['password'])
ids=subprocess.check_output(['mariadb','-h',cfg['host'],'-P',str(cfg.get('port',3306)),'-u',cfg['username'],'--batch','--skip-column-names',DB,'-e','SELECT id,itemclass,classes,races,slots,augtype FROM items ORDER BY id'],env=env,text=True)
result=cache_check.verify(r/'shared/items',[list(map(int,line.split())) for line in ids.splitlines()],m,ENABLED)
result['loader_sha256']=hashlib.sha256(loader.read_bytes()).hexdigest()
print(json.dumps(result))
'''
        results.append(json.loads(remote(prelude+f'ENABLED={enabled!r}\n'+script)))
        print('Native cache verified: '+str(enabled),flush=True)
    assert results[0]['cache_sha256']==results[2]['cache_sha256'],'Rollback cache differs'
    assert len({r['preserved_fields_sha256'] for r in results})==1,'Unrelated cache bytes changed'
    result=dict(status='passed',scope='Disposable local content, real old/new/rollback loaders; not production acceptance',passes=results)
    (HERE/'cache-rehearsal.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
finally:
    if user_created:sql(f"DROP USER '{USER}'@'%';")
    if created:sql('DROP DATABASE '+DB+';')
    remote(f'from pathlib import Path\np=Path({RUNTIME!r})/"eqemu_config.json"\np.unlink(missing_ok=True)\n')

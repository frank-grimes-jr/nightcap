"""Check the real shared-memory loader against an owned disposable catalog copy."""
import json,secrets,subprocess,uuid
from pathlib import Path
OUT=Path(__file__).parent
DB='nightcap_free_trade_'+uuid.uuid4().hex[:12]
USER='ft_'+uuid.uuid4().hex[:12]
PASSWORD=secrets.token_hex(24)
CONTAINER='akk-stack-eqemu-server-1'
BUILD='/tmp/nightcap-free-trade-build-20261004'
RUNTIME='/tmp/'+DB
MYSQL=['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
       'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb --user=root --batch --raw --skip-column-names']
def sql(q):
    p=subprocess.run(MYSQL,input=q,text=True,capture_output=True,timeout=180)
    if p.returncode:raise RuntimeError('Isolated database operation failed (SQL/private credentials withheld)')
    return p.stdout
def python(code):
    p=subprocess.run(['docker','exec','-i',CONTAINER,'python3','-'],input=code,text=True,capture_output=True,timeout=240)
    if p.returncode:raise RuntimeError('Isolated cache check failed: '+p.stderr)
    return p.stdout
tables=('items','rule_sets','rule_values','variables','logsys_categories','content_flags','zone')
created=False;user_created=False
try:
    sql('CREATE DATABASE '+DB+';');created=True
    for t in tables:
        sql(f'CREATE TABLE {DB}.{t} LIKE peq.{t}; INSERT INTO {DB}.{t} SELECT * FROM peq.{t};')
    sql(f'CREATE TABLE {DB}.instance_list LIKE peq.instance_list;')
    # Never grant or mutate anything in peq; this account owns only the test schema.
    sql(f"CREATE USER '{USER}'@'%' IDENTIFIED BY '{PASSWORD}';");user_created=True
    sql(f"GRANT ALL ON {DB}.* TO '{USER}'@'%';")
    setup='''import json,os,subprocess
from pathlib import Path
r=Path(RUNTIME);r.mkdir(mode=0o700)
(r/'shared').mkdir();(r/'logs').mkdir()
cfg=json.loads(Path('/home/eqemu/server/eqemu_config.json').read_text())
server=cfg['server'];db=server['database'];db.update(db=DB,username=USER,password=PASSWORD)
server['content_database']=dict(db)
server.setdefault('directories',{}).update(shared_memory=str(r/'shared')+'/',logs=str(r/'logs')+'/')
p=r/'eqemu_config.json';p.write_text(json.dumps(cfg));p.chmod(0o600)
source=r/'layout.cpp'
source.write_text('#include "common/item_data.h"\\n#include <cstddef>\\n#include <cstdio>\\nint main(){printf("%zu",sizeof(EQ::ItemData));'+''.join('printf(" %zu",offsetof(EQ::ItemData,'+n+'));' for n in ['ID','FreeTrade','FixedSellPrice','NoDrop','NoTransfer','Attuneable','FVNoDrop','Price'])+'puts("");}\\n')
subprocess.run(['clang++','-std=c++20','-I'+BUILD+'/source',str(source),'-o',str(r/'layout')],check=True,stdout=subprocess.DEVNULL)
'''
    prelude=f'RUNTIME={RUNTIME!r}\nBUILD={BUILD!r}\nDB={DB!r}\nUSER={USER!r}\nPASSWORD={PASSWORD!r}\n'
    python(prelude+setup)
    reports=[]
    for enabled in (True,False,True):
        sql(f"DELETE FROM {DB}.rule_values WHERE rule_name='Items:FreeTrade'; INSERT INTO {DB}.rule_values(ruleset_id,rule_name,rule_value) SELECT ruleset_id,'Items:FreeTrade','{str(enabled).lower()}' FROM {DB}.rule_sets;")
        code='''import hashlib,json,mmap,os,struct,subprocess
from pathlib import Path
r=Path(RUNTIME)
with (r/('loader-'+str(ENABLED)+'.log')).open('w') as log:
 p=subprocess.run([BUILD+'/build/bin/shared_memory','items'],cwd=r,stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0,'Native loader failed; private log retained'
log=(r/('loader-'+str(ENABLED)+'.log')).read_text()
assert not any(s in log for s in ('Unknown column','SQL syntax','Unable to connect',"doesn't exist")),'Native loader dependency failure'
layout=list(map(int,subprocess.check_output([str(r/'layout')],text=True).split()))
size=layout[0];offsets=dict(zip(['ID','FreeTrade','FixedSellPrice','NoDrop','NoTransfer','Attuneable','FVNoDrop','Price'],layout[1:]))
cfg=json.loads((r/'eqemu_config.json').read_text())['server']['database']
env=dict(os.environ,MYSQL_PWD=cfg['password'])
rows=subprocess.check_output(['mariadb','-h',cfg['host'],'-P',str(cfg.get('port',3306)),'-u',cfg['username'],'--batch','--raw','--skip-column-names',cfg['db'],'-e','SELECT id,nodrop,notransfer,attuneable,fvnodrop,price FROM items ORDER BY id'],env=env,text=True).splitlines()
f=(r/'shared/items').open('rb');mem=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
offset_count,maximum,current=struct.unpack_from('<III',mem,4)
assert current==len(rows)==maximum
element_start=16+4*offset_count
converted=0
for row in rows:
 id,nodrop,no_transfer,attune,fv,price=map(int,row.split('\\t'))
 index=struct.unpack_from('<I',mem,16+id*4)[0];assert index<current
 start=element_start+index*size
 read=lambda name,fmt:struct.unpack_from(fmt,mem,start+offsets[name])[0]
 assert read('ID','<I')==id
 fixed=1000 if ENABLED and nodrop==0 else 0
 assert read('FreeTrade','<B')==int(ENABLED)
 assert read('FixedSellPrice','<I')==fixed
 assert read('NoDrop','<B')==(255 if ENABLED else nodrop),id
 assert read('NoTransfer','<B')==(0 if ENABLED else int(no_transfer!=0)),id
 assert read('Attuneable','<B')==(0 if ENABLED else int(attune!=0)),id
 assert read('FVNoDrop','<B')==(0 if ENABLED else fv),id
 assert read('Price','<I')==max(price,fixed),id
 converted+=bool(fixed)
print(json.dumps({'policy':ENABLED,'items_checked':current,'fixed_payout_items':converted,'item_struct_bytes':size,'cache_sha256':hashlib.sha256(mem).hexdigest()}))
mem.close();f.close()
'''
        reports.append(json.loads(python(prelude+f'ENABLED={enabled!r}\n'+code)))
    assert reports[0]['cache_sha256']==reports[2]['cache_sha256'],'Enable/disable/enable cache did not reproduce'
    result={'status':'passed','scope':'Local disposable full item catalog; real native shared-memory loader; not hosted activation',
            'database':DB,'passes':reports}
    (OUT/'cache-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
finally:
    if user_created:sql(f"DROP USER '{USER}'@'%';")
    if created:sql('DROP DATABASE '+DB+';')
    if created:print('Removed only the test-owned database and account.')

"""Create a fresh LOCAL content-only DB plus remapped synthetic Palwar rows."""
from pathlib import Path
import gzip,json,secrets,subprocess,re,hashlib,sys
HERE=Path(__file__).resolve().parent
DB='nightcap_palwar_vox_20261027'; USER='nightcap_palwar_vox'
SERVER='akk-stack-eqemu-server-1'; MYSQL='akk-stack-mariadb-1'
RUNTIME='/tmp/nightcap-balance-palwar-vox-20261027'
SOURCE='/tmp/nightcap-paladin-grip-20261026-v1/source'

def run(args,data=None):
 r=subprocess.run(args,input=data,capture_output=True)
 if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-2000:])
 return r.stdout
def sql(q):
 return run(['docker','exec','-i',MYSQL,'sh','-c','MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names'],q.encode()).decode()
def lit(v):
 if v is None:return 'NULL'
 if isinstance(v,bool):return '1' if v else '0'
 if isinstance(v,(int,float)):return str(v)
 return "CONVERT(0x"+str(v).encode('utf-8').hex()+" USING utf8mb4)" if str(v) else "''"
def insert(t,r,replace=False):
 assert re.fullmatch('[A-Za-z0-9_]+',t) and all(re.fullmatch('[A-Za-z0-9_]+',k) for k in r)
 return ('REPLACE' if replace else 'INSERT')+' INTO `'+DB+'`.`'+t+'` ('+','.join('`'+k+'`' for k in r)+') VALUES ('+','.join(lit(v) for v in r.values())+');'

if __name__=='__main__':
 existing=sql("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='"+DB+"'; SELECT User FROM mysql.user WHERE User='"+USER+"';").splitlines()
 if existing:
  if '--resume-empty' not in sys.argv or existing!=[DB] or sql("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='"+DB+"';").strip()!='0':raise RuntimeError('Refusing existing destination or user')
 tables=sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME;").splitlines()
 assert tables and all(re.fullmatch('[A-Za-z0-9_]+',t) for t in tables)
 schema=run(['docker','exec',SERVER,'python3','-c','from pathlib import Path; print(Path("'+SOURCE+'/common/database_schema.h").read_text())']).decode()
 body=schema.split('static std::vector<std::string> GetContentTables()',1)[1].split('};',1)[0]
 content=re.findall(r'"([a-z_]+)"',body)
 assert {'items','spells_new','aa_ranks','zone'}<=set(content)
 assert not any(t.startswith(('character','account')) or t in ['inventory','sharedbank'] for t in content)
 assert not set(content)-set(tables)
 password=secrets.token_hex(32)
 if not existing:sql('CREATE DATABASE `'+DB+'`;')
 # Account grammar requires literal strings, not scalar CONVERT expressions.
 assert re.fullmatch('[a-z_]+',USER) and re.fullmatch('[0-9a-f]{64}',password)
 sql("CREATE USER '"+USER+"'@'%' IDENTIFIED BY '"+password+"'; GRANT ALL ON `"+DB+"`.* TO '"+USER+"'@'%';")
 (HERE/'database-created.json').write_text(json.dumps({'database':DB,'user':USER,'scope':'New local isolated database; resume explicitly after any failure'})+'\n')
 sql('\n'.join('CREATE TABLE `'+DB+'`.`'+t+'` LIKE `peq`.`'+t+'`;' for t in tables))
 print('Created',len(tables),'empty tables',flush=True)
 for t in content:
  sql('INSERT INTO `'+DB+'`.`'+t+'` SELECT * FROM `peq`.`'+t+'`;')
 print('Copied',len(content),'public-content tables only',flush=True)
 public=json.loads(gzip.decompress((HERE/'public-combat-reference.json.gz').read_bytes()))
 if public['selected_ruleset'] not in ([],['default']):raise RuntimeError('Unexpected selected ruleset')
 for t,p in public['tables'].items():
  if t!='zone':sql('DELETE FROM `'+DB+'`.`'+t+'`;')
  rows=[dict(zip(p['columns'],r)) for r in p['rows']]
  for start in range(0,len(rows),200):sql('\n'.join(insert(t,r,True) for r in rows[start:start+200]))
  print('Fresh public',t,len(rows),flush=True)
 private=json.loads((HERE/'palwar-private-reference.json').read_text())['tables']
 for t in ['items','npc_types']:
  for start in range(0,len(private[t]),100):sql('\n'.join(insert(t,r,True) for r in private[t][start:start+100]))
 # All identity-bearing rows are remapped into an isolated synthetic identity.
 rows={'character_multiclass':[{'character_id':1,'class2':1,'class3':7}]}
 for t,key in [('character_skills','id'),('character_alternate_abilities','id'),('character_spells','id'),('character_memmed_spells','id'),('character_buffs','character_id')]:
  rows[t]=[{**r,key:1} for r in private[t]]
 for t,data in rows.items():sql('\n'.join(insert(t,r) for r in data))
 # No login account or persistent character profile is needed by the mock client.
 counts=sql('SELECT COUNT(*) FROM `'+DB+'`.account; SELECT COUNT(*) FROM `'+DB+'`.character_data;').splitlines()
 assert counts==['0','0'],counts
 cfg={'server':{'auto_database_updates':'false','world':{'shortname':'palwar_vox_test','longname':'Isolated Palwar Vox test','tcp':{'ip':'127.0.0.1','port':'1'}},'database':{'host':'mariadb','port':'3306','db':DB,'username':USER,'password':password},'directories':{'quests':'quests','plugins':'plugins','lua_modules':'lua_modules','logs':'logs','maps':'maps','shared_memory':'shared/','patches':'/home/eqemu/server','opcodes':'/home/eqemu/server'}}}
 script='''import sys,json,os,shutil
from pathlib import Path
r=Path('/tmp/nightcap-balance-palwar-vox-20261027');assert r.is_dir()
for n in ('quests','plugins','lua_modules','logs','maps','shared'):(r/n).mkdir(exist_ok=True)
p=r/'eqemu_config.json';assert not p.exists();p.write_text(json.dumps(json.load(sys.stdin)));os.chmod(p,0o600)
src=Path('/tmp/nightcap-balance-20260912/maps')
for p in src.rglob('*'):
 if p.is_file() and p.name.startswith(('permafrost.','soldungb.')):
  dest=r/'maps'/p.relative_to(src);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
print('Isolated config and map files staged')
'''
 print(run(['docker','exec','-i',SERVER,'python3','-c',script],json.dumps(cfg).encode()).decode(),flush=True)
 receipt={'database':DB,'user':USER,'tables':len(tables),'copied_public_tables':content,'account_rows':0,'character_profile_rows':0,'synthetic_character_id':1,'public_capture_sha256':hashlib.sha256((HERE/'public-combat-reference.json.gz').read_bytes()).hexdigest(),'private_capture_sha256':hashlib.sha256((HERE/'palwar-private-reference.json').read_bytes()).hexdigest(),'production_changed':False}
 (HERE/'database-ready.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print('READY',DB,flush=True)

"""Read-only full content preimages from production; no player tables or writes."""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import thj_item_parity,pet_content,wpm_content,starter_retune
OUT=ROOT/'tools/fixtures/thj-combined-preimages-20261018.json.gz'
if OUT.exists():raise SystemExit('Capture exists; use a new dated filename for future preflight')
ids=set(thj_item_parity.snapshot())|{i+o for i in starter_retune.APPROVED_IDS for o in (0,200000,400000,600000)}|set(range(960000,960330))
for content in (pet_content,wpm_content):
    ids.update(row['id'] for row in content.snapshot()['tables']['items'])
remote=r'''
import datetime,gzip,json,re,subprocess,sys
root='/opt/nightcap/deploy/production'
db=['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','--default-character-set=utf8mb4','peq']
def sql(q):
 p=subprocess.run(db,input=q,cwd=root,text=True,capture_output=True,timeout=90)
 if p.returncode:raise RuntimeError(p.stderr[-1500:])
 return p.stdout.splitlines()
filters={'items':ITEM_FILTER,'rule_values':"rule_name IN ('Spells:NightcapTHJDamageScaling','Spells:NightcapHeroicSpellScaling','Character:ItemHealAmtCap','Character:ItemSpellDmgCap')",'rule_sets':'1=1','variables':"varname='RuleSet'"}
schemas={};queries=[]
for table,where in filters.items():
 cols=[x.split('\t')[0] for x in sql('SHOW COLUMNS FROM '+table)]
 assert all(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',c) for c in cols)
 schemas[table]={'columns':cols,'create':sql('SHOW CREATE TABLE '+table)[0].split('\t',1)[1]}
 fields=','.join("'%s',CAST(`%s` AS CHAR)"%(c,c) for c in cols)
 queries.append("SELECT '%s',JSON_OBJECT(%s) FROM %s WHERE %s;"%(table,fields,table,where))
q='SET SESSION max_statement_time=45; START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;\n'+'\n'.join(queries)+'\nROLLBACK;'
out={'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':'production_read_only','schemas':schemas,'query':q,'tables':{k:[] for k in filters}}
for line in sql(q):
 table,raw=line.split('\t',1);out['tables'][table].append(json.loads(raw))
out['zone_sha256']=subprocess.check_output(['docker','compose','exec','-T','game','sha256sum','/opt/nightcap/bin/zone'],cwd=root,text=True).split()[0]
sys.stdout.buffer.write(gzip.compress(json.dumps(out,ensure_ascii=False).encode(),mtime=0))
'''.replace('ITEM_FILTER',repr('id IN ('+','.join(map(str,sorted(ids)))+')'))
cmd=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
p=subprocess.run(cmd,input=remote.encode(),capture_output=True,timeout=180)
if p.returncode:raise SystemExit(p.stderr.decode(errors='replace')[-1500:])
data=json.loads(gzip.decompress(p.stdout));assert len(data['tables']['items'])==len(ids),(len(ids),len(data['tables']['items']))
OUT.write_bytes(p.stdout)
print(json.dumps({'captured_utc':data['captured_utc'],'items':len(ids),'zone_sha256':data['zone_sha256']}))

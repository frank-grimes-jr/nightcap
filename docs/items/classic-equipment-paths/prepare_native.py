"""Provision isolated diagnostic data; never modifies production content or players."""
import gzip,hashlib,json,subprocess,sys
from pathlib import Path
from capture import remote,HERE,ROOT
sys.path.insert(0,str(ROOT/'tools'))
from capture_lantern_content import SSH
R='/tmp/nightcap-classic-equipment-paths-20261121'
C='akk-stack-eqemu-server-1'
def run(a,**kw):return subprocess.run(a,check=True,**kw)
def main():
    pins=json.loads((HERE/'runtime.json').read_bytes())
    # Stream public-content caches only; remote operation reads files, writes nothing.
    out=ROOT/'artifacts/classic-equipment-paths-20261121';out.mkdir(parents=True,exist_ok=True)
    for name in ('items','spells'):
        p=out/(name+'.gz')
        if not p.exists():
            with p.open('wb') as f:
                run([*SSH[:-1], 'sudo -n gzip -c /opt/nightcap/deploy/production/data/server/shared/'+name],stdout=f,timeout=300)
        raw=gzip.decompress(p.read_bytes());assert hashlib.sha256(raw).hexdigest()==pins['caches'][name]
        run(['docker','exec',C,'mkdir','-p',R+'/shared'])
        run(['docker','exec','-i',C,'tee',R+'/shared/'+name],input=raw,stdout=subprocess.DEVNULL,timeout=180)
    code=r'''
import json,subprocess,tempfile,os
from pathlib import Path
R=Path('/tmp/nightcap-classic-equipment-paths-20261121')
c=json.loads(Path('/tmp/nightcap-classic-stack-20261114/eqemu_config.json').read_bytes())['server']['database']
assert c['db']=='nightcap_balance_20260912' and c['username']=='nightcap_balance'
with tempfile.NamedTemporaryFile(mode='w',delete=False) as f:
 f.write('[client]\nuser='+c['username']+'\npassword='+c['password']+'\nhost='+c['host']+'\nport='+str(c['port'])+'\n');p=f.name
os.chmod(p,0o600)
try:
 def sql(q):return subprocess.check_output(['mysql','--defaults-extra-file='+p,'-N','-B',c['db'],'-e',q],text=True)
 print(sql('SHOW COLUMNS FROM character_multiclass'))
 cases=json.loads((R/'input.json').read_bytes())['cases']
 membership={int(x['character_id']):x['classes'] for x in cases}
 assert set(membership)==set(range(920100,920107))
 assert sql('SELECT COUNT(*) FROM character_data WHERE id BETWEEN 920100 AND 920106').strip()=='0'
 for ident,classes in membership.items():
  assert len(classes)==2
  existing=sql('SELECT class2,COALESCE(class3,0) FROM character_multiclass WHERE character_id='+str(ident)).strip()
  expected=str(classes[1])+'\t0'
  assert not existing or existing==expected, 'Synthetic fixture conflict'
  if not existing:sql('INSERT INTO character_multiclass(character_id,class2,class3) VALUES ('+str(ident)+','+str(classes[1])+',NULL)')
 d=json.loads((R/'runtime.json').read_bytes());diff=[]
 for row in d['npcs']:
  fields=list(row);q='SELECT JSON_OBJECT('+','.join(repr(k)+',`'+k+'`' for k in fields)+') FROM npc_types WHERE id='+str(row['id'])
  actual=json.loads(sql(q));diff += [{'id':row['id'],'field':k,'local':actual[k],'production':row[k]} for k in fields if actual[k]!=row[k]]
 (R/'npc-comparison.json').write_text(json.dumps(diff,indent=2)+'\n');print('NPC differences',len(diff))
finally:os.unlink(p)
'''
    for name in ('runtime.json','input.json'):
        run(['docker','cp',str(HERE/name),C+':'+R+'/'+name])
    run(['docker','exec','-i',C,'python3','-'],input=code.encode(),timeout=120)
    run(['docker','cp',C+':'+R+'/npc-comparison.json',str(HERE/'npc-comparison.json')])
if __name__=='__main__':main()

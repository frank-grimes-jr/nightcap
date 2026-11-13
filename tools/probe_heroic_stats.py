"""Read-only production heroic-stat audit; no player identities or mutations."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REMOTE = r'''
import base64,datetime,hashlib,json,pathlib,subprocess
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,check=True,timeout=60)
 return p.stdout
def query(sql):
 p=subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','peq'],cwd='/opt/nightcap/deploy/production',input='START TRANSACTION READ ONLY; '+sql+'; ROLLBACK;',capture_output=True,text=True,timeout=60)
 if p.returncode:raise RuntimeError('Read-only query failed: '+p.stderr[-500:])
 return p.stdout
out={'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':'production'}
out['rules']=query("SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name LIKE '%Heroic%' OR rule_name='World:DefaultRuleset' ORDER BY ruleset_id,rule_name")
out['rulesets']=query('SELECT * FROM rule_sets')
out['zone_rulesets']=query('SELECT ruleset,COUNT(*) AS zone_rows FROM zone GROUP BY ruleset')
out['ruleset_variable']=query("SELECT varname,value FROM variables WHERE varname IN ('RuleSet','RuleSetName')")
out['content']=query('SELECT COUNT(*) AS heroic_items, SUM(id BETWEEN 940000 AND 940999) AS hunt_augments FROM items WHERE heroic_str<>0 OR heroic_sta<>0 OR heroic_dex<>0 OR heroic_agi<>0 OR heroic_int<>0 OR heroic_wis<>0 OR heroic_cha<>0')
out['examples']=query('SELECT id,Name,heroic_str,heroic_sta,heroic_dex,heroic_agi,heroic_int,heroic_wis,heroic_cha FROM items WHERE id BETWEEN 940000 AND 940999 AND (heroic_str<>0 OR heroic_sta<>0 OR heroic_dex<>0 OR heroic_agi<>0 OR heroic_int<>0 OR heroic_wis<>0 OR heroic_cha<>0) ORDER BY id LIMIT 8')
out['runtime']=json.loads(run(['docker','inspect','nightcap-production-game-1']))[0]
out['runtime']={k:out['runtime'][k] for k in ('Image','Mounts')}
processes=[]
for line in run(['docker','top','nightcap-production-game-1','-eo','pid,comm']).splitlines()[1:]:
 pid,name=line.split()
 if name in ('zone','world'):
  processes.append([name,hashlib.sha256(pathlib.Path('/proc/'+pid+'/exe').read_bytes()).hexdigest()])
out['native_processes']=processes
base=pathlib.Path('/opt/nightcap/deploy/production/data/public')
raw=(base/'channel.json').read_bytes();env=json.loads(raw);manifest=json.loads(base64.b64decode(env['manifest']))
out['release']=manifest.get('release');out['channel_sha256']=hashlib.sha256(raw).hexdigest()
f=next(f for f in manifest['files'] if f['path']=='uifiles/nightcap/equi_inventory.xml')
out['inventory_descriptor']=f
from urllib.parse import urlsplit
p=base/urlsplit(f['url']).path.lstrip('/')
data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==f['sha256']
out['inventory_xml_base64']=base64.b64encode(data).decode()
out['channel_base64']=base64.b64encode(raw).decode()
print(json.dumps(out))
'''

if __name__ == '__main__':
    ssh = ['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
    p = subprocess.run(ssh,input=REMOTE,capture_output=True,text=True,timeout=180)
    if p.returncode:raise RuntimeError(p.stderr[-2000:])
    out=json.loads(p.stdout)
    import base64
    dest=ROOT/'artifacts/heroic-stats';dest.mkdir(parents=True,exist_ok=True)
    (dest/'equi_inventory.xml').write_bytes(base64.b64decode(out.pop('inventory_xml_base64')))
    (dest/'channel.json').write_bytes(base64.b64decode(out.pop('channel_base64')))
    (dest/'production.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

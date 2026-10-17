"""Read-only follow-up: compare native lifetimes and retained incident records."""
import datetime
import json
import subprocess
from pathlib import Path

ROOT=Path('/opt/nightcap/deploy/production')
OUT=Path('/opt/nightcap/backups/dynamic-zone-worker-lifetime-20261017')
def run(args,source=None):
    p=subprocess.run(args,cwd=ROOT,input=source,text=True,capture_output=True,check=True)
    return p.stdout

before=json.loads((OUT/'runtime-after.json').read_text())
source='before='+repr(before)+'''
import datetime,json
from pathlib import Path
after={}; unloads=[]
for pid,v in before.items():
 p=Path('/proc',pid)
 after[pid]={'name':(p/'exe').resolve().name,'start':(p/'stat').read_text().split()[21]}
 for name,offset in v['logs'].items():
  with Path(name).open('rb') as f:
   assert Path(name).stat().st_size>=offset
   f.seek(offset)
   for raw in f:
    line=raw.decode(errors='replace').strip()
    if any(s in line for s in ('Going to sleep','Proper zone shutdown','Shutting down','StartShutdownTimer')):
     unloads.append({'pid':pid,'file':name,'line':line})
print(json.dumps({'processes':after,'lifecycle_lines':unloads}))
'''
runtime=json.loads(run(['docker','compose','exec','-T','game','python3','-'],source))
identity=lambda d:{k:(v['name'],v['start']) for k,v in d.items()}
assert identity(runtime['processes'])==identity(before)
services=json.loads((OUT/'services-before.json').read_text())
current=json.loads(run(['docker','inspect',*[k.lstrip('/') for k in services]]))
for r in current:
 old=services[r['Name']]
 assert (r['Id'],r['Image'],r['State']['StartedAt'],r['RestartCount'])==(old['id'],old['image'],old['started'],old['restarts'])
 assert r['State']['Running']
 if 'Health' in r['State']: assert r['State']['Health']['Status']=='healthy'
sql="SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name='Zone:KillProcessOnDynamicShutdown';"
rule=run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','peq'],sql)
assert rule.splitlines()[1:]==['1\tZone:KillProcessOnDynamicShutdown\tfalse']
p=subprocess.run(['docker','logs','--since','2026-10-17T02:15:00Z','--timestamps','nightcap-production-game-1'],cwd=ROOT,text=True,capture_output=True,check=True)
incidents=[x for x in (p.stdout+'\n'+p.stderr).splitlines() if any(s in x for s in ('Going to sleep','Proper zone shutdown complete. --','a native process exited; restarting the complete runtime'))]
result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'all_15_native_lifetimes_preserved':True,'all_5_service_identities_preserved':True,
        'rule':rule,'lifecycle_since_reload':runtime['lifecycle_lines'],
        'incident_records':incidents,'idle_unload_observed':any('Going to sleep' in x['line'] for x in runtime['lifecycle_lines'])}
(OUT/'followup.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

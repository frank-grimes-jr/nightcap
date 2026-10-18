"""Read-only status while another operation owns production maintenance."""
import datetime
import json
import subprocess

root='/opt/nightcap/deploy/production'
def run(args,source=None):
    return subprocess.run(args,cwd=root,input=source,text=True,capture_output=True,check=True).stdout
rows=json.loads(run(['docker','inspect','nightcap-production-game-1','nightcap-production-gateway-1']))
services={r['Name']:{'status':r['State']['Status'],'running':r['State']['Running']} for r in rows}
db=['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq']
rates=run(db,"SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name LIKE 'Zone:LootTier%' ORDER BY rule_name;")
print(json.dumps({'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'status':'pending_activation','services':services,'live_rates':rates,
                 'reason':'Concurrent cooldown deployment maintenance; this tuning made no production writes'},indent=2))

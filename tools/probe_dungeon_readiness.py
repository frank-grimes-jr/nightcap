"""Read-only production dungeon contract diagnostics; no player rows or mutations."""
import datetime
import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--contract', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
contract = json.loads(args.contract.read_text())
code = '''import datetime,json,subprocess
def query(sql):
 p=subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--quick','--skip-column-names','peq'],cwd='/opt/nightcap/deploy/production',input='SET SESSION max_session_mem_used=134217728; START TRANSACTION READ ONLY;\\n'+sql+';\\nROLLBACK;\\n',text=True,capture_output=True,timeout=180)
 if p.returncode: raise RuntimeError('Read-only database probe failed; credential-bearing output withheld')
 return p.stdout.splitlines()
report={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Production read-only contract checks; no player records','checks':{}}
for family,checks in contract.items():
 values=query(';\\n'.join(c['sql'] for c in checks))
 assert len(values)==len(checks),(family,len(values),len(checks))
 report['checks'][family]={'total':len(checks),'failures':[{'label':c['label'],'expected':c['expected'],'actual':v} for c,v in zip(checks,values) if c['expected']!=v]}
report['readiness']=query("SELECT @@group_concat_max_len; SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND engine='InnoDB' AND table_name IN ('nightcap_dungeon_state','nightcap_dungeon_runs','nightcap_dungeon_members','nightcap_dungeon_kills','nightcap_dungeon_deaths','nightcap_dungeon_loot','nightcap_dungeon_spawns','nightcap_dungeon_checkpoints','nightcap_dungeon_corpses','nightcap_dungeon_respawns','instance_list','instance_list_player','character_advloot_claims','nightcap_vigil_state','nightcap_vigil_characters'); SELECT revision,enabled FROM nightcap_dungeon_state WHERE id=1")
p=subprocess.run(['docker','compose','logs','--no-color','--tail','1200','game'],cwd='/opt/nightcap/deploy/production',text=True,capture_output=True,timeout=30)
report['drift_logs']=[line for line in (p.stdout+p.stderr).splitlines() if any(s in line for s in ('Dungeon schema drift','Dungeon content drift','Dungeon item cache drift','Chapterhouse cache drift'))][-20:]
print(json.dumps(report))
'''
ssh = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', 'C:/Users/verre/.ssh/nightcap_ovh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=yes', 'ubuntu@135.148.47.202', 'sudo -n python3 -']
p = subprocess.run(ssh, input='contract='+repr(contract)+'\n'+code, text=True, encoding='utf-8', capture_output=True, timeout=300)
if p.returncode:
    raise RuntimeError(p.stderr[-2000:])
report = json.loads(p.stdout)
args.output.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))

"""Read-only deployment prerequisites; never exports configuration secrets."""
import hashlib,json,shutil,subprocess
from pathlib import Path
r=Path('/opt/nightcap/deploy/production')
def out(*args):return subprocess.check_output(args,cwd=r,text=True)
cid=out('docker','compose','ps','-q','game').strip()
start=out('docker','exec',cid,'cat','/opt/nightcap/start.py')
assert 'subprocess.run([str(BIN/\'shared_memory\')], check=True)' in start
assert 'restarting the complete runtime' in start
sql="SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name='Items:FreeTrade'; SELECT ruleset_id,name FROM rule_sets; SELECT varname,value FROM variables WHERE varname='RuleSet';"
rules=out('docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq','-e',sql)
cache=r/'data/server/shared/items'
print(json.dumps({'supervisor_sha256':hashlib.sha256(start.encode()).hexdigest(),'rebuilds_cache_on_start':True,'full_runtime_supervisor':True,'rules':rules,'disk_free_bytes':shutil.disk_usage(r).free,'cache_bytes':cache.stat().st_size,'cache_sha256':hashlib.sha256(cache.read_bytes()).hexdigest(),'cache_header_hex':cache.read_bytes()[:16].hex()}))

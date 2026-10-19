"""Read-only production inspection; run over SSH stdin on the host."""
import json
import subprocess

ROOT = '/opt/nightcap/deploy/production'

def run(args, source=None):
    return subprocess.run(args, cwd=ROOT, input=source, text=True,
                          capture_output=True, check=True).stdout

db = ['docker', 'compose', 'exec', '-T', 'db', 'mariadb',
      '--defaults-extra-file=/run/secrets/db_backup_config', '--batch', 'peq']
queries = """
SELECT * FROM rule_values WHERE rule_name LIKE 'Zone:LootTier%';
SELECT * FROM rule_sets;
SELECT varname,value FROM variables WHERE varname='RuleSet';
"""
print(run(db, queries))
print(run(['docker', 'compose', 'exec', '-T', 'game', 'python3', '-'], """
from pathlib import Path
import json,hashlib
p=Path('/srv/nightcap')
print(json.dumps({'quest_dirs':[str(x) for x in p.glob('*quest*')],
 'bin':{n:hashlib.sha256(Path('/opt/nightcap/bin',n).read_bytes()).hexdigest() for n in ('world','zone')}}))
"""))
print(run(['find','/opt/nightcap/releases','-maxdepth','2','-name','*manifest*']))

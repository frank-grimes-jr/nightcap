"""Read-only production rule, runtime and retained-source inspection over SSH."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('/opt/nightcap/deploy/production')

def run(args, source=None):
    return subprocess.run(args, cwd=ROOT, input=source, text=True,
                          capture_output=True, check=True).stdout

db = ['docker', 'compose', 'exec', '-T', 'db', 'mariadb',
      '--defaults-extra-file=/run/secrets/db_backup_config', '--batch', 'peq']
queries = {
    'rulesets': 'SELECT * FROM rule_sets;',
    'active': "SELECT varname,value FROM variables WHERE varname='RuleSet';",
    'zone_rulesets': 'SELECT ruleset,COUNT(*) AS zones FROM zone GROUP BY ruleset;',
    'shutdown_rules': "SELECT * FROM rule_values WHERE rule_name IN ('Zone:KillProcessOnDynamicShutdown','Zone:AutoShutdownDelay','Zone:StateSavingOnShutdown') ORDER BY ruleset_id,rule_name;",
}
result = {'queries': {k: run(db, q) for k, q in queries.items()}}
result['services'] = run(['docker','compose','ps','--format','json'])
result['runtime'] = run(['docker','compose','exec','-T','game','python3','-'], '''
from pathlib import Path
import hashlib,json
out={}
for p in Path('/proc').iterdir():
 if not p.name.isdigit(): continue
 try:
  exe=(p/'exe').resolve()
  if exe.name not in ('zone','world','loginserver','ucs'): continue
  logs={str(f.resolve()):f.resolve().stat().st_size for f in (p/'fd').iterdir() if '/logs/' in str(f.resolve()) and f.resolve().is_file()}
  out[p.name]={'name':exe.name,'start':(p/'stat').read_text().split()[21],'logs':logs}
 except (FileNotFoundError,PermissionError): pass
print(json.dumps({'processes':out,'supervisor':Path('/opt/nightcap/start.py').read_text(),'binaries':{n:hashlib.sha256(Path('/opt/nightcap/bin',n).read_bytes()).hexdigest() for n in ('world','zone')}}))
''')
result['retained_roots'] = [str(p) for p in Path('/tmp').glob('nightcap*') if p.is_dir()]
print(json.dumps(result,indent=2))

"""One-time guarded loot tuning. RELOAD_SOURCE is supplied by the reviewed runner.

If reload verification fails, keep the persisted approved rates, retain the
receipt, and inspect/retry the reload. Never replay an uncertain write
automatically and never restore player data.
"""
import datetime
import fcntl
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path('/opt/nightcap/deploy/production')
OUT = Path('/opt/nightcap/backups/loot-quality-rates-20261018')
CHANGES = {'Zone:LootTierRareChance': ('1000','2000'),
           'Zone:LootTierEpicChance': ('200','500'),
           'Zone:LootTierLegendaryChance': ('25','100')}
NAMES = ','.join("'"+n+"'" for n in CHANGES)

def statements(reverse=False):
    pairs = {n: (b,a) if reverse else (a,b) for n,(a,b) in CHANGES.items()}
    guard = ' OR '.join("(ruleset_id=1 AND BINARY rule_name='"+n+"' AND BINARY rule_value='"+a+"')" for n,(a,b) in pairs.items())
    cases = ' '.join("WHEN '"+n+"' THEN '"+b+"'" for n,(a,b) in pairs.items())
    return ("DELETE FROM loot_rate_guard; INSERT INTO loot_rate_guard SELECT COUNT(*) FROM rule_values WHERE "+guard+"; "
            "UPDATE rule_values SET rule_value=CASE rule_name "+cases+" END WHERE ruleset_id=1 AND rule_name IN ("+NAMES+"); "
            "SET @changed=ROW_COUNT(); DELETE FROM loot_rate_guard; INSERT INTO loot_rate_guard VALUES (@changed); ")
FORWARD = statements()
INVERSE = statements(True)
GUARD_TABLE = 'CREATE TEMPORARY TABLE loot_rate_guard (n INT CHECK(n=3)); '
LOCK_ROWS = 'SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name IN ('+NAMES+') ORDER BY rule_name FOR UPDATE; '
DB = ['docker','compose','exec','-T','db','mariadb',
      '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq']

def run(args, source=None):
    return subprocess.run(args,cwd=ROOT,input=source,text=True,capture_output=True,check=True).stdout

def sql(query):
    return run(DB,query)

def game(source):
    return run(['docker','compose','exec','-T','game','python3','-'],source)

SNAPSHOT = '''
from pathlib import Path
import json
out={}
for p in Path('/proc').iterdir():
 if not p.name.isdigit(): continue
 try:
  name=(p/'exe').resolve().name
  if name not in ('world','zone','loginserver','ucs'): continue
  logs={str(f.resolve()):f.resolve().stat().st_size for f in (p/'fd').iterdir() if '/logs/' in str(f.resolve()) and f.resolve().is_file()}
  out[p.name]={'name':name,'start':(p/'stat').read_text().split()[21],'logs':logs}
 except (FileNotFoundError,PermissionError): pass
print(json.dumps(out))
'''

def identity(rows):
    return {k:(v['name'],v['start']) for k,v in rows.items()}

def services():
    rows=json.loads(run(['docker','inspect',*['nightcap-production-'+x+'-1' for x in ('game','db','gateway','web','tunnel')]]))
    return {r['Name']:{'id':r['Id'],'image':r['Image'],'started':r['State']['StartedAt'],
        'restarts':r['RestartCount'],'running':r['State']['Running'],
        'health':r['State'].get('Health',{}).get('Status')} for r in rows}

def save(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2)+'\n')

before=json.loads((OUT/'runtime-before.json').read_text());after=json.loads(game(SNAPSHOT))
print(json.dumps({pid:{'before':before[pid],'after':after[pid]} for pid in ('30','37')},indent=2))
print(game("from pathlib import Path; import json; print(json.dumps({pid:{'cmd':Path('/proc',pid,'cmdline').read_text().replace(chr(0),' '),'fds':[(x.name,str(x.resolve())) for x in Path('/proc',pid,'fd').iterdir()]} for pid in ('30','37')},indent=2))"))

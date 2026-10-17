"""One-time guarded correction. RELOAD_SOURCE is supplied by the reviewed runner.

If reload verification fails, keep the safe persisted false value, retain the
receipt, and inspect/retry the reload. Never re-enable the known restart cause
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
OUT = Path('/opt/nightcap/backups/dynamic-zone-worker-lifetime-20261017')
NAME = 'Zone:KillProcessOnDynamicShutdown'
FORWARD = f"UPDATE rule_values SET rule_value='false' WHERE ruleset_id=1 AND rule_name='{NAME}' AND rule_value='true';"
INVERSE = f"UPDATE rule_values SET rule_value='true' WHERE ruleset_id=1 AND rule_name='{NAME}' AND rule_value='false';"
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

os.umask(0o077)
with (ROOT/'.deployment.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sql("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='rule_values';").strip()=='InnoDB'
    assert sql("SELECT ruleset_id FROM rule_sets WHERE name='default';").strip()=='1'
    assert sql(f"SELECT ruleset_id,rule_value FROM rule_values WHERE rule_name='{NAME}';").strip()=='1\ttrue'
    before=sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;')
    row=sql(f"SELECT * FROM rule_values WHERE rule_name='{NAME}';")
    fields=row.split('\t'); assert fields[:3]==['1',NAME,'true']
    fields[2]='false'; expected=before.replace(row,'\t'.join(fields),1)
    assert expected!=before and before.count(row)==1
    original=json.loads(game(SNAPSHOT)); baseline=services()
    assert sum(v['name']=='zone' for v in original.values())==12
    assert sum(v['name']=='world' for v in original.values())==1
    assert all(v['running'] for v in baseline.values())
    assert all(v['health']=='healthy' for k,v in baseline.items() if k.endswith(('game-1','db-1')))
    OUT.mkdir(mode=0o700)
    (OUT/'rules-before.tsv').write_text(before)
    (OUT/'forward.sql').write_text(FORWARD+'\n')
    (OUT/'rollback.sql').write_text(INVERSE+'\n')
    (OUT/'reload_rules.py').write_text(RELOAD_SOURCE)
    save('runtime-before.json',original); save('services-before.json',baseline)
    rehearsal=sql('START TRANSACTION; '+FORWARD+' SELECT ROW_COUNT(); SELECT * FROM rule_values ORDER BY ruleset_id,rule_name; '+INVERSE+' SELECT ROW_COUNT(); ROLLBACK;')
    assert rehearsal=='1\n'+expected+'1\n'
    assert sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;')==before
    fresh=json.loads(game(SNAPSHOT)); assert identity(fresh)==identity(original)
    result={'rule':NAME,'ruleset_id':1,'previous':'true','value':'false',
            'backup_directory':str(OUT),'rules_backup_sha256':hashlib.sha256(before.encode()).hexdigest(),
            'forward_inverse_rehearsal':True,'status':'commit_pending'}
    save('result.json',result)
    assert sql('START TRANSACTION; '+FORWARD+' SELECT ROW_COUNT(); COMMIT;').strip()=='1'
    result.update(status='committed_reload_pending',changed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save('result.json',result)
    assert sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;')==expected
    (OUT/'rules-after.tsv').write_text(expected)
    result['reload']=json.loads(game(RELOAD_SOURCE))
    time.sleep(5)
    after=json.loads(game(SNAPSHOT)); assert identity(after)==identity(original)
    evidence='before='+repr(fresh)+'''
from pathlib import Path
import json
out={}
for pid,v in before.items():
 if v['name'] not in ('world','zone'): continue
 lines=[]
 for name,offset in v['logs'].items():
  with Path(name).open('rb') as f:
   assert Path(name).stat().st_size>=offset
   f.seek(offset); lines.extend(f.read(4*1024*1024).decode(errors='replace').splitlines())
 out[pid]=[x for x in lines if 'rule' in x.lower()]
print(json.dumps(out))
'''
    logs=json.loads(game(evidence))
    assert len(logs)==13
    assert all(any('Loaded' in line and 'rule' in line for line in lines) for lines in logs.values())
    assert services()==baseline
    assert sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;')==expected
    result.update(status='activated_verified',other_rules_unchanged=True,all_15_native_processes_unchanged=True,
                  all_5_services_unchanged=True,reload_logs=logs,services=baseline,
                  idle_unload_verification='pending',player_acceptance='pending')
    save('runtime-after.json',after); save('result.json',result)
    print(json.dumps(result,indent=2))

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

os.umask(0o077)
with (ROOT/'.deployment.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert sql("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='rule_values';").strip()=='InnoDB'
    assert sql("SELECT ruleset_id FROM rule_sets WHERE name='default';").strip()=='1'
    active=sql("SELECT value FROM variables WHERE varname='RuleSet';").strip()
    assert active in ('','default'), 'Inspect nondefault world ruleset before activation'
    binaries=json.loads(game("from pathlib import Path; import hashlib,json; print(json.dumps({n:hashlib.sha256(Path('/opt/nightcap/bin',n).read_bytes()).hexdigest() for n in ('world','zone')}))"))
    assert binaries['world']=='70cceaca060ed6338cb72acc726bb24ccae162b42ba88dfb89432b609c7ef8e5'
    # Both retained manifests have byte-identical loot/rule/reload sources.
    assert binaries['zone'] in (
        '3c1d74926cb7cff032a3ee8c48c210e37740156e7e36cc0eeddd07f847e88d1a',
        'd3908e0348715e94955d84f629e4f27e91f15c7dd661e437efbba580ce3d216a',
        '29b8093147ffbc4c0d387a4e3fa55a3a041dbb9ae7da731b493b21601a6dec2f',
    ), 'Runtime changed; revalidate source/reload protocol'
    rows=sql(f"SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name IN ({NAMES}) ORDER BY rule_name;")
    wanted=''.join('1\t'+n+'\t'+CHANGES[n][0]+'\n' for n in sorted(CHANGES))
    assert rows==wanted, 'Unexpected rates or alternate overrides; inspect before writing'
    before=sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;')
    expected=before
    for n,(old,new) in CHANGES.items():
        token='1\t'+n+'\t'+old+'\t'
        assert expected.count(token)==1
        expected=expected.replace(token,'1\t'+n+'\t'+new+'\t',1)
    original=json.loads(game(SNAPSHOT)); baseline=services()
    assert sum(v['name']=='zone' for v in original.values())==12
    assert sum(v['name']=='world' for v in original.values())==1
    assert all(v['running'] for v in baseline.values())
    assert all(v['health']=='healthy' for k,v in baseline.items() if k.endswith(('game-1','db-1')))
    OUT.mkdir(mode=0o700)
    (OUT/'rules-before.tsv').write_text(before)
    (OUT/'forward.sql').write_text(GUARD_TABLE+'START TRANSACTION; '+LOCK_ROWS+FORWARD+'COMMIT;\n')
    (OUT/'rollback.sql').write_text(GUARD_TABLE+'START TRANSACTION; '+LOCK_ROWS+INVERSE+'COMMIT;\n')
    (OUT/'reload_rules.py').write_text(RELOAD_SOURCE)
    save('runtime-before.json',original); save('services-before.json',baseline)
    rehearsal=sql(GUARD_TABLE+'START TRANSACTION; '+LOCK_ROWS+FORWARD+'SELECT * FROM rule_values ORDER BY ruleset_id,rule_name; '+INVERSE+'SELECT * FROM rule_values ORDER BY ruleset_id,rule_name; ROLLBACK;')
    assert rehearsal==wanted+expected+before
    assert sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;')==before
    fresh=json.loads(game(SNAPSHOT)); assert identity(fresh)==identity(original)
    result={'rules':CHANGES,'ruleset_id':1,'binaries':binaries,
            'backup_directory':str(OUT),'rules_backup_sha256':hashlib.sha256(before.encode()).hexdigest(),
            'forward_inverse_rehearsal':True,'status':'commit_pending'}
    save('result.json',result)
    assert sql(GUARD_TABLE+'START TRANSACTION; '+LOCK_ROWS+FORWARD+'COMMIT;')==wanted
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
                  drop_distribution_player_QA='pending',player_acceptance='pending')
    save('runtime-after.json',after); save('result.json',result)
    print(json.dumps(result,indent=2))

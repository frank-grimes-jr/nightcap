"""Guarded one-row rule activation; RELOAD_SOURCE supplied by the local runner."""
import fcntl
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path('/opt/nightcap/deploy/production')
OUT = Path('/opt/nightcap/backups/passive-aa-twenty-20261013')
DB = ['docker','compose','exec','-T','db','mariadb',
      '--defaults-extra-file=/run/secrets/db_backup_config',
      '--batch','--raw','--skip-column-names','peq']
NAME = 'AA:PassiveExpPercent'
FORWARD = f"UPDATE rule_values SET rule_value='20' WHERE ruleset_id=1 AND rule_name='{NAME}' AND rule_value='40';"
ROLLBACK = f"UPDATE rule_values SET rule_value='40' WHERE ruleset_id=1 AND rule_name='{NAME}' AND rule_value='20';"

def run(args, **kw):
    return subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True, **kw).stdout

def sql(query):
    return run(DB, input=query)

def game(code):
    return run(['docker','compose','exec','-T','game','python3','-'], input=code)

SNAPSHOT = '''from pathlib import Path
import json
out={}
for p in Path('/proc').iterdir():
 if not p.name.isdigit(): continue
 try:
  name=(p/'exe').resolve().name
  if name not in ('world','zone'): continue
  logs={}
  for f in (p/'fd').iterdir():
   path=f.resolve()
   if '/logs/' in str(path) and path.is_file(): logs[str(path)]=path.stat().st_size
  out[p.name]={'name':name,'start':(p/'stat').read_text().split()[21],'logs':logs}
 except (FileNotFoundError,PermissionError): pass
print(json.dumps(out))
'''

def reload_and_verify(original):
    # Capture offsets immediately before this request, not before the backup.
    fresh = json.loads(game(SNAPSHOT))
    identity = lambda rows: {k:(v['name'],v['start']) for k,v in rows.items()}
    assert identity(fresh) == identity(original), 'Process identity changed before reload'
    reload_result = json.loads(game(RELOAD_SOURCE))
    time.sleep(4)
    after = json.loads(game(SNAPSHOT))
    assert identity(after) == identity(original), 'Process identity changed after reload'
    evidence_code = 'before='+repr(fresh)+"\nfrom pathlib import Path\nimport json, os\nout={}\nfor pid,v in before.items():\n lines=[]\n for name,offset in v['logs'].items():\n  with Path(name).open('rb') as f:\n   assert os.fstat(f.fileno()).st_size >= offset, 'Log rotated during reload'\n   f.seek(offset)\n   lines.extend(f.read(1024*1024).decode(errors='replace').splitlines())\n out[pid]=[line for line in lines if 'rule' in line.lower()]\nprint(json.dumps(out))\n"
    logs = json.loads(game(evidence_code))
    assert set(logs) == set(original)
    assert all(any('Loaded' in line and 'rule' in line for line in lines) for lines in logs.values()), 'Missing reload completion logs'
    services = [{k:row.get(k) for k in ('Service','State','Health')}
                for row in map(json.loads,run(['docker','compose','ps','--format','json']).splitlines())]
    assert len(services) == 5 and all(v['State']=='running' for v in services)
    assert all(v['Health']=='healthy' for v in services if v['Service'] in ('game','db'))
    return {'reload':reload_result,'reload_logs':logs,'processes_unchanged':True,'services':services}

def activate_rule(before, expected, target_before, runtime_before, result):
    fields = target_before.split('\t'); fields[2] = '20'
    target_after = '\t'.join(fields)
    forward_not_applied = False
    try:
        forward_count = sql('START TRANSACTION; '+FORWARD+' SELECT ROW_COUNT(); COMMIT;').strip()
        forward_not_applied = forward_count == '0'
        assert forward_count == '1', 'Guarded forward update did not change exactly one row'
        result['status'] = 'committed_reload_pending'
        (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        assert sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;') == expected
        (OUT/'rules-after.tsv').write_text(expected)
        print('Rule committed; reloading world and all zones without restarting.', flush=True)
        result.update(reload_and_verify(runtime_before))
        assert sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;') == expected
        result['status'] = 'activated_verified'
        (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    except BaseException as failure:
        result['status'] = 'recovery_pending'
        result['failure'] = type(failure).__name__
        result['forward_not_applied'] = forward_not_applied
        # Evidence storage failure must never suppress rule recovery.
        try:
            (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        except OSError:
            print('Recovery pending; result file could not be written.', flush=True)
        if forward_not_applied:
            # A confirmed no-op cannot establish ownership of another writer's value.
            raise
        try:
            current = sql(f"SELECT * FROM rule_values WHERE rule_name='{NAME}';")
            assert current in (target_before,target_after), 'Rule changed externally; preserve it'
            if current == target_after:
                assert sql('START TRANSACTION; '+ROLLBACK+' SELECT ROW_COUNT(); COMMIT;').strip() == '1'
            assert sql(f"SELECT * FROM rule_values WHERE rule_name='{NAME}';") == target_before
            # Only this rule is reverted; concurrent unrelated rules are retained.
            result['recovery'] = reload_and_verify(runtime_before)
            result['status'] = 'rolled_back_verified'
            result['value'] = '40'
            try:
                (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            except OSError:
                print('Rule rollback and reload verified; result file could not be written.', flush=True)
        except BaseException as recovery_failure:
            result['recovery_failure'] = type(recovery_failure).__name__
            try:
                (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            except OSError:
                print('Recovery failed; result file could not be written.', flush=True)
            raise
        raise

os.umask(0o077)
with (ROOT/'.deployment.lock').open('a') as lock, Path('/var/lock/nightcap-gm.lock').open('a') as gm_lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    fcntl.flock(gm_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not (ROOT/'private/gm-maintenance.json').exists(), 'GM maintenance is active'
    assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip() == '1'
    expected_binaries = {'world':'efd54a1023a569274a76f65d3d2a18a173906762472a1bce186e3e14629d3c18',
                         'zone':'5dfe3d8a944a29ac963644298eb7a1563a08748ae72ae210edd78268ea106681'}
    actual_binaries = json.loads(game("from pathlib import Path\nimport hashlib,json\nprint(json.dumps({name:hashlib.sha256((Path('/opt/nightcap/bin')/name).read_bytes()).hexdigest() for name in ['world','zone']}))"))
    assert actual_binaries == expected_binaries, 'Production binary changed since exact-source tests'
    assert sql("SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name IN ('AA:ExpPerPoint','AA:NormalizedAAEnabled','AA:UnusedAAPointCap','Character:AAExpMinLevel') ORDER BY rule_name;").strip() == '1\tAA:ExpPerPoint\t4000\n1\tAA:NormalizedAAEnabled\tfalse\n1\tAA:UnusedAAPointCap\t-1\n1\tCharacter:AAExpMinLevel\t1'
    assert sql("SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='rule_values';").strip() == 'InnoDB'
    assert sql("SELECT ruleset_id FROM rule_sets WHERE name='default';").strip() == '1'
    assert sql(f"SELECT ruleset_id,rule_value FROM rule_values WHERE rule_name='{NAME}';").strip() == '1\t40'
    assert sql("SELECT ruleset_id FROM rule_sets WHERE name=COALESCE((SELECT value FROM variables WHERE varname='RuleSet'),'default');").strip() == '1'
    before = sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;')
    target_before = sql(f"SELECT * FROM rule_values WHERE rule_name='{NAME}';")
    fields = target_before.split('\t')
    assert fields[:3] == ['1', NAME, '40'] and before.count(target_before) == 1
    fields[2] = '20'
    expected = before.replace(target_before, '\t'.join(fields), 1)
    assert expected != before
    runtime_before = json.loads(game(SNAPSHOT))
    assert sum(v['name']=='world' for v in runtime_before.values()) == 1
    assert sum(v['name']=='zone' for v in runtime_before.values()) == 12
    assert all(v['logs'] for v in runtime_before.values()), 'Need per-process reload evidence'
    OUT.mkdir(mode=0o700)
    (OUT/'rules-before.tsv').write_text(before)
    (OUT/'palwar-before.tsv').write_text(sql("SELECT UTC_TIMESTAMP(),name,level,exp,aa_exp,aa_points,aa_points_spent,e_percent_to_aa FROM character_data WHERE name='Palwar';"))
    (OUT/'forward.sql').write_text(FORWARD+'\n')
    (OUT/'rollback.sql').write_text(ROLLBACK+'\n')
    (OUT/'reload_rules.py').write_text(RELOAD_SOURCE)
    (OUT/'runtime-before.json').write_text(json.dumps(runtime_before,indent=2))
    dump = ['docker','compose','exec','-T','db','mariadb-dump',
            '--defaults-extra-file=/run/secrets/db_backup_config','--single-transaction',
            '--routines','--triggers','--events','--hex-blob','peq']
    with (OUT/'peq-before.sql.gz').open('xb') as dest:
        proc = subprocess.Popen(dump, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        with gzip.GzipFile(fileobj=dest,mode='wb') as zipped:
            shutil.copyfileobj(proc.stdout,zipped)
        proc.stdout.close()
        error = proc.stderr.read()
        assert proc.wait()==0, error.decode()
    with gzip.open(OUT/'peq-before.sql.gz','rb') as source:
        uncompressed = sum(len(c) for c in iter(lambda:source.read(1024*1024),b''))
    assert uncompressed > 100_000_000
    with (OUT/'peq-before.sql.gz').open('rb') as source:
        backup_sha = hashlib.file_digest(source,'sha256').hexdigest()
    print(json.dumps({'backup_verified':True,'uncompressed_bytes':uncompressed}),flush=True)
    assert sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;') == before
    rehearsal = sql('START TRANSACTION; '+FORWARD+' SELECT ROW_COUNT(); SELECT * FROM rule_values ORDER BY ruleset_id,rule_name; '+ROLLBACK+' SELECT ROW_COUNT(); ROLLBACK;')
    assert rehearsal == '1\n'+expected+'1\n', 'Forward/rollback rehearsal mismatch'
    assert sql('SELECT * FROM rule_values ORDER BY ruleset_id,rule_name;') == before
    result = {'changed_rows':1,'rule':NAME,'value':'20','previous_value':'40','ruleset_id':1,
              'binaries':actual_binaries, 'activated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
              'other_rules_unchanged':True,'rollback_rehearsed':True,
              'backup_sha256':backup_sha,'backup_directory':str(OUT),
              'backup_uncompressed_bytes':uncompressed}
    result = activate_rule(before,expected,target_before,runtime_before,result)
    (OUT/'palwar-after.tsv').write_text(sql("SELECT UTC_TIMESTAMP(),name,level,exp,aa_exp,aa_points,aa_points_spent,e_percent_to_aa FROM character_data WHERE name='Palwar';"))
    print(json.dumps(result),flush=True)

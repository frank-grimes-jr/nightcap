"""Independent rehearsal: generated hub SQL only touches a fresh random schema."""
import copy
import hashlib
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if len(sys.argv) != 3:
    raise SystemExit('usage: rehearse_compact_hub.py ARTIFACT_DIRECTORY hub-vN')
ART = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT/'tools'))
from pok_hub_migration import sql_value

NAME = 'nightcap_hub_review_' + uuid.uuid4().hex
assert re.fullmatch(r'nightcap_hub_review_[0-9a-f]{32}', NAME)
REPORT = {'schema': NAME, 'live_writes': False, 'checks': [], 'scratch_removed': False}
created = False

def sql(query, database=None, expect_ok=True):
    args = ['docker', 'exec', '-i', 'akk-stack-mariadb-1', 'sh', '-c',
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot --batch --raw --skip-column-names "$@"', 'mysql']
    if database:
        assert database == NAME
        args.append(database)
    p = subprocess.run(args, input=query, text=True, encoding='utf-8', capture_output=True, timeout=120)
    if expect_ok and p.returncode:
        raise RuntimeError(p.stderr[-1500:])
    return p

def insert(table, row):
    return 'INSERT INTO `'+table+'` ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(map(sql_value,row.values()))+');'

def snapshot():
    result = {t: [] for t in before['rows']}
    queries = []
    for table in before['rows']:
        fields = ','.join(sql_value(c)+f',CAST(`{c}` AS CHAR)' for c in before['schemas'][table]['columns'])
        queries.append(f'SELECT {sql_value(table)},JSON_OBJECT({fields}) FROM `{table}`;')
    for line in sql('\n'.join(queries), NAME).stdout.splitlines():
        table, payload = line.split('\t', 1)
        result[table].append(json.loads(payload))
    return {t: sorted(rows, key=lambda x: json.dumps(x, sort_keys=True)) for t, rows in result.items()}


def check(name, ok, detail=None):
    REPORT['checks'].append({'name': name, 'passed': bool(ok), 'detail': detail})
    print(name + ': ' + ('PASS' if ok else 'FAIL'), flush=True)
    if not ok:
        raise AssertionError(name + ': ' + str(detail))

generation = sys.argv[2]
assert re.fullmatch(r'hub-v[0-9]+', generation)
REPORT['generation'] = generation
before = json.loads((ART/'hub-before.json').read_bytes())
forward = (ART/generation/'forward.sql').read_text()
rollback = (ART/generation/'rollback.sql').read_text()
REPORT['sql_sha256'] = {'forward': hashlib.sha256(forward.encode()).hexdigest(), 'rollback': hashlib.sha256(rollback.encode()).hexdigest()}
try:
    check('generated_sql_has_no_database_switch_or_peq_qualification', not re.search(r'\bUSE\s|\bpeq\s*\.', forward+rollback, re.I))
    sql('CREATE DATABASE `'+NAME+'` CHARACTER SET utf8mb4;')
    created = True
    setup = []
    for table, schema in before['schemas'].items():
        setup.append(schema['create']+';')
        setup.extend(insert(table,row) for row in before['rows'][table])
    sentinels = []
    template = before['rows']['zone_state_spawns'][0]
    for offset, overrides in enumerate(({'is_corpse':'1'}, {'instance_id':'777'}, {'zone_id':'203'}, {'npc_id':'123','spawngroup_id':'123','spawn2_id':'123'})):
        row = copy.deepcopy(template)
        row.update(id=str(900000000+offset), **overrides)
        sentinels.append(row)
        setup.append(insert('zone_state_spawns',row))
    sql('\n'.join(setup), NAME)
    baseline = snapshot()
    check('captured_preimages_round_trip', all(sorted(before['rows'][t],key=lambda x:json.dumps(x,sort_keys=True)) == [r for r in baseline[t] if not (t=='zone_state_spawns' and int(r['id'])>=900000000)] for t in baseline))
    for table, statement, undo in (
        ('npc_types', "UPDATE npc_types SET name='Review_Drift' WHERE id=999220;", 'UPDATE npc_types SET name='+sql_value(next(r['name'] for r in before['rows']['npc_types'] if r['id']=='999220'))+' WHERE id=999220;'),
        ('merchantlist', 'UPDATE merchantlist SET item=item+1 ORDER BY merchantid,slot LIMIT 1;', 'UPDATE merchantlist SET item=item-1 ORDER BY merchantid,slot LIMIT 1;'),
        ('zone_state_spawns', 'UPDATE zone_state_spawns SET hp=hp+1 WHERE id='+template['id']+';', 'UPDATE zone_state_spawns SET hp=hp-1 WHERE id='+template['id']+';')):
        sql(statement, NAME)
        drifted = snapshot()
        failed = sql(forward, NAME, False)
        check('preimage_drift_rejected_'+table, failed.returncode != 0 and 'preimage row drift: '+table in failed.stderr, failed.stderr[-160:])
        check('drift_failure_atomic_'+table, snapshot() == drifted)
        sql(undo, NAME)
        check('drift_fixture_restored_'+table, snapshot() == baseline)
    for table in ('spawngroup','spawnentry','merchantlist'):
        sql(f'ALTER TABLE `{table}` ENGINE=MyISAM;', NAME)
        drifted = snapshot()
        failed = sql(forward, NAME, False)
        check('engine_drift_rejected_'+table, failed.returncode != 0 and 'Hub table engine changed: '+table in failed.stderr, failed.stderr[-160:])
        check('engine_drift_failure_atomic_'+table, snapshot() == drifted)
        sql(f'ALTER TABLE `{table}` ENGINE=InnoDB;', NAME)
    sql('CREATE TRIGGER review_hub_trigger BEFORE UPDATE ON merchantlist FOR EACH ROW SET NEW.item=NEW.item;', NAME)
    failed = sql(forward, NAME, False)
    check('trigger_drift_rejected', failed.returncode != 0 and 'Review hub table triggers: merchantlist' in failed.stderr, failed.stderr[-160:])
    check('trigger_drift_failure_atomic', snapshot() == baseline)
    sql('DROP TRIGGER review_hub_trigger;', NAME)
    sql(forward, NAME)
    actual = snapshot()
    expected_after = json.loads((ART/generation/'after.json').read_bytes())['rows']
    expected_after['zone_state_spawns'] = sentinels
    expected_after = {t: sorted(rows, key=lambda x: json.dumps(x,sort_keys=True)) for t,rows in expected_after.items()}
    check('forward_exact_expected_content_including_float_precision', actual == expected_after)
    check('forward_deletes_only_22_target_states', len(baseline['zone_state_spawns'])-len(actual['zone_state_spawns']) == 22)
    check('forward_preserves_corpse_instance_zone_and_unrelated_npc', actual['zone_state_spawns'] == sorted(sentinels,key=lambda x:json.dumps(x,sort_keys=True)))
    check('forward_preserves_merchant_stock_and_spawn_topology', all(actual[t]==baseline[t] for t in ('merchantlist','spawngroup','spawnentry')))
    REPORT['actual_after'] = str(ART/(generation+'-review-after.json'))
    (ART/(generation+'-review-after.json')).write_text(json.dumps(actual,separators=(',',':'))+'\n')
    applied_twice = sql(forward, NAME, False)
    check('second_forward_rejected_and_atomic', applied_twice.returncode != 0 and snapshot() == actual)
    rollback_result = sql(rollback, NAME, False)
    check('generated_rollback_executes', rollback_result.returncode == 0, rollback_result.stderr[-1000:])
    restored = snapshot()
    expected = copy.deepcopy(baseline)
    expected['zone_state_spawns'] = sorted(sentinels,key=lambda x:json.dumps(x,sort_keys=True))
    check('rollback_restores_all_content_without_stale_states', restored == expected)
    REPORT['status'] = 'passed'
except Exception as exc:
    REPORT['status'] = 'failed'
    REPORT['error'] = str(exc)[-1800:]
finally:
    if created:
        assert re.fullmatch(r'nightcap_hub_review_[0-9a-f]{32}', NAME)
        sql('DROP DATABASE `'+NAME+'`;')
        REPORT['scratch_removed'] = True
    (ART/(generation+'-review-report.json')).write_text(json.dumps(REPORT,indent=2)+'\n')
    print(json.dumps(REPORT,indent=2))
sys.exit(0 if REPORT['status']=='passed' else 1)

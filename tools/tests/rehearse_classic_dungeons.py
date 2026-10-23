"""Actual additive SQL rehearsal in a new disposable LOCAL database only."""
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from dungeon_migration import insert
from dungeon_catalog import items
from rehearse_dungeons import query

def main():
    folder=ROOT/'docs/dungeons/classic-expansion-20261022'
    capture=json.loads(Path(sys.argv[1]).read_text())
    baseline=json.loads((ROOT/'docs/dungeons/install-rows.json').read_text())
    target=json.loads((ROOT/'docs/dungeons/target-content.json').read_text())
    name='nightcap_dungeon_rehearsal_'+uuid.uuid4().hex[:12]
    print('Isolated local rehearsal: '+name,flush=True)
    query('CREATE DATABASE `'+name+'` CHARACTER SET utf8mb4;', 'information_schema')
    tables=set(target['ddl'])|{'spawn2','doors','character_tasks','character_activities','completed_tasks','tasksets'}
    for table in sorted(tables):
        if not table.startswith('nightcap_'):
            query(f'CREATE TABLE `{table}` LIKE peq.`{table}`;',name)
    query((ROOT/'server-mods/sql/20261016_dungeons.sql').read_text(),name)
    for table in ('npc_types','spawn2','spawnentry','spawngroup','doors'):
        query('\n'.join(insert(table,r) for r in capture[table]),name)
    for table,rows in baseline.items():
        if table=='items':rows=[r['values'] for r in items()]
        query('\n'.join(insert(table,r) for r in rows),name)
    # A representative existing run, credit, earned reward and fixed deadline
    # must survive the expansion. These are synthetic records in the clone.
    run='00000000-0000-4000-8000-000000000001';drop='00000000-0000-4000-8000-000000000002'
    query(f"INSERT INTO nightcap_dungeon_runs(run_id,instance_id,instance_start,zone_id,owner_id,mode,seed,revision,expires_at) VALUES ('{run}',60000,1,36,42,1,123,2026101601,9999999999); INSERT INTO nightcap_dungeon_members(run_id,character_id,reward_item,reward_drop_id) VALUES ('{run}',42,960001,'{drop}'); INSERT INTO nightcap_dungeon_kills VALUES ('{run}',42,1);",name)
    preserve=('items','nightcap_dungeon_runs','nightcap_dungeon_members','nightcap_dungeon_kills')
    def hashes():return {t:query('CHECKSUM TABLE `'+t+'` EXTENDED;',name).stdout.strip().split('\t')[-1] for t in preserve}
    before=hashes();migration=(ROOT/'server-mods/sql/20261022_classic_dungeons.sql').read_text()
    # Dangling task ownership blocks reuse even when no task definition exists.
    query('INSERT INTO tasksets(id,taskid) VALUES(4242,9714);',name)
    blocked=query(migration,name,False)
    assert blocked.returncode and 'Reserved task reference collision: tasksets' in blocked.stderr,blocked.stderr
    query('DELETE FROM tasksets WHERE id=4242; DROP PROCEDURE nightcap_classic_dungeons_20261022;',name)
    # Simulate failure after all inserts: the procedure must roll back all rows.
    fault=migration.replace('COMMIT;',"SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='synthetic expansion failure'; COMMIT;")
    failed=query(fault,name,False)
    assert failed.returncode and 'synthetic expansion failure' in failed.stderr,failed.stderr
    assert query('SELECT COUNT(*) FROM npc_types WHERE id BETWEEN 998800 AND 998814;',name).stdout.strip()=='0'
    assert before==hashes()
    query('DROP PROCEDURE nightcap_classic_dungeons_20261022;',name)
    query(migration,name)
    assert before==hashes()
    checks=json.loads((ROOT/'docs/dungeons/runtime-contract.json').read_text())['content']
    values=query(';\n'.join(c['sql'] for c in checks)+';',name).stdout.strip().splitlines()
    assert len(values)==len(checks)
    assert all(v==c['expected'] for v,c in zip(values,checks)),[(c['label'],v) for c,v in zip(checks,values) if v!=c['expected']]
    repeat=query(migration,name,False)
    assert repeat.returncode and 'Reserved identity collision' in repeat.stderr,repeat.stderr
    assert before==hashes()
    query('DROP PROCEDURE nightcap_classic_dungeons_20261022;',name)
    evidence={'status':'passed_local_isolated_SQL','database':name,'runtime_checks':len(checks),
        'dangling_task_collision_rejected':True,'mid_transaction_failure_rolled_back':True,
        'repeat_rejected':True,'existing_item_run_reward_credit_hashes':before,
        'migration_sha256':hashlib.sha256(migration.encode()).hexdigest(),'production_changed':False}
    (folder/'rehearsal.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence),flush=True)

if __name__=='__main__':
    raise SystemExit('Historical pre-reward rehearsal is frozen. Use tools/tests/rehearse_classic_rewards.py for the combined current candidate.')

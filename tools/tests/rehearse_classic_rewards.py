"""Run reward migration/fault/collision checks in a fresh isolated LOCAL DB."""
import hashlib,json,re,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from dungeon_migration import insert
from rehearse_dungeons import query

def main():
    folder=ROOT/'docs/dungeons/classic-rewards-20261022'
    content=json.loads(Path(sys.argv[1]).read_text())
    audit=json.loads((folder/'preimages.json').read_text())
    baseline=json.loads((ROOT/'docs/dungeons/install-rows.json').read_text())
    target=json.loads((ROOT/'docs/dungeons/target-content.json').read_text())
    db='nightcap_dungeon_rehearsal_'+uuid.uuid4().hex[:12]
    print('Isolated local reward rehearsal: '+db,flush=True)
    query('CREATE DATABASE `'+db+'` CHARACTER SET utf8mb4;','information_schema')
    tables=set(target['ddl'])|{'spawn2','doors','character_tasks','character_activities','completed_tasks','tasksets','spells_new','inventory','timers','character_item_recast'}
    for t in sorted(tables):
        if not t.startswith('nightcap_'):query(f'CREATE TABLE `{t}` LIKE peq.`{t}`;',db)
    claims=(ROOT/'server-mods/sql/20260930_advanced_loot.sql').read_text()
    claims=re.search(r'CREATE TABLE character_advloot_claims \(.*?ENGINE=InnoDB;',claims,re.S)[0]
    claims=claims.replace('ENGINE=InnoDB;','ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;')
    query(claims,db)
    query((ROOT/'server-mods/sql/20261016_dungeons.sql').read_text(),db)
    for t in ('npc_types','spawn2','spawnentry','spawngroup','doors'):
        query('\n'.join(insert(t,r) for r in content[t]),db)
    for t,rows in baseline.items():
        if t=='items':rows=audit['items']
        query('\n'.join(insert(t,r) for r in rows),db)
    query('\n'.join(insert('spells_new',r) for r in audit['spells']),db)
    query((ROOT/'server-mods/sql/20261022_classic_dungeons.sql').read_text(),db)
    run='00000000-0000-4000-8000-000000000001';drop='00000000-0000-4000-8000-000000000002'
    query(f"INSERT INTO nightcap_dungeon_runs(run_id,instance_id,instance_start,zone_id,owner_id,mode,seed,revision,expires_at) VALUES ('{run}',60000,1,36,42,1,123,2026101601,9999999999); INSERT INTO nightcap_dungeon_members(run_id,character_id,reward_item,reward_drop_id) VALUES ('{run}',42,960001,'{drop}'); INSERT INTO nightcap_dungeon_kills VALUES ('{run}',42,1); INSERT INTO nightcap_dungeon_checkpoints VALUES ('{run}','[]',1);",db)
    preserve=('nightcap_dungeon_runs','nightcap_dungeon_members','nightcap_dungeon_kills','nightcap_dungeon_checkpoints','character_advloot_claims')
    def hashes(tables):return {t:query('CHECKSUM TABLE `'+t+'` EXTENDED;',db).stdout.strip().split('\t')[-1] for t in tables}
    before=hashes(preserve);item_before=hashes(('items',))
    migration=(ROOT/'server-mods/sql/20261022_classic_dungeon_rewards.sql').read_text()
    def reject(text,reason):
        p=query(text,db,False)
        assert p.returncode and reason in p.stderr,p.stderr
        query('DROP PROCEDURE nightcap_classic_rewards_20261022;',db)
    cases=[
      ('orphan inventory','INSERT INTO inventory(character_id,slot_id,item_id,charges) VALUES(4242,23,960330,1);','DELETE FROM inventory WHERE character_id=4242;','Reward reference collision: inventory.item_id'),
      ('orphan entitlement',f"UPDATE nightcap_dungeon_members SET reward_item=960413 WHERE run_id='{run}';",f"UPDATE nightcap_dungeon_members SET reward_item=960001 WHERE run_id='{run}';",'Reward reference collision: nightcap_dungeon_members.reward_item'),
      ('serialized checkpoint',f"UPDATE nightcap_dungeon_checkpoints SET payload='[{{\"item_id\":960400}}]' WHERE run_id='{run}';",f"UPDATE nightcap_dungeon_checkpoints SET payload='[]' WHERE run_id='{run}';",'Serialized reward reference collision'),
      ('item recast timestamp','INSERT INTO character_item_recast(id,recast_type,timestamp) VALUES(4242,91,2100000000);','DELETE FROM character_item_recast WHERE id=4242;','Reserved item recast collision'),
      ('full preimage drift','UPDATE items SET attack=1 WHERE id=960000;','UPDATE items SET attack=0 WHERE id=960000;','Full reward preimage mismatch: 960000'),
      ('utility spell drift','UPDATE spells_new SET effect_base_value1=9 WHERE id=80;','UPDATE spells_new SET effect_base_value1=1 WHERE id=80;','Planar utility spell preimage mismatch')]
    for label,setup,cleanup,reason in cases:
        query(setup,db);reject(migration,reason);query(cleanup,db)
        assert item_before==hashes(('items',)) and before==hashes(preserve),label
    fault=migration.replace('COMMIT;',"SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='synthetic reward failure'; COMMIT;")
    reject(fault,'synthetic reward failure')
    assert item_before==hashes(('items',)) and before==hashes(preserve)
    query(migration,db)
    assert before==hashes(preserve)
    assert query('SELECT COUNT(*) FROM items WHERE id BETWEEN 960000 AND 960413 AND magic=1;',db).stdout.strip()=='414'
    contract=json.loads((ROOT/'docs/dungeons/runtime-contract.json').read_text())
    for family,checks in contract.items():
        values=query(';\n'.join(c['sql'] for c in checks)+';',db).stdout.strip().splitlines()
        assert len(values)==len(checks)
        failures=[(c['label'],v,c['expected']) for c,v in zip(checks,values) if v!=c['expected']]
        assert not failures,(family,failures)
    after=hashes(('items',));reject(migration,'Reserved reward item collision')
    assert after==hashes(('items',)) and before==hashes(preserve)
    result=dict(status='passed_local_isolated_SQL',database=db,collision_and_drift_cases=[c[0] for c in cases],
                mid_transaction_failure_rolled_back=True,repeat_rejected=True,all_magic_count=414,
                preserved=before,schema_checks=len(contract['schema']),content_checks=len(contract['content']),
                migration_sha256=hashlib.sha256(migration.encode()).hexdigest(),production_changed=False)
    (folder/'rehearsal.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()

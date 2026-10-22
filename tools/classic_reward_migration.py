"""Compile guarded reward additions from reviewed public preimages, offline."""
import hashlib
import json
from pathlib import Path
from dungeon_catalog import existing_items,items
from dungeon_contract import predicate
from dungeon_migration import ITEM_REFERENCES,insert
from dungeon_prepare import sql

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'docs/dungeons/classic-rewards-20261022'
REFERENCES={**ITEM_REFERENCES,'nightcap_dungeon_members':['reward_item'],
            'nightcap_dungeon_loot':['item_id']}
RESERVED_PATTERN=r'(^|[^0-9])960(3[3-9][0-9]|40[0-9]|41[0-3])([^0-9]|$)'

def generate():
    evidence=json.loads((FOLDER/'preimages.json').read_text())
    preimages=evidence['items'];definitions=items();new=definitions[330:]
    assert len(preimages)==330 and {r['id'] for r in preimages}==set(range(960000,960330))
    captured={r['id']:r for r in preimages}
    for row in existing_items():
        for k,v in row['values'].items():
            assert str(captured[row['id']][k])==str(v),(row['id'],k,captured[row['id']][k],v)
    out=['-- Candidate only. Disable acquisition and stop writers before this migration.',
         '-- Apply Classic dungeon expansion first. Preserve all earned items/receipts.',
         '-- Build matching world, zone, shared_memory and regenerate the item cache.',
         'DELIMITER //','CREATE PROCEDURE nightcap_classic_rewards_20261022()','BEGIN',
         'DECLARE state_revision BIGINT UNSIGNED; DECLARE state_enabled INT;',
         'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
         'START TRANSACTION;',
         'SELECT revision,enabled INTO state_revision,state_enabled FROM nightcap_dungeon_state WHERE id=1 FOR UPDATE;',
         "IF state_revision IS NULL OR state_revision<>2026101601 OR state_enabled<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Disable dungeon acquisition before reward migration'; END IF;",
         "IF NOT EXISTS (SELECT 1 FROM tasks WHERE id=9741) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Classic dungeon expansion must be installed first'; END IF;",
         "IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='items' AND engine='InnoDB') OR EXISTS (SELECT 1 FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table='items') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reward item storage contract failed'; END IF;",
         "IF EXISTS (SELECT 1 FROM items WHERE id BETWEEN 960330 AND 960413) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reserved reward item collision'; END IF;",
         "IF EXISTS (SELECT 1 FROM items WHERE recasttype BETWEEN 91 AND 93) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reserved reward cooldown collision'; END IF;"]
    for table,columns in sorted(REFERENCES.items()):
        for column in columns:
            out.append(f"IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{column}') THEN IF EXISTS (SELECT 1 FROM `{table}` WHERE `{column}` BETWEEN 960330 AND 960413) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reward reference collision: {table}.{column}'; END IF; END IF;")
    for table in ('nightcap_dungeon_checkpoints','nightcap_dungeon_corpses'):
        out.append(f"IF EXISTS (SELECT 1 FROM `{table}` WHERE payload REGEXP {sql(RESERVED_PATTERN)}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Serialized reward reference collision: {table}'; END IF;")
    out.append("IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='timers') THEN IF EXISTS (SELECT 1 FROM timers WHERE type BETWEEN 191 AND 193) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reserved persistent cooldown collision'; END IF; END IF;")
    out.append("IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='character_item_recast') THEN IF EXISTS (SELECT 1 FROM character_item_recast WHERE recast_type BETWEEN 91 AND 93) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reserved item recast collision'; END IF; END IF;")
    checks=[]
    for spell in evidence['spells']:
        check=dict(label='rewards/spell/'+str(spell['id']),sql='SELECT COUNT(*) FROM spells_new WHERE '+predicate(spell),expected='1')
        checks.append(check)
        out.append("IF NOT (("+check['sql']+") <=> 1) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Planar utility spell preimage mismatch'; END IF;")
    checks.append(dict(label='rewards/cooldowns',sql='SELECT COUNT(*) FROM items WHERE recasttype BETWEEN 91 AND 93 AND id NOT IN ('+','.join(str(r['id']) for r in new if r['values']['clickeffect']>0)+')',expected='0'))
    for row in preimages:
        out.append("IF NOT EXISTS (SELECT 1 FROM items WHERE "+predicate(row)+") THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Full reward preimage mismatch: "+str(row['id'])+"'; END IF;")
    out += ['UPDATE items SET magic=1 WHERE id BETWEEN 960000 AND 960329 AND magic=0;',
            "IF ROW_COUNT()<>220 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected MAGIC update count'; END IF;"]
    out += [insert('items',r['values']) for r in new]
    out += ['COMMIT;','END//','DELIMITER ;','CALL nightcap_classic_rewards_20261022();','DROP PROCEDURE nightcap_classic_rewards_20261022;','']
    migration=ROOT/'server-mods/sql/20261022_classic_dungeon_rewards.sql'
    migration.write_text('\n'.join(out),encoding='utf-8',newline='\n')
    (FOLDER/'runtime-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    (FOLDER/'install-rows.json').write_text(json.dumps([r['values'] for r in new],indent=2)+'\n')
    print(json.dumps({'new_items':len(new),'magic_updates':220,'migration_sha256':hashlib.sha256(migration.read_bytes()).hexdigest()}))

if __name__=='__main__':generate()

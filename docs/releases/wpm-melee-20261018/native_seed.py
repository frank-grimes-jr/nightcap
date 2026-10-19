"""Generate synthetic-test-only SQL; never a production migration."""
import gzip
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import wpm_aa,wpm_content,pet_content
from wpm_migration import insert


def main():
    sql=['''DELIMITER //
CREATE PROCEDURE wpm_fixture_guard()
BEGIN
 IF DATABASE()<>'nightcap_wpm_balance_20261018' THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Synthetic WPM database required';
 END IF;
END//
DELIMITER ;
CALL wpm_fixture_guard();
DROP PROCEDURE wpm_fixture_guard;
''']
    snapshots=[pet_content.snapshot()['tables'],wpm_content.snapshot()['tables']]
    for name in ('pet-support','rabid-bear'):
        snapshots.append(json.loads(gzip.decompress((ROOT/f'tools/fixtures/{name}-20261018.json.gz').read_bytes()))['tables'])
    merged={t:{} for t in ('items','spells_new','npc_types')}
    for snapshot in snapshots:
        for table in merged:
            for row in snapshot.get(table,[]):
                if row['id'] in merged[table] and merged[table][row['id']]!=row:raise ValueError('Fixture preimages disagree')
                merged[table][row['id']]=row
    for table,rows in merged.items():
        sql.extend(insert(table,row).replace('INSERT INTO','REPLACE INTO',1) for row in rows.values())
    for table,rows in wpm_aa.baseline().items():
        sql.append('DELETE FROM '+table+';')
        sql.extend(insert(table,row) for row in rows)
    sql.append('DELETE FROM loottable_entries WHERE loottable_id=13516;')
    sql.extend(insert('loottable_entries',r) for r in pet_content.snapshot()['tables']['loottable_entries'])
    # This database contains only existing synthetic fixture characters.
    # The candidate uses new identities; no copied character inventory is changed.
    sql.append('CREATE TABLE IF NOT EXISTS character_pet_armor LIKE peq.character_pet_armor;')
    sql.append((ROOT/'server-mods/sql/2026-10-18-pet-equipment.sql').read_text())
    for name,value in {'Character:MaxLevel':'65','Character:MaxExpLevel':'65','Expansion:CurrentExpansion':'4',
                       'World:UseClientBasedExpansionSettings':'true','Character:ItemSpellDmgCap':'250',
                       'Character:ItemHealAmtCap':'250'}.items():
        sql.append(insert('rule_values',dict(ruleset_id=1,rule_name=name,rule_value=value,notes='Synthetic WPM fixture')).replace('INSERT INTO','REPLACE INTO',1))
    pet=ROOT/'docs/releases/thj-pet-scaling-20261018/content'
    current=Path(__file__).resolve().parent/'content'
    migrations=[pet/'rabid-forward.sql',pet/'pet-support-forward.sql',pet/'pet-content-forward.sql',
                current/'aa-forward.sql',current/'items-forward.sql',
                ROOT/'server-mods/sql/2026-10-18-shared-output-caps.sql',current/'heroic-rule-forward.sql']
    sql.extend(p.read_text() for p in migrations)
    # Rehearse composition and idempotence after both acquisition paths exist.
    sql.extend(p.read_text() for p in migrations)
    target=ROOT.parent/'wpm-native-seed.sql';target.write_text('\n'.join(sql),encoding='utf-8')
    print(json.dumps({'output':str(target),'status':'synthetic_only','migrations':len(migrations)}))


if __name__=='__main__':main()

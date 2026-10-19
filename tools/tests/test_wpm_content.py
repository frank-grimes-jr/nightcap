import os
import unittest
import wpm_content as content
import wpm_aa
from wpm_migration import insert,migration,predicate


class WPMContent(unittest.TestCase):
    def test_pairing_and_acquisition(self):
        items=content.item_rows();spells=content.spell_rows()
        self.assertEqual(len(items),12);self.assertEqual(len(spells),12)
        self.assertEqual(len({r['id'] for r in items}),12)
        schema=set(content.snapshot()['tables']['items'][0])
        self.assertTrue(all(set(r)==schema for r in items))
        self.assertTrue(all(r['id']<=1048575 for r in items))
        self.assertTrue(all(len(r)==237 for r in spells))
        self.assertTrue(all(r['mana']==0 and r['cast_time']==0 for r in spells))
        self.assertTrue(all(r[f'classes{i}']==255 for r in spells for i in range(1,17)))
        raw=('\r\n'.join(content.client_rows().values())+'\r\n').encode('latin1')
        self.assertEqual(content.client_spells(raw),raw)
        with self.assertRaises(ValueError):content.client_spells(raw.replace(b'Holy Shield Rune',b'Holy Shield X'))
        for group in content.groups():
            if group['table']=='lootdrop_entries':
                self.assertEqual(sum(r['chance'] for r in group['after']),100)
                self.assertEqual(len(group['after']),4)
            if group['table']=='loottable_entries':self.assertEqual(list(group['key']),['lootdrop_id'])
        for old,new in content.gear_changes():
            self.assertEqual(old['damage'],new['damage']);self.assertEqual(old['delay'],new['delay'])
            self.assertEqual(old['augslot2type'],new['augslot2type'])
        rollback=content.groups(True)
        self.assertEqual(len(rollback),3)
        self.assertTrue(all(g['table']=='loottable_entries' and not g['after'] for g in rollback))

    def test_generated_migrations_current_and_content_only(self):
        for rollback in (False,True):
            name='items-acquisition-rollback.sql' if rollback else 'items-forward.sql'
            self.assertEqual((content.RELEASE/name).read_text(),migration(content.groups(rollback),'nightcap_wpm_items_20261018'))
        self.assertTrue(all(g['table'] in ('aa_ability','aa_ranks','aa_rank_effects','aa_rank_prereqs') for g in wpm_aa.groups()))
        self.assertIn('BINARY `Name`',predicate({'Name':'Hopebringer'}))

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','isolated DB rehearsal opt-in')
    def test_real_database_replay_and_owned_content_preserving_rollback(self):
        from pok_hub_migration import read_sql
        rows={**content.snapshot()['tables'],**wpm_aa.baseline()}
        tables=('items','spells_new','lootdrop','lootdrop_entries','loottable_entries','npc_types',
                'aa_ability','aa_ranks','aa_rank_effects','aa_rank_prereqs')
        sql=['DROP PROCEDURE IF EXISTS wpm_test_items;','DROP PROCEDURE IF EXISTS wpm_test_aa;',
             'DROP PROCEDURE IF EXISTS wpm_test_rollback;']
        for table in tables:
            sql.extend([f'CREATE TEMPORARY TABLE template_{table} LIKE peq.{table};',f'CREATE TEMPORARY TABLE {table} LIKE template_{table};'])
            sql.extend(insert(table,r) for r in rows.get(table,[]))
        for groups,name in ((content.groups(),'wpm_test_items'),(wpm_aa.groups(),'wpm_test_aa')):
            sql.extend([migration(groups,name),migration(groups,name)])
            for i,g in enumerate(groups):
                sql.append(f"SELECT '{name}_{i}', COUNT(*) FROM {g['table']} WHERE "+predicate(g['key'])+';')
        sql.extend([migration(content.groups(True),'wpm_test_rollback')]*2)
        sql.append("SELECT 'ACQUISITION',COUNT(*) FROM loottable_entries WHERE lootdrop_id BETWEEN 988620 AND 988622;")
        for row in content.item_rows():sql.append(f"SELECT 'OWNED_{row['id']}',COUNT(*) FROM items WHERE "+predicate(row)+';')
        result=dict(line.split('\t',1) for line in read_sql('\n'.join(sql)).splitlines() if '\t' in line)
        self.assertEqual(result.pop('ACQUISITION'),'0')
        for groups,name in ((content.groups(),'wpm_test_items'),(wpm_aa.groups(),'wpm_test_aa')):
            for i,g in enumerate(groups):self.assertEqual(int(result.pop(f'{name}_{i}')),len(g['after']))
        self.assertTrue(result and all(v=='1' for v in result.values()))

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','isolated DB rehearsal opt-in')
    def test_late_collision_rolls_back_and_case_drift_rejected(self):
        from pok_hub_migration import read_sql
        for case in ('late_collision','case_drift'):
            with self.subTest(case=case):
                rows=content.snapshot()['tables'];sql=[]
                for table in ('items','spells_new','lootdrop','lootdrop_entries','loottable_entries','npc_types'):
                    sql.extend([f'CREATE TEMPORARY TABLE template_{table} LIKE peq.{table};',f'CREATE TEMPORARY TABLE {table} LIKE template_{table};'])
                    sql.extend(insert(table,r) for r in rows.get(table,[]))
                if case=='late_collision':
                    last=next(g for g in reversed(content.groups()) if g['table']=='loottable_entries')
                    sql.append(insert('loottable_entries',dict(last['after'][0],loottable_id=1)))
                else:
                    old,_=content.gear_changes()[0]
                    sql.append(f"UPDATE items SET Name=LOWER(Name) WHERE id={old['id']};")
                guarded=migration(content.groups(),'wpm_test_failure').replace('CALL wpm_test_failure();', '''DELIMITER //
CREATE PROCEDURE wpm_test_catch()
BEGIN
 DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET @failed=1;
 SET @failed=0;
 CALL wpm_test_failure();
END//
DELIMITER ;
CALL wpm_test_catch();
DROP PROCEDURE wpm_test_catch;''')
                sql.extend([guarded,"SELECT 'FAILED',@failed;",
                    'SELECT \'NEW_ITEMS\',COUNT(*) FROM items WHERE id IN ('+','.join(str(r['id']) for r in content.item_rows())+');',
                    'SELECT \'NEW_SPELLS\',COUNT(*) FROM spells_new WHERE id BETWEEN 42840 AND 42851;'])
                values=dict(line.split('\t',1) for line in read_sql('\n'.join(sql)).splitlines() if '\t' in line)
                self.assertEqual(values,{'FAILED':'1','NEW_ITEMS':'0','NEW_SPELLS':'0'})

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','isolated DB rehearsal opt-in')
    def test_heroic_rule_enable_disable_replay(self):
        from pok_hub_migration import read_sql
        sql=['CREATE TEMPORARY TABLE template_rule_values LIKE peq.rule_values;',
             'CREATE TEMPORARY TABLE rule_values LIKE template_rule_values;']
        for operation in ('forward','forward','disable','disable','enable','enable'):
            sql.append((content.RELEASE/f'heroic-rule-{operation}.sql').read_text())
        sql.append("SELECT rule_value FROM rule_values WHERE rule_name='Combat:NightcapHeroicMeleeScaling';")
        self.assertEqual(read_sql('\n'.join(sql)).strip(),'true')


if __name__=='__main__':unittest.main()

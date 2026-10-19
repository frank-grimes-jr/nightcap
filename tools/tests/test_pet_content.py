import os
import unittest
import pet_content as policy
from rabid_bear import predicate


class PetContent(unittest.TestCase):
    def test_proc_resources_targets_scaling_and_client_pairing(self):
        spells=policy.spell_rows();items=policy.item_rows()
        self.assertEqual(len({r['id'] for r in spells}),8)
        self.assertEqual(len({r['id'] for r in items}),8)
        for row in spells:
            kind=(row['id']-42830)%2;tier=(row['id']-42830)//2
            self.assertEqual(len(row),237)
            self.assertEqual(row['targettype'],6)
            self.assertEqual(row['goodEffect'],1)
            self.assertEqual(row['mana'],0)
            self.assertEqual(row['cast_time'],0)
            self.assertEqual(row['effectid1'],55 if kind else 0)
            self.assertEqual(row['effect_base_value1'],(policy.RUNES if kind else policy.HEALS)[tier])
            self.assertEqual(row['formula1'],100)
            self.assertEqual(row['max1'],0)
            self.assertEqual(list(row.values())[219],0) # native NO_HEAL_DAMAGE_ITEM_MOD
            self.assertTrue(all(row[f'classes{i}']==255 for i in range(1,17)))
            self.assertTrue(all(row[f'components{i}']==-1 for i in range(1,5)))
        for row in items:
            self.assertLessEqual(row['id'],1048575)
            self.assertEqual(row['augtype'],(1<<3)|(1<<7))
            self.assertEqual(row['augrestrict'],2)
            self.assertEqual(row['procrate'],0)
            self.assertIn(row['proceffect'],policy.SPELL_IDS)
            self.assertEqual(row['price'],0)
            self.assertEqual(row['nopet'],0)
        raw='\r\n'.join('^'.join('' if v is None else str(v) for v in r.values()) for r in policy.snapshot()['tables']['spells_new']).encode('latin1')
        paired=policy.client_spells(raw)
        self.assertEqual(policy.client_spells(paired),paired)
        with self.assertRaisesRegex(ValueError,'identity drift'):
            policy.client_spells(paired.replace(b'Healing Fragment 1',b'Healing Fragment X'))

    def test_gear_changes_preserve_weapon_ratio_and_cosmetics(self):
        changes=policy.gear_changes()
        self.assertEqual(len(changes),33)
        for old,new in changes:
            changed={k for k in old if old[k]!=new[k]}
            self.assertLessEqual(changed,{'spelldmg','healamt','haste','augslot3type','augslot3visible'})
            self.assertEqual(old['damage'],new['damage'])
            self.assertEqual(old['delay'],new['delay'])
            self.assertEqual(old['augslot2type'],new['augslot2type'])
            self.assertTrue(all(new[k]>=old[k] for k in ('spelldmg','healamt','haste')))
        drops=[r for t,r,_ in policy.new_rows() if t=='lootdrop_entries']
        self.assertEqual(sum(r['chance'] for r in drops),100)
        self.assertEqual(len(drops),8)

    def test_generated_sql_current(self):
        for rollback in (False,True):
            name='pet-content-acquisition-rollback.sql' if rollback else 'pet-content-forward.sql'
            self.assertEqual((policy.RELEASE/name).read_text(),policy.migration(rollback))

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','local DB rehearsal opt-in')
    def test_real_database_activation_idempotence_and_preserving_rollback(self):
        from pok_hub_migration import read_sql
        source=policy.snapshot()['tables'];sql=[]
        for table in ('items','spells_new','lootdrop','lootdrop_entries','loottable_entries','npc_types'):
            sql += [f'CREATE TEMPORARY TABLE template_{table} LIKE peq.{table};',
                    f'CREATE TEMPORARY TABLE {table} LIKE template_{table};']
            sql += [policy.insert(table,row) for row in source.get(table,[])]
        sql += [policy.migration(),policy.migration()]
        for table,row,_ in policy.new_rows():
            label=f"NEW_{table}_{row.get('id',row.get('item_id',row.get('loottable_id',0)))}"
            sql.append(f"SELECT '{label}', COUNT(*) FROM {table} WHERE {predicate(row)};")
        for old,row in policy.gear_changes():
            sql.append(f"SELECT 'GEAR_{row['id']}', COUNT(*) FROM items WHERE {predicate(row)};")
        sql += [policy.migration(True),policy.migration(True)]
        sql.append(f"SELECT 'ACQUISITION', COUNT(*) FROM loottable_entries WHERE lootdrop_id={policy.DROP_ID};")
        for row in policy.item_rows():
            sql.append(f"SELECT 'KEPT_{row['id']}', COUNT(*) FROM items WHERE {predicate(row)};")
        values=dict(line.split('\t',1) for line in read_sql('\n'.join(sql)).splitlines() if '\t' in line)
        self.assertEqual(values.pop('ACQUISITION'),'0')
        self.assertTrue(values)
        self.assertTrue(all(v=='1' for v in values.values()),values)


if __name__=='__main__': unittest.main()

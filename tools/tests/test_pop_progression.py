import os
import json
import unittest
import pop_progression as policy
from pet_content import insert
from rabid_bear import predicate


class PopProgression(unittest.TestCase):
    def test_earned_progression_and_deterministic_append(self):
        data=policy.snapshot();rows=policy.additions(data)
        self.assertEqual(len(rows),389)
        originals={(r['merchantid'],r['slot']) for r in data['tables']['merchantlist']}
        self.assertTrue(all((r['merchantid'],r['slot']) not in originals and r['slot']<=500 for r in rows))
        identities=json.loads((policy.RELEASE/'catalog-policy.json').read_text())['merchants']
        captured={r['id']:r for r in data['tables']['npc_types']}
        self.assertEqual(len(identities),16)
        for row in identities:
            self.assertEqual(row['name'],captured[row['npc_id']]['name'])
            self.assertEqual(row['merchant_id'],captured[row['npc_id']]['merchant_id'])
        for name,expected in [('forward.sql',policy.migration()),('vendor_restock.sql',policy.migration(False))]:
            self.assertEqual((policy.RELEASE/name).read_text(),expected)
            self.assertNotIn('character_',expected)

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','local DB rehearsal opt-in')
    def test_real_database_preserves_stock_and_repeated_activation(self):
        from pok_hub_migration import read_sql
        data=policy.snapshot();sql=[]
        for table in ('items','spells_new','merchantlist','npc_types','rule_values'):
            sql += [f'CREATE TEMPORARY TABLE template_{table} LIKE peq.{table};',f'CREATE TEMPORARY TABLE {table} LIKE template_{table};']
            if table=='spells_new':
                rows=[dict(id=int(key),name=row['name']) for key,row in data['original_spells'].items()]
            else: rows=data['tables'][table]
            sql += [insert(table,row) for row in rows]
        sql += [policy.migration(),policy.migration(),policy.migration(False)]
        for row in data['tables']['merchantlist']+policy.additions(data):
            sql.append(f"SELECT 'ROW_{row['merchantid']}_{row['slot']}',COUNT(*) FROM merchantlist WHERE {predicate(row)};")
        sql.append("SELECT 'ERA',rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Expansion:CurrentExpansion';")
        sql.append("SELECT 'LEVEL',rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Character:MaxLevel';")
        values=dict(line.split('\t',1) for line in read_sql('\n'.join(sql)).splitlines() if '\t' in line)
        self.assertEqual(values.pop('ERA'),'4');self.assertEqual(values.pop('LEVEL'),'65')
        self.assertEqual(len(values),1747+389);self.assertTrue(all(v=='1' for v in values.values()))

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','local DB rehearsal opt-in')
    def test_late_destination_conflict_rolls_back_rules_and_prior_inserts(self):
        from pok_hub_migration import read_sql
        data=policy.snapshot();sql=[]
        for table in ('items','spells_new','merchantlist','npc_types','rule_values'):
            sql += [f'CREATE TEMPORARY TABLE template_{table} LIKE peq.{table};',f'CREATE TEMPORARY TABLE {table} LIKE template_{table};']
            rows=([dict(id=int(key),name=row['name']) for key,row in data['original_spells'].items()]
                  if table=='spells_new' else data['tables'][table])
            sql += [insert(table,row) for row in rows]
        sql.append(insert('merchantlist',dict(policy.additions(data)[-1],item=1)))
        migration=policy.migration().replace('CALL nightcap_pop_progression_20261018();', '''DELIMITER //
CREATE PROCEDURE test_pop_failure()
BEGIN
 DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET @failed=1;
 SET @failed=0;
 CALL nightcap_pop_progression_20261018();
END//
DELIMITER ;
CALL test_pop_failure();
DROP PROCEDURE test_pop_failure;''')
        sql += [migration,"SELECT 'FAILED',@failed;","SELECT 'ROWS',COUNT(*) FROM merchantlist;"]
        for row in data['tables']['rule_values']:
            sql.append(f"SELECT '{row['rule_name']}',COUNT(*) FROM rule_values WHERE {predicate(row)};")
        values=dict(line.split('\t',1) for line in read_sql('\n'.join(sql)).splitlines() if '\t' in line)
        self.assertEqual(values.pop('FAILED'),'1');self.assertEqual(values.pop('ROWS'),'1748')
        self.assertTrue(all(v=='1' for v in values.values()))


if __name__=='__main__':unittest.main()

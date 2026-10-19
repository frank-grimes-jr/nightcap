import os
import unittest
from test_pet_equipment import ROOT


@unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','local DB rehearsal opt-in')
class SharedCaps(unittest.TestCase):
    def test_caps_idempotent_preserve_other_rules_and_reject_drift(self):
        from pok_hub_migration import read_sql
        migration=(ROOT/'server-mods/sql/2026-10-18-shared-output-caps.sql').read_text()
        sql=['CREATE TEMPORARY TABLE rule_template LIKE peq.rule_values;',
             'CREATE TEMPORARY TABLE rule_values LIKE rule_template;',
             "INSERT INTO rule_values (ruleset_id,rule_name,rule_value,notes) VALUES (1,'Character:ItemSpellDmgCap','250','keep'),(1,'Character:ItemHealAmtCap','250','keep'),(1,'Nightcap:Headroom','30','keep');",
             migration,migration,
             "SELECT 'UPDATED',COUNT(*) FROM rule_values WHERE rule_value='750' AND notes='keep';",
             "SELECT 'OTHER',rule_value FROM rule_values WHERE rule_name='Nightcap:Headroom';",
             "UPDATE rule_values SET rule_value='251' WHERE rule_name='Character:ItemHealAmtCap';"]
        guarded=migration.replace('CALL nightcap_output_caps_20261018();','''DELIMITER //
CREATE PROCEDURE test_caps_failure()
BEGIN
 DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET @failed=1;
 SET @failed=0;
 CALL nightcap_output_caps_20261018();
END//
DELIMITER ;
CALL test_caps_failure();
DROP PROCEDURE test_caps_failure;''')
        sql += [guarded,"SELECT 'FAILED',@failed;","SELECT 'DRIFT_KEPT',rule_value FROM rule_values WHERE rule_name='Character:ItemHealAmtCap';"]
        values=dict(line.split('\t',1) for line in read_sql('\n'.join(sql)).splitlines() if '\t' in line)
        self.assertEqual(values,dict(UPDATED='2',OTHER='30',FAILED='1',DRIFT_KEPT='251'))


if __name__=='__main__':unittest.main()

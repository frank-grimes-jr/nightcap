"""Real MariaDB staging-failure atomicity; uses only temporary item rows."""
import os,unittest
from thj_item_migration import migration
from wpm_migration import insert
import thj_combined_content as content
class ItemStaging(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','isolated DB opt-in')
    def test_missing_hash_or_value_batch_rejects_before_any_item_write(self):
        from pok_hub_migration import read_sql
        pairs=content.item_changes()[:3];columns=content.capture()['schemas']['items']['columns']
        from wpm_migration import predicate
        for table in ('nightcap_thj_item_preimages','nightcap_thj_item_values'):
            with self.subTest(table=table):
                setup=['CREATE TEMPORARY TABLE items LIKE peq.items;']+[insert('items',old) for old,new in pairs]
                script=migration(pairs,columns)
                call='CALL nightcap_thj_items_20261018();'
                replacement=f"DELETE FROM {table} WHERE id={pairs[-1][0]['id']};\n"+"""DELIMITER //
CREATE PROCEDURE nightcap_thj_test_catch()
BEGIN
 DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET @failed=1;
 SET @failed=0; CALL nightcap_thj_items_20261018();
END//
DELIMITER ;
CALL nightcap_thj_test_catch();
DROP PROCEDURE nightcap_thj_test_catch;"""
                setup += [script.replace(call,replacement),"SELECT 'FAILED',@failed;"]
                for old,new in pairs:setup.append("SELECT 'PRESERVED',COUNT(*) FROM items WHERE "+predicate(old)+';')
                self.assertEqual(read_sql('\n'.join(setup)).strip(),'FAILED\t1\n'+'\n'.join(['PRESERVED\t1']*len(pairs)))
if __name__=='__main__':unittest.main()

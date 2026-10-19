import json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import thj_combined_content as content
from thj_item_migration import migration,row_hash
from wpm_migration import insert

class CombinedContent(unittest.TestCase):
    def test_starter_dungeon_and_companion_preservation(self):
        before=content.after_companions(content.original_items());after=content.proposed_items(before)
        self.assertEqual([after[4204+o]['ac'] for o in (0,200000,400000,600000)],[6,7,8,9])
        self.assertEqual([after[i]['ac'] for i in (960003,960005,960219,960221)],[12,16,24,32])
        sword=next(i for i,r in before.items() if r['Name']=='Bronze Long Sword')
        self.assertEqual([after[sword+o]['damage'] for o in (0,200000,400000,600000)],[4,5,6,7])
        for ident,row in after.items():
            for field in ('id','Name','delay','classes','slots','reqlevel','reclevel','proceffect','worneffect','focuseffect','augslot1type','augslot2type','augslot3type','augslot4type','augslot5type','augslot6type'):
                self.assertEqual(row[field],before[ident][field],(ident,field))
        self.assertEqual(after[651912]['worneffect'],42847)
        self.assertEqual(after[651912]['hp'],30)
        self.assertEqual(after[626740]['augslot2type'],before[626740]['augslot2type'])

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','session-local temporary item table')
    def test_real_database_repeat_recovery_and_reapply(self):
        from pok_hub_migration import read_sql
        pairs=content.item_changes();columns=content.capture()['schemas']['items']['columns']
        setup=['CREATE TEMPORARY TABLE thj_template LIKE peq.items;','CREATE TEMPORARY TABLE items LIKE thj_template;']
        setup.extend(insert('items',old) for old,new in pairs)
        forward=migration(pairs,columns,content.after_companions(content.original_items()))
        rollback=migration(content.recovery_changes(),columns)
        sql=setup+[forward,forward,rollback,rollback,forward,forward]
        # Every full-row afterimage was checked by each migration. Verify total too.
        sql.append("SELECT 'COUNT',COUNT(*) FROM items;")
        self.assertEqual(read_sql('\n'.join(sql)).strip(),f'COUNT\t{len(pairs)}')

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','session-local temporary item table')
    def test_late_unowned_field_drift_rejects_every_update(self):
        from pok_hub_migration import read_sql
        pairs=content.item_changes();columns=content.capture()['schemas']['items']['columns']
        setup=['CREATE TEMPORARY TABLE thj_template LIKE peq.items;','CREATE TEMPORARY TABLE items LIKE thj_template;']
        setup.extend(insert('items',old) for old,new in pairs)
        setup.append(f"UPDATE items SET Name=LOWER(Name) WHERE id={pairs[-1][0]['id']};")
        guarded=migration(pairs,columns).replace('CALL nightcap_thj_items_20261018();', '''DELIMITER //
CREATE PROCEDURE nightcap_thj_test_catch()
BEGIN
 DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET @failed=1;
 SET @failed=0; CALL nightcap_thj_items_20261018();
END//
DELIMITER ;
CALL nightcap_thj_test_catch();
DROP PROCEDURE nightcap_thj_test_catch;''')
        from wpm_migration import predicate
        setup += [guarded,"SELECT 'FAILED',@failed;",'SELECT \'FIRST_PRESERVED\',COUNT(*) FROM items WHERE '+predicate(pairs[0][0])+';']
        self.assertEqual(read_sql('\n'.join(setup)).strip(),'FAILED\t1\nFIRST_PRESERVED\t1')

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','session-local temporary item table')
    def test_afterimage_failure_rolls_back_all_updates(self):
        from pok_hub_migration import read_sql
        pairs=content.item_changes();columns=content.capture()['schemas']['items']['columns']
        setup=['CREATE TEMPORARY TABLE thj_template LIKE peq.items;','CREATE TEMPORARY TABLE items LIKE thj_template;']
        setup.extend(insert('items',old) for old,new in pairs)
        guarded=migration(pairs,columns)
        guarded=guarded.replace(' SET finished=FALSE; OPEN targets; verify_rows: LOOP',
            f" UPDATE items SET Name=CONCAT(Name,' fault') WHERE id={pairs[-1][0]['id']};\n SET finished=FALSE; OPEN targets; verify_rows: LOOP")
        guarded=guarded.replace('CALL nightcap_thj_items_20261018();','''DELIMITER //
CREATE PROCEDURE nightcap_thj_test_catch()
BEGIN
 DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET @failed=1;
 SET @failed=0; CALL nightcap_thj_items_20261018();
END//
DELIMITER ;
CALL nightcap_thj_test_catch();
DROP PROCEDURE nightcap_thj_test_catch;''')
        guarded=guarded.replace('DROP TEMPORARY TABLE nightcap_thj_item_preimages;','')
        expression="SHA2(CONCAT_WS('|',"+','.join("IFNULL(HEX(CAST(i.`"+c+"` AS CHAR CHARACTER SET utf8mb4)),'NULL')" for c in columns)+'),256)'
        setup += [guarded,"SELECT 'FAILED',@failed;",f"SELECT 'ALL_PRESERVED',COUNT(*) FROM items i JOIN nightcap_thj_item_preimages p ON p.id=i.id WHERE BINARY {expression}=BINARY p.before_hash;"]
        self.assertEqual(read_sql('\n'.join(setup)).strip(),f'FAILED\t1\nALL_PRESERVED\t{len(pairs)}')

if __name__=='__main__':unittest.main()

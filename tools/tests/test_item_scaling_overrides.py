import os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import item_scaling_overrides as compiler
import thj_combined_content as combined
import tier_spell_scaling
from wpm_migration import insert

class Regeneration(unittest.TestCase):
    def test_generic_planner_cannot_overwrite_owned_policy(self):
        rows=list(combined.original_items().values())
        protected=[r for r in rows if r['id']%200000 in compiler.protected_bases()]
        protected=[{k:(int(v) if k in tier_spell_scaling.FIELDS+tier_spell_scaling.STATS and k!='Name' else v) for k,v in r.items()} for r in protected]
        self.assertEqual(tier_spell_scaling.plan(protected),[])
        compiler.sync(check=True)
        tier_spell_scaling.sync_sql(check=True)

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','session-local temporary item table')
    def test_regeneration_matches_reviewed_item_afterimages(self):
        from pok_hub_migration import read_sql
        before=combined.original_items();after=combined.proposed_items(combined.after_companions(before))
        sql=['CREATE TEMPORARY TABLE thj_template LIKE peq.items;','CREATE TEMPORARY TABLE items LIKE thj_template;']
        sql.extend(insert('items',row) for row in before.values())
        sql += [compiler.block(),compiler.block()]
        expected=[]
        for row in compiler.overrides():
            fields=sorted(row['fields']);ident=row['id']
            sql.append("SELECT id,"+','.join('`'+f+'`' for f in fields)+f' FROM items WHERE id={ident};')
            expected.append('\t'.join(map(str,[ident,*[after[ident][f] for f in fields]])))
        self.assertEqual(read_sql('\n'.join(sql)).strip(),'\n'.join(expected))

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','session-local temporary item table')
    def test_missing_or_renamed_identity_rejected_before_starter_updates(self):
        from pok_hub_migration import read_sql
        before=combined.original_items()
        guarded=compiler.block().replace('CALL nightcap_reviewed_item_scaling();','''DELIMITER //
CREATE PROCEDURE nightcap_compiler_test_catch()
BEGIN
 DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET @failed=1;
 SET @failed=0; CALL nightcap_reviewed_item_scaling();
END//
DELIMITER ;
CALL nightcap_compiler_test_catch();
DROP PROCEDURE nightcap_compiler_test_catch;''')
        for missing,renamed in [(805532,None),(5532,None),(None,5532)]:
            with self.subTest(missing=missing,renamed=renamed):
                sql=['CREATE TEMPORARY TABLE thj_template LIKE peq.items;','CREATE TEMPORARY TABLE items LIKE thj_template;']
                sql.extend(insert('items',row) for ident,row in before.items() if ident!=missing)
                if renamed:
                    sql.append(f"UPDATE items SET Name=LOWER(Name) WHERE id={renamed};")
                sql += [guarded,"SELECT @failed,ac FROM items WHERE id=4204;"]
                self.assertEqual(read_sql('\n'.join(sql)).strip(),f'1\t{before[4204]["ac"]}')

if __name__=='__main__':unittest.main()

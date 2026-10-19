"""Replay SQL emitted by the native transfer test against session-local tables.

Opt in with NIGHTCAP_DB_TESTS=1 and NIGHTCAP_TEST_EVIDENCE pointing to that trace.
Permanent PEQ tables are only read as a schema template. Closing the one mysql
session removes all temporary tables, including on an assertion/error.
"""
import json
import os
from pathlib import Path
import unittest
from pok_hub_migration import read_sql


@unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS') == '1', 'database rehearsal requires explicit opt-in')
class PetArmorDatabase(unittest.TestCase):
    def test_complete_instance_roundtrip_and_rollback(self):
        trace = json.loads((Path(os.environ['NIGHTCAP_TEST_EVIDENCE'])/'pet-transfer-sql.json').read_text())
        columns = ['character_id','slot_id','item_id','charges','color','augment_one','augment_two','augment_three',
                   'augment_four','augment_five','augment_six','instnodrop','custom_data','ornament_icon',
                   'ornament_idfile','ornament_hero_model','guid']
        expected = dict(zip(columns,[77,33,1001,0,0xff010203,201,202,203,204,205,206,1,"key^quote'\\line\n^",601,602,-4,901]))
        values = ["X'"+value.encode().hex()+"'" if isinstance(value,str) else str(value) for value in expected.values()]
        insert = 'INSERT INTO inventory ('+','.join(columns)+') VALUES ('+','.join(values)+');'
        fields = ','.join("'"+c+"',`"+c+'`' for c in columns)
        def snapshot(label, table):
            return f"SELECT '{label}',JSON_OBJECT({fields}) FROM {table};"
        schema = (Path(__file__).resolve().parents[2]/'server-mods/sql/2026-09-19-pet-armor.sql').read_text()
        schema = schema.replace('CREATE TABLE character_pet_armor LIKE inventory;',
                                'CREATE TEMPORARY TABLE character_pet_armor LIKE inventory;')
        sql = ['CREATE TEMPORARY TABLE nightcap_inventory_template LIKE peq.inventory;',
               'CREATE TEMPORARY TABLE inventory LIKE nightcap_inventory_template;', schema,
               (Path(__file__).resolve().parents[2]/'server-mods/sql/2026-10-18-pet-equipment.sql').read_text(), insert]
        sql += [q+';' for q in trace['equip'][5:]]
        sql += [snapshot('EQUIPPED','character_pet_armor'), "SELECT 'CURSOR_EMPTY',COUNT(*) FROM inventory;"]
        sql += [q+';' for q in trace['remove'][5:]]
        sql += [snapshot('RETURNED','inventory'), "SELECT 'ARMOR_EMPTY',COUNT(*) FROM character_pet_armor;"]
        # Restore the original fixture serial, then exercise rollback after INSERT
        # and after DELETE using the exact production statements.
        sql += ['UPDATE inventory SET guid=901;']
        for end,label in ((10,'ROLLBACK_INSERT'),(11,'ROLLBACK_DELETE')):
            sql += [q+';' for q in trace['equip'][5:end]] + ['ROLLBACK;',snapshot(label,'inventory')]
            sql += [f"SELECT '{label}_ARMOR',COUNT(*) FROM character_pet_armor;"]
        # A one-byte custom-data change must fail the binary preimage predicate.
        sql += ["UPDATE inventory SET custom_data=CONCAT(custom_data,' ');",trace['equip'][8]+';']
        # Count through the exact CAS WHERE clause without writing anything.
        where = trace['equip'][8].split(' WHERE ',1)[1].removesuffix(' FOR UPDATE')
        sql += ["SELECT 'STALE_CUSTOM_DATA',COUNT(*) FROM inventory WHERE "+where+';']
        rows = {}
        for line in read_sql('\n'.join(sql)).splitlines():
            if '\t' not in line: continue
            label,value = line.split('\t',1)
            if label in ('EQUIPPED','RETURNED','ROLLBACK_INSERT','ROLLBACK_DELETE'):
                rows[label] = json.loads(value)
            elif label in ('CURSOR_EMPTY','ARMOR_EMPTY','ROLLBACK_INSERT_ARMOR','ROLLBACK_DELETE_ARMOR','STALE_CUSTOM_DATA'):
                self.assertEqual(value,'0',label)
                rows[label] = 0
        equipped = {**expected,'slot_id':2}
        self.assertEqual(rows['EQUIPPED'],equipped)
        self.assertEqual(rows['RETURNED'],{**expected,'guid':902})
        self.assertEqual(rows['ROLLBACK_INSERT'],expected)
        self.assertEqual(rows['ROLLBACK_DELETE'],expected)
        self.assertEqual(len(rows),9)
        (Path(os.environ['NIGHTCAP_TEST_EVIDENCE'])/'pet-database-rehearsal.json').write_text(
            json.dumps({'status':'passed','scope':'session-local temporary tables only','checks':rows},indent=2)+'\n')


if __name__ == '__main__': unittest.main()

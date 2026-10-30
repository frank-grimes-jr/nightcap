"""Execute native-generated SQL against a connection-local MariaDB shadow table.

Set NIGHTCAP_ITEM_XP_DB_TEST=1. Only peq.inventory's schema is read; real rows
are never selected or changed. The temporary inventory table disappears on close.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import test_free_trade as native


@unittest.skipUnless(os.environ.get('NIGHTCAP_ITEM_XP_DB_TEST') == '1', 'explicit disposable DB test opt-in')
class ItemXPDatabaseTests(unittest.TestCase):
    def test_exact_saved_row_and_replay(self):
        import pymysql
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'updates.sql'
            native.FreeTradeTests.compile_run(self, r'''
#include "common/item_xp_inventory.h"
#include <fstream>
int main() {
    NightcapBazaar::Row before={"7","21","1001","32767","123","1","2","3","4","5","6","1","","8","9","10","42"};
    auto partial=before; partial[12]="6E696768746361705F6974656D5F78705E313A313030313A3132335E";
    auto upgraded=before; upgraded[2]="201001"; upgraded[4]="456";
    std::ofstream out(R"PATH(''' + output.as_posix() + r''')PATH");
    out<<NightcapItemXP::UpdateSQL(before,partial)<<'\n';
    out<<NightcapItemXP::UpdateSQL(partial,upgraded)<<'\n';
}
''')
            queries = output.read_text().splitlines()
        container = os.environ.get('NIGHTCAP_ITEM_XP_DB_CONTAINER','akk-stack-mariadb-1')
        details = json.loads(subprocess.check_output(['docker','inspect',container], text=True))[0]
        env = dict(entry.split('=',1) for entry in details['Config']['Env'] if '=' in entry)
        password = env.get('MARIADB_ROOT_PASSWORD') or env.get('MYSQL_ROOT_PASSWORD')
        standalone = container != 'akk-stack-mariadb-1'
        schema,port = 'peq',3307
        if standalone:
            self.assertEqual(details['Config']['Labels'].get('nightcap.task'),'power-source-item-xp')
            binding=details['NetworkSettings']['Ports']['3306/tcp'][0]
            self.assertEqual(binding['HostIp'],'127.0.0.1')
            schema,port='item_xp_test',int(binding['HostPort'])
        db = pymysql.connect(host='127.0.0.1',port=port,user='root',password=password,database=schema,
                             autocommit=True,connect_timeout=5,read_timeout=15,write_timeout=15)
        self.addCleanup(db.close)
        cursor = db.cursor()
        if standalone:
            # Explicit synthetic schema: native persisted fields and InnoDB
            # semantics, not a claim of current deployment-schema verification.
            cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
              character_id INT UNSIGNED NOT NULL, slot_id INT UNSIGNED NOT NULL,
              item_id INT UNSIGNED NOT NULL, charges SMALLINT UNSIGNED NOT NULL,
              color INT UNSIGNED NOT NULL, augment_one INT UNSIGNED NOT NULL,
              augment_two INT UNSIGNED NOT NULL, augment_three INT UNSIGNED NOT NULL,
              augment_four INT UNSIGNED NOT NULL, augment_five INT UNSIGNED NOT NULL,
              augment_six INT UNSIGNED NOT NULL, instnodrop TINYINT UNSIGNED NOT NULL,
              custom_data TEXT NULL, ornament_icon INT UNSIGNED NOT NULL,
              ornament_idfile INT UNSIGNED NOT NULL, ornament_hero_model INT NOT NULL,
              guid BIGINT UNSIGNED NOT NULL, PRIMARY KEY(character_id,slot_id)
            ) ENGINE=InnoDB''')
        cursor.execute('SHOW CREATE TABLE '+schema+'.inventory')
        definition = cursor.fetchone()[1]
        self.assertTrue(definition.startswith('CREATE TABLE `inventory`'))
        self.assertIn('ENGINE=InnoDB', definition)
        cursor.execute(definition.replace('CREATE TABLE `inventory`','CREATE TEMPORARY TABLE `inventory`',1))
        columns = ['character_id','slot_id','item_id','charges','color','augment_one','augment_two',
                   'augment_three','augment_four','augment_five','augment_six','instnodrop','custom_data',
                   'ornament_icon','ornament_idfile','ornament_hero_model','guid']
        insert = 'INSERT INTO inventory ('+','.join(columns)+') VALUES ('+','.join(['%s']*len(columns))+')'
        select = 'SELECT '+','.join(columns)+' FROM inventory'
        original = [7,21,1001,32767,123,1,2,3,4,5,6,1,'',8,9,10,42]
        partial = original.copy(); partial[12]='nightcap_item_xp^1:1001:123^'
        upgraded = original.copy(); upgraded[2]=201001; upgraded[4]=456

        def seed(row):
            cursor.execute('DELETE FROM inventory')
            cursor.execute(insert,row)

        def read():
            cursor.execute(select)
            return list(cursor.fetchone())

        for query,before,after in zip(queries,[original,partial],[partial,upgraded]):
            seed(before)
            cursor.execute(query); self.assertEqual(cursor.rowcount,1)
            self.assertEqual(read(),after)
            cursor.execute(query); self.assertEqual(cursor.rowcount,0,'same award cannot replay')
            for field,name in enumerate(columns):
                if name=='guid':
                    continue
                drift=before.copy()
                drift[field] = 'foreign^1^' if name=='custom_data' else drift[field]+1
                seed(drift); cursor.execute(query)
                self.assertEqual(cursor.rowcount,0,name)
                self.assertEqual(read(),drift)
            saved_guid=before.copy();saved_guid[-1]=987
            seed(saved_guid);cursor.execute(query);self.assertEqual(cursor.rowcount,1)
            expected=after.copy();expected[-1]=987
            self.assertEqual(read(),expected,'saved GUID retained despite regenerated runtime serial')
        nullable=original.copy();nullable[12]=None
        seed(nullable);cursor.execute(queries[0]);self.assertEqual(cursor.rowcount,1)
        self.assertEqual(read(),partial)
        seed(original)
        db.begin();cursor.execute(queries[0]);db.rollback()
        self.assertEqual(read(),original,'rollback retains complete preimage')


if __name__ == '__main__':
    unittest.main()

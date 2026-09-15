"""MariaDB integration tests: all game table names are session-local temp copies."""
import json
from pathlib import Path
import subprocess
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / 'fixtures/bag-vendor-stock-20260915.jsonl'
FIELDS = ('id', 'price', 'bagslots', 'bagwr', 'bagsize', 'bagtype', 'nodrop', 'sellrate')
MYSQL = ['docker', '--context', 'desktop-linux', 'exec', '-i',
         'akk-stack-mariadb-1', 'sh', '-c',
         'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" '
         'exec mysql --user=root --batch --raw --skip-column-names "$@"', 'mysql']


class BagPricingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = (ROOT / 'eq-solo-gm/scripts/bag_vendor_prices.sql').read_text(encoding='utf-8')
        cls.rows = [json.loads(line) for line in FIXTURE.read_text(encoding='utf-8-sig').splitlines()]
        # Never select peq: even --force or failed temp-table creation cannot
        # fall through to persistent game tables in this empty, unique schema.
        cls.database = 'nightcap_bag_test_' + uuid.uuid4().hex
        result = subprocess.run(MYSQL, input='CREATE DATABASE ' + cls.database + ';',
                                text=True, capture_output=True, timeout=40)
        if result.returncode:
            raise RuntimeError('Scratch database creation failed: ' + result.stderr)

    @classmethod
    def tearDownClass(cls):
        # Created without IF NOT EXISTS above; this run owns the entire schema.
        subprocess.run(MYSQL, input='DROP DATABASE ' + cls.database + ';',
                       text=True, capture_output=True, check=True, timeout=40)

    def fixture(self):
        # Deliberately no CREATE/UPDATE on persistent game tables. These names
        # shadow the real tables for only this mysql connection, then disappear.
        values = ','.join('(' + ','.join(str(row[k]) for k in FIELDS) + ')' for row in self.rows)
        return '''CREATE TEMPORARY TABLE items (
            id INT PRIMARY KEY, price INT UNSIGNED, bagslots INT, bagwr INT,
            bagsize INT, bagtype INT, nodrop INT, sellrate DECIMAL(10,4)) ENGINE=InnoDB;
            CREATE TEMPORARY TABLE merchantlist (merchantid INT, slot INT, item INT, PRIMARY KEY(merchantid,slot)) ENGINE=InnoDB;
            CREATE TEMPORARY TABLE npc_types (id INT PRIMARY KEY, name VARCHAR(80), class INT, merchant_id INT) ENGINE=InnoDB;
            INSERT INTO npc_types VALUES(999225,'Bartholomew_Packwell',41,99225);
            INSERT INTO items VALUES ''' + values + ''';
            INSERT INTO items VALUES(1,123,0,0,0,0,1,1);
            INSERT INTO merchantlist SELECT 99225,bagslots,id FROM items WHERE id<>1;
            '''

    def run_sql(self, sql, force=False):
        args = MYSQL + [self.database]
        if force:
            args.append('--force')
        return subprocess.run(args, input=sql, text=True, encoding='utf-8',
                              capture_output=True, timeout=40)

    def states(self, result):
        return [json.loads(line[6:]) for line in result.stdout.splitlines() if line.startswith('STATE\t')]

    def state_sql(self):
        return "SELECT 'STATE', JSON_OBJECT('id',id,'price',price,'nodrop',nodrop,'bagslots',bagslots) FROM items ORDER BY id;"

    def test_apply_is_priced_monotonic_and_preserves_unrelated_item(self):
        result = self.run_sql(self.fixture() + self.script + self.state_sql())
        self.assertEqual(result.returncode, 0, result.stderr)
        states = self.states(result)
        self.assertEqual(next(r['price'] for r in states if r['id']==1), 123)
        bags = sorted((r for r in states if r['id']!=1), key=lambda r:r['bagslots'])
        self.assertEqual(len(bags), 22)
        self.assertEqual((bags[0]['price'], bags[-1]['price']), (10000, 7500000))
        self.assertTrue(all(a['price'] < b['price'] for a,b in zip(bags,bags[1:])))
        self.assertTrue(all(r['nodrop']==0 for r in bags))

    def test_apply_repeat_and_exact_rollback_repeat(self):
        sql = self.fixture() + self.script + self.script
        sql += 'SET @nightcap_bag_rollback=1;' + self.script + self.script + self.state_sql()
        result = self.run_sql(sql)
        self.assertEqual(result.returncode, 0, result.stderr)
        prices = {r['id']:r['price'] for r in self.states(result)}
        self.assertEqual(prices, {1:123, **{r['id']:r['price'] for r in self.rows}})

    def test_drift_rejects_without_repricing_even_if_mysql_force_is_used(self):
        for drift in (
            'UPDATE items SET price=7 WHERE id=53684;',
            'UPDATE items SET nodrop=1 WHERE id=53684;',
            'UPDATE items SET bagtype=58 WHERE id=53684;',
            'UPDATE items SET price=10000 WHERE id=53684;',
            'DELETE FROM merchantlist WHERE item=53684;',
            'INSERT INTO merchantlist VALUES(99225,999,1);',
            'UPDATE merchantlist SET item=6504 WHERE item=53684;',
            'UPDATE npc_types SET merchant_id=1;',
            'SET @nightcap_bag_rollback=2;',
        ):
            with self.subTest(drift=drift):
                result = self.run_sql(self.fixture() + drift + self.script + self.state_sql(), force=True)
                self.assertIn('CONSTRAINT', result.stderr)
                states = self.states(result)
                self.assertEqual(len(states), 23)
                original = {r['id']:r['price'] for r in self.rows}
                if drift.startswith('UPDATE items SET price=7 '):
                    original[53684] = 7
                elif drift.startswith('UPDATE items SET price=10000 '):
                    original[53684] = 10000
                self.assertEqual({r['id']:r['price'] for r in states if r['id']!=1}, original)


if __name__ == '__main__':
    unittest.main()

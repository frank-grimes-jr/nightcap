"""Exercise the shipped UPDATE statements against neighboring placement/state rows."""
import ast
import json
import re
import sqlite3
import unittest
import sys
from pathlib import Path

SQL = Path(__file__).resolve().parents[2] / 'docs/ops/crushbone-waypoint-20261009'
if len(sys.argv)>1 and sys.argv[1]=='--sql-dir':
    SQL=Path(sys.argv[2]).resolve()
    del sys.argv[1:3]

class WaypointMigrationTest(unittest.TestCase):
    def test_snapshot_order_uses_identity_not_numeric_rendering(self):
        tree=ast.parse((SQL/'deploy.py').read_text())
        definition=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='canonical')
        namespace={'json':json}
        exec(compile(ast.Module(body=[definition],type_ignores=[]),'canonical','exec'),namespace)
        canonical=namespace['canonical']
        expected={'spawn2':[{'id':1,'heading':0.0,'x':100.0},{'id':2,'heading':0,'x':158}]}
        actual={'spawn2':[{'id':1,'heading':0.0,'x':100.0},{'id':2,'heading':0.0,'x':158.0}]}
        self.assertEqual(canonical(expected),canonical(actual))
        actual['spawn2'][1]['x']=159.0
        self.assertNotEqual(canonical(expected),canonical(actual))

    def test_waypoint_snapshot_order_uses_zone_name(self):
        tree=ast.parse((SQL/'deploy.py').read_text())
        definition=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='canonical')
        namespace={'json':json}
        exec(compile(ast.Module(body=[definition],type_ignores=[]),'canonical','exec'),namespace)
        rows={'nightcap_waypoints':[{'zone':'crushbone','x':158},{'zone':'blackburrow','x':200}]}
        self.assertEqual([r['zone'] for r in namespace['canonical'](rows)['nightcap_waypoints']],['blackburrow','crushbone'])

    def status_helpers(self):
        tree=ast.parse((SQL/'world_status.py').read_text(encoding='utf-8'))
        definitions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('decode_status','parse_status')]
        namespace={'re':re}
        exec(compile(ast.Module(body=definitions,type_ignores=[]),'status_helpers','exec'),namespace)
        return namespace

    def test_status_decodes_only_through_summary_terminal(self):
        decode=self.status_helpers()['decode_status']
        self.assertEqual(decode(b'12 zones available.\xc1\0'),'12 zones available.')
        with self.assertRaises(UnicodeDecodeError):
            decode(b'bad \xc1 status 12 zones available.')

    def test_status_requires_every_reported_row(self):
        parse=self.status_helpers()['parse_status']
        rows=[f'#{i} :: D :: 127.0.0.1:9000 :: {int(i==3)} :: :0 ::  :: ({i+100})' for i in range(1,13)]
        summary='12 servers listed. 12 servers online.^0 zones are static zones, 0 zones are booted zones, 12 zones available.'
        parsed=parse('^'.join(rows)+'^'+summary)
        self.assertEqual(sum(r['players'] for r in parsed),1)
        with self.assertRaisesRegex(AssertionError,'Incomplete'):
            parse('^'.join(rows[:2]+rows[3:])+'^'+summary)
        with self.assertRaisesRegex(AssertionError,'Unrecognized'):
            parse('^'.join(rows[:2]+[rows[1]]+rows[3:])+'^'+summary)

    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript('''
        CREATE TABLE nightcap_waypoints(zone TEXT PRIMARY KEY, zone_id INT, x REAL,
          y REAL,z REAL,heading REAL,is_dungeon INT);
        INSERT INTO nightcap_waypoints VALUES('crushbone',58,610,292,2,0,0),
          ('blackburrow',17,10,20,30,0,0);
        CREATE TABLE spawn2(id INT PRIMARY KEY,spawngroupID INT,zone TEXT,version INT,
          x REAL,y REAL,z REAL,heading REAL);
        INSERT INTO spawn2 VALUES(3266061,999240,'crushbone',0,610,292,2,0),
          (85,100,'crushbone',0,610,292,2,0),
          (3266062,999240,'blackburrow',0,10,20,30,0);
        CREATE TABLE zone_state_spawns(id INT PRIMARY KEY,zone_id INT,instance_id INT,
          is_corpse INT,is_zone INT,npc_id INT,spawn2_id INT,spawngroup_id INT,
          x REAL,y REAL,z REAL,heading REAL,hp INT,loot_data TEXT);
        INSERT INTO zone_state_spawns VALUES
          (1,58,0,0,0,999240,3266061,999240,610,292,3.5,0,60000,'keep'),
          (2,58,0,1,0,999240,3266061,999240,610,292,2,0,0,'corpse'),
          (3,58,7,0,0,999240,3266061,999240,610,292,2,0,60000,'instance'),
          (4,58,0,0,0,58001,85,100,610,292,2,0,100,'orc'),
          (5,58,0,0,0,0,3266061,999240,610,292,2,0,0,'placeholder');
        ''')

    def rows(self, table):
        return self.db.execute(f'SELECT * FROM {table} ORDER BY 1').fetchall()

    def tearDown(self):
        self.db.close()

    def test_forward_changes_only_marker_and_destination(self):
        before = {t:self.rows(t) for t in ('spawn2','nightcap_waypoints','zone_state_spawns')}
        self.db.executescript((SQL/'forward.sql').read_text())
        self.assertEqual(self.db.execute("SELECT x,y,z,heading,is_dungeon FROM nightcap_waypoints WHERE zone='crushbone'").fetchone(),(158,-644,4,0,1))
        self.assertEqual(self.db.execute('SELECT x,y,z,heading FROM spawn2 WHERE id=3266061').fetchone(),(158,-644,4,0))
        self.assertEqual(self.rows('spawn2')[0],before['spawn2'][0])
        self.assertEqual(self.rows('spawn2')[2],before['spawn2'][2])
        self.assertEqual(self.rows('nightcap_waypoints')[0],before['nightcap_waypoints'][0])
        after=self.rows('zone_state_spawns')
        self.assertEqual(after[1:4],before['zone_state_spawns'][1:4])
        for i in (0,4):
            self.assertEqual(after[i][:8],before['zone_state_spawns'][i][:8])
            self.assertEqual(after[i][8:12],(158,-644,4,0))
            self.assertEqual(after[i][12:],before['zone_state_spawns'][i][12:])

    def test_inverse_restores_durable_rows(self):
        before={t:self.rows(t) for t in ('spawn2','nightcap_waypoints')}
        self.db.executescript((SQL/'forward.sql').read_text())
        self.db.executescript((SQL/'rollback.sql').read_text())
        self.assertEqual(before,{t:self.rows(t) for t in before})

    def test_repeat_has_no_further_effect(self):
        self.db.executescript((SQL/'forward.sql').read_text())
        before={t:self.rows(t) for t in ('spawn2','nightcap_waypoints','zone_state_spawns')}
        self.db.executescript((SQL/'forward.sql').read_text())
        self.assertEqual(before,{t:self.rows(t) for t in before})

    def test_stale_durable_coordinates_are_not_overwritten(self):
        self.db.execute("UPDATE nightcap_waypoints SET x=100 WHERE zone='crushbone'")
        self.db.execute('UPDATE spawn2 SET x=100 WHERE id=3266061')
        self.db.executescript((SQL/'forward.sql').read_text())
        self.assertEqual(self.db.execute("SELECT x FROM nightcap_waypoints WHERE zone='crushbone'").fetchone(),(100,))
        self.assertEqual(self.db.execute('SELECT x FROM spawn2 WHERE id=3266061').fetchone(),(100,))

if __name__ == '__main__':
    unittest.main()

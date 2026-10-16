"""Execute placement SQL against the observed Unrest defect and neighboring rows."""
import sqlite3
import unittest
from pathlib import Path

SQL = Path(__file__).resolve().parents[2] / 'docs/ops/unrest-waypoint-20261013'


class UnrestWaypointTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript('''
        CREATE TABLE nightcap_waypoints(zone TEXT PRIMARY KEY,zone_id INT,x REAL,y REAL,z REAL,heading REAL,is_dungeon INT);
        INSERT INTO nightcap_waypoints VALUES('unrest',63,118,881,3.75,0,0),('befallen',36,35,-82,3,0,1);
        CREATE TABLE spawn2(id INT PRIMARY KEY,spawngroupID INT,zone TEXT,version INT,x REAL,y REAL,z REAL,heading REAL);
        INSERT INTO spawn2 VALUES(3266123,999240,'unrest',0,118,881,3.75,0),
          (3266037,999228,'unrest',0,52,-38,3,0),(12,999240,'befallen',0,35,-82,3,0),
          (13,101,'unrest',0,118,881,3.75,0);
        CREATE TABLE zone_state_spawns(id INT PRIMARY KEY,zone_id INT,instance_id INT,is_corpse INT,is_zone INT,npc_id INT,spawn2_id INT,spawngroup_id INT,x REAL,y REAL,z REAL,heading REAL,hp INT,loot_data TEXT);
        INSERT INTO zone_state_spawns VALUES
          (1,63,0,0,0,999240,3266123,999240,118,881,4.2,0,60000,'keep'),
          (2,63,0,0,0,0,3266123,999240,118,881,3.75,0,0,'dormant'),
          (3,63,0,1,0,999240,3266123,999240,118,881,3.75,0,0,'corpse'),
          (4,63,7,0,0,999240,3266123,999240,118,881,3.75,0,60000,'instance'),
          (5,63,0,0,0,999228,3266037,999228,52,-38,3,0,60000,'keeper'),
          (6,36,0,0,0,999240,12,999240,35,-82,3,0,60000,'other zone'),
          (7,63,0,0,1,999240,3266123,999240,118,881,3.75,0,0,'metadata'),
          (8,63,0,0,0,999240,14,999240,118,881,3.75,0,60000,'other spawn'),
          (9,63,0,0,0,101,3266123,999240,118,881,3.75,0,100,'other npc');
        CREATE TABLE nightcap_character_waypoints(character_id INT,zone TEXT);
        INSERT INTO nightcap_character_waypoints VALUES(42,'befallen'),(50,'unrest');
        ''')

    def tearDown(self):
        self.db.close()

    def rows(self, table):
        return self.db.execute(f'SELECT * FROM {table} ORDER BY 1').fetchall()

    def apply(self, action='forward'):
        # SQLite exercises the actual guards/updates; MariaDB locking syntax is
        # removed here. Production must use one fail-fast MariaDB connection.
        sql = (SQL / f'{action}.sql').read_text().replace('START TRANSACTION;', 'BEGIN;').replace(' FOR UPDATE', '').replace(' ENGINE=MEMORY', '').replace('DROP TEMPORARY TABLE', 'DROP TABLE')
        try:
            self.db.executescript(sql)
        except sqlite3.Error:
            self.db.rollback()
            raise

    def test_portal_and_recall_reach_existing_eye(self):
        self.apply()
        for table, predicate in [('spawn2','id=3266123'),('nightcap_waypoints',"zone='unrest'")]:
            self.assertEqual(self.db.execute(f'SELECT x,y,z,heading FROM {table} WHERE {predicate}').fetchone(), (52,-38,3,0))

    def test_preserves_neighbors_progress_and_nonposition_state(self):
        before={t:self.rows(t) for t in ('spawn2','nightcap_waypoints','zone_state_spawns','nightcap_character_waypoints')}
        self.apply()
        self.assertEqual(self.rows('spawn2')[:-1],before['spawn2'][:-1])
        self.assertEqual(self.rows('nightcap_waypoints')[0],before['nightcap_waypoints'][0])
        self.assertEqual(self.rows('nightcap_waypoints')[1][-1],0)
        self.assertEqual(self.rows('nightcap_character_waypoints'),before['nightcap_character_waypoints'])
        after=self.rows('zone_state_spawns')
        self.assertEqual(after[2:],before['zone_state_spawns'][2:])
        for i in (0,1):
            self.assertEqual(after[i][:8],before['zone_state_spawns'][i][:8])
            self.assertEqual(after[i][8:12],(52,-38,3,0))
            self.assertEqual(after[i][12:],before['zone_state_spawns'][i][12:])

    def test_rollback_preserves_new_activity(self):
        self.apply()
        self.db.execute("UPDATE zone_state_spawns SET hp=12345,loot_data='new activity' WHERE id=1")
        self.db.commit()
        self.apply('rollback')
        self.assertEqual(self.db.execute('SELECT x,y,z,heading,hp,loot_data FROM zone_state_spawns WHERE id=1').fetchone(),(118,881,3.75,0,12345,'new activity'))
        self.assertEqual(self.db.execute("SELECT x,y,z FROM nightcap_waypoints WHERE zone='unrest'").fetchone(),(118,881,3.75))

    def test_missing_saved_state_is_supported(self):
        self.db.execute('DELETE FROM zone_state_spawns')
        self.db.commit()
        self.apply()
        self.assertEqual(self.rows('zone_state_spawns'),[])

    def test_drift_rejects_entire_transaction(self):
        for table,predicate in [('spawn2','id=3266123'),('nightcap_waypoints',"zone='unrest'"),('spawn2','id=3266037')]:
            with self.subTest(table=table,predicate=predicate):
                self.db.execute(f'UPDATE {table} SET x=x+1 WHERE {predicate}')
                self.db.commit()
                before={t:self.rows(t) for t in ('spawn2','nightcap_waypoints','zone_state_spawns')}
                with self.assertRaises(sqlite3.IntegrityError):
                    self.apply()
                self.assertEqual(before,{t:self.rows(t) for t in before})
                self.db.execute('DROP TABLE IF EXISTS unrest_waypoint_guard')
                self.db.execute(f'UPDATE {table} SET x=x-1 WHERE {predicate}')
                self.db.commit()


if __name__ == '__main__':
    unittest.main()

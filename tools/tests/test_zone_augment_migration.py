"""Real MariaDB rehearsal in a disposable schema; never modify peq.

Run with ZONE_AUGMENT_DB_TESTS=1 against the local akk-stack container.
"""
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import zone_augment_combat as change


class GeneratedMigration(unittest.TestCase):
    def test_checked_in_sql_matches_generator(self):
        for enabled, name in ((True, 'enable'), (False, 'disable')):
            self.assertEqual((change.RELEASE / f'{name}-hateplaneb.sql').read_text(encoding='utf-8'), change.migration(enabled))


@unittest.skipUnless(os.environ.get('ZONE_AUGMENT_DB_TESTS') == '1', 'explicit disposable MariaDB test opt-in')
class MariaDBMigration(unittest.TestCase):
    def sql(self, source, check=True, schema=True):
        command = ['docker', 'exec', '-i', 'akk-stack-mariadb-1', 'sh', '-c',
                   'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names']
        result = subprocess.run(command, input=(f'USE `{self.schema}`;\n' if schema else '') + source,
                                text=True, encoding='utf-8', capture_output=True, timeout=40)
        if check:
            self.assertEqual(result.returncode, 0, result.stderr[-1800:])
        return result

    def setUp(self):
        self.schema = 'nightcap_augment_test_' + secrets.token_hex(6)
        assert re.fullmatch(r'nightcap_augment_test_[0-9a-f]{12}', self.schema)
        self.sql(f'CREATE DATABASE `{self.schema}`;', schema=False)
        self.addCleanup(lambda: self.sql(f'DROP DATABASE `{self.schema}`;', schema=False))
        self.sql('''CREATE TABLE nightcap_zone_hunt_state(id INT PRIMARY KEY,revision BIGINT,enabled INT) ENGINE=InnoDB;
CREATE TABLE nightcap_zone_hunt_zones(zone_id INT PRIMARY KEY,augment_base INT,gear_base INT,min_level INT,night_only INT,enabled INT) ENGINE=InnoDB;
CREATE TABLE nightcap_zone_hunt_sources(zone_id INT,spawn_id INT,npc_id INT,PRIMARY KEY(zone_id,spawn_id,npc_id)) ENGINE=InnoDB;
CREATE TABLE items(id INT PRIMARY KEY,Name VARCHAR(80),augtype INT) ENGINE=InnoDB;
CREATE TABLE inventory(character_id INT,item_id INT) ENGINE=InnoDB;
CREATE TABLE nightcap_zone_hunt_forges(request_id VARCHAR(40),output_id INT) ENGINE=InnoDB;
INSERT INTO nightcap_zone_hunt_state VALUES(1,2026100901,1);
INSERT INTO nightcap_zone_hunt_zones VALUES(186,940592,940596,46,0,0),(76,940560,940564,46,0,1),(18,940128,940132,28,0,0);
INSERT INTO nightcap_zone_hunt_sources VALUES(76,100,76001);
INSERT INTO inventory VALUES(1,940592);
INSERT INTO nightcap_zone_hunt_forges VALUES('earned-receipt',940593);
''' + '\n'.join(f"INSERT INTO items VALUES({i},'{'Blackspire Prism' if i==940592 else 'existing definition'}',{2097152 if i<940596 else 0});" for i in range(940592,940600)))

    def fingerprint(self):
        return self.sql('SELECT * FROM items ORDER BY id; SELECT * FROM inventory; SELECT * FROM nightcap_zone_hunt_forges; SELECT * FROM nightcap_zone_hunt_sources; SELECT * FROM nightcap_zone_hunt_zones WHERE zone_id<>186 ORDER BY zone_id; SELECT * FROM nightcap_zone_hunt_state;').stdout

    def test_enable_rollback_and_preservation(self):
        before = self.fingerprint()
        self.sql(change.migration())
        self.assertEqual(self.sql('SELECT enabled FROM nightcap_zone_hunt_zones WHERE zone_id=186;').stdout.strip(), '1')
        self.assertEqual(self.fingerprint(), before)
        self.sql(change.migration(False))
        self.assertEqual(self.sql('SELECT enabled FROM nightcap_zone_hunt_zones WHERE zone_id=186;').stdout.strip(), '0')
        self.assertEqual(self.fingerprint(), before)

    def test_preimage_drift_and_replay_fail_closed(self):
        mutations = [
            'UPDATE nightcap_zone_hunt_state SET revision=0;',
            'UPDATE nightcap_zone_hunt_state SET enabled=0;',
            'DELETE FROM nightcap_zone_hunt_state;',
            'UPDATE nightcap_zone_hunt_zones SET enabled=1 WHERE zone_id=186;',
            'UPDATE nightcap_zone_hunt_zones SET augment_base=940560 WHERE zone_id=186;',
            'DELETE FROM nightcap_zone_hunt_zones WHERE zone_id=186;',
            "UPDATE items SET Name='blackspire prism' WHERE id=940592;",
            'DELETE FROM items WHERE id=940595;',
            'INSERT INTO nightcap_zone_hunt_sources VALUES(186,1,186001);',
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                # Each subtest gets a fresh disposable schema and never touches peq.
                old_schema = self.schema
                self.setUp()
                try:
                    self.sql(mutation)
                    before = self.fingerprint()
                    zones = self.sql('SELECT * FROM nightcap_zone_hunt_zones ORDER BY zone_id;').stdout
                    self.assertNotEqual(self.sql(change.migration(), check=False).returncode, 0)
                    self.assertEqual(before, self.fingerprint())
                    self.assertEqual(zones, self.sql('SELECT * FROM nightcap_zone_hunt_zones ORDER BY zone_id;').stdout)
                finally:
                    self.sql(f'DROP DATABASE `{self.schema}`;', schema=False)
                    self._cleanups.pop()
                    self.schema = old_schema


if __name__ == '__main__':
    unittest.main()

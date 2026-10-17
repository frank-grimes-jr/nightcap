"""Rehearse generated cooldown migration in one disposable LOCAL MariaDB schema.

Only akk-stack-mariadb-1 is supported. No peq data is read or written. The root
credential stays in the container environment. Cleanup drops only the exact
random nightcap_cooldown_test_ schema successfully created by this process.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import cooldown_identity_migration as migration

CATALOG = None
CATALOG_SHA = None
REPORT = {"container": "akk-stack-mariadb-1", "production_touched": False,
          "checks": [], "scratch_removed": False}


def literal(value):
    return "CONVERT(0x" + str(value).encode("utf-8").hex() + " USING utf8mb4)"


class CooldownMigrationRehearsal(unittest.TestCase):
    @classmethod
    def query(cls, statement, *, root=False, ok=True):
        if not root and not cls.created:
            raise RuntimeError("test database has not been created")
        command = ["docker", "exec", "-i", REPORT["container"], "sh", "-c",
                   'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" '
                   'exec mariadb -uroot --batch --raw --skip-column-names '
                   '--default-character-set=utf8mb4 "$@"', "mariadb"]
        if not root:
            command.append(cls.database)
        result = subprocess.run(command, input=statement, text=True, encoding="utf-8",
                                capture_output=True, timeout=120)
        if ok and result.returncode:
            raise RuntimeError(result.stderr[-1800:])
        return result

    @classmethod
    def setUpClass(cls):
        cls.database = "nightcap_cooldown_test_" + uuid.uuid4().hex
        if not re.fullmatch(r"nightcap_cooldown_test_[0-9a-f]{32}", cls.database):
            raise RuntimeError("unsafe scratch schema")
        cls.created = False
        REPORT["schema"] = cls.database
        cls.forward = migration.sql(CATALOG, CATALOG_SHA)
        cls.rollback = migration.sql(CATALOG, CATALOG_SHA, rollback=True)
        for sql in (cls.forward, cls.rollback):
            if re.search(r"\bUSE\s|\b(?:peq|mysql)\s*\.", sql, re.I):
                raise RuntimeError("generated migration escapes selected scratch schema")
        REPORT["forward_sha256"] = hashlib.sha256(cls.forward.encode()).hexdigest()
        REPORT["rollback_sha256"] = hashlib.sha256(cls.rollback.encode()).hexdigest()
        cls.query(f"CREATE DATABASE `{cls.database}` CHARACTER SET utf8mb4;", root=True)
        cls.created = True
        cls.addClassCleanup(cls.cleanup)
        # Match retained persistence types. Catalog tables need only fields
        # present in the SELECT capture; names/text are retained without quoting.
        cls.query("""
CREATE TABLE timers(char_id INT NOT NULL,type MEDIUMINT UNSIGNED NOT NULL,
 start INT UNSIGNED NOT NULL,duration INT UNSIGNED NOT NULL,enable TINYINT NOT NULL,
 PRIMARY KEY(char_id,type)) ENGINE=InnoDB;
CREATE TABLE character_item_recast(id INT UNSIGNED NOT NULL,recast_type INT UNSIGNED NOT NULL,
 timestamp INT UNSIGNED NOT NULL,PRIMARY KEY(id,recast_type)) ENGINE=InnoDB;
""")
        for table, key in (("aa_ability", "abilities"), ("aa_ranks", "ranks"),
                           ("items", "items"), ("spells_new", "spells")):
            rows = CATALOG[key]
            if table == "spells_new":
                rows = [{("EndurTimerIndex" if c == "timer_id" else c): value
                         for c, value in row.items()} for row in rows]
            columns = list(rows[0])
            definitions = [f"`{c}` " + ("TEXT" if c.lower() == "name" else "BIGINT") for c in columns]
            cls.query(f"CREATE TABLE `{table}` ({','.join(definitions)},PRIMARY KEY(id)) ENGINE=InnoDB;")
            for offset in range(0, len(rows), 500):
                values = ",".join("(" + ",".join(literal(row[c]) for c in columns) + ")"
                                  for row in rows[offset:offset + 500])
                cls.query(f"INSERT INTO `{table}` ({','.join('`'+c+'`' for c in columns)}) VALUES {values};")

    @classmethod
    def cleanup(cls):
        if not cls.created or REPORT.get("schema") != cls.database:
            raise RuntimeError("scratch cleanup identity mismatch")
        if not re.fullmatch(r"nightcap_cooldown_test_[0-9a-f]{32}", cls.database):
            raise RuntimeError("unsafe scratch cleanup target")
        cls.query(f"DROP DATABASE `{cls.database}`;", root=True)
        cls.created = False
        REPORT["scratch_removed"] = True

    def setUp(self):
        self.query("""
TRUNCATE TABLE timers;
TRUNCATE TABLE character_item_recast;
DROP TABLE IF EXISTS nightcap_cooldown_schema,nightcap_cooldown_backup_v1,nightcap_cooldown_rollback_v1;
""")
        self.now = int(self.query("SELECT UNIX_TIMESTAMP();").stdout.strip())

    def tearDown(self):
        REPORT["checks"].append(self._testMethodName)

    def timer(self, key, seconds, *, char=101, start=None, enabled=1):
        start = self.now if start is None else start
        self.query(f"INSERT INTO timers VALUES({char},{key},{start},{seconds},{enabled}) "
                   "ON DUPLICATE KEY UPDATE start=VALUES(start),duration=VALUES(duration),enable=VALUES(enable);")

    def deadline(self, key, char=101):
        value = self.query(f"SELECT start+duration FROM timers WHERE char_id={char} AND type={key};").stdout.strip()
        return int(value) if value else None

    def snapshot(self):
        data = {"timers": self.query("SELECT char_id,type,start,duration,enable FROM timers ORDER BY char_id,type;").stdout,
                "items": self.query("SELECT id,recast_type,timestamp FROM character_item_recast ORDER BY id,recast_type;").stdout}
        for table, order in (("nightcap_cooldown_schema", "id"),
                             ("nightcap_cooldown_backup_v1", "char_id,type"),
                             ("nightcap_cooldown_rollback_v1", "char_id,type")):
            data[table] = ""
            if self.query(f"SHOW TABLES LIKE '{table}';").stdout.strip():
                data[table] = self.query(f"SELECT * FROM {table} ORDER BY {order};").stdout
        return data

    def apply(self):
        self.query(self.forward)

    def reject_atomically(self, sql):
        before = self.snapshot()
        result = self.query(sql, ok=False)
        self.assertNotEqual(result.returncode, 0, "migration unexpectedly succeeded")
        self.assertIn("cooldown_assert.ok", result.stderr, "failure did not come from the intended SQL guard")
        self.assertEqual(self.snapshot(), before, "failure changed timers, item records, or receipt rows")

    def test_aa_ambiguous_group_preserves_all_family_deadlines_without_ownership(self):
        self.timer(1001, 900, start=self.now - 120)
        self.apply()
        self.assertEqual(self.deadline(migration.AA + 109), self.now + 780)
        self.assertEqual(self.deadline(migration.AA + 98), self.now + 780)
        # Independently walk catalog chains: no ownership table exists here,
        # so every possible successor must survive even when currently unowned.
        ranks = {int(r["id"]): r for r in CATALOG["ranks"]}
        families = set()
        for ability in CATALOG["abilities"]:
            rid = int(ability["first_rank_id"])
            seen = set()
            while rid in ranks and rid not in seen:
                seen.add(rid)
                rank = ranks[rid]
                if int(rank["spell"]) > 0 and int(rank["spell_type"]) == 1:
                    families.add(int(ability["id"]))
                rid = int(rank["next_id"])
        self.assertGreater(len(families), 2)
        for family in families:
            self.assertEqual(self.deadline(migration.AA + family), self.now + 780, family)

    def test_item_aliases_and_timestamp_lead_keep_longest_deadline(self):
        self.timer((-61985) & 0xffff, 1000, start=self.now - 100)
        self.query(f"INSERT INTO character_item_recast VALUES(101,61985,{self.now+1200}),"
                   f"(101,32278,{self.now+600}),(101,2,{self.now+900});")
        item_before = self.query("SELECT * FROM character_item_recast ORDER BY id,recast_type;").stdout
        self.apply()
        self.assertEqual(self.deadline(migration.ITEM + 61985), self.now + 1200)
        self.assertEqual(self.deadline(migration.ITEM + 127521), self.now + 900)
        self.assertEqual(self.deadline(migration.ITEM + 32278), self.now + 600)
        self.assertIsNone(self.deadline(migration.ITEM + 2))
        self.assertEqual(self.query("SELECT * FROM character_item_recast ORDER BY id,recast_type;").stdout, item_before)

    def test_all_twenty_discipline_groups_include_legacy_11_through_19(self):
        for group in range(20):
            self.timer(14 + group, 1000 + group)
        self.timer(42, 777)
        self.apply()
        for group in range(20):
            self.assertEqual(self.deadline(migration.DISC + group), self.now + 1000 + group, group)
        self.assertEqual(self.deadline(42), self.now + 777)

    def test_unlinked_disciplines_carry_ambiguous_legacy_key_13(self):
        spells = [int(row["id"]) for row in CATALOG["spells"]
                  if int(row["IsDiscipline"]) and int(row["timer_id"]) == -1]
        self.assertTrue(spells, "capture contains no unlinked discipline fixture")
        self.timer(13, 1800)
        self.apply()
        for spell in spells:
            self.assertEqual(self.deadline(migration.UNLINKED_DISC + spell), self.now + 1800)
        self.timer(migration.UNLINKED_DISC + spells[0], 3600)
        self.query(self.rollback)
        self.assertEqual(self.deadline(13), self.now + 3600)
        self.assertEqual(self.query("SELECT COUNT(*) FROM timers WHERE type>=1048576;").stdout.strip(), "0")

    def test_existing_new_key_merges_max_deadline_and_second_apply_rejects(self):
        self.timer(1001, 900, start=self.now - 120)
        self.timer(migration.AA + 109, 4300, start=self.now - 300)
        self.apply()
        self.assertEqual(self.deadline(migration.AA + 109), self.now + 4000)
        self.assertEqual(self.deadline(migration.AA + 98), self.now + 780)
        self.reject_atomically(self.forward)

    def test_failure_after_timer_inserts_rolls_back_timer_backup_and_receipt_rows(self):
        self.timer(1001, 900)
        self.query(f"INSERT INTO character_item_recast VALUES(101,32278,{self.now+700});")
        anchor = "INSERT INTO nightcap_cooldown_schema VALUES"
        self.assertIn(anchor, self.forward)
        failed = self.forward.replace(anchor, "INSERT INTO cooldown_assert VALUES(0);\n" + anchor, 1)
        self.reject_atomically(failed)
        self.assertEqual(self.query("SELECT COUNT(*) FROM nightcap_cooldown_backup_v1;").stdout.strip(), "0")
        self.assertEqual(self.query("SELECT COUNT(*) FROM nightcap_cooldown_schema;").stdout.strip(), "0")

    def test_failure_after_receipt_insert_rolls_back_every_persistent_write(self):
        self.timer(1001, 900)
        self.query(f"INSERT INTO character_item_recast VALUES(101,32278,{self.now+700});")
        self.assertLess(self.forward.index("INSERT INTO nightcap_cooldown_schema VALUES"),
                        self.forward.index("COMMIT;"))
        failed = self.forward.replace("COMMIT;", "INSERT INTO cooldown_assert VALUES(0);\nCOMMIT;", 1)
        self.reject_atomically(failed)
        self.assertEqual(self.query("SELECT COUNT(*) FROM nightcap_cooldown_backup_v1;").stdout.strip(), "0")
        self.assertEqual(self.query("SELECT COUNT(*) FROM nightcap_cooldown_schema;").stdout.strip(), "0")

    def test_rollback_projects_new_waits_and_removes_every_namespaced_row(self):
        self.timer(1001, 900)
        self.timer(42, 777)
        self.query(f"INSERT INTO character_item_recast VALUES(101,61985,{self.now+1200});")
        self.apply()
        self.timer(migration.AA + 109, 7200)
        self.timer(migration.AA + 98, 100, start=self.now - 200, enabled=0)
        self.timer(migration.ITEM + 32278, 100, start=self.now - 200)
        self.timer(migration.DISC + 19, 2400)
        item_before = self.query("SELECT * FROM character_item_recast ORDER BY id,recast_type;").stdout
        self.query(self.rollback)
        self.assertEqual(self.deadline(1001), self.now + 7200)
        self.assertEqual(self.deadline(33), self.now + 2400)
        self.assertEqual(self.deadline(42), self.now + 777)
        self.assertEqual(self.query("SELECT COUNT(*) FROM timers WHERE type>=1048576;").stdout.strip(), "0")
        self.assertEqual(self.query("SELECT COUNT(*) FROM nightcap_cooldown_schema;").stdout.strip(), "0")
        self.assertEqual(self.query("SELECT * FROM character_item_recast ORDER BY id,recast_type;").stdout, item_before)

    def test_rollback_rejects_unrepresentable_new_key_without_partial_changes(self):
        self.timer(1001, 900)
        self.apply()
        self.timer(migration.AA + 999999, 7200)
        self.reject_atomically(self.rollback)

    def test_catalog_preimage_drift_rejects_before_player_rows_change(self):
        self.timer(1001, 900)
        cases = [("aa_ability", "first_rank_id", 109),
                 ("aa_ranks", "spell_type", 258), ("items", "recasttype", 61985)]
        unlinked = next(int(row["id"]) for row in CATALOG["spells"]
                        if int(row["IsDiscipline"]) and int(row["timer_id"]) == -1)
        cases.append(("spells_new", "EndurTimerIndex", unlinked))
        for table, column, identity in cases:
            old = int(self.query(f"SELECT {column} FROM {table} WHERE id={identity};").stdout.strip())
            try:
                self.query(f"UPDATE {table} SET {column}={old+1} WHERE id={identity};")
                self.reject_atomically(self.forward)
            finally:
                self.query(f"UPDATE {table} SET {column}={old} WHERE id={identity};")

    def test_same_count_item_membership_swap_rejects_before_player_rows_change(self):
        self.timer(1001, 900)
        original = next(row for row in CATALOG["items"] if int(row["id"]) == 61985)
        replacement_id = max(int(row["id"]) for row in CATALOG["items"]) + 1
        replacement = dict(original, id=replacement_id)
        columns = list(replacement)
        count_sql = "SELECT COUNT(*) FROM items WHERE clickeffect>0 AND recastdelay>0;"
        before_count = self.query(count_sql).stdout
        try:
            self.query(f"UPDATE items SET clickeffect=0 WHERE id={original['id']};")
            self.query(f"INSERT INTO items ({','.join('`'+c+'`' for c in columns)}) VALUES "
                       f"({','.join(literal(replacement[c]) for c in columns)});")
            self.assertEqual(self.query(count_sql).stdout, before_count,
                             "membership swap must evade a count-only guard")
            self.reject_atomically(self.forward)
        finally:
            self.query(f"DELETE FROM items WHERE id={replacement_id};")
            self.query(f"UPDATE items SET clickeffect={original['clickeffect']} WHERE id={original['id']};")

    def test_positive_item_click_and_delay_drift_rejects_with_unchanged_membership(self):
        self.timer(1001, 900)
        original = next(row for row in CATALOG["items"] if int(row["id"]) == 61985)
        for column in ("clickeffect", "recastdelay"):
            with self.subTest(column=column):
                try:
                    self.query(f"UPDATE items SET {column}={int(original[column])+1} WHERE id=61985;")
                    self.reject_atomically(self.forward)
                finally:
                    self.query(f"UPDATE items SET {column}={original[column]} WHERE id=61985;")

    def test_precreated_nontransactional_receipt_rejects_before_player_rows_change(self):
        self.timer(1001, 900)
        self.query("CREATE TABLE nightcap_cooldown_schema (id TINYINT UNSIGNED PRIMARY KEY,"
                   "version INT UNSIGNED NOT NULL,catalog_sha256 CHAR(64) NOT NULL) ENGINE=MyISAM;")
        self.reject_atomically(self.forward)

    def test_precreated_backup_engine_and_column_mismatch_reject_forward_and_rollback(self):
        for rollback in (False, True):
            for engine, key_type in (("MyISAM", "MEDIUMINT UNSIGNED"), ("InnoDB", "INT UNSIGNED")):
                with self.subTest(rollback=rollback, engine=engine, key_type=key_type):
                    self.setUp()
                    self.timer(1001, 900)
                    if rollback:
                        self.apply()
                    table = "nightcap_cooldown_rollback_v1" if rollback else "nightcap_cooldown_backup_v1"
                    self.query(f"CREATE TABLE {table} (char_id INT NOT NULL,type {key_type} NOT NULL,"
                               "start INT UNSIGNED NOT NULL,duration INT UNSIGNED NOT NULL,"
                               f"enable TINYINT NOT NULL,PRIMARY KEY(char_id,type)) ENGINE={engine};")
                    self.reject_atomically(self.rollback if rollback else self.forward)

    def test_nontransactional_tables_wrong_key_type_and_triggers_fail_closed(self):
        def recreate(timer_engine="InnoDB", item_engine="InnoDB", key_type="MEDIUMINT UNSIGNED"):
            # Recreate these disposable tables instead of converting their
            # engines in place: Windows-mounted Docker datadirs can fail the
            # intermediate tablespace rename during an ALTER ENGINE round trip.
            self.query(f"""
DROP TABLE timers,character_item_recast;
CREATE TABLE timers(char_id INT NOT NULL,type {key_type} NOT NULL,
 start INT UNSIGNED NOT NULL,duration INT UNSIGNED NOT NULL,enable TINYINT NOT NULL,
 PRIMARY KEY(char_id,type)) ENGINE={timer_engine};
CREATE TABLE character_item_recast(id INT UNSIGNED NOT NULL,recast_type INT UNSIGNED NOT NULL,
 timestamp INT UNSIGNED NOT NULL,PRIMARY KEY(id,recast_type)) ENGINE={item_engine};
""")
            self.timer(1001, 900)
        for timer_engine, item_engine, key_type in (
                ("MyISAM", "InnoDB", "MEDIUMINT UNSIGNED"),
                ("InnoDB", "MyISAM", "MEDIUMINT UNSIGNED"),
                ("InnoDB", "InnoDB", "INT UNSIGNED")):
            with self.subTest(timer_engine=timer_engine, item_engine=item_engine, key_type=key_type):
                try:
                    recreate(timer_engine, item_engine, key_type)
                    self.reject_atomically(self.forward)
                finally:
                    recreate()
        with self.subTest(trigger="unexpected"):
            try:
                self.query("CREATE TRIGGER cooldown_test_trigger BEFORE INSERT ON timers "
                           "FOR EACH ROW SET NEW.enable=NEW.enable;")
                self.reject_atomically(self.forward)
            finally:
                self.query("DROP TRIGGER IF EXISTS cooldown_test_trigger;")


def main():
    global CATALOG, CATALOG_SHA
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--failfast", action="store_true")
    args = parser.parse_args()
    data = args.catalog.read_bytes()
    CATALOG = json.loads(data)
    CATALOG_SHA = hashlib.sha256(data).hexdigest()
    REPORT["catalog_sha256"] = CATALOG_SHA
    REPORT["captured_at"] = CATALOG.get("captured_at")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CooldownMigrationRehearsal)
    class ImmediateErrors(unittest.TextTestResult):
        def addError(self, test, error):
            super().addError(test, error)
            self.stream.writeln(str(error[1]))
            self.stream.flush()
    result = unittest.TextTestRunner(verbosity=2, resultclass=ImmediateErrors,
                                    failfast=args.failfast).run(suite)
    REPORT["tests_run"] = result.testsRun
    REPORT["failures"] = len(result.failures)
    REPORT["errors"] = len(result.errors)
    REPORT["passed"] = result.wasSuccessful()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(REPORT, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(REPORT, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

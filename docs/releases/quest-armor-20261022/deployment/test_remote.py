"""Isolated operator faults and optional LOCAL disposable MariaDB rehearsal.

python .../test_remote.py -v
python .../test_remote.py --local-sql

No production calls are made. The SQL mode permits only akk-stack-mariadb-1,
creates one random scratch schema and a TEMPORARY inventory table, then removes
that exact schema. Credentials remain inside the local container environment.
"""
from __future__ import annotations

import base64
import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
import uuid

HERE = Path(__file__).resolve().parent
COLUMNS = ["character_id", "slot_id", "item_id", "charges", "color", "augment_one",
           "augment_two", "augment_three", "augment_four", "augment_five", "augment_six",
           "instnodrop", "custom_data", "ornament_icon", "ornament_idfile", "ornament_hero_model", "guid"]


def load_operator():
    spec = importlib.util.spec_from_file_location("isolated_quest_operator", HERE / "remote.py")
    module = importlib.util.module_from_spec(spec)
    # fcntl is only used by the Linux CLI entrypoint. Tests exercise execute()
    # directly, so Windows needs an import placeholder, not a lock imitation.
    with mock.patch.dict(sys.modules, {"fcntl": types.ModuleType("fcntl")} if os.name == "nt" else {}):
        spec.loader.exec_module(module)
    return module


def rows_fixture():
    rows = []
    for slot, item in ((7, 4176), (17, 4174), (19, 4180), (22, 999)):
        row = {column: 0 for column in COLUMNS}
        row.update(character_id=29, slot_id=slot, item_id=item, charges=3, color=16711935,
                   augment_one=940001, augment_two=940002, augment_three=940003,
                   augment_four=940004, augment_five=940005, augment_six=940006,
                   instnodrop=1, custom_data="CaseSensitive 'quote' \\ slash é" if slot != 22 else None,
                   ornament_icon=1234, ornament_idfile=5678, ornament_hero_model=9,
                   guid=18446744073709550000 + slot)
        rows.append(row)
    return rows


class Fixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="remote-tests-", dir=HERE)
        self.directory = Path(self.temp.name).resolve()
        assert self.directory.is_relative_to(HERE)
        self.r = load_operator()
        self.r.ROOT = self.directory / "production"
        self.r.QUESTS = self.r.ROOT / "quests"
        self.r.OUT = self.directory / "receipts"
        self.r.QUESTS.mkdir(parents=True)
        self.events, self.queries = [], []
        self.locked = self.paused = False
        self.clients = 0
        self.rows = rows_fixture()
        self.fail_install = self.fail_sql = self.bad_after = False
        self.reload_count = 12
        scripts = []
        for index in range(11):
            relative = f"zone{index}/npc.pl"
            before, after = f"original-{index}".encode(), f"candidate-{index}".encode()
            path = self.r.QUESTS / relative
            path.parent.mkdir()
            path.write_bytes(before)
            scripts.append({"path": relative, "before_sha256": self.r.sha(before),
                            "after_sha256": self.r.sha(after), "payload": base64.b64encode(after).decode()})
        self.r.DATA = {"scripts": scripts, "targets": [], "npcs": [], "commit": "fixture-commit"}
        self.original_install = self.r.install
        self.original_reload = self.r.reload_quests
        self.r.snapshot = lambda: {"services": ["unchanged"], "native": ["unchanged"],
                                   "cache_sha256": "cache", "channel_sha256": "channel"}
        self.r.probe = self.probe
        self.r.control = self.control
        self.r.gateway_paused = lambda: self.paused
        self.r.pause = self.pause
        self.r.install = self.install
        self.r.reload_quests = self.reload
        self.r.inventory = lambda: (COLUMNS[:], copy.deepcopy(self.rows))
        self.r.sql = self.sql
        self.r.time = types.SimpleNamespace(sleep=lambda _: None)
        self.real_save = self.r.save
        self.r.save = self.save

    def close(self):
        assert self.directory.is_relative_to(HERE)
        self.temp.cleanup()

    def probe(self):
        return {"clients": self.clients, "world_locked": self.locked, "cache_targets": [],
                "scripts": {entry["path"]: self.r.sha((self.r.QUESTS / entry["path"]).read_bytes())
                            for entry in self.r.DATA["scripts"]}}

    def control(self, action):
        if action in ("lock", "unlock"):
            self.locked = action == "lock"
            self.events.append(action)
        return self.clients if action == "count" else self.locked

    def pause(self, value):
        self.events.append("pause" if value else "unpause")
        self.paused = value

    def install(self, entry, data):
        assert self.paused and self.locked
        self.events.append("install:" + entry["path"])
        if self.fail_install and len([e for e in self.events if e.startswith("install:")]) == 6:
            raise OSError("injected sixth-file replacement failure")
        (self.r.QUESTS / entry["path"]).write_bytes(data)

    def reload(self, action):
        assert self.paused and self.locked
        self.events.append("reload")
        assert self.reload_count == 12, "Need twelve quest reload acknowledgments"
        return {"acknowledgments": 12, "lines": ["Reloaded [Quest] (22)"] * 12}

    def sql(self, query):
        if query.startswith("SELECT id,name"):
            return "29\tPalwar\n"
        if query.startswith("SELECT ENGINE"):
            return "InnoDB\n"
        assert "START TRANSACTION" in query and "UPDATE inventory" in query
        assert self.paused and self.locked and self.clients == 0
        self.events.append("inventory-write")
        self.queries.append(query)
        if self.fail_sql:
            raise RuntimeError("injected guarded SQL failure")
        for row in self.rows:
            if row["slot_id"] in self.r.PAIRS:
                row["item_id"] = self.r.PAIRS[row["slot_id"]][1]
        if self.bad_after:
            self.rows[-1]["charges"] += 1
        return ""

    def save(self, name, value):
        if name == "apply-verified.json":
            assert self.paused and self.locked
            assert "reload" in self.events and "inventory-write" in self.events
        self.events.append("save:" + name)
        return self.real_save(name, value)


class OperatorTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.addCleanup(self.f.close)
        self.r = self.f.r

    def assert_held(self):
        self.assertTrue(self.f.paused)
        self.assertTrue(self.f.locked)
        self.assertNotIn("unpause", self.f.events)

    def test_connected_clients_admission_fails_before_any_write(self):
        self.f.clients = 1
        with self.assertRaisesRegex(AssertionError, "fully exit"):
            self.r.execute("apply")
        self.assertEqual(self.f.events, [])
        self.assertFalse(self.r.OUT.exists())

    def test_script_preimage_drift_fails_before_any_write(self):
        (self.r.QUESTS / self.r.DATA["scripts"][3]["path"]).write_bytes(b"external-edit")
        with self.assertRaises(AssertionError):
            self.r.execute("apply")
        self.assertEqual(self.f.events, [])
        self.assertFalse(self.r.OUT.exists())

    def test_apply_holds_until_reload_and_inventory_proof(self):
        before = copy.deepcopy(self.f.rows)
        result = self.r.execute("apply")
        self.assertTrue(result["admissions_restored"])
        self.assertFalse(self.f.paused or self.f.locked)
        events = self.f.events
        self.assertLess(events.index("reload"), events.index("inventory-write"))
        self.assertLess(events.index("save:palwar-after-private.json"), events.index("unpause"))
        self.assertLess(events.index("save:apply-verified.json"), events.index("unpause"))
        self.assertEqual(len([e for e in events if e.startswith("install:")]), 11)
        for old, new in zip(before, self.f.rows):
            expected = dict(old)
            if old["slot_id"] in self.r.PAIRS:
                expected["item_id"] = self.r.PAIRS[old["slot_id"]][1]
            self.assertEqual(new, expected)

    def test_partial_eleven_file_failure_retains_hold(self):
        self.f.fail_install = True
        with self.assertRaisesRegex(OSError, "sixth-file"):
            self.r.execute("apply")
        self.assert_held()
        changed = sum(self.r.sha((self.r.QUESTS / e["path"]).read_bytes()) == e["after_sha256"]
                      for e in self.r.DATA["scripts"])
        self.assertEqual(changed, 5)
        self.assertEqual(self.f.queries, [])

    def test_missing_reload_ack_holds_before_inventory_write(self):
        self.f.reload_count = 11
        with self.assertRaisesRegex(AssertionError, "twelve"):
            self.r.execute("apply")
        self.assert_held()
        self.assertEqual(self.f.queries, [])

    def test_guarded_sql_failure_retains_hold_and_attempt_receipt(self):
        self.f.fail_sql = True
        with self.assertRaisesRegex(RuntimeError, "SQL failure"):
            self.r.execute("apply")
        self.assert_held()
        self.assertTrue((self.r.OUT / "palwar-write-started.json").exists())
        self.assertFalse((self.r.OUT / "palwar-after-private.json").exists())

    def test_afterimage_mismatch_retains_hold_and_rollback_cannot_reopen(self):
        self.f.bad_after = True
        with self.assertRaisesRegex(AssertionError, "afterimage"):
            self.r.execute("apply")
        self.assert_held()
        held_rows = copy.deepcopy(self.f.rows)
        with self.assertRaisesRegex(AssertionError, "Unresolved inventory"):
            self.r.execute("rollback")
        self.assert_held()
        self.assertEqual(self.f.rows, held_rows)
        self.assertEqual(len(self.f.queries), 1)

    def test_rollback_restores_scripts_and_retains_repaired_inventory(self):
        self.r.execute("apply")
        repaired = copy.deepcopy(self.f.rows)
        result = self.r.execute("rollback")
        self.assertEqual(result["palwar"]["state"], "committed exactly")
        self.assertEqual(self.f.rows, repaired)
        self.assertEqual(len(self.f.queries), 1)
        self.assertTrue(all(self.r.sha((self.r.QUESTS / e["path"]).read_bytes()) == e["before_sha256"]
                            for e in self.r.DATA["scripts"]))

    def test_uncertain_sql_session_blocks_rollback_even_with_exact_preimage(self):
        self.f.fail_sql = True
        with self.assertRaises(RuntimeError):
            self.r.execute("apply")
        before = copy.deepcopy(self.f.rows)
        self.assertTrue((self.r.OUT / "palwar-sql-uncertain.json").exists())
        with self.assertRaisesRegex(AssertionError, "SQL.*unproven|SQL.*uncertain|SQL.*incomplete"):
            self.r.execute("rollback")
        self.assert_held()
        self.assertEqual(self.f.rows, before)
        self.assertEqual(len(self.f.queries), 1)

    def test_reconciliation_accepts_exact_preimage_only_after_sql_completion_proof(self):
        before = copy.deepcopy(self.f.rows)
        self.r.execute("apply")
        self.f.rows = before
        result = self.r.reconcile_repair()
        self.assertEqual(result["state"], "not committed")
        self.assertFalse(result["player_state_restored"])
        self.assertEqual(self.f.rows, before)
        self.assertEqual(len(self.f.queries), 1)

    def test_missing_sql_completion_marker_keeps_rollback_held(self):
        self.r.execute("apply")
        repaired = copy.deepcopy(self.f.rows)
        (self.r.OUT / "palwar-sql-returned.json").unlink()
        self.f.events.clear()
        with self.assertRaisesRegex(AssertionError, "SQL.*unproven|SQL.*incomplete|completion"):
            self.r.execute("rollback")
        self.assert_held()
        self.assertEqual(self.f.rows, repaired)
        self.assertEqual(len(self.f.queries), 1)

    def test_private_before_receipt_hash_drift_keeps_rollback_held(self):
        self.r.execute("apply")
        path = self.r.OUT / "palwar-before-private.json"
        retained = json.loads(path.read_text())
        retained["rows"][0]["charges"] += 1
        path.write_text(json.dumps(retained))
        self.f.events.clear()
        with self.assertRaisesRegex(AssertionError, "Private inventory preimage drift"):
            self.r.execute("rollback")
        self.assert_held()
        self.assertEqual(len(self.f.queries), 1)

    def test_successful_apply_cannot_be_replayed(self):
        self.r.execute("apply")
        events, rows = list(self.f.events), copy.deepcopy(self.f.rows)
        with self.assertRaises(AssertionError):
            self.r.execute("apply")
        self.assertEqual(self.f.events, events)
        self.assertEqual(self.f.rows, rows)

    def test_retained_attempt_blocks_direct_repair_replay(self):
        self.f.fail_sql = True
        with self.assertRaises(RuntimeError):
            self.r.execute("apply")
        with self.assertRaises(FileExistsError):
            self.r.repair()
        self.assertEqual(len(self.f.queries), 1)
        self.assert_held()

    def test_gateway_hold_survives_world_control_failure(self):
        self.r.OUT.mkdir()
        self.r.control = mock.Mock(side_effect=OSError("world unavailable"))
        report = self.r.retain_hold()
        self.assertTrue(self.f.paused)
        self.assertEqual(self.f.events[0], "pause")
        self.assertIn("world_error", report)

    def test_real_reload_parser_requires_exactly_twelve_clean_acknowledgments(self):
        self.r.OUT.mkdir()
        self.r.game = mock.Mock()
        for count, error, accepted in ((11, "", False), (12, "", True), (13, "", False),
                                        (12, "\nperl error: injected", False)):
            with self.subTest(count=count, error=error):
                self.r.command = mock.Mock(return_value=("Reloaded [Quest] (22)\n" * count) + error)
                if accepted:
                    self.assertEqual(self.f.original_reload("test")["acknowledgments"], 12)
                else:
                    with self.assertRaises(AssertionError):
                        self.f.original_reload("test")

    def test_real_atomic_install_recovers_recognized_partial_and_rejects_foreign_partial(self):
        entry = self.r.DATA["scripts"][0]
        path = self.r.QUESTS / entry["path"]
        backup = self.r.OUT / "originals" / entry["path"]
        backup.parent.mkdir(parents=True)
        backup.write_bytes(path.read_bytes())
        temporary = path.with_name(path.name + ".quest-armor-partial")
        target = base64.b64decode(entry["payload"])
        temporary.write_bytes(target[:4])
        # Windows lacks Unix ownership/directory-fsync APIs. File writes, fsync,
        # os.replace, prefix validation and cleanup execute for real on both OSes.
        with tempfile.TemporaryFile() as directory_fd:
            patches = []
            if os.name == "nt":
                real_open = os.open
                patches = [mock.patch.object(os, "fchmod", create=True), mock.patch.object(os, "fchown", create=True),
                           mock.patch.object(os, "O_DIRECTORY", 0, create=True),
                           mock.patch.object(os, "open", side_effect=lambda p, flags, *a, **kw:
                               os.dup(directory_fd.fileno()) if Path(p).is_dir() else real_open(p, flags, *a, **kw))]
            for patch in patches:
                patch.start()
            try:
                self.f.original_install(entry, target)
                self.assertEqual(path.read_bytes(), target)
                self.assertFalse(temporary.exists())
                temporary.write_bytes(b"foreign-content")
                with self.assertRaisesRegex(AssertionError, "Foreign partial"):
                    self.f.original_install(entry, backup.read_bytes())
                self.assertEqual(path.read_bytes(), target)
                self.assertEqual(temporary.read_bytes(), b"foreign-content")
            finally:
                for patch in reversed(patches):
                    patch.stop()


def local_sql_rehearsal():
    fixture = Fixture()
    try:
        fixture.r.execute("apply")
        query = fixture.queries[0]
        normal = rows_fixture()
        expected = copy.deepcopy(fixture.rows)
        literal = fixture.r.literal
    finally:
        fixture.close()
    schema = "nightcap_quest_armor_test_" + uuid.uuid4().hex
    assert re.fullmatch(r"nightcap_quest_armor_test_[0-9a-f]{32}", schema)
    command = ["docker", "exec", "-i", "akk-stack-mariadb-1", "sh", "-c",
               'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" '
               'exec mariadb -uroot --batch --raw --skip-column-names --default-character-set=utf8mb4']
    def run(statement):
        result = subprocess.run(command, input=statement, text=True, encoding="utf-8", capture_output=True, timeout=45)
        if result.returncode:
            raise RuntimeError(result.stderr[-1800:])
        return result.stdout
    created = False
    try:
        run(f"CREATE DATABASE `{schema}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
        created = True
        definitions = [f"`{c}` " + ("TEXT NULL" if c == "custom_data" else "BIGINT UNSIGNED") for c in COLUMNS]
        create = "CREATE TEMPORARY TABLE inventory (" + ",".join(definitions) + ",PRIMARY KEY(character_id,slot_id)) ENGINE=InnoDB;"
        columns = ",".join("`" + c + "`" for c in COLUMNS)
        def insert(rows):
            return "INSERT INTO inventory (" + columns + ") VALUES " + ",".join(
                "(" + ",".join(literal(row[c]) for c in COLUMNS) + ")" for row in rows) + ";"
        expression = "JSON_OBJECT(" + ",".join("'" + c + "',`" + c + "`" for c in COLUMNS) + ")"
        select = "SELECT " + expression + " FROM inventory ORDER BY slot_id;"
        # Catch only the expected SIGNAL in an outer anonymous block so the same
        # connection can inspect rollback; never use mariadb --force.
        body = query.removeprefix("DELIMITER //\n").removesuffix("END//\nDELIMITER ;\n") + "END;"
        guarded = ("SET @failed=0;\nDELIMITER //\nBEGIN NOT ATOMIC\n"
                   "DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET @failed=1;\n" + body +
                   "\nEND//\nDELIMITER ;\nSELECT @failed;\n" + select)
        checks = []
        for label, starting, repeats, fail, ending in (
            ("three guarded updates preserve all 17 fields and unrelated row", normal, 1, 0, expected),
            ("one full-row charge drift rolls back every update", [{**r, "charges": r["charges"] + (r["slot_id"] == 7)} for r in normal], 1, 1, None),
            ("binary custom-data case drift rolls back every update", [{**r, "custom_data": r["custom_data"].lower() if r["slot_id"] == 7 else r["custom_data"]} for r in normal], 1, 1, None),
            ("binary custom-data trailing-space drift rolls back every update", [{**r, "custom_data": r["custom_data"] + " " if r["slot_id"] == 7 else r["custom_data"]} for r in normal], 1, 1, None),
            ("replay rejects while retaining repaired rows", normal, 2, 1, expected),
        ):
            try:
                output = run("\n".join([f"USE `{schema}`;", create, insert(starting),
                                         query if repeats == 2 else "", guarded]))
            except RuntimeError as error:
                raise RuntimeError(label + ": " + str(error)) from error
            lines = output.splitlines()
            assert int(lines[0]) == fail, (label, output)
            actual = [json.loads(line) for line in lines[1:]]
            assert actual == (ending if ending is not None else starting), (label, actual)
            checks.append(label)
        version = run("SELECT VERSION();").strip()
    finally:
        if created:
            assert re.fullmatch(r"nightcap_quest_armor_test_[0-9a-f]{32}", schema)
            run(f"DROP DATABASE `{schema}`;")
    print(json.dumps({"status": "passed", "container": "akk-stack-mariadb-1", "mariadb_version": version,
                      "checks": checks, "columns_preserved": len(COLUMNS), "temporary_inventory": True,
                      "scratch_schema_removed": True, "production_touched": False}, indent=2))


if __name__ == "__main__":
    if "--local-sql" in sys.argv:
        local_sql_rehearsal()
    else:
        unittest.main()

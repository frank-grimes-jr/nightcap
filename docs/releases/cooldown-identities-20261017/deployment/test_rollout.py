"""Offline failure and preservation checks for the real release operator."""
import contextlib
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path[:0] = [str(HERE), str(REPO / "tools")]
if os.name == "nt":
    sys.modules.setdefault("fcntl", types.SimpleNamespace(LOCK_EX=2, LOCK_NB=4, flock=lambda *a: None))
spec = importlib.util.spec_from_file_location("cooldown_release_under_test", HERE / "rollout.py")
op = importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)


class TimerPreservationTests(unittest.TestCase):
    def setUp(self):
        self.before = [[7, 1001, 100, 300, 1], [7, 1002, 90, 500, 1],
                       [7, 1186, 100, 650, 1], [7, 25, 100, 200, 1],
                       [8, 1001, 80, 50, 1], [7, 1003, 100, 900, 0]]
        self.pairs = [(1001, op.migration.AA + 98), (1001, op.migration.AA + 109),
                      (1002, op.migration.AA + 109), (1003, op.migration.AA + 110),
                      (1186, op.migration.ITEM + 64350), (1186, op.migration.ITEM + 129886)]
        self.items = {64350, 129886}
        self.item_rows = [[7, 64350, 900], [7, 129886, 700], [8, 64350, 100]]
        self.after = self.before + [[7, op.migration.AA + 98, 100, 300, 1],
                                   [7, op.migration.AA + 109, 90, 500, 1],
                                   [7, op.migration.ITEM + 64350, 100, 800, 1],
                                   [7, op.migration.ITEM + 129886, 100, 650, 1]]

    def verify(self, after=None, before=None, now=200):
        return op.validate_timers(self.before if before is None else before,
                                  self.after if after is None else after,
                                  self.item_rows, self.pairs, self.items, now)

    def test_ambiguous_families_item_aliases_and_timestamp_lead_keep_exact_maximum(self):
        self.assertEqual(self.verify(), 4)

    def test_missing_short_disabled_or_inflated_successor_is_rejected(self):
        for mutation in ("missing", "short", "disabled", "inflated"):
            with self.subTest(mutation=mutation):
                rows = copy.deepcopy(self.after)
                if mutation == "missing": rows.pop()
                elif mutation == "short": rows[-2][3] -= 1
                elif mutation == "disabled": rows[-1][4] = 0
                else: rows[-1][3] += 1
                with self.assertRaises(AssertionError): self.verify(rows)

    def test_wrong_family_character_or_fabricated_successor_is_rejected(self):
        for row in ([7, op.migration.AA + 110, 100, 300, 1],
                    [8, op.migration.AA + 98, 100, 300, 1],
                    [7, op.migration.AA + 9999, 100, 300, 1]):
            with self.subTest(row=row), self.assertRaises(AssertionError):
                self.verify(self.after + [row])

    def test_legacy_mutation_removal_duplicates_and_prior_new_namespace_are_rejected(self):
        for mutation in ("change", "remove", "duplicate", "preexisting"):
            with self.subTest(mutation=mutation):
                before, after = copy.deepcopy(self.before), copy.deepcopy(self.after)
                if mutation == "change": after[3][3] += 1
                elif mutation == "remove": after.pop(3)
                elif mutation == "duplicate": after.append(after[0])
                else: before.append(after[-1])
                with self.assertRaises(AssertionError): self.verify(after, before)

    def test_natural_expiry_during_maintenance_does_not_require_refunded_rows(self):
        self.assertEqual(self.verify(copy.deepcopy(self.before), now=1001), 0)

    def test_receipt_backup_and_item_timestamp_preimages_are_all_required(self):
        for failure in ("receipt", "backup", "item"):
            with self.subTest(failure=failure), contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(op, "receipt", return_value="1\t1\twrong" if failure == "receipt" else "1\t1\tdigest"))
                stack.enter_context(patch.object(op, "timers", return_value=[] if failure == "backup" else self.before))
                stack.enter_context(patch.object(op, "item_recasts", return_value=[] if failure == "item" else self.item_rows))
                with self.assertRaises(AssertionError):
                    op.verify_migration({}, "digest", self.before, self.item_rows)


class Runtime:
    def __init__(self):
        self.events = []
        self.running_services = {name: True for name in ("game", "gateway", "db", "web", "tunnel")}
        self.fail = None
        self.opened = False
        self.services = {name: {"id": name, "running": True} for name in self.running_services}

    def compact(self, name): return self.services[name]
    def state(self, name): return {"Id": name, "State": {"Running": self.running_services[name], "ExitCode": 0, "OOMKilled": False}}
    def compose(self, *args):
        self.events.append(("compose",) + args)
        name = args[-1]
        if args[0] == "stop": self.running_services[name] = False
        elif args[0] == "up":
            self.running_services[name] = True
            if name == "gateway": self.opened = True
        if self.fail: self.fail(args)
    def select(self, image): self.events.append(("select", image))
    def player_data(self): return {"character_data": "same", "character_item_recast": "same"}
    def database_backup(self): self.events.append(("backup",)); return {"gzip_integrity": "passed"}
    def running(self, *args, **kwargs): self.events.append(("running",)); return {"started_at": "2026-10-18T10:00:00Z"}
    def closed_ports(self): self.events.append(("closed_ports",))


@contextlib.contextmanager
def operator_fixture(opening=False):
    with tempfile.TemporaryDirectory(prefix="cooldown-operator-test-") as directory, contextlib.ExitStack() as stack:
        root = Path(directory)
        evidence, private = root / "evidence", root / "private"
        evidence.mkdir(); private.mkdir()
        runtime = Runtime()
        for name, value in {"ROOT": root, "STAGE": root, "EVIDENCE": evidence, "PRIVATE": private, "r": runtime}.items():
            stack.enter_context(patch.object(op, name, value))
        stack.enter_context(patch.object(op, "manifest", return_value={"client_channel_sha256": "channel", "client_release": 2026101801}))
        stack.enter_context(patch.object(op, "sha", return_value="digest"))
        stack.enter_context(patch.object(op.shutil, "disk_usage", return_value=types.SimpleNamespace(free=10 * 1024**3)))
        stack.enter_context(patch.object(op, "untouched"))
        stack.enter_context(patch.object(op, "preserved"))
        stack.enter_context(patch.object(op, "custom", return_value={"nightcap_trade_audit": "same"}))
        stack.enter_context(patch.object(op, "timers", return_value=[[7, 1001, 100, 300, 1]]))
        stack.enter_context(patch.object(op, "item_recasts", return_value=[]))
        stack.enter_context(patch.object(op, "market_state", return_value=["1", "1", "80", "0", "4", "2.500000", "2026-10-17 10:00:00"]))
        stack.enter_context(patch.object(op.capture, "capture", return_value={"abilities": []}))
        stack.enter_context(patch.object(op.migration, "sql", side_effect=lambda c, d, rollback=False: "REVERSE" if rollback else "FORWARD"))
        stack.enter_context(patch.object(op.migration, "mappings", return_value=([], [])))
        stack.enter_context(patch.object(op, "rehearse"))
        stack.enter_context(patch.object(op, "verify_migration", return_value=2))
        stack.enter_context(patch.object(op, "verify_market", return_value={"before": "80", "after": "81"}))
        stack.enter_context(patch.object(op, "health"))
        stack.enter_context(patch.object(op, "binaries", return_value={"zone": "candidate"}))
        stack.enter_context(patch.object(op.time, "sleep"))
        stack.enter_context(patch.object(op, "sql", side_effect=lambda statement, *a, **k: runtime.events.append(("sql", statement)) or ""))
        p = {"manifest_sha256": "digest", "services": runtime.services, "new_image_id": "candidate", "cache_sha256": "cache"}
        op.save("preflight.json", p)
        if opening:
            runtime.running_services["gateway"] = False
            a = {"game": runtime.compact("game"), "runtime": {"started_at": "2026-10-18T10:00:00Z"},
                 "market_rotation": {"before": "80", "after": "81"}, "player_tables_preserved": 2, "custom_tables_preserved": 1}
            for name, value, secret in [("verified-closed.json", a, False), ("catalog.json", {}, True),
                    ("migration-inputs.json", {"catalog_sha256": "digest"}, False),
                    ("stopped-timers.json", [], True), ("stopped-item-recasts.json", [], True),
                    ("stopped-data.json", {}, True), ("market-before.json", [], False),
                    ("migration-applied.json", {"catalog_sha256": "digest"}, False)]:
                op.save(name, value, secret)
        yield runtime


class FailureBoundaryTests(unittest.TestCase):
    def assert_held(self, runtime):
        self.assertFalse(runtime.running_services["gateway"])
        self.assertFalse(runtime.running_services["game"])
        self.assertTrue(list(op.EVIDENCE.glob("held-*.json")))
        self.assertNotIn(("select", "old"), runtime.events)

    def test_migration_lost_ack_holds_both_services_and_cannot_replay(self):
        with operator_fixture() as runtime:
            def lost_ack(statement, *a, **k):
                runtime.events.append(("sql", statement))
                raise RuntimeError("commit may have succeeded; acknowledgment lost")
            with patch.object(op, "sql", side_effect=lost_ack):
                with self.assertRaises(RuntimeError): op.activate()
                self.assert_held(runtime)
                self.assertTrue((op.EVIDENCE / "migration-attempted.json").exists())
                with self.assertRaises(AssertionError): op.activate()
            self.assertEqual(runtime.events.count(("sql", "FORWARD")), 1)
            self.assertFalse(any(event[0] == "select" for event in runtime.events))

    def test_postcommit_receipt_or_preservation_failure_never_starts_any_image(self):
        for boundary in ("verify_migration", "preserved"):
            with self.subTest(boundary=boundary), operator_fixture() as runtime:
                calls = 0
                def fail_after_commit(*args, **kwargs):
                    nonlocal calls
                    calls += 1
                    if boundary == "verify_migration" or calls == 2: raise RuntimeError("preservation mismatch")
                with patch.object(op, boundary, side_effect=fail_after_commit):
                    with self.assertRaises(RuntimeError): op.activate()
                self.assert_held(runtime)
                self.assertEqual(runtime.events.count(("sql", "FORWARD")), 1)
                self.assertFalse(any(event[0] == "select" for event in runtime.events))

    def test_candidate_start_lost_ack_and_market_failure_hold_without_old_image(self):
        for boundary in ("start", "market"):
            with self.subTest(boundary=boundary), operator_fixture() as runtime:
                if boundary == "start":
                    runtime.fail = lambda args: (_ for _ in ()).throw(RuntimeError("start acknowledgment lost")) if args[0] == "up" else None
                with patch.object(op, "verify_market", side_effect=RuntimeError("unexpected market")):
                    with self.assertRaises(RuntimeError): op.activate()
                self.assert_held(runtime)
                self.assertEqual([event for event in runtime.events if event[0] == "select"], [("select", "candidate")])
                self.assertFalse(runtime.opened)

    def test_gateway_stop_failure_still_attempts_game_stop(self):
        with operator_fixture() as runtime:
            runtime.fail = lambda args: (_ for _ in ()).throw(RuntimeError("gateway stop acknowledgment lost")) if args[-1] == "gateway" else None
            op.hold("test uncertain stop")
            self.assertIn(("compose", "stop", "-t", "90", "game"), runtime.events)
            self.assertFalse(runtime.running_services["game"])
            held = json.loads(next(op.EVIDENCE.glob("held-*.json")).read_text())
            self.assertTrue(held["both_stopped"])
            self.assertEqual(held["running"], {"gateway": False, "game": False})
            self.assertEqual(held["stop_errors"], {"gateway": "RuntimeError"})

    def test_failed_stop_and_unknown_inspection_are_never_reported_as_stopped(self):
        for unavailable_state in (False, True):
            with self.subTest(unavailable_state=unavailable_state), operator_fixture() as runtime:
                def failed_stop(args):
                    if args[-1] == "gateway":
                        runtime.running_services["gateway"] = True
                        raise RuntimeError("stop rejected")
                runtime.fail = failed_stop
                original_state = runtime.state
                def inspect(name):
                    if unavailable_state and name == "gateway": raise OSError("inspection unavailable")
                    return original_state(name)
                with patch.object(runtime, "state", side_effect=inspect):
                    op.hold("test failed stop")
                held = json.loads(next(op.EVIDENCE.glob("held-*.json")).read_text())
                self.assertFalse(held["both_stopped"])
                self.assertIs(held["running"]["gateway"], None if unavailable_state else True)
                self.assertIs(held["running"]["game"], False)
                self.assertEqual(held["stop_errors"]["gateway"], "RuntimeError")
                self.assertEqual("gateway-verification" in held["stop_errors"], unavailable_state)

    def test_hold_stop_errors_preserve_original_activation_failure(self):
        with operator_fixture() as runtime:
            def fail(args):
                if args[0] == "up": raise ValueError("candidate start acknowledgment lost")
                if args[-1] == "gateway" and any(event[0] == "select" for event in runtime.events):
                    raise RuntimeError("hold stop acknowledgment lost")
            runtime.fail = fail
            with self.assertRaisesRegex(ValueError, "candidate start acknowledgment lost"):
                op.activate()
            self.assert_held(runtime)
            held = json.loads(next(op.EVIDENCE.glob("held-*.json")).read_text())
            self.assertEqual(held["stop_errors"], {"gateway": "RuntimeError"})

    def test_open_failures_before_and_after_access_always_hold_and_never_compare_old_player_state_after_open(self):
        for failure in ("migration", "preservation", "market", "open", "post-open"):
            with self.subTest(failure=failure), operator_fixture(opening=True) as runtime, contextlib.ExitStack() as stack:
                def preserve(*args):
                    self.assertFalse(runtime.opened, "saved-player comparison after access request")
                    if failure == "preservation": raise RuntimeError("player mismatch")
                stack.enter_context(patch.object(op, "preserved", side_effect=preserve))
                if failure == "migration": stack.enter_context(patch.object(op, "verify_migration", side_effect=RuntimeError("receipt mismatch")))
                if failure == "market": stack.enter_context(patch.object(op, "verify_market", side_effect=RuntimeError("epoch mismatch")))
                if failure == "open":
                    runtime.fail = lambda args: (_ for _ in ()).throw(RuntimeError("open acknowledgment lost")) if args[0] == "up" else None
                if failure == "post-open":
                    stack.enter_context(patch.object(op, "untouched", side_effect=lambda *a: (_ for _ in ()).throw(RuntimeError("post-open drift")) if runtime.opened else None))
                with self.assertRaises(RuntimeError): op.open_access()
                self.assert_held(runtime)
                self.assertEqual(runtime.opened, failure in ("open", "post-open"))
                self.assertFalse(any(event[0] in ("sql", "select") for event in runtime.events))

    def test_open_rejects_changed_manifest_before_requesting_access(self):
        with operator_fixture(opening=True) as runtime, patch.object(op, "sha", return_value="changed"):
            with self.assertRaises(AssertionError): op.open_access()
            self.assertFalse(runtime.opened)

    def test_successful_activation_opens_only_after_closed_verification_and_report_binds_manifest(self):
        with operator_fixture() as runtime:
            def preserve(*args):
                self.assertFalse(runtime.opened, "saved-player comparison after access request")
            with patch.object(op, "preserved", side_effect=preserve):
                op.activate()
                self.assertTrue((op.EVIDENCE / "verified-closed.json").exists())
                self.assertFalse(runtime.running_services["gateway"])
                self.assertFalse(runtime.opened)
                self.assertTrue(runtime.running_services["game"])
                op.open_access()
            self.assertTrue(runtime.opened)
            self.assertEqual(runtime.events.count(("sql", "FORWARD")), 1)
            self.assertEqual([event for event in runtime.events if event[0] == "select"], [("select", "candidate")])
            deployed = op.load("activated.json")
            self.assertEqual(deployed["status"], "deployed")
            self.assertEqual(deployed["client_release"], 2026101801)
            self.assertFalse(deployed["database_restored"])
            self.assertFalse(deployed["owner_gameplay_accepted"])
            with patch.object(op, "sha", return_value="changed"):
                with self.assertRaisesRegex(AssertionError, "Release inputs changed"):
                    op.report()

    def test_existing_open_attempt_or_hold_blocks_replay(self):
        for name in ("opening.json", "held-test.json"):
            with self.subTest(name=name), operator_fixture(opening=True) as runtime:
                op.save(name, {})
                with self.assertRaises(AssertionError): op.open_access()
                self.assertFalse(runtime.events)


class MarketAndScratchTests(unittest.TestCase):
    def test_market_requires_exactly_one_rotation_with_unchanged_policy_in_start_window(self):
        before = ["1", "1", "103", "0", "4", "2.500000", "2026-10-18 09:00:00"]
        after = ["1", "1", "104", "0", "4", "2.500000", "2026-10-18 10:00:15"]
        op.validate_market_state(before, after, "2026-10-18T10:00:00Z")
        for field, value in ((2, "103"), (2, "105"), (3, "1"), (4, "5"), (5, "3.000000"),
                             (1, "0"), (6, "2026-10-18 09:59:59"), (6, "2026-10-18 10:01:01")):
            with self.subTest(field=field, value=value):
                changed = after.copy(); changed[field] = value
                with self.assertRaises(AssertionError): op.validate_market_state(before, changed, "2026-10-18T10:00:00Z")

    def test_market_invalid_offer_count_or_eligibility_rejects(self):
        before = ["1", "1", "103", "0", "4", "2.500000", "2026-10-18 09:00:00"]
        after = ["1", "1", "104", "0", "4", "2.500000", "2026-10-18 10:00:15"]
        for result in (("42", "104\t41", "0\n0\n0"), ("42", "104\t42", "1\n0\n0"),
                       ("42", "104\t42", "0\n1\n0"), ("42", "104\t42", "0\n0\n1")):
            with self.subTest(result=result), patch.object(op, "market_state", return_value=after), patch.object(op, "sql", side_effect=result):
                with self.assertRaises(AssertionError): op.verify_market(before, "2026-10-18T10:00:00Z")

    def test_scratch_failure_cleans_only_created_schema_and_never_applies_to_live(self):
        calls = []
        def query(statement, db="peq", **kwargs):
            calls.append((statement, db))
            if statement.startswith("SELECT COUNT(*)"): return "0"
            if statement == "FORWARD": raise RuntimeError("scratch migration failed")
            return ""
        with patch.object(op, "sql", side_effect=query):
            with self.assertRaises(RuntimeError): op.rehearse({}, "digest", [], [], "FORWARD", "REVERSE")
        self.assertIn(("FORWARD", op.SCRATCH), calls)
        self.assertEqual([statement for statement, db in calls if statement.startswith("DROP DATABASE")], ["DROP DATABASE " + op.SCRATCH + ";"])
        self.assertFalse(any(statement in ("FORWARD", "REVERSE") and db == "peq" for statement, db in calls))

    def test_preexisting_scratch_is_not_modified_or_removed(self):
        with patch.object(op, "sql", return_value="1") as query:
            with self.assertRaises(AssertionError): op.rehearse({}, "digest", [], [], "FORWARD", "REVERSE")
            self.assertEqual(query.call_count, 1)

    def test_database_selector_rejects_unknown_schema_before_subprocess(self):
        with patch.object(op.subprocess, "run") as run:
            with self.assertRaises(AssertionError): op.sql("SELECT 1", db="another_live_database")
            run.assert_not_called()


class ManifestAndCaptureTests(unittest.TestCase):
    @contextlib.contextmanager
    def manifest_fixture(self):
        with tempfile.TemporaryDirectory(prefix="cooldown-manifest-test-") as directory:
            root = Path(directory)
            helper = root / "runtime_ops.py"; helper.write_text("helper")
            files = {}
            for name in ("bin/zone", "rollout.py", "capture.py", "cooldown_identity_migration.py"):
                path = root / name; path.parent.mkdir(exist_ok=True); path.write_text(name)
                files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            files["bin/zone"] = "d3908e0348715e94955d84f629e4f27e91f15c7dd661e437efbba580ce3d216a"
            value = {"files": files, "runtime_helper_sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
                     "zone_sha256": files["bin/zone"], "previous_zone": "3c1d74926cb7cff032a3ee8c48c210e37740156e7e36cc0eeddd07f847e88d1a"}
            def digest(path):
                return files["bin/zone"] if Path(path) == root / "bin/zone" else hashlib.sha256(Path(path).read_bytes()).hexdigest()
            with patch.object(op, "STAGE", root), patch.object(op, "HELPER", helper), patch.object(op, "sha", side_effect=digest):
                yield root, value

    def test_manifest_pins_zone_and_rejects_changed_payload(self):
        with self.manifest_fixture() as (root, value):
            (root / "manifest.json").write_text(json.dumps(value))
            self.assertEqual(op.manifest()["zone_sha256"], value["zone_sha256"])
            (root / "capture.py").write_text("altered")
            with self.assertRaises(AssertionError): op.manifest()

    def test_manifest_requires_every_executable_release_helper(self):
        for name in ("rollout.py", "capture.py", "cooldown_identity_migration.py"):
            with self.subTest(name=name), self.manifest_fixture() as (root, value):
                del value["files"][name]
                (root / "manifest.json").write_text(json.dumps(value))
                with self.assertRaises(AssertionError): op.manifest()

    def test_manifest_rejects_path_escape_and_wrong_binary_pair(self):
        for failure in ("escape", "previous", "candidate"):
            with self.subTest(failure=failure), self.manifest_fixture() as (root, value):
                if failure == "escape": value["files"]["../escape"] = "digest"
                else: value["previous_zone" if failure == "previous" else "zone_sha256"] = "wrong"
                (root / "manifest.json").write_text(json.dumps(value))
                with self.assertRaises(AssertionError): op.manifest()

    def test_capture_uses_only_readonly_transactions_and_column_names(self):
        calls = []
        def query(statement, **kwargs):
            calls.append((statement, kwargs))
            return "id\tname\n1\tExample\n"
        result = op.capture.capture(query)
        self.assertEqual(len(calls), len(op.capture.QUERIES))
        self.assertEqual(result["abilities"], [{"id": "1", "name": "Example"}])
        for statement, kwargs in calls:
            self.assertTrue(statement.startswith("START TRANSACTION READ ONLY; SELECT "))
            self.assertTrue(statement.endswith("; ROLLBACK;"))
            self.assertEqual(kwargs, {"headers": True})


if __name__ == "__main__":
    unittest.main(verbosity=2)

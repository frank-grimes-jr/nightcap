"""Admission gates specific to this zone-only release, with no external service calls."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


class Release(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parent
        spec = importlib.util.spec_from_file_location("combat_release",root/"release.py")
        self.op = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{"fcntl":types.SimpleNamespace()}):
            spec.loader.exec_module(self.op)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        o = self.op
        o.EVIDENCE = Path(tmp.name)
        o.ACTIVE = o.EVIDENCE/"activation"
        o.ACTIVE.mkdir()
        self.write(o.EVIDENCE/"preflight.json",{"image":"candidate"})
        self.game = {"image_id":"candidate","running":True}
        self.gateway = {"running":False}
        self.closed = {"game":self.game,"runtime":{"started_at":"now"}}
        self.write(o.ACTIVE/"verified-closed.json",self.closed)
        self.write(o.ACTIVE/"expected-boot-state.json",{"earned":3})
        self.dump = o.ACTIVE/"test-backup"
        self.dump.write_bytes(b"synthetic backup")
        self.write(o.ACTIVE/"backup.json",{"gzip_integrity":True,"compressed_bytes":16,"path":str(self.dump),"sha256":o.sha(self.dump)})
        o.m={"source_revision":"main","client_release":2026111301,"client_channel_sha256":"signed"}
        o.r, o.prior, o.p = Mock(), Mock(), Mock()
        o.r.compact.side_effect=lambda name: self.game if name=="game" else self.gateway
        o.r.running.return_value={"started_at":"now","restart_count":0,"processes":[["zone"]]*12,
                                  "errors":{"native":0,"quest":0,"database":0},"image_id":"candidate"}
        o.p.a.prior.saved.return_value={"earned":3}
        o.p.save.side_effect=self.write
        o.r.compose.side_effect=lambda *args:self.gateway.update(running=True)

    @staticmethod
    def write(path,value):
        path.write_text(json.dumps(value))

    def test_reopen_with_candidate_and_original_channel(self):
        self.op.open_access()
        dep = self.op.read(self.op.ACTIVE/"deployed.json")
        self.assertEqual(dep["client_release"],2026111301)
        self.assertTrue(dep["gateway_open"])
        self.assertFalse(dep["owner_gameplay_accepted"])

    def test_changed_backup_stops_open(self):
        self.dump.write_bytes(b"changed")
        with self.assertRaises(AssertionError): self.op.open_access()
        self.op.r.compose.assert_not_called()

    def test_missing_worker_stops_open(self):
        self.op.r.running.return_value["processes"].pop()
        with self.assertRaises(AssertionError): self.op.open_access()
        self.op.r.compose.assert_not_called()

    def test_saved_player_state_stops_open(self):
        self.op.p.a.prior.saved.return_value={"earned":4}
        with self.assertRaises(AssertionError): self.op.open_access()
        self.op.r.compose.assert_not_called()

    def test_publication_drift_stops_open(self):
        self.op.p.unchanged.side_effect=AssertionError("publication")
        with self.assertRaises(AssertionError): self.op.open_access()
        self.op.r.compose.assert_not_called()

    def test_closed_recovery_rejects_attempted_open(self):
        self.write(self.op.ACTIVE/"started.json",{})
        self.write(self.op.ACTIVE/"opening.json",{})
        with self.assertRaises(AssertionError): self.op.recover_closed()
        self.op.r.compose.assert_not_called()

    def test_reopen_failure_holds(self):
        self.op.r.compose.side_effect=RuntimeError("failed")
        with self.assertRaises(RuntimeError): self.op.open_access()
        self.op.p.h.hold.assert_called_once_with(self.op.ACTIVE)


if __name__ == "__main__":
    unittest.main()

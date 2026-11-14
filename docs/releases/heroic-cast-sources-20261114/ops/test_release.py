"""Verify the staged source and build pins and the pre-admission resume boundary."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


class Gate(unittest.TestCase):
    def setUp(self):
        here = Path(__file__).resolve().parent
        spec = importlib.util.spec_from_file_location("heroic_deployment",here/"release.py")
        self.op = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules,{"fcntl":types.SimpleNamespace()}):
            spec.loader.exec_module(self.op)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.op.STAGE = Path(tmp.name)
        self.combat = Mock()
        self.combat.EVIDENCE = self.op.STAGE/"evidence"
        self.combat.EVIDENCE.mkdir()
        self.combat.ACTIVE = self.combat.EVIDENCE/"activation"
        self.combat.p.a.prior.players.return_value = 0

    def preflight(self):
        (self.combat.EVIDENCE/"preflight.json").write_text("{}")
        self.combat.read.return_value = {"manifest_sha256":"sha","services":{"game":"original"}}
        self.combat.sha.return_value = "sha"
        self.combat.r.compact.return_value = "original"

    def test_release_build_matches_fixed_policy(self):
        here = Path(__file__).resolve().parent
        build = json.loads((here/"shipping-candidate.json").read_bytes())
        data = json.loads((here/"shipping-measurement.json").read_bytes())
        self.assertEqual(build["feature_patch_sha256"],self.op.PATCH)
        self.assertEqual(set(build["units"]),self.op.UNITS)
        self.assertEqual(build["baseline"],self.op.BASE_ZONE)
        self.assertEqual(data["result"],"PASS")
        for name in ("baseline","candidate"):
            self.assertEqual(data["samples"][name]["rows"],190)
        for name, digest in data["samples"]["candidate"]["source_sha256"].items():
            if Path(name).name in build["source_postimages"]:
                self.assertEqual(build["source_postimages"][Path(name).name],digest)

    def test_deploy_fresh(self):
        self.op.deploy(self.combat)
        self.combat.preflight.assert_called_once_with()
        self.combat.p.activate.assert_called_once_with()
        self.combat.open_access.assert_called_once_with()

    def test_occupied_preflight_holds(self):
        self.combat.p.a.prior.players.return_value = 1
        with self.assertRaisesRegex(AssertionError,"Players online"):
            self.op.deploy(self.combat)
        self.combat.p.activate.assert_not_called()

    def test_resume_from_preflight(self):
        self.preflight()
        self.op.deploy(self.combat)
        self.combat.preflight.assert_not_called()
        self.combat.p.unchanged.assert_called_once()
        self.combat.p.activate.assert_called_once_with()

    def test_service_drift_holds(self):
        self.preflight()
        self.combat.r.compact.return_value = "unexpected"
        with self.assertRaises(AssertionError):
            self.op.deploy(self.combat)
        self.combat.p.activate.assert_not_called()

    def test_started_activation_cannot_resume_as_fresh(self):
        self.preflight()
        self.combat.ACTIVE.mkdir()
        with self.assertRaises(AssertionError):
            self.op.deploy(self.combat)
        self.combat.p.activate.assert_not_called()


if __name__ == "__main__":
    unittest.main()

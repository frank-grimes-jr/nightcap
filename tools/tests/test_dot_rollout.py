"""Stage authentication and binding controls; no production service calls."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]


class DotRollout(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        stage = Path(tmp.name)
        path = ROOT / 'docs/balance/dot-initial-damage-20261112/rollout.py'
        spec = importlib.util.spec_from_file_location('dot_rollout', path)
        self.mod = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'fcntl': types.SimpleNamespace()}):
            spec.loader.exec_module(self.mod)
        self.mod.STAGE = stage
        self.mod.PRIOR = stage / 'prior.py'
        self.mod.PRIOR.write_text('pinned prior operator')
        self.mod.PRIOR_SHA256 = self.mod.sha(self.mod.PRIOR)
        (stage / 'bin').mkdir()
        (stage / 'source').mkdir()
        (stage / 'bin/zone').write_bytes(b'candidate')
        (stage / 'source/spell_effects.cpp').write_bytes(b'reviewed source')
        self.proof = {'status': 'PASS', 'baseline_reproduced': True,
                      'source_delta': ['zone/spell_effects.cpp'],
                      'binary_sha256': {'baseline': 'old', 'candidate': self.mod.sha(stage / 'bin/zone')},
                      'candidate_source_sha256': self.mod.sha(stage / 'source/spell_effects.cpp')}
        (stage / 'native-build.json').write_text(json.dumps(self.proof))
        (stage / 'verification.json').write_text(json.dumps({'green': {
            'dot_initial_damage': 2, 'gameplay_policies': 2, 'thj_spell_scaling': 2,
            'thj_behavior_native': 1, 'client_spell_cast_times': 4}}))
        self.manifest = {'owner_authorization': self.mod.AUTHORIZATION,
                         'prior_operator_sha256': self.mod.PRIOR_SHA256,
                         'base_image_id': 'old-image', 'base_hashes': {'bin/zone': 'old'},
                         'binaries': {'zone': self.proof['binary_sha256']['candidate']},
                         'client_channel_sha256': 'retained-client'}
        self.prior = types.SimpleNamespace(initialize=Mock(), r=Mock(),
            m={'client_channel_sha256': 'retained-client'})
        self.prior.r.image_hashes.return_value = {'bin/zone': 'old'}
        self.module = patch.object(self.mod.importlib.util, 'module_from_spec', return_value=self.prior)
        self.module.start()
        self.addCleanup(self.module.stop)
        self.spec = patch.object(self.mod.importlib.util, 'spec_from_file_location', return_value=Mock())
        self.spec.start()
        self.addCleanup(self.spec.stop)
        self.save_manifest()

    def save_manifest(self):
        self.manifest['files'] = {p.relative_to(self.mod.STAGE).as_posix(): self.mod.sha(p)
            for p in self.mod.STAGE.rglob('*') if p.is_file() and p.name not in ('manifest.json', 'prior.py')}
        (self.mod.STAGE / 'manifest.json').write_text(json.dumps(self.manifest))

    def test_binds_authenticated_stage_to_existing_preservation_functions(self):
        result = self.mod.initialize()
        self.assertIs(result, self.prior)
        self.assertEqual(result.STAGE, self.mod.STAGE)
        self.assertEqual(result.EVIDENCE, self.mod.STAGE / 'evidence')
        self.assertEqual(result.m['binaries'], self.manifest['binaries'])
        self.assertEqual(result.TAG, 'nightcap-game:dot-no-initial-damage-20261112-v1')

    def test_rejects_unreviewed_prior_operator(self):
        self.mod.PRIOR.write_text('different operator')
        with self.assertRaises(AssertionError):
            self.mod.initialize()
        self.prior.initialize.assert_not_called()

    def test_rejects_source_payload_drift(self):
        (self.mod.STAGE / 'source/spell_effects.cpp').write_bytes(b'other code')
        with self.assertRaises(AssertionError):
            self.mod.initialize()
        self.prior.initialize.assert_not_called()

    def test_rejects_wrong_shipping_base(self):
        self.prior.r.image_hashes.return_value = {'bin/zone': 'different'}
        with self.assertRaises(AssertionError):
            self.mod.initialize()

    def test_rejects_extra_native_source_changes(self):
        self.proof['source_delta'].append('zone/spells.cpp')
        (self.mod.STAGE / 'native-build.json').write_text(json.dumps(self.proof))
        self.save_manifest()
        with self.assertRaises(AssertionError):
            self.mod.initialize()

    def test_rejects_client_channel_replacement(self):
        self.manifest['client_channel_sha256'] = 'different'
        self.save_manifest()
        with self.assertRaises(AssertionError):
            self.mod.initialize()


if __name__ == '__main__':
    unittest.main()

"""Offline activation, pairing and recovery controls; no server/network access."""
import base64
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.modules['runtime_ops'] = types.SimpleNamespace(ROOT=Path('/not-a-server'))
if sys.platform == 'win32':
    sys.modules['fcntl'] = types.SimpleNamespace()
spec = importlib.util.spec_from_file_location('aa_duration_rollout', Path(__file__).with_name('rollout.py'))
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)

OLD_CHANNEL = '1' * 64
NEW_CHANNEL = '2' * 64
ZONE = '3' * 64
OLD_BINARIES = {'world': 'world', 'zone': 'old-zone', 'ucs': 'ucs', 'loginserver': 'login', 'shared_memory': 'divine-summon-loader'}
OLD_HASHES = {**{'bin/' + name: digest for name, digest in OLD_BINARIES.items()},
              'start.py': 'current-start', 'configure.py': 'current-configure', 'accounts.py': 'current-accounts'}


class Runtime:
    def __init__(self):
        self.image = 'old'
        self.states = {'game': True, 'gateway': True}
        self.failure = None
        self.calls = []
        self.running_checks = []
        self.drift = self.custom_drift = False
        self.channel = OLD_CHANNEL
        self.public_other = 'same'
        self.generation = 0
        self.initial_restarts = 1
        self.ROOT = Path('/not-a-server')

    def compact(self, name):
        image = self.image if name == 'game' else name
        if self.failure == 'baseline' and name == 'game':
            image = 'external'
        data = {'id': name + '-' + (str(self.generation) if name == 'game' else 'stable'), 'image_id': image,
                'started_at': image + '-' + str(self.generation if name == 'game' else 0),
                'restarts': self.initial_restarts if name == 'game' and not self.generation else 0,
                'running': self.states.get(name, True), 'health': 'healthy', 'oom_killed': False}
        if self.failure == 'support' and name == 'web':
            data['id'] = 'changed-web'
        return data

    def state(self, name):
        return {'State': {'Running': self.states[name], 'ExitCode': 0, 'OOMKilled': False}}

    def image_hashes(self, image):
        result = dict(OLD_HASHES)
        if image == 'new':
            result['bin/zone'] = ZONE
            if self.failure == 'loader':
                result['bin/shared_memory'] = 'stale-loader'
        return result

    def runtime(self):
        return {'global/player.pl': 'changed' if self.failure == 'quests' else 'same'}

    def public(self):
        if self.failure == 'public_unknown':
            raise RuntimeError('Cannot read public channel')
        return {'channel.json': self.channel, 'launcher-channel.json': self.public_other, 'nightcap-friends.zip': 'zip', 'guide.html': 'guide'}

    def content_data(self):
        return 'changed' if self.failure == 'content' else 'content'

    def policies(self):
        return 'changed' if self.failure == 'policies' else 'rules'

    def closed_ports(self):
        if self.failure == 'ports':
            raise RuntimeError('Public port drift')

    def player_data(self):
        if self.image == 'new' and self.failure == 'data':
            self.drift = True
        return {'inventory': 'changed' if self.drift else 'same', 'character_advloot_claims': 'receipts'}

    def extras(self):
        if self.image == 'new' and self.failure == 'custom':
            self.custom_drift = True
        return {'nightcap_forge_receipts': 'changed' if self.custom_drift else 'same'}

    def compose(self, *args):
        self.calls.append(args)
        service = args[-1]
        self.states[service] = args[0] == 'up'
        if args[0] == 'up' and service == 'game':
            self.generation += 1
        if args[0] == 'up' and service == 'gateway' and self.failure in ('gateway', 'gateway_data'):
            self.drift = self.failure == 'gateway_data'
            raise RuntimeError('Lost gateway acknowledgment')

    def running(self, image, hashes, expected_restarts=0):
        self.running_checks.append((image, dict(hashes), expected_restarts))
        assert image == self.image
        assert hashes == {**OLD_BINARIES, **({'zone': ZONE} if image == 'new' else {})}
        assert expected_restarts == (self.initial_restarts if not self.generation else 0)
        if image == 'new' and self.failure == 'health':
            raise RuntimeError('Unhealthy candidate')
        if image == 'new' and self.failure == 'new_restart':
            raise RuntimeError('Candidate restart count is one, expected zero')
        if image == 'new' and self.failure == 'publish_during_activation':
            self.channel = NEW_CHANNEL
        if image == 'new' and self.failure == 'unexpected_gateway':
            self.states['gateway'] = True
        return {'image_id': image, 'started_at': image + '-' + str(self.generation), 'restart_count': expected_restarts}

    def call(self, *args):
        self.calls.append(args)

    def out(self, *args):
        if '--format' in args:
            return 'old' if args[-1].endswith('base-20261016') else 'new'
        return json.dumps([{'RootFS': {'Layers': ['base'] + (['zone'] if args[-1] == 'new' else [])}}])

    def database_backup(self):
        return {'verified': True}


class Harness:
    def __init__(self, case):
        self.case = case
        self.r = Runtime()
        self.m = {'binaries': {'zone': ZONE}, 'base_binaries': dict(OLD_BINARIES),
                  'client_channel_sha256': OLD_CHANNEL, 'client_release': 2026101302, 'baseline_restarts': 1}
        self.p = {'manifest_sha256': 'manifest', 'old_image_id': 'old', 'new_image_id': 'new', 'zone_sha256': ZONE,
                  'old_hashes': dict(OLD_HASHES), 'services': {name: self.r.compact(name) for name in ('game', 'gateway', 'db', 'web', 'tunnel')},
                  'runtime': self.r.runtime(), 'public': self.r.public(), 'policies': 'rules', 'content': 'content', 'backup': 'verified-backup'}
        self.evidence = {'preflight.json': copy.deepcopy(self.p)}
        self.selected = []

    def select(self, image):
        self.case.assertFalse(any(self.r.states.values()), 'Image selected with live access or game process')
        self.selected.append(image)
        self.r.image = image

    def save(self, name, value):
        self.case.assertNotIn(name, self.evidence, 'Existing evidence must never be overwritten')
        self.evidence[name] = copy.deepcopy(value)

    def verify_publication(self, m):
        assert self.r.channel == m['client_channel_sha256'], 'Wrong client publication'
        return {'release': m['client_release'], 'channel_sha256': m['client_channel_sha256'], 'verified_files': 106}

    def context(self):
        stack = ExitStack()
        for name, replacement in (
            ('r', self.r), ('manifest', lambda: self.m), ('load', lambda name: copy.deepcopy(self.evidence[name])),
            ('save', self.save), ('exists', lambda name: name in self.evidence), ('sha', lambda _: 'manifest'),
            ('policies', self.r.policies), ('extras', self.r.extras), ('select', self.select),
            ('verify_publication', self.verify_publication)):
            stack.enter_context(patch.object(q, name, replacement))
        stack.enter_context(patch.object(q.time, 'sleep'))
        stack.enter_context(patch('builtins.print'))
        return stack

    def run(self, action):
        with self.context():
            try:
                action()
            except (AssertionError, RuntimeError) as error:
                return error
        return None


class RolloutTests(unittest.TestCase):
    def test_unexpected_gateway_during_activation_retains_candidate(self):
        h = Harness(self)
        h.r.failure = 'unexpected_gateway'
        self.assertIsNotNone(h.run(q.activate))
        self.assertEqual(h.selected, ['new'])
        self.assertTrue(h.r.states['game'])
        self.assertFalse(h.r.states['gateway'])
        self.assertTrue(h.evidence['recovery-held.json']['access_may_have_opened'])

    def test_unexpected_open_gateway_retains_candidate_and_holds_access(self):
        h = Harness(self)
        self.assertIsNone(h.run(q.activate))
        h.r.states['gateway'] = True
        h.r.drift = True
        self.assertIsNotNone(h.run(q.open_access))
        self.assertEqual(h.selected, ['new'])
        self.assertTrue(h.r.states['game'])
        self.assertFalse(h.r.states['gateway'])
        self.assertTrue(h.r.drift)
        self.assertTrue(h.evidence['recovery-held.json']['access_may_have_opened'])
        self.assertFalse(h.evidence['recovery-held.json']['database_restored'])

    def test_success_activation_holds_then_opens_with_unchanged_client(self):
        h = Harness(self)
        self.assertIsNone(h.run(q.activate))
        self.assertEqual(h.selected, ['new'])
        self.assertTrue(h.r.states['game'])
        self.assertFalse(h.r.states['gateway'])
        self.assertIn('activated-closed.json', h.evidence)
        self.assertNotIn('activated.json', h.evidence)
        h.r.channel = OLD_CHANNEL
        self.assertIsNone(h.run(q.open_access))
        self.assertTrue(h.r.states['gateway'])
        self.assertFalse(h.evidence['activated.json']['database_restored'])
        self.assertEqual([args for args in h.r.calls if args[0] == 'up' and args[-1] == 'gateway'],
                         [('up', '-d', '--wait', '--wait-timeout', '60', 'gateway')])
        self.assertTrue(all(check[2] == 0 for check in h.r.running_checks))
        self.assertTrue(all(check[1]['shared_memory'] == 'divine-summon-loader' for check in h.r.running_checks))

    def test_baseline_drift_does_not_touch_running_services(self):
        h = Harness(self)
        h.r.failure = 'baseline'
        self.assertIsNotNone(h.run(q.activate))
        self.assertEqual(h.r.calls, [])
        self.assertEqual(h.selected, [])

    def test_unrelated_loader_change_is_rejected_before_stop(self):
        h = Harness(self)
        h.r.failure = 'loader'
        self.assertIsNotNone(h.run(q.activate))
        self.assertEqual(h.r.calls, [])

    def test_health_failure_rolls_back_to_old_paired_channel(self):
        for failure in ('health', 'new_restart'):
            with self.subTest(failure=failure):
                h = Harness(self)
                h.r.failure = failure
                self.assertIsNotNone(h.run(q.activate))
                self.assertEqual(h.selected, ['new', 'old'])
                self.assertTrue(all(h.r.states.values()))
                self.assertIn('rolled-back.json', h.evidence)

    def test_data_drift_is_never_restored_and_recovery_holds(self):
        for failure in ('data', 'custom'):
            with self.subTest(failure=failure):
                h = Harness(self)
                h.r.failure = failure
                self.assertIsNotNone(h.run(q.activate))
                self.assertEqual(h.selected, ['new', 'old'])
                self.assertFalse(h.r.states['gateway'])
                self.assertTrue(h.r.states['game'])
                self.assertIn('recovery-held.json', h.evidence)
                self.assertFalse(h.evidence['recovery-held.json']['database_restored'])
                self.assertTrue(h.r.drift or h.r.custom_drift)

    def test_new_publication_during_failed_activation_forbids_reopen(self):
        h = Harness(self)
        h.r.failure = 'publish_during_activation'
        self.assertIsNotNone(h.run(q.activate))
        self.assertEqual(h.selected, ['new', 'old'])
        self.assertFalse(h.r.states['gateway'])
        self.assertIn('recovery-held.json', h.evidence)

    def test_wrong_or_missing_publication_refuses_open(self):
        for channel in (NEW_CHANNEL, 'unexpected'):
            with self.subTest(channel=channel):
                h = Harness(self)
                self.assertIsNone(h.run(q.activate))
                h.r.channel = channel
                self.assertIsNotNone(h.run(q.open_access))
                self.assertFalse(h.r.states['gateway'])
                self.assertNotIn('opening.json', h.evidence)
                self.assertIn('recovery-held.json', h.evidence)

    def test_drift_before_open_is_held_without_access(self):
        for failure in ('data', 'custom', 'support', 'quests', 'content', 'policies', 'public_unknown', 'ports'):
            with self.subTest(failure=failure):
                h = Harness(self)
                self.assertIsNone(h.run(q.activate))
                h.r.channel = OLD_CHANNEL
                h.r.failure = failure
                self.assertIsNotNone(h.run(q.open_access))
                self.assertFalse(h.r.states['gateway'])
                self.assertNotIn('opening.json', h.evidence)
                self.assertIn('recovery-held.json', h.evidence)

    def test_other_public_entrypoint_cannot_change_with_client(self):
        h = Harness(self)
        self.assertIsNone(h.run(q.activate))
        h.r.channel = OLD_CHANNEL
        h.r.public_other = 'changed-launcher'
        self.assertIsNotNone(h.run(q.open_access))
        self.assertFalse(h.r.states['gateway'])
        self.assertNotIn('opening.json', h.evidence)

    def test_lost_gateway_ack_holds_candidate_without_replay_or_sql_restore(self):
        for failure in ('gateway', 'gateway_data'):
            with self.subTest(failure=failure):
                h = Harness(self)
                self.assertIsNone(h.run(q.activate))
                h.r.channel = OLD_CHANNEL
                h.r.failure = failure
                self.assertIsNotNone(h.run(q.open_access))
                self.assertEqual(h.selected, ['new'])
                self.assertTrue(h.r.states['game'])
                self.assertFalse(h.r.states['gateway'])
                self.assertTrue(h.evidence['recovery-held.json']['access_may_have_opened'])
                self.assertFalse(h.evidence['recovery-held.json']['database_restored'])
                calls = list(h.r.calls)
                self.assertIsNotNone(h.run(q.open_access))
                self.assertEqual(h.r.calls, calls)
                self.assertEqual(sum(args[0] == 'up' and args[-1] == 'gateway' for args in calls), 1)
                self.assertEqual(h.r.drift, failure == 'gateway_data')

    def test_successful_actions_are_not_replayed(self):
        h = Harness(self)
        self.assertIsNone(h.run(q.activate))
        calls = list(h.r.calls)
        self.assertIsNotNone(h.run(q.activate))
        self.assertEqual(h.r.calls, calls)
        h.r.channel = OLD_CHANNEL
        self.assertIsNone(h.run(q.open_access))
        calls = list(h.r.calls)
        self.assertIsNotNone(h.run(q.open_access))
        self.assertEqual(h.r.calls, calls)

    def test_preflight_allows_observed_one_restart_and_retains_full_image(self):
        h = Harness(self)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            stage = Path(directory)
            h.r.EVIDENCE = stage / 'evidence'
            h.evidence.clear()
            with h.context(), patch.object(q, 'STAGE', stage), patch.object(q, 'validate_image'):
                q.preflight()
        self.assertEqual(h.r.running_checks[0][2], 1)
        self.assertEqual(h.evidence['preflight.json']['old_hashes'], OLD_HASHES)
        self.assertEqual(h.evidence['preflight.json']['zone_sha256'], ZONE)
        self.assertFalse(any(args[0] in ('stop', 'up') for args in h.r.calls))

    def test_preflight_rejects_unexpected_prior_restarts(self):
        h = Harness(self)
        h.r.initial_restarts = 2
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            h.r.EVIDENCE = Path(directory) / 'evidence'
            with h.context(), patch.object(q, 'STAGE', Path(directory)):
                with self.assertRaises(AssertionError):
                    q.preflight()
        self.assertEqual(h.r.calls, [])

    def test_preflight_rejects_newer_unreviewed_baseline(self):
        h = Harness(self)
        h.m['base_binaries']['zone'] = 'unreviewed-zone'
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            h.r.EVIDENCE = Path(directory) / 'evidence'
            with h.context(), patch.object(q, 'STAGE', Path(directory)):
                with self.assertRaisesRegex(AssertionError, 'Deployed baseline differs'):
                    q.preflight()
        self.assertEqual(h.r.calls, [])


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / 'stage'
        self.stage.mkdir()
        self.public = self.root / 'data/public'
        self.release = self.public / 'release/2026101302'
        self.release.mkdir(parents=True)
        (self.release / 'dinput8.dll').write_bytes(b'verified proxy')
        self.signed = {'release': 2026101302, 'expires': '2099-01-01T00:00:00Z', 'files': [
            {'path': 'dinput8.dll', 'sha256': q.sha(self.release / 'dinput8.dll'), 'size': 14, 'required': True,
             'url': 'https://play.nightcapgame.org/release/2026101302/dinput8.dll'}]}
        self.receipt = {'release': 2026101302, 'verified_files': 1, 'signature': 'valid against shipped production public key'}
        self.m = {'client_release': 2026101302, 'files': {}}
        self.write_signed()

    def write_signed(self):
        envelope = {'manifest': base64.b64encode(json.dumps(self.signed).encode()).decode(), 'signature': {'bytes': 'verified-by-pinned-receipt'}}
        (self.public / 'channel.json').write_text(json.dumps(envelope))
        self.m['client_channel_sha256'] = q.sha(self.public / 'channel.json')
        self.receipt['channel_sha256'] = self.m['client_channel_sha256']
        self.write_receipt()

    def write_receipt(self):
        path = self.stage / q.CLIENT_RECEIPT
        path.write_text(json.dumps(self.receipt))
        self.m['files'][q.CLIENT_RECEIPT] = q.sha(path)

    def verify(self):
        with patch.object(q, 'ROOT', self.root), patch.object(q, 'STAGE', self.stage):
            return q.verify_publication(self.m)

    def test_exact_signed_channel_and_assets_pass(self):
        self.assertEqual(self.verify()['verified_files'], 1)

    def test_missing_signature_verification_rejected(self):
        self.receipt['signature'] = 'not verified'
        self.write_receipt()
        with self.assertRaisesRegex(AssertionError, 'signature not verified'):
            self.verify()

    def test_unpinned_receipt_rejected(self):
        (self.stage / q.CLIENT_RECEIPT).write_text('{}')
        with self.assertRaisesRegex(AssertionError, 'receipt drift'):
            self.verify()

    def test_unpublished_channel_rejected(self):
        (self.public / 'channel.json').write_bytes(b'old channel')
        with self.assertRaisesRegex(AssertionError, 'not published'):
            self.verify()

    def test_expired_signature_contract_rejected(self):
        self.signed['expires'] = '2000-01-01T00:00:00Z'
        self.write_signed()
        with self.assertRaisesRegex(AssertionError, 'expired'):
            self.verify()

    def test_wrong_release_receipt_rejected(self):
        self.receipt['release'] = 2026101301
        self.write_receipt()
        with self.assertRaisesRegex(AssertionError, 'release mismatch'):
            self.verify()

    def test_tampered_published_asset_rejected(self):
        (self.release / 'dinput8.dll').write_bytes(b'altered proxy!')
        with self.assertRaisesRegex(AssertionError, 'asset differs'):
            self.verify()

    def test_unexpected_release_file_rejected(self):
        (self.release / 'extra.dll').write_bytes(b'extra')
        with self.assertRaisesRegex(AssertionError, 'Unexpected published files'):
            self.verify()

    def test_unsafe_asset_path_rejected(self):
        self.signed['files'][0]['path'] = '../outside.dll'
        self.write_signed()
        with self.assertRaises(AssertionError):
            self.verify()


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.stage = Path(self.temp.name)
        self.helper = self.stage / 'runtime_ops.py'
        self.helper.write_text('reviewed helper')
        for name in ('zone', 'rollout.py', 'test_rollout.py'):
            (self.stage / name).write_text('reviewed ' + name)
        receipt = {'signature': 'valid against shipped production public key', 'release': 2026101302,
                   'channel_sha256': NEW_CHANNEL, 'verified_files': 106}
        (self.stage / q.CLIENT_RECEIPT).write_text(json.dumps(receipt))
        self.m = {'runtime_helper_sha256': q.sha(self.helper), 'client_release': 2026101302,
                  'client_channel_sha256': NEW_CHANNEL, 'binaries': {'zone': q.sha(self.stage / 'zone')},
                  'base_binaries': {name: '4' * 64 for name in q.BINARY_NAMES}, 'baseline_restarts': 1,
                  'files': {name: q.sha(self.stage / name) for name in ('zone', 'rollout.py', 'test_rollout.py', q.CLIENT_RECEIPT)}}

    def read(self):
        (self.stage / 'manifest.json').write_text(json.dumps(self.m))
        with patch.object(q, 'STAGE', self.stage), patch.object(q, 'r', types.SimpleNamespace(__file__=str(self.helper))):
            return q.manifest()

    def test_complete_baseline_is_required_and_valid_manifest_passes(self):
        self.assertEqual(self.read()['base_binaries'], self.m['base_binaries'])
        del self.m['base_binaries']
        with self.assertRaisesRegex(AssertionError, 'reviewed native baseline'):
            self.read()

    def test_missing_divine_loader_baseline_hash_rejected(self):
        del self.m['base_binaries']['shared_memory']
        with self.assertRaisesRegex(AssertionError, 'reviewed native baseline'):
            self.read()

    def test_missing_signed_channel_hash_rejected(self):
        del self.m['client_channel_sha256']
        with self.assertRaisesRegex(AssertionError, 'Missing signed client channel hash'):
            self.read()

    def test_unpinned_signature_receipt_rejected(self):
        del self.m['files'][q.CLIENT_RECEIPT]
        with self.assertRaisesRegex(AssertionError, 'Unpinned release input'):
            self.read()

    def test_staged_zone_hash_drift_rejected(self):
        (self.stage / 'zone').write_bytes(b'changed binary')
        with self.assertRaises(AssertionError):
            self.read()


class MaintenanceTests(unittest.TestCase):
    def test_inflight_gm_sql_rejected(self):
        with patch.object(q.Path, 'exists', return_value=False), patch.object(q, 'r', types.SimpleNamespace(sql=lambda _: '0')):
            with self.assertRaisesRegex(AssertionError, 'GM SQL'):
                q.require_no_gm_work()

    def test_existing_gm_maintenance_rejected(self):
        with patch.object(q.Path, 'exists', return_value=True):
            with self.assertRaisesRegex(AssertionError, 'GM maintenance'):
                q.require_no_gm_work()

    def test_idle_gm_allowed(self):
        with patch.object(q.Path, 'exists', return_value=False), patch.object(q, 'r', types.SimpleNamespace(sql=lambda _: '1')):
            q.require_no_gm_work()


if __name__ == '__main__':
    unittest.main(verbosity=2)

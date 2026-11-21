"""Exercise production rollout sequencing with mocked runtime operations."""
import importlib.util
from itertools import repeat
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    'aa_purchase_release', Path(__file__).with_name('release.py')
)
release = importlib.util.module_from_spec(spec)
if sys.platform == 'win32':
    # The production entry point uses flock on Linux. Tests call deploy directly.
    with patch.dict(sys.modules, {'fcntl': SimpleNamespace()}):
        spec.loader.exec_module(release)
else:
    spec.loader.exec_module(release)


class RolloutTests(unittest.TestCase):
    def setUp(self):
        directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.active = directory / 'evidence' / 'activation'
        self.preflight = directory / 'preflight.json'
        manifest_path = directory / 'manifest.json'
        manifest_path.write_text('{}', encoding='utf-8')
        channel = directory / 'data/public/channel.json'
        channel.parent.mkdir(parents=True)
        channel.write_text('{}', encoding='utf-8')
        self.backup = directory / 'backup.gz'
        self.backup.write_bytes(b'mocked stopped database dump')
        self.events = []
        self.clock = 0
        self.running = True
        self.gateway = True
        self.image = self.selected = 'incumbent'
        self.players = iter(())
        self.game_stop_seconds = 2
        self.partial_gateway_stop = False
        self.partial_gateway_open = False
        self.bad_backup = False
        self.saved_state_drift = False
        self.market_drift = False
        self.caches = {'items': 'item-pin', 'spells': 'spell-pin'}
        self.runtime_files = {'quests/example.lua': 'quest-pin'}
        self.hashes = {'incumbent': {'bin/zone': 'old'}, 'target': {'bin/zone': 'new'}}
        self.manifest = {
            'image': 'incumbent', 'base_hashes': {'bin/zone': 'old'},
            'binaries': {'zone': 'new'}, 'channel': release.sha(channel),
            'caches': self.caches, 'source': 'a' * 40,
            'services': {name: self.compact(name)
                         for name in ('game', 'gateway', 'db', 'web', 'tunnel')},
        }
        self.approved = {
            'result': 'PASS', 'baseline': 'incumbent', 'candidate': 'target',
            'manifest': release.sha(manifest_path), 'binaries': {'zone': 'new'},
            'runtime_files': self.runtime_files,
        }
        self.write_preflight()
        operator = SimpleNamespace(
            a=SimpleNamespace(prior=SimpleNamespace(players=self.player_count, saved=self.saved)),
            h=SimpleNamespace(caches=lambda: self.caches, publication=lambda: {'wiki': 'current'},
                              hold=self.hold),
            p=SimpleNamespace(startup=SimpleNamespace(startup_guards=lambda: self.events.append('startup guards')),
                              market=SimpleNamespace(market=self.market, verify_market=self.verify_market),
                              contract=lambda: None),
            base=SimpleNamespace(health=lambda: None, boot_state=self.boot_state),
        )
        runtime = SimpleNamespace(
            image_hashes=self.hashes.__getitem__, compact=self.compact,
            runtime=lambda: dict(self.runtime_files), running=self.running_image,
            closed_ports=lambda: None, compose=self.compose, state=self.state,
            database_backup=self.database_backup, select=self.select,
        )
        self.enterContext(patch.multiple(
            release, create=True, ACTIVE=self.active, ROOT=directory, STAGE=directory,
            m=self.manifest, op=operator, r=runtime, save=self.save,
            sql=lambda statement: '1\tRule\tunchanged',
            time=SimpleNamespace(sleep=self.sleep, monotonic=lambda: self.clock),
            shutil=SimpleNamespace(disk_usage=lambda path: SimpleNamespace(free=4 * 1024**3)),
        ))

    def write_preflight(self):
        self.preflight.write_text(json.dumps(self.approved), encoding='utf-8')

    def compact(self, service):
        if service == 'game':
            return {'running': self.running, 'image_id': self.image}
        if service == 'gateway':
            return {'running': self.gateway}
        return {'service': service, 'running': True}

    def sleep(self, seconds):
        self.events.append(('wait', seconds))
        self.clock += seconds

    def player_count(self):
        count = next(self.players, 0)
        self.events.append(('players', count))
        return count

    def running_image(self, candidate, binaries):
        self.assertTrue(self.running)
        self.assertEqual(self.image, candidate)
        self.assertEqual(binaries, {'zone': self.hashes[candidate]['bin/zone']})
        self.events.append(('verify', candidate, self.gateway))
        return {'errors': {'native': 0}, 'restart_count': 0,
                'processes': [('zone', binaries['zone'])] * 12, 'started_at': candidate}

    def compose(self, *args):
        if args == ('stop', 'gateway'):
            self.events.append('stop gateway')
            self.gateway = False
            if self.partial_gateway_stop:
                self.partial_gateway_stop = False
                raise RuntimeError('lost gateway stop acknowledgement')
        elif args == ('stop', '-t', '90', 'game'):
            self.assertFalse(self.gateway)
            self.events.append('stop game')
            self.clock += self.game_stop_seconds
            self.running = False
        elif args == ('up', '-d', '--no-deps', '--wait', '--wait-timeout', '240', 'game'):
            self.assertFalse(self.gateway)
            self.events.append('start game')
            self.image = self.selected
            self.running = True
        elif args == ('up', '-d', '--no-deps', '--wait', '--wait-timeout', '60', 'gateway'):
            self.assertTrue((self.active / 'verified-closed.json').is_file())
            self.assertTrue((self.active / 'opening.json').is_file())
            self.events.append('open gateway')
            self.gateway = True
            if self.partial_gateway_open:
                raise RuntimeError('lost gateway opening acknowledgement')
        else:
            self.fail(f'Unexpected compose command: {args}')

    def state(self, service):
        self.assertEqual(service, 'game')
        return {'State': {'Running': self.running, 'OOMKilled': False, 'ExitCode': 0}}

    def saved(self):
        if self.image == 'target':
            return {'players': 'changed' if self.saved_state_drift else 'preserved'}
        return {'players': 'preserved'}

    def market(self):
        self.assertFalse(self.running)
        return {'rotation': 1}

    def database_backup(self):
        self.assertFalse(self.running)
        self.assertFalse(self.gateway)
        self.events.append('backup')
        return {'path': str(self.backup), 'gzip_integrity': True,
                'sha256': 'bad' if self.bad_backup else release.sha(self.backup)}

    def boot_state(self, saved):
        self.assertTrue((self.active / 'backup.json').exists())
        self.events.append('model startup state')
        return saved

    def select(self, image):
        self.assertFalse(self.running)
        self.assertFalse(self.gateway)
        self.events.append('select image')
        self.selected = image

    def verify_market(self, before, started_at):
        self.assertFalse(self.gateway)
        self.assertEqual(before, {'rotation': 1})
        self.assertEqual(started_at, 'target')
        self.events.append('verify market')
        if self.market_drift:
            raise RuntimeError('unexpected market drift')
        return {'rotation': 2}

    def save(self, path, value):
        with path.open('x', encoding='utf-8') as stream:
            json.dump(value, stream)
        self.events.append(path.name)

    def hold(self, folder):
        self.assertEqual(folder, self.active)
        self.gateway = self.running = False
        self.events.append('hold')

    def assert_failed_closed(self):
        self.assertFalse(self.gateway)
        self.assertFalse((self.active / 'deployed.json').exists())

    def test_authorized_drain_and_verification_precede_opening(self):
        self.players = iter((1, 1, 0))
        release.deploy(allow_admission_drain=True)
        ordered_events = [
            'started.json', 'stop gateway', ('wait', 125), ('players', 0),
            'stop game', 'stopped.json', 'backup', 'backup.json', 'model startup state',
            'select image', 'start game', ('verify', 'target', False), 'verify market',
            'verified-closed.json', 'opening.json', 'open gateway',
            ('verify', 'target', True), 'deployed.json',
        ]
        positions = [self.events.index(event) for event in ordered_events]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(self.events.count('startup guards'), 2)
        self.assertTrue(self.gateway)
        self.assertEqual(release.read(self.active / 'deployed.json')['image'], 'target')

    def test_changed_incumbent_blocks_before_maintenance(self):
        self.hashes['incumbent']['bin/zone'] = 'different'
        with self.assertRaises(AssertionError):
            release.deploy()
        self.assertFalse(self.active.exists())
        self.assertTrue(self.gateway)

    def test_stale_preflight_or_changed_candidate_blocks_before_maintenance(self):
        for failure in ('manifest', 'image'):
            with self.subTest(failure=failure):
                if failure == 'manifest':
                    self.approved['manifest'] = 'stale'
                    self.write_preflight()
                else:
                    self.approved['manifest'] = release.sha(release.STAGE / 'manifest.json')
                    self.write_preflight()
                    self.hashes['target']['bin/zone'] = 'different'
                with self.assertRaises(AssertionError):
                    release.deploy()
                self.assertFalse(self.active.exists())
                self.assertTrue(self.gateway)

    def test_stop_that_partially_closes_gateway_blocks_activation(self):
        self.partial_gateway_stop = True
        with self.assertRaisesRegex(RuntimeError, 'lost gateway stop'):
            release.deploy()
        self.assert_failed_closed()
        self.assertTrue(self.running)
        self.assertNotIn('hold', self.events)
        self.assertEqual(release.read(self.active / 'held-access.json'),
                         {'game_transition': False, 'opening_attempted': False})
        self.assertNotIn('backup', self.events)
        self.assertNotIn('select image', self.events)

    def test_drain_timeout_closes_admissions_without_stopping_players(self):
        self.players = repeat(1)
        with self.assertRaisesRegex(AssertionError, 'World did not drain'):
            release.deploy(allow_admission_drain=True)
        self.assert_failed_closed()
        self.assertTrue(self.running)
        self.assertNotIn('hold', self.events)
        self.assertNotIn('stop game', self.events)

    def test_supervisor_timeout_blocks_backup_even_with_zero_exit_status(self):
        self.game_stop_seconds = 75
        with self.assertRaisesRegex(AssertionError, 'forced-exit boundary'):
            release.deploy()
        self.assert_failed_closed()
        self.assertNotIn('backup', self.events)

    def test_failed_backup_blocks_image_selection(self):
        self.bad_backup = True
        with self.assertRaises(AssertionError):
            release.deploy()
        self.assert_failed_closed()
        self.assertNotIn('select image', self.events)

    def test_saved_state_drift_blocks_opening(self):
        self.saved_state_drift = True
        with self.assertRaises(AssertionError):
            release.deploy()
        self.assert_failed_closed()
        self.assertNotIn('verified-closed.json', self.events)
        self.assertNotIn('open gateway', self.events)

    def test_market_drift_blocks_opening(self):
        self.market_drift = True
        with self.assertRaisesRegex(RuntimeError, 'market drift'):
            release.deploy()
        self.assert_failed_closed()
        self.assertNotIn('open gateway', self.events)

    def test_uncertain_open_is_held_and_terminal_attempt_cannot_replay(self):
        self.partial_gateway_open = True
        with self.assertRaisesRegex(RuntimeError, 'lost gateway opening'):
            release.deploy()
        self.assert_failed_closed()
        self.assertTrue(self.running)
        self.assertNotIn('hold', self.events)
        self.assertTrue((self.active / 'opening.json').is_file())
        self.assertEqual(release.read(self.active / 'held-access.json'),
                         {'game_transition': True, 'opening_attempted': True})
        events = list(self.events)
        with self.assertRaises(AssertionError):
            release.deploy()
        self.assertEqual(self.events, events)


if __name__ == '__main__':
    unittest.main()

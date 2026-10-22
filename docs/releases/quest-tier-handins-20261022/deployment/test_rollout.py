"""Offline fault tests for paired quest/native rollout; never connects to production."""
import contextlib
import copy
import hashlib
import importlib.util
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('quest_rollout', Path(__file__).with_name('rollout.py'))
op = importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)
QUESTS = ['quests/lua_modules/items.lua', 'quests/overthere/Kurron_Ni.pl'] + [
    'quests/soltemple/' + name + '.pl' for name in ('Gardern', 'Joyce', 'Sultin', 'Vilissia', 'Vurgo')]


class Runtime:
    def __init__(self):
        self.events = []
        self.fail = None
        self.image = 'old'
        self.opened = False
        self.running_services = {'game': True, 'gateway': True}

    def compact(self, name):
        return {'image_id': self.image if name == 'game' else name,
                'running': self.running_services.get(name, True)}

    def state(self, name):
        return {'Id': name, 'State': {'Running': self.running_services[name], 'ExitCode': 0, 'OOMKilled': False}}

    def compose(self, *args):
        self.events.append(args)
        self.running_services[args[-1]] = args[0] != 'stop'
        if args[0] == 'up' and args[-1] == 'gateway':
            self.opened = True
        if self.fail:
            self.fail(args)

    def select(self, image):
        self.events.append(('select', image))
        self.image = image

    def image_hashes(self, image):
        return {'bin/zone': image}

    def database_backup(self):
        self.events.append(('backup',))
        return {'gzip_integrity': 'passed'}

    def running(self, image, binaries):
        return {'image_id': image, 'started_at': '2026-10-22T18:00:00Z'}

    def closed_ports(self):
        pass


@contextlib.contextmanager
def lifecycle():
    with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
        root = Path(directory)
        evidence = root / 'evidence'
        evidence.mkdir()
        runtime = Runtime()
        data = {'player': {'inventory': 'earned-now', 'zone_state_spawns': 'exact-cache'},
                'custom': {'timers': 'current-deadlines'}}
        for name, value in {'ROOT': root, 'STAGE': root, 'EVIDENCE': evidence, 'r': runtime}.items():
            stack.enter_context(patch.object(op, name, value))
        stack.enter_context(patch.object(op, 'manifest', return_value={
            'base_hashes': {'bin/zone': 'old'}, 'client_channel_sha256': 'client'}))
        stack.enter_context(patch.object(op, 'sha', return_value='digest'))
        stack.enter_context(patch.object(op, 'untouched'))
        stack.enter_context(patch.object(op, 'health'))
        stack.enter_context(patch.object(op, 'install_quests', side_effect=lambda folder: runtime.events.append(('quests',))))
        stack.enter_context(patch.object(op, 'binaries', side_effect=lambda recovery=False: {'zone': 'old' if recovery else 'new'}))
        stack.enter_context(patch.object(op, 'saved_state', side_effect=lambda: copy.deepcopy(data)))
        stack.enter_context(patch.object(op, 'market', return_value=['before']))
        stack.enter_context(patch.object(op, 'verify_market', return_value={'rotation': 'once'}))
        stack.enter_context(patch.object(op.time, 'sleep'))
        stack.enter_context(patch.object(op.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=2**30)))
        op.save(evidence / 'preflight.json', {'manifest_sha256': 'digest', 'old_image_id': 'old',
            'new_image_id': 'new', 'services': {s: runtime.compact(s) for s in ('game', 'gateway')}})
        yield runtime, data, evidence


@contextlib.contextmanager
def files():
    with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
        root = Path(directory) / 'production'
        stage = Path(directory) / 'stage'
        root.mkdir(); stage.mkdir()
        helper = Path(directory) / 'helper.py'
        helper.write_text('trusted helper')
        for name in QUESTS:
            for base, text in ((root / 'data/server', 'old '), (stage, 'new ')):
                path = base / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text + name)
        (stage / 'bin').mkdir()
        (stage / 'bin/zone').write_bytes(b'new binary')
        (stage / 'rollout.py').write_text('operator')
        manifest = {'runtime_helper_sha256': op.sha(helper),
            'quest_preimages': {name: op.sha(root / 'data/server' / name) for name in QUESTS},
            'files': {name: op.sha(stage / name) for name in QUESTS + ['bin/zone', 'rollout.py']},
            'base_hashes': {'bin/zone': op.BASE_ZONE}, 'zone_sha256': op.sha(stage / 'bin/zone')}
        (stage / 'manifest.json').write_text(json.dumps(manifest))
        for name, value in {'ROOT': root, 'STAGE': stage, 'HELPER': helper}.items():
            stack.enter_context(patch.object(op, name, value))
        # Ownership changes have no portable Windows implementation; file I/O,
        # hashes, exclusive opens, copy ordering and atomic replace remain real.
        stack.enter_context(patch.object(op.os, 'chown', create=True))
        yield root, stage, manifest


class ManifestAndInstall(unittest.TestCase):
    def test_low_preflight_disk_stops_before_runtime_or_image_mutation(self):
        with files() as (root, stage, manifest), patch.object(op, 'EVIDENCE', stage / 'evidence'), \
                patch.object(op.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=0)), \
                patch.object(op, 'r', Mock()) as runtime:
            with self.assertRaises(AssertionError): op.preflight()
            self.assertEqual(runtime.mock_calls, [])

    def test_exact_seven_files_and_zone_authenticate(self):
        with files() as (root, stage, manifest):
            self.assertEqual(op.manifest(), manifest)

    def test_missing_extra_traversal_helper_and_binary_tampering_fail(self):
        for fault in ('missing', 'extra', 'traversal', 'helper', 'binary', 'zone_binding', 'base'):
            with self.subTest(fault=fault), files() as (root, stage, manifest):
                if fault == 'missing': del manifest['quest_preimages'][QUESTS[-1]]
                elif fault == 'extra': manifest['files']['quests/unauthorized.pl'] = 'anything'
                elif fault == 'traversal': manifest['files']['../escape'] = 'anything'
                elif fault == 'helper': op.HELPER.write_text('drift')
                elif fault == 'binary': (stage / 'bin/zone').write_bytes(b'drift')
                elif fault == 'zone_binding': manifest['zone_sha256'] = 'different'
                else: manifest['base_hashes']['bin/zone'] = 'different'
                (stage / 'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(AssertionError): op.manifest()

    def test_last_preimage_drift_prevents_all_live_writes(self):
        with files() as (root, stage, manifest):
            live = root / 'data/server'
            (live / QUESTS[-1]).write_text('intervening release')
            before = {name: (live / name).read_bytes() for name in QUESTS}
            folder = stage / 'attempt'; folder.mkdir()
            with self.assertRaises(AssertionError): op.install_quests(folder)
            self.assertEqual({name: (live / name).read_bytes() for name in QUESTS}, before)
            self.assertFalse((folder / 'quest-install-started.json').exists())

    def test_partial_install_keeps_all_preimages_and_no_success_receipt(self):
        with files() as (root, stage, manifest):
            folder = stage / 'attempt'; folder.mkdir()
            replace = op.os.replace
            calls = []
            def interrupted(source, target):
                calls.append(target)
                if len(calls) == 3: raise OSError('simulated disk failure')
                replace(source, target)
            with patch.object(op.os, 'replace', side_effect=interrupted):
                with self.assertRaises(OSError): op.install_quests(folder)
            self.assertTrue((folder / 'quest-install-started.json').exists())
            self.assertFalse((folder / 'quest-installed.json').exists())
            for name in QUESTS:
                self.assertEqual(op.sha(folder / 'quest-preimages' / name), manifest['quest_preimages'][name])
            self.assertEqual(op.sha(root / 'data/server' / QUESTS[0]), manifest['files'][QUESTS[0]])
            self.assertEqual(op.sha(root / 'data/server' / QUESTS[2]), manifest['quest_preimages'][QUESTS[2]])
            with self.assertRaises(FileExistsError): op.install_quests(folder)

    def test_success_changes_only_allowlisted_files_and_preserves_preimages(self):
        with files() as (root, stage, manifest):
            unrelated = root / 'data/server/quests/southkarana/Shakrn_Meadowgreen.lua'
            unrelated.parent.mkdir(parents=True); unrelated.write_text('already live Ascended reward')
            folder = stage / 'attempt'; folder.mkdir()
            op.install_quests(folder)
            self.assertEqual(unrelated.read_text(), 'already live Ascended reward')
            self.assertEqual(op.load(folder / 'quest-installed.json'), {n: manifest['files'][n] for n in QUESTS})
            for name in QUESTS:
                self.assertEqual(op.sha(root / 'data/server' / name), manifest['files'][name])
                self.assertEqual(op.sha(folder / 'quest-preimages' / name), manifest['quest_preimages'][name])

    def test_receipts_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / 'receipt.json'
            op.save(receipt, {'original': True})
            with self.assertRaises(FileExistsError): op.save(receipt, {'replacement': True})
            self.assertEqual(op.load(receipt), {'original': True})

    def test_untouched_enforces_other_quests_services_client_content_and_caches(self):
        for fault in (None, 'service', 'other_quest', 'client', 'wiki', 'content', 'cache'):
            with self.subTest(fault=fault), files() as (root, stage, manifest), contextlib.ExitStack() as stack:
                shared = root / 'data/server/shared'; shared.mkdir()
                for name in ('items', 'spells'): (shared / name).write_text('retained ' + name)
                runtime = Mock()
                runtime.compact.side_effect = lambda name: {'id': name}
                old_runtime = {**manifest['quest_preimages'], 'quests/southkarana/Shakrn_Meadowgreen.lua': 'live armor'}
                runtime.runtime.return_value = {**old_runtime, **{n: manifest['files'][n] for n in QUESTS}}
                runtime.public.return_value = {'channel.json': 'game2026102203', 'launcher-channel.json': 'retained'}
                p = {'services': {n: {'id': n} for n in ('db', 'web', 'tunnel')}, 'runtime': old_runtime,
                     'public': copy.deepcopy(runtime.public.return_value), 'wiki_release': 'live-robe-and-armor',
                     'content': {'items': 'retained'}, 'cache_sha256': {n: op.sha(shared / n) for n in ('items', 'spells')}}
                stack.enter_context(patch.object(op, 'r', runtime))
                content = stack.enter_context(patch.object(op, 'content', return_value=p['content']))
                link = stack.enter_context(patch.object(Path, 'readlink', return_value=Path('live-robe-and-armor')))
                if fault == 'service': runtime.compact.side_effect = lambda name: {'id': 'recreated'}
                elif fault == 'other_quest': runtime.runtime.return_value['quests/southkarana/Shakrn_Meadowgreen.lua'] = 'old Normal reward'
                elif fault == 'client': runtime.public.return_value['channel.json'] = 'older client'
                elif fault == 'wiki': link.return_value = Path('older-wiki')
                elif fault == 'content': content.return_value = {'items': 'changed'}
                elif fault == 'cache': (shared / 'items').write_text('changed cache')
                if fault:
                    with self.assertRaises(AssertionError): op.untouched(p, True)
                else:
                    op.untouched(p, True)


class LifecycleFaults(unittest.TestCase):
    def test_success_orders_backup_pair_install_start_and_separate_open(self):
        with lifecycle() as (runtime, data, evidence):
            op.activate()
            self.assertFalse(runtime.opened)
            self.assertEqual(op.load(evidence / 'activation/stopped-state.json'), data)
            self.assertLess(runtime.events.index(('backup',)), runtime.events.index(('quests',)))
            self.assertLess(runtime.events.index(('quests',)), runtime.events.index(('select', 'new')))
            op.open_access()
            self.assertTrue(op.load(evidence / 'activation/deployed.json')['gateway_open'])
            self.assertFalse(op.load(evidence / 'activation/deployed.json')['database_restored'])

    def test_activation_faults_hold_both_services_and_never_restore_database(self):
        for fault in ('stop', 'start', 'backup', 'install', 'state_before', 'state_after', 'market', 'health', 'disk'):
            with self.subTest(fault=fault), lifecycle() as (runtime, data, evidence), contextlib.ExitStack() as stack:
                if fault in ('stop', 'start'):
                    fired = [False]
                    def fail(args):
                        if args[0] == ('stop' if fault == 'stop' else 'up') and not fired[0]:
                            fired[0] = True; raise RuntimeError(fault)
                    runtime.fail = fail
                elif fault == 'backup': stack.enter_context(patch.object(runtime, 'database_backup', side_effect=RuntimeError(fault)))
                elif fault == 'install': stack.enter_context(patch.object(op, 'install_quests', side_effect=OSError(fault)))
                elif fault.startswith('state_'):
                    values = [data, {'changed': True}] if fault == 'state_before' else [data, data, {'changed': True}]
                    stack.enter_context(patch.object(op, 'saved_state', side_effect=values))
                elif fault == 'disk': stack.enter_context(patch.object(op.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=0)))
                else: stack.enter_context(patch.object(op, 'verify_market' if fault == 'market' else 'health', side_effect=RuntimeError(fault)))
                with self.assertRaises((RuntimeError, AssertionError, OSError)): op.activate()
                self.assertFalse(runtime.running_services['game']); self.assertFalse(runtime.running_services['gateway'])
                self.assertFalse(runtime.opened)
                receipts = list((evidence / 'activation').glob('held-*.json'))
                self.assertEqual(len(receipts), 1)
                self.assertFalse(op.load(receipts[0])['database_restored'])
                self.assertFalse((evidence / 'activation/verified-closed.json').exists())
                with self.assertRaises(AssertionError): op.activate()

    def test_drift_before_activation_does_not_stop_or_install(self):
        for fault in ('manifest', 'runtime', 'image'):
            with self.subTest(fault=fault), lifecycle() as (runtime, data, evidence), contextlib.ExitStack() as stack:
                if fault == 'manifest': stack.enter_context(patch.object(op, 'sha', return_value='changed'))
                elif fault == 'runtime': runtime.image = 'newer-release'
                else: stack.enter_context(patch.object(runtime, 'image_hashes', return_value={'bin/zone': 'wrong'}))
                with self.assertRaises(AssertionError): op.activate()
                self.assertEqual(runtime.events, [])

    def test_open_refuses_player_timer_or_cache_drift(self):
        for group, name in (('player', 'inventory'), ('player', 'zone_state_spawns'), ('custom', 'timers')):
            with self.subTest(table=name), lifecycle() as (runtime, data, evidence):
                op.activate(); data[group][name] = 'changed'
                with self.assertRaises(AssertionError): op.open_access()
                self.assertFalse(runtime.opened)
                self.assertFalse(runtime.running_services['game'])

    def test_lost_gateway_acknowledgment_closes_both_and_cannot_replay(self):
        with lifecycle() as (runtime, data, evidence):
            op.activate()
            def fail(args):
                if args[0] == 'up' and args[-1] == 'gateway': raise RuntimeError('lost acknowledgment')
            runtime.fail = fail
            with self.assertRaises(RuntimeError): op.open_access()
            self.assertTrue(runtime.opened)
            self.assertFalse(any(runtime.running_services.values()))
            self.assertFalse((evidence / 'activation/deployed.json').exists())
            with self.assertRaises(AssertionError): op.open_access()

    def test_stop_failure_still_attempts_other_service_and_records_uncertainty(self):
        with lifecycle() as (runtime, data, evidence):
            runtime.compose = Mock(side_effect=RuntimeError('daemon unavailable'))
            folder = evidence / 'held'; folder.mkdir()
            op.hold(folder)
            self.assertEqual(runtime.compose.call_count, 2)
            receipt = op.load(next(folder.glob('held-*.json')))
            self.assertEqual(receipt['running'], {'game': True, 'gateway': True})
            self.assertEqual(len(receipt['errors']), 2)


class BuildIsolation(unittest.TestCase):
    def test_build_uses_authenticated_local_base_and_no_network(self):
        runtime = Mock(); runtime.out.side_effect = ['sha256:base', 'sha256:base', 'sha256:new']
        with tempfile.TemporaryDirectory() as directory, patch.object(op, 'STAGE', Path(directory)), patch.object(op, 'r', runtime):
            self.assertEqual(op.build_image({'base_image_id': 'sha256:base'}), 'sha256:new')
            args = runtime.call.call_args.args
            self.assertIn('--pull=false', args)
            self.assertEqual(args[args.index('--network') + 1], 'none')
            self.assertIn('COPY bin/zone /opt/nightcap/bin/zone', (Path(directory) / 'Dockerfile').read_text())

    def test_base_tag_drift_prevents_build(self):
        runtime = Mock(); runtime.out.return_value = 'sha256:other'
        with tempfile.TemporaryDirectory() as directory, patch.object(op, 'STAGE', Path(directory)), patch.object(op, 'r', runtime):
            with self.assertRaises(AssertionError): op.build_image({'base_image_id': 'sha256:base'})
            self.assertEqual(runtime.call.call_count, 1)


if __name__ == '__main__':
    unittest.main()

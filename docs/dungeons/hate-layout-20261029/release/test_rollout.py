"""Offline rollout fault injection; all runtime/SQL/image operations are fakes.

Receipt files, exclusive opens and manifest hashes are real. Windows substitutes
ownership and directory fsync; Linux exercises the real POSIX operations.
"""
import contextlib
import copy
import importlib.util
import json
import os
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('hate_rollout', Path(__file__).with_name('rollout.py'))
op = importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)


def receipt(path, value):
    with path.open('x') as stream:
        json.dump(value, stream)


class Runtime:
    def __init__(self, hashes):
        self.events = []
        self.image = 'base'
        self.hashes = hashes
        self.running_services = {'game': True, 'gateway': True}
        self.exit_code = 0
        self.opened = False
        self.fail = None
        self.STAGE = None

    def compact(self, name):
        return {'image_id': self.image if name == 'game' else name,
                'running': self.running_services.get(name, True),
                'health': 'healthy', 'oom_killed': False, 'restarts': 0}

    def state(self, name):
        return {'Image': self.image, 'State': {'Running': self.running_services[name],
                'OOMKilled': False, 'ExitCode': self.exit_code if name == 'game' else 0}}

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
        return {**self.hashes, **({'bin/zone':'new-zone','bin/world':'new-world','bin/shared_memory':'new-loader'} if image!='base' else {'bin/zone':'old-zone'})}

    def database_backup(self):
        assert not any(self.running_services.values()), 'backup needs stopped writers and access'
        self.events.append(('backup',))
        return {'gzip_integrity': 'passed', 'fresh': len(self.events)}

    def running(self, image, binaries, restarts=None):
        assert self.running_services['game'] and self.image == image
        self.events.append(('running', image))
        return {'image_id': image, 'started_at': '2026-10-24T12:00:00Z'}

    def runtime(self):
        return self.quest_tree if hasattr(self, 'quest_tree') else {'quests/current.pl': 'retained'}

    def closed_ports(self):
        pass


@contextlib.contextmanager
def lifecycle(preflight=True):
    with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
        stage = Path(directory)
        (stage / 'bin').mkdir()
        (stage / 'bin/zone').write_bytes(b'new-zone')
        (stage / 'bin/world').write_bytes(b'new-world')
        (stage / 'bin/shared_memory').write_bytes(b'new-loader')
        evidence = stage / 'evidence'
        hashes = {'bin/' + n: n for n in op.NAMES}
        hashes['bin/zone'] = 'old-zone'
        manifest = {'base_image_id': 'base', 'base_hashes': hashes,
                    'zone_sha256': 'new-zone', 'candidate_hashes':{'bin/zone':'new-zone','bin/world':'new-world','bin/shared_memory':'new-loader'}, 'client_channel_sha256': 'digest', 'client_channel_new_sha256': 'new-client', 'files': {'quests/'+n: 'new-'+n for n in op.QUESTS}}
        runtime = Runtime(hashes)
        runtime.quest_tree = {'quests/'+n: 'old-'+n for n in op.QUESTS}
        runtime.quest_tree['plugins/unrelated.pl'] = 'preserved'
        manifest['runtime_preimage'] = dict(runtime.quest_tree)
        data = {'character_data': 'current-earned-level', 'inventory': 'current-items',
                'character_disciplines': 'current-earned-disciplines', 'timers': 'current-deadlines'}
        base = types.SimpleNamespace(PUBLIC={'items', 'rule_values'}, EVIDENCE=evidence,
                health=Mock(), saved_state=Mock(side_effect=lambda: copy.deepcopy(data)))

        def boot_state(stopped):
            receipt(base.EVIDENCE / 'expected-boot-state.json', stopped)
            return copy.deepcopy(stopped)

        base.boot_state = Mock(side_effect=boot_state)
        startup = types.SimpleNamespace(startup_guards=Mock())
        market = types.SimpleNamespace(market=Mock(return_value=['before']),
                                      verify_market=Mock(return_value={'rotation': 'once'}))
        for name, value in {'ROOT': stage, 'STAGE': stage, 'EVIDENCE': evidence,
                            'r': runtime, 'base': base, 'startup': startup, 'market_ops': market}.items():
            stack.enter_context(patch.object(op, name, value, create=True))
        stack.enter_context(patch.object(op, 'manifest', return_value=manifest))
        stack.enter_context(patch.object(op, 'sha', return_value='digest'))
        if os.name == 'nt':
            stack.enter_context(patch.object(op, 'save', side_effect=receipt))
        public = {'channels': {'channel.json': 'digest', 'other.json': 'retained'}, 'wiki': 'current'}
        stack.enter_context(patch.object(op, 'publication', side_effect=lambda: copy.deepcopy(public)))
        stack.enter_context(patch.object(op, 'check_quest_preimages'))
        def install(folder):
            assert not any(runtime.running_services.values())
            runtime.events.append(('install-quests',))
            runtime.quest_tree.update(manifest['files'])
        stack.enter_context(patch.object(op, 'install_quests', side_effect=install))
        stack.enter_context(patch.object(op, 'caches', return_value={'items': 'current', 'spells': 'current'}))
        stack.enter_context(patch.object(op, 'content', return_value={'items': 'current', 'rules': 'current'}))
        stack.enter_context(patch.object(op, 'contract', return_value={'required': 3}))
        stack.enter_context(patch.object(op, 'public_preflight', return_value=31))
        def install_content(folder):
            assert not any(runtime.running_services.values())
            assert (folder/'backup.json').exists()
            runtime.events.append(('install-content',))
            receipt(folder/'content-install-started.json', {'forward_sha256':'digest'})
            receipt(folder/'content-installed.json', {'checks':{'required':3},'player_restore':False})
        stack.enter_context(patch.object(op, 'install_content', side_effect=install_content))
        stack.enter_context(patch.object(op.time, 'sleep'))
        stack.enter_context(patch.object(op.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=2**30)))
        plan = {'manifest_sha256': 'digest', 'image': 'candidate',
                'services': {s: runtime.compact(s) for s in ('game', 'gateway', 'db', 'web', 'tunnel')},
                'runtime': runtime.runtime(), 'publication': op.publication(),
                'caches': op.caches(), 'content': op.content()}
        if preflight:
            evidence.mkdir()
            receipt(evidence / 'preflight.json', plan)
        yield types.SimpleNamespace(runtime=runtime, base=base, startup=startup, market=market,
                                    data=data, evidence=evidence, manifest=manifest, plan=plan, public=public)


@contextlib.contextmanager
def manifest_files():
    with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
        stage = Path(directory) / 'stage'
        stage.mkdir()
        (stage / 'bin').mkdir()
        names = ('bin/zone', 'bin/world', 'bin/shared_memory', 'rollout.py') + tuple(op.PAYLOAD) + tuple('quests/'+n for n in op.QUESTS)
        for name in names:
            (stage / name).parent.mkdir(parents=True, exist_ok=True)
            (stage / name).write_text('trusted ' + name)
        helpers = {}
        for name in ('runtime', 'state', 'startup', 'market'):
            path = Path(directory) / (name + '.py')
            path.write_text('trusted ' + name)
            helpers[name] = {'path': str(path.resolve()), 'sha256': op.sha(path)}
        manifest = {'files': {n: op.sha(stage / n) for n in names},
                    'quest_preimages': {n: 'old' for n in op.QUESTS},
                    'owner_live_qa_authorized': True, 'client_channel_sha256': 'a'*64, 'client_channel_new_sha256': 'b'*64,
                    'contract': {'path':str((stage/'runtime-contract.json').resolve()),'sha256':op.sha(stage/'runtime-contract.json')}, 'helpers': helpers,
                    'zone_sha256': op.sha(stage / 'bin/zone'), 'candidate_hashes':{n:op.sha(stage/n) for n in ('bin/zone','bin/world','bin/shared_memory')}, 'base_hashes': {'bin/zone': 'old'}}
        (stage / 'manifest.json').write_text(json.dumps(manifest))
        stack.enter_context(patch.object(op, 'STAGE', stage))
        yield stage, manifest


class ManifestTests(unittest.TestCase):
    def test_contract_cannot_point_to_a_different_authenticated_file(self):
        with manifest_files() as (stage,manifest):
            other=stage.parent/'old-contract.json'
            other.write_bytes((stage/'runtime-contract.json').read_bytes())
            manifest['contract']={'path':str(other.resolve()),'sha256':op.sha(other)}
            (stage/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaises(AssertionError):op.manifest()

    def test_exact_manifest_authenticates(self):
        with manifest_files() as (stage, manifest):
            self.assertEqual(op.manifest(), manifest)

    def test_manifest_rejects_tampering_and_scope_changes(self):
        for fault in ('missing', 'extra', 'traversal', 'helper_missing', 'helper_extra',
                      'helper_hash', 'relative_helper', 'contract_hash', 'zone', 'operator',
                      'zone_binding', 'unchanged_zone', 'quest_missing', 'quest_extra',
                      'quest_tampered', 'preimage_missing', 'owner_unauthorized',
                      'same_client', 'invalid_client_hash'):
            with self.subTest(fault=fault), manifest_files() as (stage, manifest):
                if fault == 'missing': del manifest['files']['rollout.py']
                elif fault == 'extra': manifest['files']['extra.sql'] = 'hash'
                elif fault == 'traversal': manifest['files']['../escape'] = 'hash'
                elif fault == 'helper_missing': del manifest['helpers']['state']
                elif fault == 'helper_extra': manifest['helpers']['extra'] = manifest['helpers']['state']
                elif fault == 'helper_hash': Path(manifest['helpers']['state']['path']).write_text('drift')
                elif fault == 'relative_helper': manifest['helpers']['state']['path'] = 'state.py'
                elif fault == 'contract_hash': Path(manifest['contract']['path']).write_text('drift')
                elif fault == 'zone': (stage / 'bin/zone').write_text('drift')
                elif fault == 'operator': (stage / 'rollout.py').write_text('drift')
                elif fault == 'zone_binding': manifest['zone_sha256'] = 'wrong'
                elif fault == 'quest_missing': del manifest['files']['quests/'+op.QUESTS[0]]
                elif fault == 'quest_extra': manifest['files']['quests/extra.pl'] = 'hash'
                elif fault == 'quest_tampered': (stage/'quests'/op.QUESTS[0]).write_text('drift')
                elif fault == 'preimage_missing': del manifest['quest_preimages'][op.QUESTS[0]]
                elif fault == 'owner_unauthorized': manifest['owner_live_qa_authorized'] = False
                elif fault == 'same_client': manifest['client_channel_new_sha256'] = manifest['client_channel_sha256']
                elif fault == 'invalid_client_hash': manifest['client_channel_new_sha256'] = 'short'
                else: manifest['base_hashes']['bin/zone'] = manifest['zone_sha256']
                (stage / 'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(AssertionError): op.manifest()

    def test_binaries_select_exact_three_file_pair(self):
        with lifecycle() as f:
            old = op.binaries(True)
            new = op.binaries()
            self.assertEqual({n for n in old if old[n] != new[n]}, {'zone','world','shared_memory'})
            self.assertEqual(old['zone'], 'old-zone')
            self.assertEqual(new['zone'], 'new-zone')


class PreflightTests(unittest.TestCase):
    def test_preflight_success_does_not_mutate_gameplay(self):
        with lifecycle(False) as f, patch.object(op, 'build_image', return_value='candidate'):
            op.preflight()
            self.assertTrue((f.evidence / 'preflight.json').exists())
            self.assertFalse(any(event[0] in ('stop', 'up', 'select', 'backup') for event in f.runtime.events))

    def test_preflight_faults_never_stop_select_backup_or_open(self):
        for fault in ('health', 'image', 'hash', 'contract', 'disk', 'build', 'post_build_drift'):
            with self.subTest(fault=fault), lifecycle(False) as f, contextlib.ExitStack() as stack:
                build = stack.enter_context(patch.object(op, 'build_image', return_value='candidate'))
                if fault == 'health': f.base.health.side_effect = RuntimeError(fault)
                elif fault == 'image': f.runtime.image = 'unexpected'
                elif fault == 'hash': stack.enter_context(patch.object(f.runtime, 'image_hashes', return_value={}))
                elif fault == 'contract': stack.enter_context(patch.object(op, 'contract', side_effect=AssertionError(fault)))
                elif fault == 'disk': stack.enter_context(patch.object(op.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=0)))
                elif fault == 'build': build.side_effect = RuntimeError(fault)
                else: build.side_effect = lambda m: setattr(f.runtime, 'image', 'unexpected') or 'candidate'
                with self.assertRaises((AssertionError, RuntimeError)): op.preflight()
                self.assertFalse(any(event[0] in ('stop', 'up', 'select', 'backup') for event in f.runtime.events))
                self.assertFalse((f.evidence / 'preflight.json').exists())

    def test_unchanged_checks_every_preservation_boundary(self):
        for fault in ('service', 'runtime', 'publication', 'caches', 'content'):
            with self.subTest(fault=fault), lifecycle() as f, contextlib.ExitStack() as stack:
                if fault == 'service': stack.enter_context(patch.object(f.runtime, 'compact', return_value={}))
                elif fault == 'runtime': stack.enter_context(patch.object(f.runtime, 'runtime', return_value={}))
                else: stack.enter_context(patch.object(op, fault, return_value={}))
                with self.assertRaises(AssertionError): op.transition()
                self.assertEqual(f.runtime.events, [])
                self.assertFalse((f.evidence / 'activation').exists())


class LifecycleTests(unittest.TestCase):
    def assert_held(self, f, recovery=False):
        folder = f.evidence / ('recovery' if recovery else 'activation')
        self.assertFalse(any(f.runtime.running_services.values()))
        self.assertFalse((folder / 'verified-closed.json').exists())
        receipts = list(folder.glob('held-*.json'))
        self.assertEqual(len(receipts), 1)
        self.assertFalse(op.read(receipts[0])['database_restored'])
        self.assertFalse((folder / 'deployed.json').exists())

    def test_forward_then_separate_verified_open(self):
        with lifecycle() as f:
            op.transition()
            folder = f.evidence / 'activation'
            self.assertFalse(f.runtime.opened)
            self.assertFalse(f.runtime.running_services['gateway'])
            self.assertEqual(op.read(folder / 'stopped-state.json'), f.data)
            events = f.runtime.events
            self.assertLess(events.index(('stop', '-t', '90', 'game')), events.index(('backup',)))
            self.assertLess(events.index(('backup',)), events.index(('select', 'candidate')))
            self.assertLess(events.index(('backup',)), events.index(('install-content',)))
            self.assertLess(events.index(('install-content',)), events.index(('install-quests',)))
            self.assertLess(events.index(('select', 'candidate')), events.index(('up', '-d', '--wait', '--wait-timeout', '240', 'game')))
            f.public['channels']['channel.json'] = 'new-client'
            op.open_access()
            deployed = op.read(folder / 'deployed.json')
            self.assertTrue(deployed['gateway_open'])
            self.assertFalse(deployed['database_restored'])
            self.assertFalse(deployed['owner_gameplay_accepted'])

    def test_failed_backup_never_selects_an_image(self):
        with lifecycle() as f, patch.object(f.runtime, 'database_backup', side_effect=RuntimeError('backup')):
            with self.assertRaises(RuntimeError): op.transition()
            self.assert_held(f)
            self.assertFalse(any(event[0] == 'select' for event in f.runtime.events))

    def test_distinct_expected_boot_state_and_market_rotation_are_verified(self):
        with lifecycle() as f:
            f.data['zone_state_spawns'] = 'saved-before-boot'
            before = copy.deepcopy(f.data)
            expected = {**before, 'zone_state_spawns': 'consumed-by-supported-startup'}
            def expected_boot(stopped):
                self.assertEqual(stopped, before)
                receipt(f.base.EVIDENCE / 'expected-boot-state.json', expected)
                return expected
            f.base.boot_state.side_effect = expected_boot
            def start(args):
                if args[0] == 'up' and args[-1] == 'game':
                    f.data.update(expected)
            f.runtime.fail = start
            f.market.market.return_value = ['old-stock']
            f.market.verify_market.return_value = {'old-stock': 'rotated-once'}
            op.transition()
            folder = f.evidence / 'activation'
            self.assertEqual(op.read(folder / 'stopped-state.json'), before)
            self.assertEqual(op.read(folder / 'expected-boot-state.json'), expected)
            f.market.verify_market.assert_called_with(['old-stock'], '2026-10-24T12:00:00Z')
            self.assertEqual(op.read(folder / 'verified-closed.json')['market'], {'old-stock': 'rotated-once'})
            f.public['channels']['channel.json'] = 'new-client'
            op.open_access()
            self.assertTrue(f.runtime.running_services['gateway'])

    def test_stop_exit_failure_holds_without_snapshot_or_selection(self):
        with lifecycle() as f:
            f.runtime.exit_code = 1
            with self.assertRaises(AssertionError): op.transition()
            self.assert_held(f)
            f.base.saved_state.assert_not_called()
            self.assertFalse(any(event[0] in ('backup', 'select') for event in f.runtime.events))

    def test_state_drift_before_selection_or_after_start_holds(self):
        for phase in ('backup', 'started'):
            with self.subTest(phase=phase), lifecycle() as f:
                f.base.saved_state.side_effect = [f.data, {'changed': True}] if phase == 'backup' else [f.data, f.data, f.data, {'changed': True}]
                with self.assertRaises(AssertionError): op.transition()
                self.assert_held(f)
                self.assertEqual(any(e[0] == 'select' for e in f.runtime.events), phase == 'started')
                self.assertFalse(f.runtime.opened)

    def test_post_start_failures_keep_gateway_closed(self):
        for fault in ('start', 'runtime', 'health', 'market', 'contract', 'content'):
            with self.subTest(fault=fault), lifecycle() as f, contextlib.ExitStack() as stack:
                if fault == 'start':
                    f.runtime.fail = lambda args: (_ for _ in ()).throw(RuntimeError('start')) if args[0] == 'up' else None
                elif fault == 'runtime': stack.enter_context(patch.object(f.runtime, 'running', side_effect=RuntimeError(fault)))
                elif fault == 'health': f.base.health.side_effect = RuntimeError(fault)
                elif fault == 'market': f.market.verify_market.side_effect = RuntimeError(fault)
                elif fault == 'contract': stack.enter_context(patch.object(op, 'contract', side_effect=AssertionError(fault)))
                else:
                    original = op.content.return_value
                    stack.enter_context(patch.object(op, 'content', side_effect=lambda: {} if f.runtime.image == 'candidate' else original))
                with self.assertRaises((RuntimeError, AssertionError)): op.transition()
                self.assert_held(f)
                self.assertFalse(f.runtime.opened)

    def test_existing_attempt_cannot_replay(self):
        with lifecycle() as f:
            (f.evidence / 'activation').mkdir()
            with self.assertRaises(AssertionError): op.transition()
            self.assertEqual(f.runtime.events, [])

    def test_open_requires_verified_receipt(self):
        with lifecycle() as f:
            with self.assertRaises(FileNotFoundError): op.open_access()
            self.assertFalse(f.runtime.opened)
            self.assertEqual(f.runtime.events, [])

    def test_pre_open_drift_never_opens_access(self):
        for fault in ('state', 'runtime', 'market', 'content'):
            with self.subTest(fault=fault), lifecycle() as f, contextlib.ExitStack() as stack:
                op.transition()
                if fault == 'state': f.data['timers'] = 'new-earned-deadline'
                elif fault == 'runtime': f.runtime.image = 'unexpected'
                elif fault == 'market': f.market.verify_market.return_value = {'rotation': 'changed'}
                else: stack.enter_context(patch.object(op, 'content', return_value={}))
                with self.assertRaises(AssertionError): op.open_access()
                self.assertFalse(f.runtime.opened)
                self.assertFalse(any(f.runtime.running_services.values()))
                self.assertFalse((f.evidence / 'activation/opening.json').exists())

    def test_uncertain_open_is_closed_and_cannot_replay(self):
        with lifecycle() as f:
            op.transition()
            f.public['channels']['channel.json'] = 'new-client'
            def fail(args):
                if args[0] == 'up' and args[-1] == 'gateway': raise RuntimeError('lost acknowledgment')
            f.runtime.fail = fail
            with self.assertRaises(RuntimeError): op.open_access()
            self.assertTrue(f.runtime.opened)
            self.assertFalse(any(f.runtime.running_services.values()))
            self.assertFalse((f.evidence / 'activation/deployed.json').exists())
            with self.assertRaises(AssertionError): op.open_access()

    def test_old_binary_recovery_is_rejected_before_any_operation(self):
        with lifecycle() as f:
            with self.assertRaisesRegex(AssertionError,"Hate186-capable"):op.transition(True)
            with self.assertRaisesRegex(AssertionError,"Hate186-capable"):op.open_access(True)
            self.assertEqual(f.runtime.events,[])

    def test_hold_attempts_both_services_when_daemon_fails(self):
        with lifecycle() as f:
            folder = f.evidence / 'activation'
            folder.mkdir()
            f.runtime.compose = Mock(side_effect=RuntimeError('daemon'))
            op.hold(folder)
            self.assertEqual(f.runtime.compose.call_count, 2)
            held = op.read(next(folder.glob('held-*.json')))
            self.assertEqual(len(held['errors']), 2)
            self.assertFalse(held['database_restored'])


class PairingTests(unittest.TestCase):
    def test_open_requires_exact_new_client_and_preserves_other_publications(self):
        for fault in ('old', 'wrong', 'other_channel', 'wiki'):
            with self.subTest(fault=fault), lifecycle() as f:
                op.transition()
                f.public['channels']['channel.json'] = 'new-client'
                if fault == 'old': f.public['channels']['channel.json'] = 'digest'
                elif fault == 'wrong': f.public['channels']['channel.json'] = 'unapproved-client'
                elif fault == 'other_channel': f.public['channels']['other.json'] = 'changed'
                else: f.public['wiki'] = 'changed'
                with self.assertRaisesRegex(AssertionError, 'Publication drift'): op.open_access()
                self.assertFalse(f.runtime.opened)
                self.assertFalse(any(f.runtime.running_services.values()))

    def test_every_quest_and_unrelated_plugin_are_checked_before_open(self):
        for name in (*op.QUESTS, 'unrelated.pl'):
            with self.subTest(name=name), lifecycle() as f:
                op.transition()
                f.public['channels']['channel.json'] = 'new-client'
                key = 'plugins/unrelated.pl' if name == 'unrelated.pl' else 'quests/'+name
                f.runtime.quest_tree[key] = 'drift'
                with self.assertRaisesRegex(AssertionError, 'Quest/plugin drift'): op.open_access()
                self.assertFalse(f.runtime.opened)
                self.assertFalse(any(f.runtime.running_services.values()))

    def test_partial_quest_install_holds_without_boot_or_replay(self):
        with lifecycle() as f:
            before = copy.deepcopy(f.data)
            def partial(folder):
                f.runtime.quest_tree['quests/'+op.QUESTS[0]] = 'new-first'
                raise OSError('fourth replacement failed')
            op.install_quests.side_effect = partial
            with self.assertRaises(OSError): op.transition()
            self.assertFalse(any(f.runtime.running_services.values()))
            self.assertFalse(any(e[0] in ('select', 'up') for e in f.runtime.events))
            self.assertEqual(f.data, before)
            self.assertTrue(list((f.evidence/'activation').glob('held-*.json')))
            with self.assertRaisesRegex(AssertionError, 'Never replay'): op.transition()

    def test_full_runtime_preimage_drift_is_rejected_before_build(self):
        with lifecycle(False) as f, patch.object(op, 'build_image') as build:
            f.runtime.quest_tree['plugins/unrelated.pl'] = 'drift'
            with self.assertRaisesRegex(AssertionError, 'Captured script tree drift'): op.preflight()
            build.assert_not_called()
            self.assertFalse(f.evidence.exists())


@contextlib.contextmanager
def quest_files():
    """Real copy/hash/replace; POSIX ownership and directory fsync are mocked on Windows."""
    with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
        root = Path(directory).resolve()
        stage = root/'stage'; stage.mkdir()
        live = root/'data/server/quests'
        evidence = stage/'evidence'; evidence.mkdir()
        folder = evidence/'activation'; folder.mkdir()
        old = {}; new = {}
        for name in (*op.QUESTS, 'unrelated.pl'):
            path = live/name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('old '+name).encode())
            old['quests/'+name] = op.sha(path)
            if name in op.QUESTS:
                candidate = stage/'quests'/name
                candidate.parent.mkdir(parents=True, exist_ok=True)
                candidate.write_bytes(('new '+name).encode())
                new['quests/'+name] = op.sha(candidate)
        receipt(evidence/'preflight.json', {'runtime': old})
        manifest = {'files': new, 'quest_preimages': {n:old['quests/'+n] for n in op.QUESTS}}
        runtime = types.SimpleNamespace(
            state=Mock(return_value={'State': {'Running': False}}),
            runtime=lambda: {'quests/'+str(p.relative_to(live)).replace('\\','/'):op.sha(p)
                             for p in live.rglob('*') if p.is_file()})
        for name, value in {'ROOT':root, 'STAGE':stage, 'EVIDENCE':evidence, 'r':runtime}.items():
            stack.enter_context(patch.object(op, name, value, create=True))
        stack.enter_context(patch.object(op, 'manifest', return_value=manifest))
        if os.name == 'nt':
            stack.enter_context(patch.object(op, 'save', side_effect=receipt))
            stack.enter_context(patch.object(op.os, 'chown', create=True))
            stack.enter_context(patch.object(op.os, 'O_DIRECTORY', 0, create=True))
            stack.enter_context(patch.object(op.os, 'open', return_value=123456))
            stack.enter_context(patch.object(op.os, 'close'))
            stack.enter_context(patch.object(op.os, 'fsync'))
        yield types.SimpleNamespace(root=root, stage=stage, live=live, folder=folder,
                                    old=old, new=new, runtime=runtime, manifest=manifest)


class QuestInstallationTests(unittest.TestCase):
    def test_exact_quest_afterimages_original_backups_and_unrelated_preservation(self):
        with quest_files() as f:
            op.install_quests(f.folder)
            self.assertEqual(f.runtime.runtime(), {**f.old, **f.new})
            backup = f.folder/'quest-backup'
            for name in op.QUESTS:
                self.assertEqual(op.sha(backup/name), f.old['quests/'+name])
                saved = op.read(backup/(name.replace('/','_')+'.receipt.json'))
                self.assertEqual(saved['before'], f.old['quests/'+name])
                self.assertEqual(saved['after'], f.new['quests/'+name])
                self.assertEqual(saved['mode'], (f.live/name).stat().st_mode & 0o777)
            self.assertEqual(len(list(backup.rglob('*.receipt.json'))), len(op.QUESTS))
            self.assertFalse(list(f.live.rglob('*pending')))

    def test_each_preimage_drift_rejects_before_any_install(self):
        for name in op.QUESTS:
            with self.subTest(name=name), quest_files() as f:
                (f.live/name).write_bytes(b'unexpected live edit')
                before = f.runtime.runtime()
                with self.assertRaises(AssertionError): op.install_quests(f.folder)
                self.assertEqual(f.runtime.runtime(), before)
                self.assertFalse((f.folder/'quest-backup').exists())

    def test_candidate_drift_never_replaces_target(self):
        with quest_files() as f:
            name = op.QUESTS[0]
            (f.stage/'quests'/name).write_bytes(b'corrupt staged content')
            with self.assertRaises(AssertionError): op.install_quests(f.folder)
            self.assertEqual(f.runtime.runtime()['quests/'+name], f.old['quests/'+name])
            self.assertEqual(op.sha(f.folder/'quest-backup'/name), f.old['quests/'+name])

    def test_failed_replace_leaves_only_complete_old_or_new_files(self):
        with quest_files() as f:
            replace = op.os.replace
            calls = []
            def fault(source, target):
                calls.append(str(target))
                if len(calls) == len(op.QUESTS): raise OSError('injected disk failure')
                replace(source, target)
            with patch.object(op.os, 'replace', side_effect=fault):
                with self.assertRaises(OSError): op.install_quests(f.folder)
            for index, name in enumerate(op.QUESTS):
                self.assertEqual(op.sha(f.live/name), (f.new if index < len(op.QUESTS)-1 else f.old)['quests/'+name])
            self.assertEqual(op.sha(f.folder/'quest-backup'/op.QUESTS[-1]), f.old['quests/'+op.QUESTS[-1]])

    def test_install_requires_both_services_stopped(self):
        with quest_files() as f:
            f.runtime.state.return_value = {'State': {'Running': True}}
            with self.assertRaises(AssertionError): op.install_quests(f.folder)
            self.assertEqual(f.runtime.runtime(), f.old)


class ContractTests(unittest.TestCase):
    def test_preinstall_contract_skips_only_exact_hate_layout_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'contract.json'
            checks = [{'sql':'SELECT '+str(i), 'expected':str(i), 'label':label}
                      for i,label in enumerate(('classic/check','hate-layout/new','hate-keeper/existing'),1)]
            path.write_text(json.dumps({'required':checks}))
            with patch.object(op,'manifest',return_value={'contract':{'path':str(path)}}), patch.object(op,'sql',create=True) as sql:
                sql.return_value='1\n3\n'
                self.assertEqual(op.contract(False),{'required':2})
                self.assertNotIn('SELECT 2',sql.call_args.args[0])
                sql.return_value='1\n2\n3\n'
                self.assertEqual(op.contract(),{'required':3})
                self.assertIn('SELECT 2',sql.call_args.args[0])

    def test_contract_rejects_wrong_values_and_row_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'contract.json'
            path.write_text(json.dumps({'required': [{'sql': 'SELECT 1', 'expected': '1', 'label': 'invariant'}]}))
            with patch.object(op, 'manifest', return_value={'contract': {'path': str(path)}}), patch.object(op, 'sql', create=True) as sql:
                for result in ('0', '', '1\n1'):
                    sql.return_value = result
                    with self.assertRaises(AssertionError): op.contract()
                sql.return_value = '1\n'
                self.assertEqual(op.contract(), {'required': 1})


class ContentInstallationTests(unittest.TestCase):
    @contextlib.contextmanager
    def installation(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            stage=Path(directory);folder=stage/'activation';folder.mkdir()
            (stage/'forward.sql').write_text('REVIEWED FORWARD SQL')
            (stage/'preflight-checks.json').write_text(json.dumps([{'sql':'SELECT PUBLIC','expected':'1'}]))
            runtime=types.SimpleNamespace(state=Mock(return_value={'State':{'Running':False}}))
            calls=[];occupied=False
            def execute(statement):
                calls.append(statement)
                if statement=='REVIEWED FORWARD SQL':
                    self.assertTrue((folder/'content-install-started.json').is_file())
                    return ''
                if statement.startswith('SELECT COUNT'):return '0\n'
                if statement.startswith('SHOW CREATE'):return 'schema\n'
                if statement.startswith('SELECT PUBLIC'):return '1\n'
                raise AssertionError('Unexpected SQL: '+statement)
            stack.enter_context(patch.object(op,'STAGE',stage))
            stack.enter_context(patch.object(op,'r',runtime,create=True))
            stack.enter_context(patch.object(op,'manifest',return_value={}))
            sql=stack.enter_context(patch.object(op,'sql',side_effect=execute,create=True))
            contract=stack.enter_context(patch.object(op,'contract',return_value={'required':650}))
            if os.name=='nt':stack.enter_context(patch.object(op,'save',side_effect=receipt))
            yield types.SimpleNamespace(stage=stage,folder=folder,calls=calls,sql=sql,execute=execute,runtime=runtime,contract=contract)

    def test_content_exact_scope_receipts_and_no_replay(self):
        with self.installation() as f:
            op.install_content(f.folder)
            captured=op.read(f.folder/'content-preimage.json')
            self.assertEqual({k:v['scope'] for k,v in captured.items()},op.OWNED)
            self.assertEqual(f.calls.count('REVIEWED FORWARD SQL'),1)
            self.assertEqual(op.read(f.folder/'content-installed.json'),{'checks':{'required':650},'player_restore':False})
            with self.assertRaises(FileExistsError):op.install_content(f.folder)
            self.assertEqual(f.calls.count('REVIEWED FORWARD SQL'),1)

    def test_preinstall_drift_blocks_forward_sql(self):
        for fault in ('running','manifest','public','occupied'):
            with self.subTest(fault=fault), self.installation() as f, contextlib.ExitStack() as stack:
                if fault=='running':f.runtime.state.return_value={'State':{'Running':True}}
                elif fault=='manifest':stack.enter_context(patch.object(op,'manifest',side_effect=AssertionError('manifest')))
                elif fault=='public':stack.enter_context(patch.object(op,'public_preflight',side_effect=AssertionError('public')))
                else:f.sql.side_effect=lambda statement:'1\n' if statement.startswith('SELECT COUNT') else f.execute(statement)
                with self.assertRaises(AssertionError):op.install_content(f.folder)
                self.assertNotIn('REVIEWED FORWARD SQL',f.calls)
                self.assertFalse((f.folder/'content-install-started.json').exists())

    def test_uncertain_sql_retains_started_receipt_and_rejects_replay(self):
        with self.installation() as f:
            def uncertain(statement):
                result=f.execute(statement)
                if statement=='REVIEWED FORWARD SQL':raise RuntimeError('lost SQL acknowledgment')
                return result
            f.sql.side_effect=uncertain
            with self.assertRaises(RuntimeError):op.install_content(f.folder)
            self.assertTrue((f.folder/'content-install-started.json').exists())
            self.assertFalse((f.folder/'content-installed.json').exists())
            f.contract.assert_not_called()
            with self.assertRaises(FileExistsError):op.install_content(f.folder)
            self.assertEqual(f.calls.count('REVIEWED FORWARD SQL'),1)

    def test_failed_afterimage_contract_does_not_record_install_success(self):
        with self.installation() as f:
            f.contract.side_effect=AssertionError('wrong afterimage')
            with self.assertRaises(AssertionError):op.install_content(f.folder)
            self.assertTrue((f.folder/'content-install-started.json').exists())
            self.assertFalse((f.folder/'content-installed.json').exists())

    def test_public_preflight_rejects_wrong_value_and_result_count(self):
        with self.installation() as f:
            for value in ('0','', '1\n1'):
                f.sql.side_effect=None;f.sql.return_value=value
                with self.assertRaises(AssertionError):op.public_preflight()

    def test_content_failure_holds_before_quests_and_image_selection(self):
        with lifecycle() as f:
            op.install_content.side_effect=RuntimeError('uncertain SQL')
            with self.assertRaises(RuntimeError):op.transition()
            self.assertFalse(any(f.runtime.running_services.values()))
            self.assertTrue((f.evidence/'activation/backup.json').exists())
            self.assertFalse(any(e[0] in ('install-quests','select','up') for e in f.runtime.events))
            with self.assertRaisesRegex(AssertionError,'Never replay'):op.transition()

    def test_content_player_mutation_is_held_before_quests_and_boot(self):
        with lifecycle() as f:
            op.install_content.side_effect=lambda folder:f.data.update(inventory='unexpected')
            # Snapshot copies are essential: the prior baseline cannot alias live state.
            with self.assertRaisesRegex(AssertionError,'Player state changed'):op.transition()
            self.assertFalse(any(f.runtime.running_services.values()))
            self.assertFalse(any(e[0] in ('install-quests','select','up') for e in f.runtime.events))

    def test_complement_fingerprints_preserve_other_rows_and_schemas(self):
        retained={'a','b'};schema='schema';calls=[]
        def execute(statement):
            calls.append(statement)
            if statement.startswith('SHOW COLUMNS'):return 'zone_id\tint\nid\tint\n'
            if statement.startswith('SHOW CREATE'):return schema
            if statement.startswith('SELECT SHA2'):return '\n'.join(sorted(retained))
            raise AssertionError(statement)
        base=types.SimpleNamespace(PUBLIC={'items',*op.OWNED},hashes=Mock(side_effect=lambda tables:{'items':'stable'}))
        with patch.object(op,'base',base,create=True),patch.object(op,'sql',side_effect=execute,create=True):
            before=op.content()
            base.hashes.assert_called_with({'items','nightcap_dungeon_state'})
            for table,scope in op.OWNED.items():
                self.assertTrue(any('FROM `'+table+'` WHERE NOT ('+scope+');' in call for call in calls))
                self.assertEqual(before[table+'/outside-owned-scope']['rows'],2)
            retained.add('c');self.assertNotEqual(before,op.content())
            retained.remove('c');schema='changed schema';self.assertNotEqual(before,op.content())

    def test_each_added_payload_is_authenticated(self):
        for name in op.PAYLOAD:
            with self.subTest(name=name),manifest_files() as (stage,manifest):
                (stage/name).write_text('drift')
                with self.assertRaises(AssertionError):op.manifest()


class ImageBuildTests(unittest.TestCase):
    def build_runtime(self):
        runtime = Mock()
        runtime.out.side_effect = ['base', 'candidate', 'base',
            json.dumps([{'RootFS': {'Layers': ['retained', 'zone-overlay']}}]),
            json.dumps([{'RootFS': {'Layers': ['retained']}}]), 'all linked', 'all linked']
        runtime.image_hashes.return_value = {'bin/zone': 'new-zone', 'bin/world': 'new-world', 'bin/shared_memory':'new-loader'}
        return runtime

    def test_build_preserves_local_layers_and_authenticates_both_native_images(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = self.build_runtime()
            with patch.object(op, 'STAGE', Path(directory)), patch.object(op, 'r', runtime, create=True):
                image = op.build_image({'base_image_id': 'base', 'base_hashes': {'bin/zone': 'old-zone', 'bin/world': 'world'}, 'zone_sha256': 'new-zone', 'candidate_hashes':{'bin/zone':'new-zone','bin/world':'new-world','bin/shared_memory':'new-loader'}})
            self.assertEqual(image, 'candidate')
            commands = [c.args for c in runtime.call.call_args_list]
            build = next(c for c in commands if c[:2] == ('docker', 'build'))
            self.assertIn('--pull=false', build)
            self.assertEqual(build[build.index('--network') + 1], 'none')
            self.assertEqual(len([c for c in commands if '--nightcap-crypto-self-test' in c]), 2)
            self.assertEqual((Path(directory) / 'Dockerfile').read_text().splitlines()[-1], 'COPY bin/ /opt/nightcap/bin/')

    def test_build_rejects_base_tag_layer_and_binary_drift(self):
        for fault in ('tag', 'layers', 'binary', 'linker'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                runtime = self.build_runtime()
                values = ['base', 'candidate', 'base',
                    json.dumps([{'RootFS': {'Layers': ['retained', 'zone-overlay']}}]),
                    json.dumps([{'RootFS': {'Layers': ['retained']}}]), 'all linked', 'all linked']
                if fault == 'tag': values[0] = 'unexpected'
                elif fault == 'layers': values[3] = json.dumps([{'RootFS': {'Layers': ['unrelated', 'zone-overlay']}}])
                elif fault == 'binary': runtime.image_hashes.return_value['bin/world'] = 'drift'
                else: values[5] = 'library not found'
                runtime.out.side_effect = values
                with patch.object(op, 'STAGE', Path(directory)), patch.object(op, 'r', runtime, create=True):
                    with self.assertRaises(AssertionError):
                        op.build_image({'base_image_id': 'base', 'base_hashes': {'bin/zone': 'old-zone', 'bin/world': 'world'}, 'zone_sha256': 'new-zone', 'candidate_hashes':{'bin/zone':'new-zone','bin/world':'new-world','bin/shared_memory':'new-loader'}})


if __name__ == '__main__':
    unittest.main(verbosity=2)

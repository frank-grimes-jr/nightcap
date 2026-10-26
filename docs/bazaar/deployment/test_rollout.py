"""Offline rollout fault injection; all runtime/SQL/image operations are fakes.

Receipt files, exclusive opens and manifest hashes are real. Directory fsync is
replaced with a portable receipt writer; POSIX durability needs Linux validation.
"""
import contextlib
import copy
import importlib.util
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('bazaar_rollout', Path(__file__).with_name('rollout.py'))
op = importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)
REAL_INSTALL=op.install_storage
REAL_ENABLE=op.enable_market


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
        return {**self.hashes, 'bin/zone': 'old-zone' if image == 'base' else 'new-zone'}

    def database_backup(self):
        assert not any(self.running_services.values()), 'backup needs stopped writers and access'
        self.events.append(('backup',))
        return {'gzip_integrity': 'passed', 'fresh': len(self.events)}

    def running(self, image, binaries, restarts=None):
        assert self.running_services['game'] and self.image == image
        self.events.append(('running', image))
        return {'image_id': image, 'started_at': '2026-10-24T12:00:00Z'}

    def runtime(self):
        return {'quests/current.pl': 'retained'}

    def closed_ports(self):
        pass


@contextlib.contextmanager
def lifecycle(preflight=True):
    with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
        stage = Path(directory)
        (stage / 'bin').mkdir()
        (stage / 'bin/zone').write_bytes(b'new-zone')
        (stage / 'migration.sql').write_text('CREATE TABLE candidate;')
        evidence = stage / 'evidence'
        hashes = {'bin/' + n: n for n in op.NAMES}
        hashes['bin/zone'] = 'old-zone'
        manifest = {'base_image_id': 'base', 'base_hashes': hashes,
                    'zone_sha256': 'new-zone', 'client_channel_sha256': 'digest','files':{'migration.sql':'digest'}}
        runtime = Runtime(hashes)
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
        stack.enter_context(patch.object(op, 'save', side_effect=receipt))
        stack.enter_context(patch.object(op, 'publication', return_value={'client': 'current', 'wiki': 'current'}))
        stack.enter_context(patch.object(op, 'caches', return_value={'items': 'current', 'spells': 'current'}))
        stack.enter_context(patch.object(op, 'content', return_value={'items': 'current', 'rules': 'current'}))
        stack.enter_context(patch.object(op, 'contract', return_value={'required': 3}))
        stack.enter_context(patch.object(op, 'rehearse_storage', return_value={'schema':'guarded'}))
        stack.enter_context(patch.object(op, 'storage', return_value={'schema':'guarded'}))
        stack.enter_context(patch.object(op, 'market_flag'))
        stack.enter_context(patch.object(op, 'install_storage', side_effect=lambda *a: runtime.events.append(('migration',))))
        stack.enter_context(patch.object(op, 'enable_market', side_effect=lambda *a: runtime.events.append(('enable',))))
        stack.enter_context(patch.object(op.time, 'sleep'))
        stack.enter_context(patch.object(op.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=2**30)))
        plan = {'manifest_sha256': 'digest', 'image': 'candidate',
                'services': {s: runtime.compact(s) for s in ('game', 'gateway', 'db', 'web', 'tunnel')},
                'runtime': runtime.runtime(), 'publication': op.publication(),
                'caches': op.caches(), 'content': op.content(),'new_storage':{'schema':'guarded'}}
        if preflight:
            evidence.mkdir()
            receipt(evidence / 'preflight.json', plan)
        yield types.SimpleNamespace(runtime=runtime, base=base, startup=startup, market=market,
                                    data=data, evidence=evidence, manifest=manifest, plan=plan)


@contextlib.contextmanager
def manifest_files():
    with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
        stage = Path(directory) / 'stage'
        stage.mkdir()
        (stage / 'bin').mkdir()
        for name in ('bin/zone', 'rollout.py', 'migration.sql'):
            (stage / name).write_text('trusted ' + name)
        helpers = {}
        for name in ('runtime', 'state', 'startup', 'market', 'contract'):
            path = Path(directory) / (name + '.py')
            path.write_text('trusted ' + name)
            helpers[name] = {'path': str(path.resolve()), 'sha256': op.sha(path)}
        manifest = {'files': {n: op.sha(stage / n) for n in ('bin/zone', 'rollout.py', 'migration.sql')},
                    'contract': helpers.pop('contract'), 'helpers': helpers,
                    'zone_sha256': op.sha(stage / 'bin/zone'), 'base_hashes': {'bin/zone': 'old'}}
        (stage / 'manifest.json').write_text(json.dumps(manifest))
        stack.enter_context(patch.object(op, 'STAGE', stage))
        yield stage, manifest


class ManifestTests(unittest.TestCase):
    def test_exact_manifest_authenticates(self):
        with manifest_files() as (stage, manifest):
            self.assertEqual(op.manifest(), manifest)

    def test_manifest_rejects_tampering_and_scope_changes(self):
        for fault in ('missing', 'extra', 'traversal', 'helper_missing', 'helper_extra',
                      'helper_hash', 'relative_helper', 'contract_hash', 'zone', 'operator',
                      'zone_binding', 'unchanged_zone'):
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
                else: manifest['base_hashes']['bin/zone'] = manifest['zone_sha256']
                (stage / 'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(AssertionError): op.manifest()

    def test_binaries_select_only_zone_change(self):
        with lifecycle() as f:
            old = op.binaries(True)
            new = op.binaries()
            self.assertEqual({n for n in old if old[n] != new[n]}, {'zone'})
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
            self.assertLess(events.index(('select', 'candidate')), events.index(('up', '-d', '--wait', '--wait-timeout', '240', 'game')))
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
            def fail(args):
                if args[0] == 'up' and args[-1] == 'gateway': raise RuntimeError('lost acknowledgment')
            f.runtime.fail = fail
            with self.assertRaises(RuntimeError): op.open_access()
            self.assertTrue(f.runtime.opened)
            self.assertFalse(any(f.runtime.running_services.values()))
            self.assertFalse((f.evidence / 'activation/deployed.json').exists())
            with self.assertRaises(AssertionError): op.open_access()





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


class ContractTests(unittest.TestCase):
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


class ImageBuildTests(unittest.TestCase):
    def build_runtime(self):
        runtime = Mock()
        runtime.out.side_effect = ['base', 'candidate', 'base',
            json.dumps([{'RootFS': {'Layers': ['retained', 'zone-overlay']}}]),
            json.dumps([{'RootFS': {'Layers': ['retained']}}]), 'all linked', 'all linked']
        runtime.image_hashes.return_value = {'bin/zone': 'new-zone', 'bin/world': 'world'}
        return runtime

    def test_build_preserves_local_layers_and_authenticates_both_native_images(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = self.build_runtime()
            with patch.object(op, 'STAGE', Path(directory)), patch.object(op, 'r', runtime, create=True):
                image = op.build_image({'base_image_id': 'base', 'base_hashes': {'bin/zone': 'old-zone', 'bin/world': 'world'}, 'zone_sha256': 'new-zone'})
            self.assertEqual(image, 'candidate')
            commands = [c.args for c in runtime.call.call_args_list]
            build = next(c for c in commands if c[:2] == ('docker', 'build'))
            self.assertIn('--pull=false', build)
            self.assertEqual(build[build.index('--network') + 1], 'none')
            self.assertEqual(len([c for c in commands if '--nightcap-crypto-self-test' in c]), 2)
            self.assertEqual((Path(directory) / 'Dockerfile').read_text().splitlines()[-1], 'COPY bin/zone /opt/nightcap/bin/zone')

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
                        op.build_image({'base_image_id': 'base', 'base_hashes': {'bin/zone': 'old-zone', 'bin/world': 'world'}, 'zone_sha256': 'new-zone'})



class BazaarMigrationTests(unittest.TestCase):
    def test_migration_and_enable_order(self):
        with lifecycle() as f:
            op.transition();events=f.runtime.events
            self.assertLess(events.index(('backup',)),events.index(('migration',)))
            self.assertLess(events.index(('migration',)),events.index(('select','candidate')))
            self.assertLess(events.index(('running','candidate')),events.index(('enable',)))
            self.assertFalse(f.runtime.opened)

    def test_migration_or_enable_failure_holds_and_never_opens(self):
        for name in ('install_storage','enable_market'):
            with self.subTest(name=name), lifecycle() as f, patch.object(op,name,side_effect=RuntimeError('uncertain SQL')):
                with self.assertRaises(RuntimeError):op.transition()
                self.assertFalse(any(f.runtime.running_services.values()))
                self.assertFalse((f.evidence/'activation/verified-closed.json').exists())
                self.assertFalse(f.runtime.opened)
                with self.assertRaises(AssertionError):op.transition()

    def test_schema_or_flag_drift_cannot_open(self):
        for name in ('storage','market_flag'):
            with self.subTest(name=name), lifecycle() as f:
                op.transition()
                with patch.object(op,name,side_effect=AssertionError('drift')):
                    with self.assertRaises(AssertionError):op.open_access()
                self.assertFalse(f.runtime.opened)
                self.assertFalse(any(f.runtime.running_services.values()))

    def test_ambiguous_migration_records_attempt_and_holds_without_replay(self):
        with lifecycle() as f, patch.object(op,'absent_storage'), patch.object(op,'sql',side_effect=RuntimeError('lost SQL acknowledgment'),create=True), patch.object(op,'install_storage',side_effect=REAL_INSTALL):
            with self.assertRaises(RuntimeError):op.transition()
            folder=f.evidence/'activation'
            self.assertTrue((folder/'migration-attempted.json').exists())
            self.assertFalse((folder/'migration-committed.json').exists())
            self.assertFalse(f.runtime.opened)
            self.assertFalse(any(f.runtime.running_services.values()))
            self.assertFalse(any(e[0]=='select' for e in f.runtime.events))
            with self.assertRaises(AssertionError):op.transition()

    def test_ambiguous_enable_holds_without_verified_open_receipt(self):
        with lifecycle() as f, patch.object(op,'sql',side_effect=RuntimeError('lost commit acknowledgment'),create=True), patch.object(op,'enable_market',side_effect=REAL_ENABLE):
            with self.assertRaises(RuntimeError):op.transition()
            folder=f.evidence/'activation'
            self.assertTrue((folder/'enable-attempted.json').exists())
            self.assertFalse((folder/'enable-committed.json').exists())
            self.assertFalse((folder/'verified-closed.json').exists())
            self.assertFalse(f.runtime.opened)
            self.assertFalse(any(f.runtime.running_services.values()))

    def test_binary_downmigration_is_not_recovery(self):
        with lifecycle() as f:
            with self.assertRaises(AssertionError):op.transition(True)
            self.assertEqual(f.runtime.events,[])

class DisableTests(unittest.TestCase):
    def test_success_preserves_earned_ownership_and_runtime(self):
        with lifecycle() as f:
            earned={'listings':[1,2],'items':[11,22],'credits':555,'receipts':[1,2,3]};before=copy.deepcopy(earned)
            statements=[]
            def sql(query):
                statements.append(query)
                if query.startswith('SELECT'):return '1\t1\t1'
                self.assertIn('UPDATE nightcap_bazaar_state SET enabled=0',query)
                self.assertNotIn('nightcap_bazaar_items',query)
                self.assertNotIn('nightcap_bazaar_credits',query)
                self.assertNotIn('nightcap_bazaar_listings',query)
                return ''
            with patch.object(op,'sql',side_effect=sql,create=True):op.disable_market()
            self.assertEqual(earned,before)
            self.assertEqual(len(statements),2)
            self.assertEqual(f.runtime.events,[])
            self.assertTrue((f.evidence/'disable/disabled.json').exists())
            with self.assertRaises(AssertionError):op.disable_market()

    def test_uncertain_disable_holds_without_replay(self):
        for fault in ('before-update','lost-ack','verification'):
            with self.subTest(fault=fault),lifecycle() as f:
                flag=[1];calls=[]
                def sql(query):
                    calls.append(query)
                    if query.startswith('SELECT'):return '1\t1\t1'
                    if fault=='before-update':raise RuntimeError('write failed')
                    flag[0]=0
                    if fault=='lost-ack':raise RuntimeError('lost commit ack')
                    return ''
                with patch.object(op,'sql',side_effect=sql,create=True),patch.object(op,'market_flag',side_effect=AssertionError('cannot verify') if fault=='verification' else None):
                    with self.assertRaises((RuntimeError,AssertionError)):op.disable_market()
                self.assertEqual(flag[0],1 if fault=='before-update' else 0)
                self.assertFalse(any(f.runtime.running_services.values()))
                self.assertTrue((f.evidence/'disable/update-attempted.json').exists())
                self.assertFalse((f.evidence/'disable/disabled.json').exists())
                self.assertEqual(len(list((f.evidence/'disable').glob('held-*.json'))),1)
                with self.assertRaises(AssertionError):op.disable_market()
                self.assertEqual(len(calls),2)

if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Isolated production orchestration fault tests; Docker/SSH are never invoked."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('pet_rollout', Path(__file__).with_name('rollout.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class Scenario:
    def __init__(self, fault=None):
        self.fault = fault
        self.events = []
        self.saved = {}
        self.selected = 'old'
        self.game = 'old-id'
        self.game_on = self.gateway_on = True
        self.exit_code = 0
        self.oom = False
        self.restart_count = 0
        self.started_at = 'now'
        self.data_dirty = False
        self.gateway_attempts = 0
        self.m = {'old_image': 'old', 'new_image': 'new', 'old_image_id': 'old-id',
                  'binaries': {'world': 'newhash'}, 'old_hashes': {'bin/world': 'oldhash'},
                  'old_restart_count': 0, 'old_started_at': 'now'}
        self.p = {'manifest_sha256': 'manifesthash', 'new_image_id': 'new-id', 'runtime': {'quest': 'q'}}

    def state(self, service):
        if service == 'game':
            return {'Id': 'game-cid', 'Image': self.game, 'RestartCount': self.restart_count,
                    'State': {'Running': self.game_on, 'ExitCode': self.exit_code,
                              'OOMKilled': self.oom, 'Health': {'Status': 'healthy'}, 'StartedAt': self.started_at}}
        return {'Id': 'gateway-cid', 'State': {'Running': self.gateway_on}}

    def compose(self, *args):
        self.events.append(('compose', *args))
        service = args[-1]
        if args[0] == 'stop':
            if service == 'gateway':
                if self.fault == 'closure':
                    raise RuntimeError('gateway stop unavailable')
                self.gateway_on = False
            else:
                self.game_on = False
                if self.fault in ('exit137', 'oom'):
                    self.exit_code = 137
                    self.oom = self.fault == 'oom'
        elif args[0] == 'up' and service == 'game':
            self.game = self.selected + '-id'
            self.game_on = True
            self.exit_code = 0
            self.oom = False
            self.restart_count = 0
            self.started_at = 'replacement-start'
            if self.selected == 'new' and self.fault in ('start', 'rollback'):
                raise RuntimeError('candidate failed after container creation')
            if self.selected == 'old' and self.fault == 'rollback':
                raise RuntimeError('recovery failed')
            if self.selected == 'new' and self.fault == 'preservation':
                self.data_dirty = True
        elif args[0] == 'up' and service == 'gateway':
            self.gateway_on = True
            self.gateway_attempts += 1
            if self.fault == 'gateway' and self.gateway_attempts == 1:
                raise RuntimeError('gateway started but wait failed')

    def call(self, *args, **kwargs):
        self.events.append(('call', *args))
        if self.fault == 'closure':
            raise RuntimeError('Docker unavailable')
        if args[:2] == ('docker', 'stop'):
            self.gateway_on = False

    def out(self, *args, **kwargs):
        if args[:3] == ('docker', 'image', 'inspect'):
            return 'wrong-id' if self.fault == 'image-drift' else 'new-id'
        if args[:2] == ('docker', 'inspect'):
            return json.dumps([{'State': {'Running': self.gateway_on}}])
        raise AssertionError(('unexpected read', args))

    def sql(self, query, isolated=False):
        if query.startswith('SELECT epoch'):
            return '11' if self.game == 'new-id' else '10'
        return 'find\t10\t10\nsell\t20\t20\nbuy\t12\t12'

    def fingerprints(self):
        return {'player': 'changed' if self.data_dirty else 'original'}

    def runtime(self):
        return {'quest': 'changed' if self.fault == 'runtime-drift' else 'q'}

    def backup(self):
        self.events.append(('backup',))
        if self.fault == 'backup':
            raise RuntimeError('dump failed')
        self.saved['backup.json'] = {'sha256': 'private-dump'}

    def rehearsal(self, before):
        self.events.append(('restore-rehearsal',))
        if self.fault == 'restore':
            raise RuntimeError('isolated restore failed')

    def select(self, image):
        self.events.append(('select', image))
        if image == 'new' and self.fault == 'switch':
            raise RuntimeError('atomic image selection failed')
        self.selected = image

    def running(self, image, binaries, expected_restarts=0):
        self.events.append(('running', image))
        assert self.game_on and self.game == image
        assert self.restart_count == expected_restarts
        if image == 'new-id' and self.fault == 'hash':
            raise AssertionError('running binary hash differs')
        return {'image_id': image, 'native_processes': 15,
                'started_at': self.started_at, 'restart_count': self.restart_count}

    def patches(self):
        return patch.multiple(release, manifest=lambda: self.m,
                              load=lambda n: self.p if n == 'preflight.json' else self.saved[n],
                              save=lambda n, v: self.saved.__setitem__(n, v), sha=lambda p: 'manifesthash',
                              state=self.state, compose=self.compose, call=self.call, out=self.out,
                              sql=self.sql, fingerprints=self.fingerprints, runtime_files=self.runtime,
                              backup=self.backup, restore_rehearsal=self.rehearsal,
                              select=self.select, running=self.running)


class RolloutFaultTests(unittest.TestCase):
    def setUp(self):
        # Any missed mock aborts instead of touching a local Docker or remote host.
        self.guards = [patch.object(subprocess, name, side_effect=AssertionError('real subprocess forbidden'))
                       for name in ('run', 'Popen', 'check_output')]
        self.guards.append(patch.object(release.time, 'sleep'))
        for guard in self.guards:
            guard.start()
            self.addCleanup(guard.stop)

    def activate(self, scenario, fails=True):
        with scenario.patches():
            if fails:
                with self.assertRaises((AssertionError, RuntimeError)):
                    release.activate()
            else:
                release.activate()

    def test_preflight_artifact_or_image_drift_never_stops_services(self):
        for fault in ('runtime-drift', 'image-drift'):
            with self.subTest(fault=fault):
                s = Scenario(fault)
                self.activate(s)
                self.assertEqual(s.events, [])
                self.assertTrue(s.game_on and s.gateway_on)

    def test_backup_or_isolated_restore_failure_never_selects_new_image(self):
        for fault in ('backup', 'restore'):
            with self.subTest(fault=fault):
                s = Scenario(fault)
                self.activate(s)
                self.assertNotIn(('select', 'new'), s.events)
                self.assertEqual(s.game, 'old-id')
                self.assertTrue(s.gateway_on)
                self.assertFalse(s.saved['rolled-back.json']['database_restored'])

    def test_switch_start_running_hash_and_gateway_failures_restore_old_image(self):
        for fault in ('switch', 'start', 'hash', 'gateway'):
            with self.subTest(fault=fault):
                s = Scenario(fault)
                self.activate(s)
                self.assertEqual(s.game, 'old-id')
                self.assertTrue(s.game_on and s.gateway_on)
                self.assertIn('rolled-back.json', s.saved)
                self.assertNotIn('activated.json', s.saved)

    def test_unclean_shutdown_rejects_activation_but_recovery_accepts_crashed_container(self):
        for fault in ('exit137', 'oom'):
            with self.subTest(fault=fault):
                s = Scenario(fault)
                self.activate(s)
                self.assertNotIn(('backup',), s.events)
                self.assertNotIn(('select', 'new'), s.events)
                self.assertEqual(s.game, 'old-id')
                self.assertTrue(s.game_on and s.gateway_on)

    def test_preservation_mismatch_or_failed_recovery_keeps_gateway_closed(self):
        for fault in ('preservation', 'rollback'):
            with self.subTest(fault=fault):
                s = Scenario(fault)
                self.activate(s)
                self.assertFalse(s.gateway_on)
                self.assertTrue(s.saved['rollback-failed.json']['gateway_held_closed'])
                self.assertNotIn('activated.json', s.saved)

    def test_failed_gateway_closure_is_never_reported_as_closed(self):
        s = Scenario('closure')
        self.activate(s)
        self.assertTrue(s.gateway_on)
        self.assertFalse(s.saved['rollback-failed.json']['gateway_held_closed'])

    def test_success_requires_two_candidate_health_samples_before_opening_gateway(self):
        s = Scenario()
        self.activate(s, fails=False)
        opening = s.events.index(('compose', 'up', '-d', '--wait', '--wait-timeout', '60', 'gateway'))
        self.assertEqual(s.events[:opening].count(('running', 'new-id')), 2)
        self.assertEqual(s.events[opening:].count(('running', 'new-id')), 1)
        self.assertIn('activated.json', s.saved)

    def test_explicit_rollback_failed_gateway_start_is_closed_again(self):
        s = Scenario('gateway')
        s.game = 'new-id'
        s.selected = 'new'
        with s.patches(), self.assertRaises(RuntimeError):
            release.rollback()
        self.assertEqual(s.game, 'old-id')
        self.assertFalse(s.gateway_on)
        evidence = next(v for k, v in s.saved.items() if k.startswith('rollback-failed-'))
        self.assertTrue(evidence['gateway_held_closed'])

    def test_running_rejects_stopped_or_oom_container_before_process_reads(self):
        actual_running = release.running
        for stopped, oom in ((True, False), (False, True)):
            s = Scenario()
            s.game_on = not stopped
            s.oom = oom
            with patch.object(release, 'state', s.state), patch.object(release, 'out') as reads:
                with self.assertRaises(AssertionError):
                    actual_running('old-id', {})
                reads.assert_not_called()

    def test_select_failure_preserves_env_and_removes_only_own_temporary_file(self):
        with tempfile.TemporaryDirectory(prefix='pet-rollout-test-') as directory:
            root = Path(directory)
            env = root / '.env'
            original = 'NIGHTCAP_GAME_IMAGE=old\nUNRELATED=preserved\n'
            env.write_text(original)
            sentinel = root / '.env.pet-pending-unrelated'
            sentinel.write_text('keep')
            with patch.object(release, 'ROOT', root), patch.object(release.os, 'chown', create=True), \
                    patch.object(release.os, 'replace', side_effect=OSError('replace failed')):
                with self.assertRaises(OSError):
                    release.select('new')
            self.assertEqual(env.read_text(), original)
            self.assertEqual(sentinel.read_text(), 'keep')
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['.env', '.env.pet-pending-unrelated'])


    def test_running_accepts_only_explicitly_pinned_restart_count_and_reports_actual_state(self):
        s = Scenario()
        s.restart_count = 1
        s.started_at = '2026-09-25T04:03:02Z'
        binaries = {name: name + '-hash' for name in ('world', 'zone', 'ucs', 'loginserver')}
        rows = [[name, binaries[name]] for name in ('world', 'ucs', 'loginserver')]
        rows.extend([['zone', binaries['zone']]] * 12)
        with patch.object(release, 'state', s.state), \
                patch.object(release, 'out', side_effect=[json.dumps(rows), '']):
            result = release.running('old-id', binaries, expected_restarts=1)
        self.assertEqual(result['restart_count'], 1)
        self.assertEqual(result['started_at'], s.started_at)
        self.assertEqual(result['native_processes'], 15)

    def test_running_default_keeps_new_candidate_zero_restart_requirement(self):
        s = Scenario()
        s.game = 'new-id'
        s.restart_count = 1
        with patch.object(release, 'state', s.state), patch.object(release, 'out') as reads:
            with self.assertRaises(AssertionError):
                release.running('new-id', {})
            reads.assert_not_called()

    def test_running_pinned_counter_rejects_both_another_restart_and_container_recreation(self):
        for actual_count in (0, 2):
            with self.subTest(actual_count=actual_count):
                s = Scenario()
                s.restart_count = actual_count
                with patch.object(release, 'state', s.state), patch.object(release, 'out') as reads:
                    with self.assertRaises(AssertionError):
                        release.running('old-id', {}, expected_restarts=1)
                    reads.assert_not_called()

    def test_preflight_requires_exact_old_baseline_before_build_or_evidence_creation(self):
        for field, actual in (('restart_count', 0), ('restart_count', 2), ('started_at', 'unexpected-start')):
            with self.subTest(field=field, actual=actual), tempfile.TemporaryDirectory(prefix='pet-baseline-test-') as directory:
                s = Scenario()
                s.restart_count = s.m['old_restart_count'] = 1
                setattr(s, field, actual)
                evidence = Path(directory) / 'not-created'
                def read(*args, **kwargs):
                    if args[:3] == ('docker', 'compose', 'config'):
                        return json.dumps({'services': {'game': {'image': 'old'}}})
                    if args[:3] == ('docker', 'image', 'inspect'):
                        return 'old-id'
                    raise AssertionError(('unexpected read', args))
                with s.patches(), patch.object(release, 'EVIDENCE', evidence), \
                        patch.object(release, 'out', side_effect=read), \
                        patch.object(release, 'image_hashes', return_value=s.m['old_hashes']), \
                        patch.object(release.shutil, 'disk_usage', return_value=SimpleNamespace(free=20_000_000_000)):
                    with self.assertRaises(AssertionError):
                        release.preflight()
                self.assertFalse(evidence.exists())
                self.assertFalse(any(event[0] in ('call', 'compose', 'select') for event in s.events))
                self.assertTrue(s.game_on and s.gateway_on)


    def test_preflight_accepts_pinned_old_restart_without_weakening_other_checks(self):
        s = Scenario()
        s.restart_count = s.m['old_restart_count'] = 1
        old = s.m['old_hashes']
        new = {'bin/world': 'newhash'}
        def read(*args, **kwargs):
            if args[:3] == ('docker', 'compose', 'config'):
                return json.dumps({'services': {'game': {'image': 'old'}}})
            if args[:3] == ('docker', 'image', 'inspect'):
                return args[-1] + '-id'
            raise AssertionError(('unexpected read', args))
        with tempfile.TemporaryDirectory(prefix='pet-baseline-test-') as directory:
            evidence = Path(directory) / 'evidence'
            with s.patches(), patch.object(release, 'EVIDENCE', evidence), \
                    patch.object(release, 'out', side_effect=read), \
                    patch.object(release, 'image_hashes', side_effect=[old, new]), \
                    patch.object(release.shutil, 'disk_usage', return_value=SimpleNamespace(free=20_000_000_000)):
                release.preflight()
            self.assertTrue(evidence.is_dir())
        self.assertEqual(s.saved['preflight.json']['new_image_id'], 'new-id')
        self.assertFalse(any(event[0] in ('compose', 'select') for event in s.events))
        self.assertTrue(s.game_on and s.gateway_on)

    def test_activate_rechecks_old_counter_and_start_before_stopping_services(self):
        for field, actual in (('restart_count', 0), ('restart_count', 2), ('started_at', 'unexpected-start')):
            with self.subTest(field=field, actual=actual):
                s = Scenario()
                s.restart_count = s.m['old_restart_count'] = 1
                setattr(s, field, actual)
                self.activate(s)
                self.assertFalse(any(event[0] in ('compose', 'call', 'select', 'backup') for event in s.events))
                self.assertTrue(s.game_on and s.gateway_on)
                self.assertFalse(s.saved)

    def test_activate_accepts_recorded_old_restart_and_replacement_must_start_clean(self):
        s = Scenario()
        s.restart_count = s.m['old_restart_count'] = 1
        self.activate(s, fails=False)
        self.assertEqual(s.game, 'new-id')
        self.assertTrue(s.gateway_on)
        self.assertEqual(s.saved['activated.json']['restart_count'], 0)
        self.assertEqual(s.saved['activated.json']['started_at'], 'replacement-start')



    def test_recovery_recreates_old_container_after_recorded_restart_and_backup_failure(self):
        for fault in ('backup', 'restore'):
            with self.subTest(fault=fault):
                s = Scenario(fault)
                s.restart_count = s.m['old_restart_count'] = 1
                self.activate(s)
                recovery = [event for event in s.events if event[:3] == ('compose', 'up', '-d') and event[-1] == 'game']
                self.assertEqual(len(recovery), 1)
                self.assertIn('--force-recreate', recovery[0])
                self.assertEqual(s.game, 'old-id')
                self.assertTrue(s.game_on and s.gateway_on)
                self.assertFalse(s.saved['rolled-back.json']['database_restored'])

    def test_explicit_rollback_recreates_old_container_and_preserves_current_progress(self):
        s = Scenario()
        s.game = 'new-id'
        s.selected = 'new'
        s.m['old_restart_count'] = 1
        with s.patches():
            release.rollback()
        recovery = [event for event in s.events if event[:3] == ('compose', 'up', '-d') and event[-1] == 'game']
        self.assertEqual(len(recovery), 1)
        self.assertIn('--force-recreate', recovery[0])
        self.assertEqual(s.game, 'old-id')
        self.assertTrue(s.game_on and s.gateway_on)
        evidence = next(v for k, v in s.saved.items() if k.startswith('rollback-'))
        self.assertTrue(evidence['current_progress_preserved'])
        self.assertFalse(evidence['database_restored'])


if __name__ == '__main__':
    unittest.main(verbosity=2)

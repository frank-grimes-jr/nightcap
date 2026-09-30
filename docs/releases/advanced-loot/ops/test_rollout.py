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
        self.m = {'client_release':2026093006,'client_channel_sha256':'manifesthash','old_image': 'old', 'new_image': 'new', 'old_image_id': 'old-id',
                  'binaries': {'world': 'newhash'}, 'old_hashes': {'bin/world': 'oldhash'},
                  'old_restart_count': 0, 'old_started_at': 'now'}
        self.p = {'manifest_sha256': 'manifesthash', 'new_image_id': 'new-id', 'runtime': {'quest': 'q'}}

    def state(self, service):
        if service == 'game':
            return {'Id': 'game-cid', 'Image': self.game, 'RestartCount': self.restart_count,
                    'HostConfig':{'PortBindings':{},'NetworkMode':'isolated'},'State': {'Running': self.game_on, 'ExitCode': self.exit_code,
                              'OOMKilled': self.oom, 'Health': {'Status': 'healthy'}, 'StartedAt': self.started_at}}
        return {'Id': 'gateway-cid','HostConfig':{'PortBindings':{},'NetworkMode':'isolated'}, 'State': {'Running': self.gateway_on}}

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
        if query.startswith('SELECT COUNT'):return '0'
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
        self.saved['migration-rehearsal.json']={'schemas':{'fixture':'schema'}}
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

    def migrate(self):
        self.events.append(('migrate',))
        if self.fault=='migration':raise RuntimeError('partial DDL failure')

    def patches(self):
        return patch.multiple(release, manifest=lambda: self.m,
                              load=lambda n: self.p if n == 'preflight.json' else self.saved[n],
                              save=lambda n, v: self.saved.__setitem__(n, v), sha=lambda p: 'manifesthash',
                              state=self.state, compose=self.compose, call=self.call, out=self.out,
                              sql=self.sql, fingerprints=self.fingerprints, runtime_files=self.runtime,
                              backup=self.backup, restore_rehearsal=self.rehearsal,
                              select=self.select, running=self.running, migrate=self.migrate, migration_preflight=lambda:None, migration_schema=lambda:{'fixture':'schema'}, verify_app_database=lambda *args:{'rolled_back':True})


class RolloutFaultTests(unittest.TestCase):
    def setUp(self):
        for name in ('run','Popen','check_output'):
            guard=patch.object(subprocess,name,side_effect=AssertionError('real subprocess forbidden'))
            guard.start();self.addCleanup(guard.stop)
        guard=patch.object(release.time,'sleep');guard.start();self.addCleanup(guard.stop)
        self.temp=tempfile.TemporaryDirectory(prefix='advloot-ops-')
        self.addCleanup(self.temp.cleanup)
        guard=patch.object(release,'EVIDENCE',Path(self.temp.name));guard.start();self.addCleanup(guard.stop)

    def execute(self,s,fails=True):
        with s.patches():
            if fails:
                with self.assertRaises((AssertionError,RuntimeError)):release.activate()
            else:release.activate()

    def test_drift_never_stops_services(self):
        for fault in ('runtime-drift','image-drift'):
            s=Scenario(fault);self.execute(s)
            self.assertEqual(s.events,[])
            self.assertTrue(s.game_on and s.gateway_on)

    def test_pre_start_failures_restore_old_without_database_restore(self):
        for fault in ('backup','restore','migration','switch','exit137','oom'):
            with self.subTest(fault=fault):
                s=Scenario(fault);self.execute(s)
                self.assertEqual(s.game,'old-id')
                self.assertTrue(s.game_on and s.gateway_on)
                self.assertFalse(s.saved['pre-start-restored.json']['database_restored'])
                self.assertNotIn('receipt-aware-boundary.json',s.saved)

    def test_after_new_start_never_selects_old(self):
        for fault in ('start','hash','preservation','rollback'):
            with self.subTest(fault=fault):
                s=Scenario(fault);self.execute(s)
                self.assertNotIn(('select','old'),s.events)
                self.assertFalse(s.gateway_on or s.game_on)
                self.assertTrue(s.saved['activation-held-closed.json']['receipt_aware_recovery_required'])
                self.assertIn('receipt-aware-boundary.json',s.saved)

    def test_actual_app_account_failure_keeps_access_closed(self):
        s=Scenario()
        with s.patches(),patch.object(release,'verify_app_database',side_effect=RuntimeError('missing app grants')):
            with self.assertRaises(RuntimeError):release.activate()
        self.assertFalse(s.gateway_on or s.game_on)
        self.assertNotIn(('select','old'),s.events)

    def test_success_stays_closed_until_matching_client_publication(self):
        s=Scenario();self.execute(s,False)
        self.assertTrue(s.game_on);self.assertFalse(s.gateway_on)
        self.assertIn('server-ready.json',s.saved);self.assertNotIn('activated.json',s.saved)
        s.m['client_channel_sha256']='wrong'
        with s.patches(),self.assertRaises(AssertionError):release.open_access()
        self.assertFalse(s.gateway_on)
        s.m['client_channel_sha256']='manifesthash'
        with s.patches():release.open_access()
        self.assertTrue(s.gateway_on)
        self.assertEqual(s.saved['activated.json']['client_release'],2026093006)

    def test_open_failure_recloses_gateway_without_old_image(self):
        s=Scenario();self.execute(s,False);s.fault='gateway'
        with s.patches(),self.assertRaises(RuntimeError):release.open_access()
        self.assertFalse(s.gateway_on)
        self.assertNotIn(('select','old'),s.events)
        self.assertTrue(s.saved['open-failed.json']['gateway_held_closed'])

    def test_direct_port_or_host_network_rejected_before_shutdown(self):
        for mode,ports in [('host',{}),('isolated',{'9000/udp':[{}]})]:
            s=Scenario();original=s.state
            def state(service):
                value=original(service);value['HostConfig']={'NetworkMode':mode,'PortBindings':ports};return value
            s.state=state
            self.execute(s)
            self.assertEqual(s.events,[])

    def test_emergency_hold_survives_corrupt_staging(self):
        s=Scenario()
        with s.patches(),patch.object(release,'manifest',side_effect=RuntimeError('stage corrupt')):
            release.hold()
        self.assertFalse(s.gateway_on or s.game_on)

    def test_failed_closure_is_not_reported_as_closed(self):
        s=Scenario('closure');self.execute(s)
        self.assertTrue(s.gateway_on)
        self.assertFalse(s.saved['pre-start-recovery-failed.json']['gateway_held_closed'])

    def test_emergency_hold_with_absent_gateway_stops_game(self):
        s=Scenario();original=s.state
        def state(service):
            if service=='gateway':raise AssertionError('container absent')
            return original(service)
        s.state=state
        with s.patches(),patch.object(release,'out',return_value=''):
            release.hold()
        self.assertFalse(s.game_on)
        self.assertTrue(next(v for k,v in s.saved.items() if k.startswith('held-'))['gateway_closed'])

    def test_pre_open_rejects_unexpected_restart(self):
        s=Scenario();self.execute(s,False);s.started_at='unexpected-restart'
        with s.patches(),self.assertRaises(AssertionError):release.open_access()
        self.assertFalse(s.gateway_on)

    def test_migration_requires_three_transactional_tables_and_no_triggers(self):
        def query(text,isolated=False):
            if 'COLUMN_NAME' in text:return '\n'.join(release.INVENTORY_COLUMNS)
            if 'ENGINE' in text:return 'character_currency\tInnoDB\ncharacter_evolving_items\tInnoDB\ninventory\tInnoDB'
            return '0'
        with patch.object(release,'sql',side_effect=query):release.migration_preflight()
        for fault in ('exists','engine','trigger','columns'):
            def broken(text,isolated=False):
                if fault=='exists' and 'TABLE_NAME IN' in text:return '1'
                if fault=='engine' and 'ENGINE' in text:return query(text).replace('InnoDB','MyISAM',1)
                if fault=='trigger' and 'TRIGGERS' in text:return '1'
                if fault=='columns' and 'COLUMN_NAME' in text:return query(text).replace('guid','unknown')
                return query(text)
            with patch.object(release,'sql',side_effect=broken),self.assertRaises(AssertionError):release.migration_preflight()

    def test_new_tables_reject_triggers(self):
        def query(text,isolated=False):return '0' if 'TRIGGERS' in text else 'ENGINE=InnoDB'
        with patch.object(release,'sql',side_effect=query):
            self.assertEqual(len(release.migration_schema()),3)
        with patch.object(release,'sql',return_value='1'),self.assertRaises(AssertionError):release.migration_schema()

if __name__=='__main__':unittest.main(verbosity=2)

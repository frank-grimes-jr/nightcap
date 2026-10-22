"""Exercise the diagnosed finish and the real guarded open with their shared receipts."""
import contextlib
import copy
import hashlib
import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import test_rollout as base

spec = importlib.util.spec_from_file_location('finish_cache', Path(__file__).with_name('finish_cache.py'))
finish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finish)
op = base.op
AFTER = {'rows': 6066, 'sha256': '6c1b6ef1a78d69ec4f9d963165fcbc53100515d86d610249dee315d9ca5fe5d4'}


@contextlib.contextmanager
def fixture():
    with base.fixture() as (runtime, data, evidence), contextlib.ExitStack() as stack:
        stage = evidence.parent
        destination = stage / 'finish-evidence'
        stack.enter_context(patch.object(finish, 'S', stage))
        stack.enter_context(patch.object(finish, 'F', destination))
        stack.enter_context(patch.object(finish.shutil, 'disk_usage', return_value=SimpleNamespace(free=2*1024**3)))
        rows = [str(n) for n in range(6551)]
        before_cache = {'rows': len(rows), 'sha256': hashlib.sha256('\n'.join(sorted(rows)).encode()).hexdigest()}
        data['player']['zone_state_spawns'] = copy.deepcopy(AFTER)
        before = copy.deepcopy(data)
        before['player']['zone_state_spawns'] = before_cache
        original = evidence / 'activation'
        original.mkdir()
        diagnosis = {
            'original': before_cache, 'scratch_restore': before_cache,
            'exact_restore_matches': True, 'rule': '7',
            'surviving_field_differences': 0, 'added_rows': 0, 'removed_nonexpired': 0,
            'removed_groups': '38\t0\t0\t0\t357\t2026-10-13 01:28:39\t2026-10-13 01:28:39\n75\t0\t0\t0\t128\t2026-10-13 01:28:39\t2026-10-13 01:28:39\n',
            'first_started_at': '2026-10-22T00:22:38.473530919Z',
        }
        for name, value in {
            'stopped-state.json': before,
            'content-committed.json': {'target': 'after', 'aa_xp_per_point': '1000000'},
            'cache-diagnosis.json': diagnosis,
            'market-before.json': ['before'],
            'held-original.json': {'running': {'game': False, 'gateway': False}},
        }.items():
            op.save(original / name, value)
        runtime.image = 'new'
        runtime.running_services = {'game': False, 'gateway': False}
        def sql(query):
            if query.startswith('SELECT * FROM nightcap_aa_state_hold_20261021.'):
                return '\n'.join(rows) + '\n'
            if query.startswith('SHOW COLUMNS'):
                return ('id\tint\nx\tfloat\ny\tdouble\nlabel\tvarchar(64)\n'
                        'payload\ttext\nraw_data\tblob\ncreated_at\ttimestamp\namount\tdecimal(10,2)\n')
            if 'WHERE NOT(' in query:
                expected = [
                    '(o.`id`<=>n.`id`)',
                    '(BINARY CAST(o.`x` AS CHAR)<=>BINARY CAST(n.`x` AS CHAR))',
                    '(BINARY CAST(o.`y` AS CHAR)<=>BINARY CAST(n.`y` AS CHAR))',
                    '(BINARY o.`label`<=>BINARY n.`label`)',
                    '(BINARY o.`payload`<=>BINARY n.`payload`)',
                    '(BINARY o.`raw_data`<=>BINARY n.`raw_data`)',
                    '(o.`created_at`<=>n.`created_at`)',
                    '(o.`amount`<=>n.`amount`)',
                ]
                assert 'WHERE NOT(' + ' AND '.join(expected) + ');' in query, query
                return '0\n'
            if 'o.zone_id IN (38,75)' in query: return '485\n'
            if query.startswith('SELECT COUNT(*)'): return '0\n'
            if query.startswith('SELECT rule_value'): return '7\n'
            raise AssertionError('Unexpected SQL, including any mutation: ' + query)
        stack.enter_context(patch.object(op, 'sql', side_effect=sql))
        yield runtime, data, original, destination


class FinishCache(unittest.TestCase):
    def test_finish_receipts_feed_real_open_without_removing_original_hold(self):
        with fixture() as (runtime, data, original, destination):
            held = (original / 'held-original.json').read_bytes()
            finish.finish(op)
            folder = destination / 'activation'
            self.assertFalse(runtime.opened)
            self.assertEqual(runtime.STAGE, folder)
            self.assertEqual(op.load(folder / 'stopped-state.json'), data)
            self.assertTrue((folder / 'verified-closed.json').is_file())
            self.assertTrue((folder / 'backup.json').is_file())
            self.assertEqual(runtime.events.count(('backup',)), 1)
            op.open_access()
            self.assertTrue(runtime.opened)
            self.assertTrue(op.load(folder / 'deployed.json')['gateway_open'])
            self.assertEqual((original / 'held-original.json').read_bytes(), held)
            self.assertFalse((original / 'opening.json').exists())
            self.assertFalse((original / 'deployed.json').exists())

    def test_cache_hash_count_and_unrelated_player_drift_reject_before_backup(self):
        for fault in ('hash', 'count', 'player', 'custom'):
            with self.subTest(fault=fault), fixture() as (runtime, data, original, destination):
                if fault == 'hash': data['player']['zone_state_spawns']['sha256'] = 'different'
                elif fault == 'count': data['player']['zone_state_spawns']['rows'] -= 1
                elif fault == 'player': data['player']['inventory'] = 'different'
                else: data['custom']['timers'] = 'different'
                with self.assertRaises(AssertionError): finish.finish(op)
                self.assertFalse(destination.exists())
                self.assertEqual(runtime.events, [])

    def test_failed_backup_holds_without_retrying_or_overwriting_receipts(self):
        with fixture() as (runtime, data, original, destination):
            def failed_backup():
                runtime.events.append(('backup',))
                raise RuntimeError('backup failed')
            with patch.object(runtime, 'database_backup', side_effect=failed_backup):
                with self.assertRaises(RuntimeError): finish.finish(op)
            self.assertTrue(list((destination / 'activation').glob('held-*.json')))
            self.assertTrue((original / 'held-original.json').is_file())
            self.assertFalse(runtime.opened)
            self.assertFalse(runtime.running_services['game'])
            with self.assertRaises(AssertionError): finish.finish(op)
            self.assertEqual(runtime.events.count(('backup',)), 1)

    def test_failed_start_holds_both_services_in_finish_operation_folder(self):
        with fixture() as (runtime, data, original, destination):
            def fail(args):
                if args[0] == 'up' and args[-1] == 'game': raise RuntimeError('start failed')
            runtime.fail = fail
            with self.assertRaises(RuntimeError): finish.finish(op)
            self.assertFalse(runtime.running_services['game'])
            self.assertFalse(runtime.running_services['gateway'])
            self.assertTrue(list((destination / 'activation').glob('held-*.json')))
            with self.assertRaises(FileNotFoundError): op.open_access()
            self.assertFalse(runtime.opened)

    def test_state_change_after_finish_prevents_real_open(self):
        with fixture() as (runtime, data, original, destination):
            finish.finish(op)
            data['custom']['timers'] = 'unexpected change'
            with self.assertRaises(AssertionError): op.open_access()
            self.assertFalse(runtime.opened)
            self.assertFalse(runtime.running_services['game'])
            self.assertTrue(list((destination / 'activation').glob('held-*.json')))


if __name__ == '__main__':
    unittest.main()

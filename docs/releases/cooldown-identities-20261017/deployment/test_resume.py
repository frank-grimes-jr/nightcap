"""Offline tests for the exact held-release continuation; no production access."""
import contextlib
import copy
import gzip
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
if os.name == 'nt':
    sys.modules.setdefault('fcntl', types.SimpleNamespace(LOCK_EX=2, LOCK_NB=4, flock=lambda *a: None))
spec = importlib.util.spec_from_file_location('resume_under_test', Path(__file__).with_name('resume.py'))
resume = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resume)


@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix='cooldown-resume-test-') as directory, contextlib.ExitStack() as stack:
        stage = Path(directory)
        evidence, private, recovery = stage / 'evidence', stage / 'private', stage / 'resume'
        for path in (evidence, private, recovery): path.mkdir()
        (recovery / 'manifest.json').write_text('{}')
        events, state = [], {'game': False, 'gateway': False}
        original = {'player': {'character_data': {'rows': 31, 'sha256': resume.BEFORE_SHA}, 'inventory': {'rows': 3, 'sha256': 'inventory'}}, 'custom': {'audit': 'same'}}
        current = copy.deepcopy(original)
        current['player']['character_data']['sha256'] = resume.AFTER_SHA
        def save(name, value, secret=False):
            with ((private if secret else evidence) / name).open('x') as stream: json.dump(value, stream)
        def load(name, secret=False): return json.loads(((private if secret else evidence) / name).read_text())
        def stopped(): assert state == {'game': False, 'gateway': False}
        def preserve(expected):
            assert not state['gateway'], 'Saved-player comparison after opening'
            assert current == expected
        def query(statement):
            events.append(('sql', statement))
            if statement.startswith('SELECT id,zone_id'): return '27\t36\t0\t35\t-82\t3\t0'
            if statement.startswith('SELECT COUNT(*)'): return '0'
            assert statement == 'FORWARD' and (evidence / 'migration-attempted.json').exists()
            stopped()
            return ''
        def compose(*args):
            events.append(('compose',) + args)
            state[args[-1]] = args[0] == 'up'
        def hold(reason):
            compose('stop', 'gateway'); compose('stop', '-t', '90', 'game')
            save('held-' + str(time.time_ns()) + '.json', {'reason': reason})
        def backup():
            events.append(('backup', runtime.STAGE))
            path = runtime.STAGE / 'private-backup' / 'peq-before.sql.gz'
            path.parent.mkdir()
            content = b'x' * 1000001 + b'\n-- Dump completed on test\n'
            with gzip.open(path, 'wb') as stream: stream.write(content)
            return {'path': str(path), 'sha256': real_sha(path), 'compressed_bytes': path.stat().st_size,
                    'uncompressed_bytes': len(content), 'gzip_integrity': 'passed'}
        runtime = types.SimpleNamespace(STAGE=stage, database_backup=backup, compose=compose,
            select=lambda image: events.append(('select', image)),
            state=lambda service: {'State': {'Running': state[service]}},
            compact=lambda service: {'id': service, 'running': state[service]},
            running=lambda *a: {'started_at': '2026-10-18T10:00:00Z'}, closed_ports=Mock())
        op = types.SimpleNamespace(EVIDENCE=evidence, PRIVATE=private, ROOT=stage, SCRATCH='scratch', r=runtime,
            save=save, load=load, stopped=stopped, preserved=preserve, sql=Mock(side_effect=query), hold=hold,
            manifest=Mock(return_value={'client_release': 2026101801, 'client_channel_sha256': 'channel'}),
            migration=types.SimpleNamespace(sql=lambda c, d, rollback=False: 'REVERSE' if rollback else 'FORWARD'),
            timers=Mock(return_value=[[27, 1001, 100, 300, 1]]), item_recasts=Mock(return_value=[]),
            market_state=Mock(return_value=['80']), untouched=Mock(), health=Mock(),
            verify_market=Mock(return_value={'before': ['80'], 'after': ['81']}), verify_migration=Mock(return_value=15),
            binaries=Mock(return_value={'zone': 'candidate'}), time=types.SimpleNamespace(sleep=Mock()),
            shutil=types.SimpleNamespace(disk_usage=lambda path: types.SimpleNamespace(free=10 * 1024**3)))
        real_sha = resume.sha
        def digest(path):
            special = {resume.HOLD_NAME: resume.HOLD_SHA, 'character-backup-diff.json': resume.DIFF_SHA, 'catalog.json': resume.CATALOG_SHA}
            return special.get(path.name) or real_sha(path)
        for name, value in {'STAGE': stage, 'RECOVERY': recovery, 'op': op, 'sha': digest}.items():
            stack.enter_context(patch.object(resume, name, value))
        stack.enter_context(patch.object(resume, 'manifest', return_value={}))
        save('preflight.json', {'manifest_sha256': resume.ORIGINAL_MANIFEST, 'new_image_id': 'candidate', 'cache_sha256': 'cache'})
        save('activation-started.json', {}); save('shutdown.json', {})
        save('stopped-data.json', original, True)
        save('stopped-timers.json', op.timers(), True); save('stopped-item-recasts.json', [], True)
        save('market-before.json', ['80'])
        save(resume.HOLD_NAME, {'both_stopped': True, 'running': {'gateway': False, 'game': False}, 'database_restored': False})
        save('character-backup-diff.json', resume.EXPECTED_DIFF, True)
        save('catalog.json', {}, True)
        (private / 'forward.sql').write_text('FORWARD'); (private / 'rollback.sql').write_text('REVERSE')
        save('migration-inputs.json', {'catalog_sha256': resume.CATALOG_SHA, 'forward_sha256': real_sha(private / 'forward.sql'), 'rollback_sha256': real_sha(private / 'rollback.sql')})
        save('stopped-migration-rehearsal.json', {'passed': True, 'catalog_sha256': resume.CATALOG_SHA, 'new_timer_rows': 15, 'live_sql_modified': False})
        save('backup.json', backup())
        events.clear()
        yield types.SimpleNamespace(op=op, events=events, state=state, data=current, stage=stage, recovery=recovery)


class RecoveryTests(unittest.TestCase):
    def test_success_preserves_port_original_receipts_and_separate_backup(self):
        with fixture() as f:
            old_data = (f.op.PRIVATE / 'stopped-data.json').read_bytes()
            old_hold = (f.op.EVIDENCE / resume.HOLD_NAME).read_bytes()
            resume.continue_activation()
            self.assertEqual(f.state, {'game': True, 'gateway': False})
            self.assertEqual([event for event in f.events if event[0] == 'backup'], [('backup', f.recovery)])
            self.assertEqual(f.op.r.STAGE, f.stage)
            self.assertEqual(f.events.count(('sql', 'FORWARD')), 1)
            self.assertEqual([e for e in f.events if e[0] == 'select'], [('select', 'candidate')])
            resume.open_access()
            self.assertTrue(f.state['gateway'])
            self.assertEqual((f.op.PRIVATE / 'stopped-data.json').read_bytes(), old_data)
            self.assertEqual((f.op.EVIDENCE / resume.HOLD_NAME).read_bytes(), old_hold)
            activated = f.op.load('activated.json')
            self.assertTrue(activated['authorized_port_preserved'])
            self.assertEqual(activated['client_release'], 2026101801)
            self.assertFalse(activated['database_restored'])
            self.assertFalse(activated['owner_gameplay_accepted'])

    def test_unknown_character_change_or_wrong_instance_fails_before_backup(self):
        for failure in ('current', 'diff', 'instance', 'other-player'):
            with self.subTest(failure=failure), fixture() as f:
                if failure == 'current': f.data['player']['character_data']['sha256'] = 'another change'
                elif failure == 'other-player': f.data['player']['inventory']['sha256'] = 'changed'
                elif failure == 'diff':
                    value = copy.deepcopy(resume.EXPECTED_DIFF)
                    value['differences'][0]['columns']['level'] = {'before': '1', 'now': '2'}
                    (f.op.PRIVATE / 'character-backup-diff.json').write_text(json.dumps(value))
                else:
                    original = f.op.sql.side_effect
                    f.op.sql.side_effect = lambda q: '27\t36\t1\t35\t-82\t3\t0' if q.startswith('SELECT id,zone_id') else original(q)
                with self.assertRaises(AssertionError): resume.continue_activation()
                self.assertFalse(any(e[0] == 'backup' for e in f.events))
                self.assertNotIn(('sql', 'FORWARD'), f.events)

    def test_preimage_or_live_migration_or_rehearsal_drift_blocks_resume(self):
        for failure in ('timers', 'items', 'marker', 'live-tables', 'high-keys', 'scratch', 'rehearsal'):
            with self.subTest(failure=failure), fixture() as f:
                if failure == 'timers': f.op.timers.return_value = []
                elif failure == 'items': f.op.item_recasts.return_value = [[27, 200, 999]]
                elif failure == 'marker': f.op.save('migration-attempted.json', {})
                elif failure == 'rehearsal':
                    path = f.op.EVIDENCE / 'stopped-migration-rehearsal.json'
                    value = json.loads(path.read_text()); value['passed'] = False; path.write_text(json.dumps(value))
                else:
                    original = f.op.sql.side_effect
                    match = {'live-tables': 'information_schema.TABLES', 'high-keys': 'type>=1048576', 'scratch': 'information_schema.SCHEMATA'}[failure]
                    f.op.sql.side_effect = lambda q: '1' if match in q else original(q)
                with self.assertRaises(AssertionError): resume.continue_activation()
                self.assertNotIn(('sql', 'FORWARD'), f.events)

    def test_supplemental_backup_failure_restores_destination_and_holds(self):
        with fixture() as f, patch.object(f.op.r, 'database_backup', side_effect=RuntimeError('backup failed')):
            with self.assertRaisesRegex(RuntimeError, 'backup failed'): resume.continue_activation()
            self.assertEqual(f.op.r.STAGE, f.stage)
            self.assertEqual(f.state, {'game': False, 'gateway': False})
            self.assertNotIn(('sql', 'FORWARD'), f.events)
            with self.assertRaises(AssertionError): resume.continue_activation()

    def test_postbackup_drift_is_rechecked_before_migration(self):
        with fixture() as f:
            original = f.op.r.database_backup
            def backup():
                value = original(); f.data['player']['inventory']['sha256'] = 'drift'; return value
            f.op.r.database_backup = backup
            with self.assertRaises(AssertionError): resume.continue_activation()
            self.assertNotIn(('sql', 'FORWARD'), f.events)
            self.assertEqual(f.state, {'game': False, 'gateway': False})

    def test_lost_commit_ack_never_replays_or_selects_any_image(self):
        with fixture() as f:
            original = f.op.sql.side_effect
            def query(statement):
                result = original(statement)
                if statement == 'FORWARD': raise RuntimeError('commit acknowledgment lost')
                return result
            f.op.sql.side_effect = query
            with self.assertRaisesRegex(RuntimeError, 'acknowledgment lost'): resume.continue_activation()
            self.assertEqual(f.state, {'game': False, 'gateway': False})
            self.assertTrue((f.op.EVIDENCE / 'migration-attempted.json').exists())
            with self.assertRaises(AssertionError): resume.continue_activation()
            self.assertEqual(f.events.count(('sql', 'FORWARD')), 1)
            self.assertFalse(any(e[0] == 'select' for e in f.events))

    def test_new_hold_before_resume_or_open_is_rejected_and_original_retained(self):
        for phase in ('resume', 'open'):
            with self.subTest(phase=phase), fixture() as f:
                if phase == 'open': resume.continue_activation()
                f.op.save('held-new.json', {})
                with self.assertRaisesRegex(AssertionError, 'New or missing hold'):
                    (resume.continue_activation if phase == 'resume' else resume.open_access)()
                self.assertFalse(f.state['gateway'])
                self.assertTrue((f.op.EVIDENCE / resume.HOLD_NAME).exists())

    def test_open_failure_holds_both_before_and_after_gateway_request(self):
        for failure in ('preimage', 'opening', 'post-open'):
            with self.subTest(failure=failure), fixture() as f:
                resume.continue_activation()
                if failure == 'preimage': f.data['player']['inventory']['sha256'] = 'changed'
                elif failure == 'opening':
                    compose = f.op.r.compose
                    def fail(*args):
                        compose(*args)
                        if args[0] == 'up': raise RuntimeError('opening acknowledgment lost')
                    f.op.r.compose = fail
                else:
                    f.op.untouched.side_effect = lambda p: (_ for _ in ()).throw(RuntimeError('post-open drift')) if f.state['gateway'] else None
                with self.assertRaises((AssertionError, RuntimeError)): resume.open_access()
                self.assertEqual(f.state, {'game': False, 'gateway': False})
                with self.assertRaises(AssertionError): resume.open_access()
                self.assertEqual(f.events.count(('sql', 'FORWARD')), 1)

    def test_modified_saved_sql_and_corrupt_original_backup_are_rejected(self):
        for failure in ('sql', 'backup'):
            with self.subTest(failure=failure), fixture() as f:
                path = f.op.PRIVATE / 'forward.sql' if failure == 'sql' else f.stage / 'private-backup' / 'peq-before.sql.gz'
                path.write_bytes(b'altered')
                with self.assertRaises(AssertionError): resume.continue_activation()
                self.assertNotIn(('sql', 'FORWARD'), f.events)


if __name__ == '__main__':
    unittest.main(verbosity=2)

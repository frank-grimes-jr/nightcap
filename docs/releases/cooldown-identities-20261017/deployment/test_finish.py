"""Offline checks for finishing a committed migration with exhausted market pools."""
import contextlib
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
helper = HERE / 'test_resume.py'
if not helper.exists(): helper = HERE.parent / 'resume' / 'test_resume.py'
spec = importlib.util.spec_from_file_location('resume_test_support', helper)
support = importlib.util.module_from_spec(spec); spec.loader.exec_module(support)
spec = importlib.util.spec_from_file_location('finish_under_test', HERE / 'finish.py')
finish = importlib.util.module_from_spec(spec); spec.loader.exec_module(finish)

BEFORE = ['1', '1', '80', '0', '4', '2.500000', '2026-10-17 10:00:00']
FIRST = ['1', '1', '81', '0', '4', '2.500000', '2026-10-18 15:03:59']
SECOND = ['1', '1', '82', '0', '4', '2.500000', '2026-10-18 16:00:15']
SECOND_STARTED = '2026-10-18T16:00:00Z'


def actor_rows():
    return [f'{1000+i}\tfind\t{0 if i < 2 else 1}\t0' for i in range(12)] + [f'{2000+i}\t{kind}\t2\t0' for i, kind in enumerate(['sell'] * 10 + ['buy'] * 6)]


def market_op(rows=None, invalid='0\n0', total='42'):
    queries = []
    def query(q):
        queries.append(q)
        if q.startswith('SELECT COUNT(*) FROM nightcap_market_offers o'): return invalid
        if q.startswith('SELECT a.npc_id'): return '\n'.join(actor_rows() if rows is None else rows)
        assert q == 'SELECT COUNT(*) FROM nightcap_market_offers;'
        return total
    return types.SimpleNamespace(market_state=Mock(return_value=FIRST), validate_market_state=Mock(), sql=Mock(side_effect=query)), queries


class MarketTests(unittest.TestCase):
    def test_two_empty_find_slots_require_exhaustion_and_all_policy_predicates(self):
        op, queries = market_op()
        with patch.object(finish, 'op', op):
            result = finish.verify_market(BEFORE, finish.FIRST_STARTED)
        self.assertEqual((result['offers'], result['maximum_slots']), (42, 44))
        self.assertEqual(len(result['exhausted_actors']), 2)
        op.validate_market_state.assert_called_once_with(BEFORE, FIRST, finish.FIRST_STARTED)
        candidates = queries[1]
        for predicate in ('c.min_expansion<=0', 'c.max_expansion>=0', "c.pool=IF(a.kind='find','find','tunnel')",
                          'i.nodrop<>0', 'i.norent<>0', 'i.stackable=0', 'i.maxcharges=0', 'i.itemclass=0',
                          'i.questitemflag=0', 'i.attuneable=0', 'c.buy_cp<c.sell_cp', 'c.buy_cp<c.find_cp',
                          "used.kind=a.kind)<IF(a.kind='sell',3,2)", 'own.npc_id=a.npc_id AND own.item_id=c.item_id',
                          'm.item=c.item_id AND n.id=a.npc_id', 'LEFT JOIN nightcap_market_offers'):
            self.assertIn(predicate, candidates)

    def test_nonempty_pool_underfill_overfill_unknown_actor_kind_and_duplicate_actor_reject(self):
        for mutation in ('candidate', 'overfill', 'kind', 'duplicate', 'partial-buy'):
            rows = actor_rows()
            if mutation == 'candidate': rows[0] = '1000\tfind\t0\t1'
            elif mutation == 'overfill': rows[0] = '1000\tfind\t2\t0'
            elif mutation == 'kind': rows[0] = '1000\tunknown\t0\t0'
            elif mutation == 'duplicate': rows.append(rows[0])
            else: rows[-1] = '2015\tbuy\t1\t1'
            op, _ = market_op(rows=rows)
            with self.subTest(mutation=mutation), patch.object(finish, 'op', op), self.assertRaises(AssertionError):
                finish.verify_market(BEFORE, finish.FIRST_STARTED)

    def test_bad_offer_policy_duplicate_cap_total_or_epoch_reject(self):
        for failure in ('policy', 'duplicate', 'total', 'epoch'):
            op, _ = market_op(invalid='1\n0' if failure == 'policy' else '0\n1' if failure == 'duplicate' else '0\n0', total='41' if failure == 'total' else '42')
            if failure == 'epoch': op.validate_market_state.side_effect = AssertionError('epoch changed')
            with self.subTest(failure=failure), patch.object(finish, 'op', op), self.assertRaises(AssertionError):
                finish.verify_market(BEFORE, finish.FIRST_STARTED)


@contextlib.contextmanager
def fixture():
    with support.fixture() as f, contextlib.ExitStack() as stack:
        rs = support.resume
        final = f.stage / 'finish'; final.mkdir(); (final / 'manifest.json').write_text('{}')
        (f.recovery / 'evidence').mkdir()
        for name, value in [('resume-started.json', {'manifest_sha256': finish.RESUME_SHA}), ('resolved-data.json', f.data), ('supplemental-backup.json', {})]:
            (f.recovery / 'evidence' / name).write_text(json.dumps(value))
        f.op.save(finish.SECOND_HOLD, {'both_stopped': True, 'running': {'gateway': False, 'game': False}, 'database_restored': False})
        f.op.save('migration-attempted.json', f.op.load('migration-inputs.json'))
        f.op.save('migration-applied.json', {'catalog_sha256': rs.CATALOG_SHA, 'legacy_rows_preserved': 9, 'new_timer_rows': 15, 'item_records_preserved': 0})
        (f.op.EVIDENCE / 'market-before.json').write_text(json.dumps(BEFORE))
        original_sha = rs.sha
        stack.enter_context(patch.object(rs, 'sha', side_effect=lambda p: finish.SECOND_HOLD_SHA if p.name == finish.SECOND_HOLD else original_sha(p)))
        stack.enter_context(patch.object(rs, 'verify_backup'))
        for name, value in {'STAGE': f.stage, 'FINISH': final, 'rs': rs, 'op': f.op}.items(): stack.enter_context(patch.object(finish, name, value))
        stack.enter_context(patch.object(finish, 'manifest', return_value={}))
        current_start = [finish.FIRST_STARTED]
        f.op.r.state = lambda service: {'Id': finish.FIRST_GAME, 'State': {'Running': f.state[service], 'StartedAt': current_start[0]}}
        f.op.r.compact = lambda service: {'id': service, 'running': f.state[service], 'image_id': 'candidate'}
        f.op.r.running = lambda *a: {'started_at': current_start[0]}
        original_compose = f.op.r.compose
        def compose(*args):
            original_compose(*args)
            if args[0] == 'up' and args[-1] == 'game': current_start[0] = SECOND_STARTED
        f.op.r.compose = compose
        def market(before, started):
            after = FIRST if before == BEFORE else SECOND
            assert (before, started) in ((BEFORE, finish.FIRST_STARTED), (FIRST, SECOND_STARTED))
            return {'before': before, 'after': after, 'offers': 42, 'maximum_slots': 44, 'exhausted_actors': []}
        stack.enter_context(patch.object(finish, 'verify_market', side_effect=market))
        yield f


class FinishTests(unittest.TestCase):
    def assert_no_sql_replay(self, f):
        self.assertTrue(all(not (e[0] == 'sql' and not e[1].startswith('SELECT ')) for e in f.events))
        self.assertFalse(any(e[0] == 'backup' for e in f.events))

    def test_success_preserves_two_holds_records_both_rotations_and_never_replays_sql(self):
        with fixture() as f:
            before = {path.name: path.read_bytes() for path in f.op.EVIDENCE.glob('held-*.json')}
            finish.restart()
            self.assertEqual(f.state, {'game': True, 'gateway': False})
            with self.assertRaises(AssertionError): finish.restart()
            finish.open_access()
            result = f.op.load('activated.json')
            self.assertEqual(result['prior_market_rotation']['after'][2], '81')
            self.assertEqual(result['market_rotation']['after'][2], '82')
            self.assertFalse(result['migration_replayed']); self.assertFalse(result['database_restored'])
            self.assertTrue(result['authorized_port_preserved'])
            self.assertEqual(before, {path.name: path.read_bytes() for path in f.op.EVIDENCE.glob('held-*.json')})
            self.assert_no_sql_replay(f)

    def test_unknown_hold_migration_or_player_drift_blocks_restart(self):
        for failure in ('hold', 'migration', 'player', 'game'):
            with self.subTest(failure=failure), fixture() as f:
                if failure == 'hold': f.op.save('held-unexplained.json', {})
                elif failure == 'migration': f.op.verify_migration.side_effect = AssertionError('receipt mismatch')
                elif failure == 'player': f.data['player']['inventory']['sha256'] = 'drift'
                else: f.op.r.state = lambda service: {'Id': 'other game', 'State': {'Running': False, 'StartedAt': finish.FIRST_STARTED}}
                with self.assertRaises(AssertionError): finish.restart()
                self.assertFalse(any(e[0] == 'select' for e in f.events)); self.assert_no_sql_replay(f)

    def test_start_ack_or_second_rotation_failure_holds_both_no_replay(self):
        for failure in ('start', 'rotation'):
            with self.subTest(failure=failure), fixture() as f:
                if failure == 'start':
                    compose = f.op.r.compose
                    def fail(*args):
                        compose(*args)
                        if args[0] == 'up': raise RuntimeError('start acknowledgment lost')
                    f.op.r.compose = fail
                else:
                    original = finish.verify_market.side_effect
                    finish.verify_market.side_effect = lambda before, started: (_ for _ in ()).throw(RuntimeError('bad rotation')) if before == FIRST else original(before, started)
                with self.assertRaises(RuntimeError): finish.restart()
                self.assertEqual(f.state, {'game': False, 'gateway': False})
                with self.assertRaises(AssertionError): finish.restart()
                self.assert_no_sql_replay(f)

    def test_open_preimage_and_postopen_failure_hold_both_without_postopen_player_compare(self):
        for failure in ('preimage', 'post-open'):
            with self.subTest(failure=failure), fixture() as f:
                finish.restart()
                if failure == 'preimage': f.data['player']['inventory']['sha256'] = 'changed'
                else: f.op.untouched.side_effect = lambda p: (_ for _ in ()).throw(RuntimeError('post-open drift')) if f.state['gateway'] else None
                with self.assertRaises((AssertionError, RuntimeError)): finish.open_access()
                self.assertEqual(f.state, {'game': False, 'gateway': False})
                with self.assertRaises(AssertionError): finish.open_access()
                self.assert_no_sql_replay(f)


if __name__ == '__main__':
    unittest.main(verbosity=2)

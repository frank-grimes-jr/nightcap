"""Exercise production stop/start failures and recovery without connecting to a server."""
import contextlib
import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('reforge_rollout', Path(__file__).with_name('rollout.py'))
op = importlib.util.module_from_spec(spec); spec.loader.exec_module(op)


class Runtime:
    def __init__(self):
        self.events = []; self.fail = None; self.image = 'old'; self.opened = False
        self.running_services = {'game': True, 'gateway': True}

    def compact(self, name):
        return {'image_id': self.image if name == 'game' else name, 'running': self.running_services.get(name, True)}

    def state(self, name):
        return {'Id': name, 'Image': self.image, 'State': {'Running': self.running_services[name], 'ExitCode': 0, 'OOMKilled': False}}

    def compose(self, *args):
        self.events.append(args)
        if args[0] == 'stop': self.running_services[args[-1]] = False
        else:
            self.running_services[args[-1]] = True
            if args[-1] == 'gateway': self.opened = True
        if self.fail: self.fail(args)

    def select(self, image):
        self.events.append(('select', image)); self.image = image

    def image_hashes(self, image): return {'bin/zone': image}
    def database_backup(self): self.events.append(('backup',)); return {'gzip_integrity': 'passed'}
    def running(self, image, binaries): return {'image_id': image, 'started_at': '2026-10-18T15:00:00Z'}
    def closed_ports(self): pass


@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
        root = Path(directory); evidence = root / 'evidence'; evidence.mkdir()
        runtime = Runtime()
        data = {'player': {'inventory': 'current-earned-items'}, 'custom': {'timers': 'current-deadlines'}}
        for name, value in {'ROOT': root, 'STAGE': root, 'EVIDENCE': evidence, 'r': runtime}.items():
            stack.enter_context(patch.object(op, name, value))
        stack.enter_context(patch.object(op, 'manifest', return_value={'base_hashes': {'bin/zone': 'old'}, 'client_channel_sha256': 'client'}))
        stack.enter_context(patch.object(op, 'sha', return_value='digest'))
        stack.enter_context(patch.object(op, 'untouched'))
        stack.enter_context(patch.object(op, 'health'))
        stack.enter_context(patch.object(op, 'validate_closed_recovery'))
        stack.enter_context(patch.object(op, 'guard_routines'))
        stack.enter_context(patch.object(op, 'apply_content'))
        stack.enter_context(patch.object(op, 'content_mode', return_value='after'))
        stack.enter_context(patch.object(op, 'aa_state', return_value={'rows':1,'sha256':'aa'}))
        stack.enter_context(patch.object(op, 'routing', return_value={'classic':50}))
        stack.enter_context(patch.object(op, 'caches', return_value={'items':'items','spells':'spells'}))
        stack.enter_context(patch.object(op, 'binaries', side_effect=lambda recovery=False: {'zone': 'old' if recovery else 'new'}))
        stack.enter_context(patch.object(op, 'saved_state', side_effect=lambda: copy.deepcopy(data)))
        stack.enter_context(patch.object(op, 'market', return_value=['before']))
        stack.enter_context(patch.object(op, 'verify_market', return_value={'rotation': 'once'}))
        stack.enter_context(patch.object(op.time, 'sleep'))
        op.save(evidence / 'preflight.json', {'manifest_sha256': 'digest', 'old_image_id': 'old', 'new_image_id': 'new',
                'services': {s: runtime.compact(s) for s in ('game', 'gateway')}})
        yield runtime, data, evidence


class ImageBuild(unittest.TestCase):
    def test_authenticated_local_tag_builds_without_registry_pull(self):
        runtime = Mock(); runtime.out.side_effect = ['sha256:base', 'sha256:base', 'sha256:new']
        with tempfile.TemporaryDirectory() as directory, patch.object(op, 'STAGE', Path(directory)), patch.object(op, 'r', runtime):
            self.assertEqual(op.build_image({'base_image_id': 'sha256:base'}), 'sha256:new')
            self.assertIn('FROM nightcap-game:all-class-aa-20261019-baseline\n', (Path(directory) / 'Dockerfile').read_text())
            runtime.call.assert_any_call('docker', 'tag', 'sha256:base', 'nightcap-game:all-class-aa-20261019-baseline')
            self.assertIn('--pull=false', runtime.call.call_args.args)

    def test_tag_drift_before_build_rejects_without_building(self):
        runtime = Mock(); runtime.out.return_value = 'sha256:other'
        with tempfile.TemporaryDirectory() as directory, patch.object(op, 'STAGE', Path(directory)), patch.object(op, 'r', runtime):
            with self.assertRaises(AssertionError): op.build_image({'base_image_id': 'sha256:base'})
            self.assertEqual(runtime.call.call_count, 1)

    def test_tag_drift_during_build_rejects_candidate(self):
        runtime = Mock(); runtime.out.side_effect = ['sha256:base', 'sha256:other']
        with tempfile.TemporaryDirectory() as directory, patch.object(op, 'STAGE', Path(directory)), patch.object(op, 'r', runtime):
            with self.assertRaises(AssertionError): op.build_image({'base_image_id': 'sha256:base'})
            self.assertEqual(runtime.out.call_count, 2)


class MarketValidation(unittest.TestCase):
    def verify(self, count=42, capacity=50, invalid='0\n0\n0\n', epoch=81):
        before = ['1','1','80','0','4','2.500000','2026-10-17 15:00:00']
        after = ['1','1','81','0','4','2.500000','2026-10-18 15:00:01']
        def query(q):
            if 'COALESCE(SUM(' in q: return str(capacity)
            if q == 'SELECT COUNT(*) FROM nightcap_market_offers;': return str(count)
            if 'GROUP BY epoch;' in q: return f'{epoch}\t{count}' if count else ''
            self.assertIn("HAVING n>IF(kind='find',1,2)", q)
            self.assertIn('o.remaining<>1', q)
            self.assertIn('i.questitemflag<>0', q)
            return invalid
        with patch.object(op, 'market', return_value=after), patch.object(op, 'sql', side_effect=query):
            return op.verify_market(before, '2026-10-18T15:00:00Z')

    def test_partial_or_exhausted_stock_is_valid(self):
        self.assertEqual(self.verify()['offers'], 42)
        self.assertEqual(self.verify(count=0)['offers'], 0)
        self.assertEqual(self.verify(count=50)['offers'], 50)

    def test_overcapacity_wrong_epoch_and_invalid_offers_are_rejected(self):
        for args in ({'count':51}, {'epoch':80}, {'invalid':'1\n0\n0\n'},
                     {'invalid':'0\n1\n0\n'}, {'invalid':'0\n0\n1\n'}):
            with self.subTest(args=args), self.assertRaises(AssertionError): self.verify(**args)


class FailureBoundaries(unittest.TestCase):
    def test_success_preserves_current_state_and_requires_separate_open(self):
        with fixture() as (runtime, data, evidence):
            op.activate()
            self.assertFalse(runtime.opened)
            self.assertEqual(op.load(evidence / 'activation/stopped-state.json'), data)
            self.assertLess(runtime.events.index(('backup',)), runtime.events.index(('select', 'new')))
            op.open_access()
            self.assertTrue(runtime.opened)
            self.assertTrue(op.load(evidence / 'activation/deployed.json')['gateway_open'])

    def test_stop_start_backup_and_preservation_failures_hold_both_services(self):
        for failure in ('stop', 'start', 'backup', 'state', 'market', 'health', 'sql'):
            with self.subTest(failure=failure), fixture() as (runtime, data, evidence), contextlib.ExitStack() as stack:
                if failure in ('stop', 'start'):
                    fired = [False]
                    def fail(args):
                        match = args[0] == ('stop' if failure == 'stop' else 'up')
                        if match and not fired[0]: fired[0] = True; raise RuntimeError(failure)
                    runtime.fail = fail
                elif failure == 'backup':
                    stack.enter_context(patch.object(runtime, 'database_backup', side_effect=RuntimeError('backup')))
                elif failure == 'state':
                    stack.enter_context(patch.object(op, 'saved_state', side_effect=[data, {'changed': True}]))
                else:
                    stack.enter_context(patch.object(op, 'apply_content' if failure == 'sql' else 'verify_market' if failure == 'market' else 'health', side_effect=RuntimeError(failure)))
                with self.assertRaises((RuntimeError, AssertionError)): op.activate()
                self.assertFalse(runtime.running_services['game']); self.assertFalse(runtime.running_services['gateway'])
                self.assertFalse(runtime.opened)
                self.assertTrue(list((evidence / 'activation').glob('held-*.json')))
                with self.assertRaises(AssertionError): op.activate()

    def test_stale_manifest_or_runtime_is_rejected_before_stopping(self):
        for failure in ('manifest', 'runtime'):
            with self.subTest(failure=failure), fixture() as (runtime, data, evidence), contextlib.ExitStack() as stack:
                if failure == 'manifest': stack.enter_context(patch.object(op, 'sha', return_value='changed'))
                else: runtime.image = 'unrelated-release'
                with self.assertRaises(AssertionError): op.activate()
                self.assertEqual(runtime.events, [])

    def test_changed_closed_state_cannot_open(self):
        with fixture() as (runtime, data, evidence):
            op.activate(); data['player']['inventory'] = 'concurrent-change'
            with self.assertRaises(AssertionError): op.open_access()
            self.assertFalse(runtime.opened); self.assertFalse(runtime.running_services['game'])

    def test_uncertain_gateway_open_is_held_and_not_replayed(self):
        with fixture() as (runtime, data, evidence):
            op.activate()
            def fail(args):
                if args[0] == 'up' and args[-1] == 'gateway': raise RuntimeError('lost acknowledgment')
            runtime.fail = fail
            with self.assertRaises(RuntimeError): op.open_access()
            self.assertTrue(runtime.opened)
            self.assertFalse(runtime.running_services['gateway']); self.assertFalse(runtime.running_services['game'])
            with self.assertRaises(AssertionError): op.open_access()

    def test_recovery_preserves_subsequent_earned_state_and_current_timers(self):
        with fixture() as (runtime, data, evidence):
            op.activate(); op.open_access()
            data['player']['inventory'] = 'later-earned-items'
            data['custom']['timers'] = 'later-deadlines'
            op.activate(True)
            self.assertEqual(runtime.image, 'old')
            self.assertEqual(op.load(evidence / 'recovery/stopped-state.json'), data)
            op.open_access(True)
            self.assertFalse(op.load(evidence / 'recovery/deployed.json')['database_restored'])
            self.assertEqual(runtime.events.count(('backup',)), 2)

    def test_recovery_refuses_unrelated_newer_release(self):
        with fixture() as (runtime, data, evidence):
            op.activate(); runtime.events.clear(); runtime.image = 'newer-unrelated-release'
            with self.assertRaises(AssertionError): op.activate(True)
            self.assertEqual(runtime.events, [])




class ContentTransition(unittest.TestCase):
    def test_unknown_aa_image_is_rejected(self):
        with patch.object(op,'aa_state',return_value={'hash':'unknown'}):
            with self.assertRaises(AssertionError): op.content_mode({'aa_before':{'hash':'before'},'aa_after':{'hash':'after'}})

    def test_forward_reverse_and_uncertain_acknowledgment(self):
        for recovery in (False,True):
            with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
                root=Path(directory); folder=root/('recovery' if recovery else 'activation'); folder.mkdir()
                stack.enter_context(patch.object(op,'STAGE',root)); stack.enter_context(patch.object(op,'EVIDENCE',root))
                stack.enter_context(patch.object(op,'guard_routines'))
                state={'hash':'after' if recovery else 'before'}
                target={'hash':'before' if recovery else 'after'}
                stack.enter_context(patch.object(op,'aa_state',side_effect=lambda:dict(state)))
                direction='rollback' if recovery else 'forward'
                (root/('healing-boon-'+direction+'.sql')).write_text('guarded '+direction)
                def execute(statement):
                    self.assertEqual(statement,'guarded '+direction)
                    self.assertTrue((folder/'sql-attempted.json').exists())
                    state.update(target)
                query=stack.enter_context(patch.object(op,'sql',side_effect=execute))
                op.apply_content(folder,{'aa_before':{'hash':'before'},'aa_after':{'hash':'after'}},recovery)
                self.assertEqual(op.load(folder/'sql-committed.json')['after'],target)
                with self.assertRaises(FileExistsError):op.apply_content(folder,{'aa_before':{'hash':'before'},'aa_after':{'hash':'after'}},recovery)
                self.assertEqual(query.call_count,1)

    def test_lost_sql_ack_is_not_replayed_by_recovery(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            root=Path(directory); (root/'activation').mkdir(); (root/'recovery').mkdir()
            (root/'healing-boon-forward.sql').write_text('forward')
            stack.enter_context(patch.object(op,'STAGE',root)); stack.enter_context(patch.object(op,'EVIDENCE',root))
            stack.enter_context(patch.object(op,'guard_routines')); stack.enter_context(patch.object(op,'aa_state',return_value='before'))
            query=stack.enter_context(patch.object(op,'sql',side_effect=RuntimeError('lost acknowledgement')))
            p={'aa_before':'before','aa_after':'after'}
            with self.assertRaises(RuntimeError):op.apply_content(root/'activation',p,False)
            self.assertFalse((root/'activation/sql-committed.json').exists())
            with self.assertRaises(AssertionError):op.apply_content(root/'recovery',p,True)
            self.assertEqual(query.call_count,1)

    def test_partial_afterimage_has_no_committed_receipt(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            root=Path(directory); folder=root/'activation'; folder.mkdir()
            (root/'healing-boon-forward.sql').write_text('forward')
            stack.enter_context(patch.object(op,'STAGE',root)); stack.enter_context(patch.object(op,'EVIDENCE',root))
            stack.enter_context(patch.object(op,'guard_routines')); stack.enter_context(patch.object(op,'aa_state',return_value='drift'))
            stack.enter_context(patch.object(op,'sql'))
            with self.assertRaises(AssertionError):op.apply_content(folder,{'aa_after':'after'},False)
            self.assertTrue((folder/'sql-attempted.json').exists())
            self.assertFalse((folder/'sql-committed.json').exists())


class ClosedRecovery(unittest.TestCase):
    def test_closed_drift_cannot_become_new_baseline(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(op,'EVIDENCE',Path(directory)):
            original=Path(directory)/'activation'; original.mkdir()
            op.save(original/'stopped-state.json',{'aa':'earned','timers':'deadlines'})
            with self.assertRaisesRegex(AssertionError,'closed-access'):
                op.validate_closed_recovery({}, {'aa':'lost','timers':'deadlines'})

    def test_first_market_rotation_must_be_authenticated(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(op,'EVIDENCE',Path(directory)), patch.object(op,'r') as runtime:
            original=Path(directory)/'activation'; original.mkdir()
            op.save(original/'stopped-state.json',{'aa':'earned'})
            op.save(original/'market-before.json',['epoch-before'])
            runtime.state.return_value={'State':{'StartedAt':'candidate-start'}}
            with patch.object(op,'verify_market',side_effect=AssertionError('bad first rotation')) as verify:
                with self.assertRaisesRegex(AssertionError,'bad first rotation'):
                    op.validate_closed_recovery({'services':{'game':{'started_at':'baseline-start'}}},{'aa':'earned'})
                verify.assert_called_once_with(['epoch-before'],'candidate-start')

    def test_open_attempt_preserves_subsequent_play(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(op,'EVIDENCE',Path(directory)):
            original=Path(directory)/'activation'; original.mkdir()
            op.save(original/'opening.json',{})
            op.save(original/'stopped-state.json',{'aa':'old'})
            op.validate_closed_recovery({}, {'aa':'new-earned'})

    def test_recovery_drift_stops_before_backup_sql_or_start(self):
        with fixture() as (runtime,data,evidence):
            op.activate(); runtime.events.clear()
            with patch.object(op,'validate_closed_recovery',side_effect=AssertionError('drift')), patch.object(op,'apply_content') as query:
                with self.assertRaises(AssertionError):op.activate(True)
                query.assert_not_called()
                self.assertNotIn(('backup',),runtime.events)
                self.assertFalse(any(e[0] in ('up','select') for e in runtime.events))
                self.assertFalse(runtime.opened)



class CatalogBaseline(unittest.TestCase):
    def test_candidate_fixture_normalizes_only_boon_preimage(self):
        import gzip,json
        candidate={'aa_ability':[{'id':389,'classes':550,'name':'Healing Boon'},{'id':1,'classes':7,'name':'Other'}]}
        before=copy.deepcopy(candidate);before['aa_ability'][0]['classes']=518
        with tempfile.TemporaryDirectory() as directory, patch.object(op,'STAGE',Path(directory)):
            (Path(directory)/'aa-catalog.json.gz').write_bytes(gzip.compress(json.dumps(candidate).encode()))
            with patch.object(op,'sql',return_value='\n'.join(json.dumps(r) for r in before['aa_ability'])):op.verify_catalog()
            before['aa_ability'][1]['classes']=9
            with patch.object(op,'sql',return_value='\n'.join(json.dumps(r) for r in before['aa_ability'])):
                with self.assertRaisesRegex(AssertionError,'differs'):op.verify_catalog()

if __name__ == '__main__': unittest.main()
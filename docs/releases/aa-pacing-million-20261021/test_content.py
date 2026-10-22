"""Exact rule and quest transitions, including uncertain writes and safe recovery."""
import contextlib
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('candidate',Path(__file__).with_name('rollout.py'))
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)

@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as tmp,contextlib.ExitStack() as stack:
        root=Path(tmp);stage=root/'stage';stage.mkdir()
        if not hasattr(op.os,'chown'):stack.enter_context(patch.object(op.os,'chown',create=True))
        state={'rules':'before'}
        p={'rules_before':'before','rules_after':'after','runtime':{},'quests_before':{},'quests_after':{}}
        for name in op.QUESTS:
            for base,data in [(root/'data/server',b'old'),(stage/'previous',b'old'),(stage,b'new')]:
                path=base/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            p['runtime'][name]=p['quests_before'][name]=op.sha(root/'data/server'/name)
            p['quests_after'][name]=op.sha(stage/name)
        runtime=type('Runtime',(),{'runtime':lambda self:{name:op.sha(root/'data/server'/name) for name in op.QUESTS}})()
        for k,v in [('ROOT',root),('STAGE',stage),('r',runtime)]:
            stack.enter_context(patch.object(op,k,v))
        stack.enter_context(patch.object(op,'rules',side_effect=lambda:state['rules']))
        def sql(q):
            assert q.startswith('START TRANSACTION; UPDATE rule_values SET rule_value=')
            state['rules']='before' if "SET rule_value='40000'" in q else 'after'
            return '1\n'
        stack.enter_context(patch.object(op,'sql',side_effect=sql))
        folder=stage/'activation';folder.mkdir()
        yield root,stage,p,state,folder

class Content(unittest.TestCase):
    def test_forward_and_inverse_preserve_other_runtime_and_exact_rule_images(self):
        with fixture() as (root,stage,p,state,folder):
            op.apply_content(folder,p,False);op.verify_rules(p,'after');op.verify_runtime(p,'after')
            recovery=stage/'recovery';recovery.mkdir()
            op.apply_content(recovery,p,True);op.verify_rules(p,'before');op.verify_runtime(p,'before')
    def test_unknown_rule_or_quest_image_rejected_before_attempt(self):
        for kind in ('rule','quest'):
            with fixture() as (root,stage,p,state,folder):
                if kind=='rule':state['rules']='external edit'
                else:(root/'data/server'/op.QUESTS[0]).write_bytes(b'external')
                with self.assertRaises(AssertionError):op.apply_content(folder,p,False)
                self.assertFalse((folder/'content-attempted.json').exists())
    def test_uncertain_commit_not_replayed_and_recovery_preserves_new_state(self):
        with fixture() as (root,stage,p,state,folder):
            def uncertain(q):
                state['rules']='after';raise RuntimeError('lost response after commit')
            with patch.object(op,'sql',side_effect=uncertain):
                with self.assertRaises(RuntimeError):op.apply_content(folder,p,False)
            self.assertTrue((folder/'content-attempted.json').exists())
            self.assertFalse((folder/'content-committed.json').exists())
            with self.assertRaises(FileExistsError):op.apply_content(folder,p,False)
            recovery=stage/'recovery';recovery.mkdir()
            op.apply_content(recovery,p,True);op.verify_rules(p,'before')
    def test_partial_quest_transition_recoverable_without_reapplying_unknown_content(self):
        with fixture() as (root,stage,p,state,folder):
            state['rules']='after'
            (root/'data/server'/op.QUESTS[0]).write_bytes(b'new')
            op.apply_content(folder,p,True);op.verify_runtime(p,'before')
    def test_corrupt_saved_quest_blocks_recovery_before_replacement(self):
        with fixture() as (root,stage,p,state,folder):
            (stage/'previous'/op.QUESTS[0]).write_bytes(b'corrupt')
            with self.assertRaises(AssertionError):op.apply_content(folder,p,True)
            self.assertEqual((root/'data/server'/op.QUESTS[0]).read_bytes(),b'old')
    def test_closed_recovery_cannot_rebaseline_unexplained_player_changes(self):
        with fixture() as (root,stage,p,state,folder),patch.object(op,'EVIDENCE',stage):
            op.save(folder/'stopped-state.json',{'inventory':'earned'})
            with self.assertRaisesRegex(AssertionError,'Unexplained'):op.validate_closed_recovery(p,{'inventory':'different'})

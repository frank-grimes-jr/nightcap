"""Offline resume failure injection; no host/runtime mutation."""
import contextlib
import copy
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import preflight_resume as resume
import test_rollout as harness


@contextlib.contextmanager
def fixture():
    with harness.lifecycle() as f, contextlib.ExitStack() as stack:
        op = harness.op
        (f.evidence/'preflight.json').unlink()
        original = {k:copy.deepcopy(v) for k,v in f.plan.items() if k != 'image'}
        original['checks'] = {'required':3}
        original['manifest_sha256'] = 'manifest-pin'
        harness.receipt(f.evidence/'preflight-started.json', original)
        (op.STAGE/'preflight.log').write_text('assert shutil.disk_usage(ROOT).free>=RESERVE\nAssertionError\n')
        (op.STAGE/'rollout.py').write_text('authenticated operator')
        (op.STAGE/'manifest.json').write_text('authenticated manifest')
        stack.enter_context(patch.object(resume,'MANIFEST_SHA','manifest-pin'))
        # Target hashes are separately tested with real hashing below; changing
        # historical production pins must never be necessary to run this harness.
        stack.enter_context(patch.object(resume,'authenticate'))
        image = stack.enter_context(patch.object(resume,'existing_image'))
        stack.enter_context(patch.object(resume.shutil,'disk_usage',return_value=types.SimpleNamespace(free=2**30)))
        yield types.SimpleNamespace(op=op,f=f,original=original,image=image)


class ResumeTests(unittest.TestCase):
    def test_success_retains_originals_and_does_not_build_or_transition(self):
        with fixture() as x:
            started=(x.f.evidence/'preflight-started.json').read_bytes()
            log=(x.op.STAGE/'preflight.log').read_bytes()
            resume.resume(x.op)
            self.assertEqual((x.f.evidence/'preflight-started.json').read_bytes(),started)
            self.assertEqual((x.op.STAGE/'preflight.log').read_bytes(),log)
            self.assertEqual(x.op.read(x.f.evidence/'preflight.json'),{**x.original,'image':resume.IMAGE})
            self.assertFalse(any(e[0] in ('stop','up','select','backup','install-content','install-quests') for e in x.f.runtime.events))
            x.image.assert_called_once()
            self.assertFalse(x.op.read(x.f.evidence/'preflight-resume-started.json')['rebuild'])
            with self.assertRaisesRegex(AssertionError,'Unexpected attempt'):resume.resume(x.op)

    def test_authentication_and_attempt_shape_fail_before_resume(self):
        for fault in ('hash','completed','activation','other_failure','service'):
            with self.subTest(fault=fault),fixture() as x,contextlib.ExitStack() as stack:
                if fault=='hash':stack.enter_context(patch.object(resume,'authenticate',side_effect=AssertionError('hash')))
                elif fault=='completed':harness.receipt(x.f.evidence/'preflight.json',{})
                elif fault=='activation':(x.f.evidence/'activation').mkdir()
                elif fault=='other_failure':(x.op.STAGE/'preflight.log').write_text('RuntimeError')
                else:x.f.runtime.image='unexpected'
                with self.assertRaises(AssertionError):resume.resume(x.op)
                x.image.assert_not_called()
                self.assertFalse((x.f.evidence/'preflight-resume-started.json').exists())

    def test_preflight_guard_failures_never_write_success_or_mutate_services(self):
        for fault in ('runtime','health','startup','contract','public','quests','image','preservation'):
            with self.subTest(fault=fault),fixture() as x,contextlib.ExitStack() as stack:
                failing=Mock(side_effect=AssertionError(fault))
                if fault=='runtime':stack.enter_context(patch.object(x.f.runtime,'running',failing))
                elif fault=='health':x.f.base.health.side_effect=AssertionError(fault)
                elif fault=='startup':x.f.startup.startup_guards.side_effect=AssertionError(fault)
                elif fault=='contract':stack.enter_context(patch.object(x.op,'contract',failing))
                elif fault=='public':stack.enter_context(patch.object(x.op,'public_preflight',failing))
                elif fault=='quests':stack.enter_context(patch.object(x.op,'check_quest_preimages',failing))
                elif fault=='image':x.image.side_effect=AssertionError(fault)
                else:stack.enter_context(patch.object(x.op,'unchanged',side_effect=[None,AssertionError(fault)]))
                with self.assertRaises(AssertionError):resume.resume(x.op)
                self.assertFalse((x.f.evidence/'preflight.json').exists())
                self.assertTrue(all(x.f.runtime.running_services.values()))
                self.assertTrue((x.f.evidence/'preflight-resume-started.json').exists())
                with self.assertRaisesRegex(AssertionError,'Unexpected attempt'):resume.resume(x.op)

    def test_final_reserve_failure_keeps_failed_attempt_and_no_success(self):
        with fixture() as x,patch.object(resume.shutil,'disk_usage',side_effect=[types.SimpleNamespace(free=2**30),types.SimpleNamespace(free=x.op.RESERVE-1)]):
            with self.assertRaisesRegex(AssertionError,'Final disk reserve'):resume.resume(x.op)
            self.assertFalse((x.f.evidence/'preflight.json').exists())
            self.assertFalse((x.f.evidence/'preflight-resume-verified.json').exists())
            self.assertTrue((x.f.evidence/'preflight-started.json').exists())

    def test_authenticate_rejects_file_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory).resolve()/'pin';path.write_bytes(b'original')
            digest=resume.sha(path);resume.authenticate(path,digest)
            path.write_bytes(b'changed')
            with self.assertRaises(AssertionError):resume.authenticate(path,digest)


class ImageTests(unittest.TestCase):
    def test_image_revalidation_has_no_build_tag_pull_or_service_commands(self):
        m={'base_image_id':'base','base_hashes':{'bin/zone':'old'},'candidate_hashes':{'bin/zone':'new'}}
        calls=[]
        def output(*args):
            calls.append(args)
            if '--format' in args:return 'base' if args[-1]==resume.BASE_TAG else resume.IMAGE
            if args[:3]==('docker','image','inspect'):
                return json.dumps([{'RootFS':{'Layers':['base','candidate'] if args[-1]==resume.IMAGE else ['base']}}])
            if 'ldd' in args:return 'linked'
            raise AssertionError(args)
        runtime=types.SimpleNamespace(out=Mock(side_effect=output),call=Mock(),image_hashes=lambda image:{'bin/zone':'new' if image==resume.IMAGE else 'old'})
        resume.existing_image(types.SimpleNamespace(r=runtime),m)
        commands=calls+[c.args for c in runtime.call.call_args_list]
        self.assertFalse(any(c[:2] in (('docker','build'),('docker','tag'),('docker','pull'),('docker','compose')) for c in commands))
        self.assertEqual(sum('--nightcap-crypto-self-test' in c for c in commands),2)
        self.assertTrue(all('--network' in c and c[c.index('--network')+1]=='none' for c in commands if c[:2]==('docker','run')))
        runtime.out.side_effect=lambda *args:'wrong' if '--format' in args else output(*args)
        with self.assertRaisesRegex(AssertionError,'Base tag drift'):resume.existing_image(types.SimpleNamespace(r=runtime),m)


if __name__ == '__main__':
    unittest.main(verbosity=2)

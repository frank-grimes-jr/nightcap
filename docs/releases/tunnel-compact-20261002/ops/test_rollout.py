"""Run the shared rollout failure tests through the actual compact adapter."""
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'tools/tests'))

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result

if __name__=='__main__':
    with tempfile.TemporaryDirectory() as directory:
        stage=Path(directory)
        previous=ROOT/'docs/releases/tunnel-social-20261001/ops'
        shutil.copyfile(previous/'rollout.py',stage/'social_rollout.py')
        shutil.copyfile(Path(__file__).with_name('rollout.py'),stage/'rollout.py')
        adapter=module('compact_rollout',stage/'rollout.py')
        tests=module('shared_rollout_tests',previous/'test_rollout.py')
        tests.r=adapter.ops
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(tests.RolloutTests)
        # The old social-specific fixture is covered instead by the compact
        # MariaDB rehearsal, including fresh cache/corpse/instance rollback.
        for name in unittest.defaultTestLoader.getTestCaseNames(tests.FileTests):
            if name!='test_after_start_saved_state_rejects_other_instances':suite.addTest(tests.FileTests(name))
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        sys.exit(not result.wasSuccessful())

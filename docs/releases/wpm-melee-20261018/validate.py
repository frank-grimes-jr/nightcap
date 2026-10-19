"""Run bounded candidate regression suites; local fixtures only, no install."""
import datetime
import json
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/tests')]
os.environ['NIGHTCAP_TEST_EVIDENCE']=str(HERE/'evidence')
patterns=['test_pet_armor_transfer.py','test_pet_*.py','test_doppelganger.py','test_rabid_bear.py','test_pop_progression.py',
          'test_aa_tbs_policy.py','test_aa_temporary_buffs.py','test_gameplay_policies.py',
          'test_client_gameplay_assets.py','test_client_gameplay_ui.py','test_wpm*.py',
          'test_monk_combat_reuse.py','test_cooldown_duration.py','test_multiclass_fists.py']
suite=unittest.TestSuite()
seen=set()
def add(tests):
    for test in tests:
        if isinstance(test,unittest.TestSuite):add(test)
        elif test.id() not in seen:suite.addTest(test);seen.add(test.id())
for pattern in patterns:add(unittest.defaultTestLoader.discover(str(ROOT/'tools/tests'),pattern=pattern))
with (HERE/'evidence/regression.log').open('w') as stream:
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed' if result.wasSuccessful() else 'failed',
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skipped':[{'test':test.id(),'reason':why} for test,why in result.skipped],'patterns':patterns,'database_scope':'session-local temporary tables',
        'native_client_gameplay_qa':'pending'}
(HERE/'evidence/regression.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report));sys.exit(0 if result.wasSuccessful() else 1)

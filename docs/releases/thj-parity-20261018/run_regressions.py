"""Run the combined candidate's bounded regression suite and retain exact results."""
import datetime,json,os,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
REL=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'tools/tests'),str(ROOT/'tools')]
evidence=REL/'evidence';evidence.mkdir(exist_ok=True)
os.environ['NIGHTCAP_DB_TESTS']='1'
os.environ['NIGHTCAP_TEST_EVIDENCE']=str(evidence)
os.environ['NIGHTCAP_NATIVE_SOURCE']=str(ROOT.parent/'thj-parity-native-context')
patterns=json.loads((ROOT/'docs/releases/wpm-melee-20261018/evidence/regression.json').read_text())['patterns']
patterns+=['test_thj_item_parity.py','test_thj_spell_scaling.py','test_starter_retune.py',
           'test_tier_spell_scaling.py','test_dungeon_catalog.py']
suite=unittest.TestSuite();seen=set()
def add(tests):
    for test in tests:
        if isinstance(test,unittest.TestSuite):add(test)
        elif test.id() not in seen:seen.add(test.id());suite.addTest(test)
for pattern in patterns:add(unittest.defaultTestLoader.discover(str(ROOT/'tools/tests'),pattern))
with (evidence/'regression.log').open('w') as log:
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='passed' if result.wasSuccessful() else 'failed',
    tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=[(str(t),why) for t,why in result.skipped],patterns=patterns,
    database_scope='session-local temporary tables; no live table writes',native_gameplay_acceptance='pending')
(evidence/'regression.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
if not result.wasSuccessful():print((evidence/'regression.log').read_text()[-16000:])
raise SystemExit(0 if result.wasSuccessful() else 1)

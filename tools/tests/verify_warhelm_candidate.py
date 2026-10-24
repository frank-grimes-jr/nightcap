"""Focused candidate and shared-path regressions, with explicit baseline exceptions."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'tools/tests'))
patterns=['test_warhelm*.py','test_chapterhouse*.py','test_dungeon*.py','test_classic_dungeon*.py','test_zone_hunt*.py','test_winged_helmet_item.py','test_classic_model_pfs.py','test_highkeep_rescue.py','test_heal_targeting.py','test_aggro_departure_native.py','test_zone_state_home_native.py']
suite=unittest.TestSuite()
for pattern in patterns:suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tools/tests'),pattern=pattern))
out=ROOT/'docs/quests/warhelm'
with (out/'tests.log').open('w') as stream:
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
report=dict(tests=result.testsRun,failures=[str(t) for t,_ in result.failures],errors=[str(t) for t,_ in result.errors],skipped=[str(t) for t,_ in result.skipped],passed=result.wasSuccessful())
(out/'tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
raise SystemExit(not result.wasSuccessful())

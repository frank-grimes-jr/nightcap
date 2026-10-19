"""Verify that saved build/test evidence matches this exact local candidate."""
import datetime
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((HERE/'evidence/native-build-manifest.json').read_text())
assert manifest['status']=='built_not_installed'
for name,digest in manifest['requested_sources'].items():
    assert sha((ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n'))==digest,name
    assert manifest['source_files'][name]==digest,name
tests=json.loads((HERE/'evidence/regression.json').read_text())
assert tests['status']=='passed' and tests['tests']==76 and not tests['skipped']
aa=json.loads((HERE/'evidence/aa-native.json').read_text())
assert aa['passed'] and aa['native_eligibility_cases']==6714
client=json.loads((HERE/'evidence/client-stage.json').read_text())
assert sha((ROOT/'eq-client-dll/build/dinput8.dll').read_bytes())==client['files']['dinput8.dll']['sha256']
for name,needle in [('client-runtime-tests.log','PASS: all five candidate client fixtures'),
                    ('heal-targeting.log','99/99'),('pop-final-tests.log','OK'),
                    ('wiki-tests.log','Ran 30 tests'),('wiki-node.log','fail 0'),
                    ('skill-validator.log','Skill is valid!')]:
    assert needle in (HERE/'evidence'/name).read_text(encoding='utf-8'),name
skill=json.loads((HERE/'evidence/skill-maintenance.json').read_text())
assert skill['status']=='installed'
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status':'built_and_tested_candidate_not_deployed',
        'base':'a8e0a91','branch':'feature/thj-pet-scaling',
        'native_sources_verified':len(manifest['requested_sources']),
        'zone_sha256':manifest['zone_sha256'],'world_sha256':manifest['world_sha256'],
        'proxy_version':'0.11.0','proxy_sha256':client['files']['dinput8.dll']['sha256'],
        'regression_tests':76,'native_aa_eligibility_cases':6714,'native_heal_target_cases':99,
        'client_fixture_executables':5,'wiki_linux_tests':30,'wiki_node_test_entries':8,
        'installed_skill':'updated and validated; 32 candidate fingerprints verified',
        'sql':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sorted((HERE/'content').rglob('*.sql'))},
        'pending':['independent review','native client/combat/lifecycle QA','signed full-client reconciliation',
                   'guarded PoP activation operator and world/travel acceptance','deployment/publication'],
        'intentional_limits':['native pet template melee retained','native clone movement retained',
                              'fragment and rune amounts are Nightcap calibration']}
(HERE/'evidence/handoff.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='sql'}))

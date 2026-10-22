raise SystemExit('Historical October16 verification is frozen; current evidence is in docs/dungeons/classic-rewards-20261022/.')

"""Record observed checks, verify exact pairing and retain open manual gates."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'docs/dungeons'
read=lambda name:json.loads((folder/name).read_text(encoding='utf-8'))
build=read('native-build-manifest.json')
for path,digest in build['overlay_normalized_sha256'].items():
    assert hashlib.sha256((ROOT/'server-mods/code'/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,path
checks={name:read(name) for name in ('activation-verification.json','cache-verification.json',
    'concurrency-verification.json','inventory-verification.json','quest-verification.json',
    'recovery-adapters-verification.json')}
assert all(value['status']=='passed' for value in checks.values())
rehearsal=read('rehearsal.json')
assert rehearsal['feature_encoding_explicit'] and rehearsal['database_default']=='latin1'
assert rehearsal['dangling_inventory_reference_rejected']
assert not any(read('reference-audit.json')['counts'].values())
assert rehearsal['schema_sha256']==hashlib.sha256((ROOT/'server-mods/sql/20261016_dungeons.sql').read_text().encode()).hexdigest()
assert rehearsal['migration_sha256']==hashlib.sha256((ROOT/'server-mods/sql/20261016_dungeon_content.sql').read_text().encode()).hexdigest()
assert checks['activation-verification.json']['activation_sha256']==hashlib.sha256((ROOT/'server-mods/sql/20261016_dungeon_enable.sql').read_text().encode()).hexdigest()
catalog=read('catalog.json');assert len(catalog['items'])==330
assert sum(len(d['bosses']) for d in catalog['dungeons'])==52
report=dict(date='2026-10-16',implemented=True,automated_verification='passed within the scopes below',
    source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    native_binaries=build['binaries'],native_source_files=len(build['source_files']),
    evidence={name:dict(status=value['status'],sha256=hashlib.sha256((folder/name).read_bytes()).hexdigest()) for name,value in checks.items()},
    observed_test_results=[
        dict(command="python -m unittest discover -s tools/tests -p test_dungeon*.py -v",passed=10,scope='compiled actual policy/spawn/credit functions, catalog/parser and integration guards'),
        dict(command="python -m unittest discover -s tools/tests -p test_zone_hunt_native.py -v",passed=4,scope='existing death/cap integration'),
        dict(command="python -m unittest discover -s tools/tests -p test_aa_tbs_policy.py -v",passed=7,scope='retained deployed AA catalog and closure'),
        dict(command='perl tools/tests/instance_keeper_visuals.t (isolated Linux runtime)',passed=18,scope='actual quest with native API doubles'),
        dict(command='go test ./cmd/nightcap-package',status='passed',scope='current merged launcher history; no client publication'),
        dict(command='wiki: python -B -m unittest -v test_wiki test_refresh',passed=14,scope='complete isolated site with six reviewed source updates'),
        dict(command='wiki: node test_search.cjs; node test_equipment.cjs',passed=13,scope='six search and seven equipment cases')],
    operational_installation='not performed',native_runtime_failure_injection='pending',
    fourteen_mode_gameplay='pending',classic_ct_geometry_paths_doors='pending in game; static identity/door checks passed',
    level_50_vox_nagafen_balance='pending',owner_acceptance='pending',production_promotion_restart='not performed; separate authorization required',
    wiki='local source updated and tested; publication pending',
    cache_scope='local test content; 330 new definitions verified and 308928 existing records byte-identical')
(folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Recorded native pairing and automated evidence with manual/release gates left open.')

"""Link the existing isolated diagnostic against this feature's fresh native objects."""
from pathlib import Path
import subprocess

ROOT=Path('/tmp/nightcap-balance-zone-hunt-20261009')
TOOLS=Path('/tmp/nightcap-zone-hunt-tools/balance')
BUILD=Path('/tmp/nightcap-market-zone-hunt-dev-20261009')
if not (ROOT/'eqemu_config.json').exists() or not (BUILD/'final-manifest.json').exists():
    raise RuntimeError('Verified candidate and isolated fixture must exist first')
for name in ('native_harness.cpp','native_runtime.cpp','native_runtime.h','build_native.py'):
    text=(TOOLS/name).read_text()
    if name=='native_harness.cpp':
        old='db.at("db") != "nightcap_balance_20260912" || db.at("username") != "nightcap_balance"'
        assert text.count(old)==1
        text=text.replace(old,'db.at("db") != "nightcap_zone_hunt_20261009" || db.at("username") != "nightcap_hunt_qa"')
    if name=='build_native.py':
        old="build = source / 'build/zone'"
        assert text.count(old)==1
        text=text.replace(old,"build = Path('/tmp/nightcap-market-zone-hunt-dev-20261009/build/zone')")
    (ROOT/name).write_text(text)
with (ROOT/'diagnostic-build.log').open('w') as log:
    result=subprocess.run(['python3',str(ROOT/'build_native.py'),'--source',str(BUILD/'source')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:
    lines=(ROOT/'diagnostic-build.log').read_text().splitlines()
    print('\n'.join(x for x in lines if 'error:' in x.lower())[-3000:]);print('\n'.join(lines[-12:]))
    raise SystemExit(result.returncode)
with (ROOT/'shared-memory.log').open('w') as log:
    subprocess.run([str(BUILD/'build/bin/shared_memory')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
with (ROOT/'diagnostic-run.log').open('w') as log:
    result=subprocess.run([str(ROOT/'balance-zone'),'tests:balance',str(ROOT/'zone-hunt-inputs.json'),str(ROOT/'zone-hunt-results.json')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:
    print('\n'.join((ROOT/'diagnostic-run.log').read_text().splitlines()[-18:]))
    raise SystemExit(result.returncode)
print('Native zone-hunt diagnostic completed; results saved in isolated runtime.')

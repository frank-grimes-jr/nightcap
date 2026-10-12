"""Run inside the development container against an isolated source copy.

Copy this file and server-mods/code to /tmp/nightcap-item-upgrade-overlay first.
This compiles objects only; it does not link or install a running game binary.
"""
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

BASE = Path('/tmp/nightcap-market-zone-hunt-dev-20261009')
OUT = Path('/tmp/nightcap-item-upgrades-box-20261012')
OVERLAY = Path('/tmp/nightcap-item-upgrade-overlay')


def main():
    OUT.mkdir(exist_ok=False)
    source = OUT / 'source'
    shutil.copytree(BASE / 'source', source, symlinks=True)
    shutil.copytree(OVERLAY, source, dirs_exist_ok=True)
    flags = {}
    for line in (BASE / 'build/zone/CMakeFiles/zone.dir/flags.make').read_text().splitlines():
        if line.startswith(('CXX_DEFINES =', 'CXX_INCLUDES =')):
            key, value = line.split(' = ', 1)
            flags[key] = shlex.split(value.replace(str(BASE / 'source'), str(source)))
    checked = {}
    for name in ('advanced_loot_inventory.cpp', 'client_packet.cpp', 'zone_hunt_forge.cpp'):
        cpp = source / 'zone' / name
        digest = hashlib.sha256(cpp.read_bytes()).hexdigest()
        with (OUT / (name + '.log')).open('w') as log:
            result = subprocess.run(['/usr/bin/clang++', *flags['CXX_DEFINES'],
                *flags['CXX_INCLUDES'], '-std=c++20', '-O0', '-c', str(cpp),
                '-o', str(OUT / (name + '.o'))], stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            print((OUT / (name + '.log')).read_text()[-7000:], flush=True)
            raise SystemExit(result.returncode)
        assert hashlib.sha256(cpp.read_bytes()).hexdigest() == digest
        checked[name] = digest
        print('Compiled ' + name, flush=True)
    probe = subprocess.run(['/tmp/nightcap-map-probe-20260920/map-probe'],
        input=json.dumps({'map': '/home/eqemu/server/maps/base/ecommons.map',
            'points': [{'x': -385, 'y': -1818, 'z': 3.75}],
            'segments': [{'from': [-385, -1806, 7.5], 'to': [-385, -1818, 7.5]}]}),
        text=True, capture_output=True, check=True)
    geometry = json.loads(probe.stdout)
    (OUT / 'geometry.json').write_text(json.dumps(geometry, indent=2) + '\n')
    for sample in geometry['points'][0]['samples']:
        assert sample['ground_hit'] and abs(sample['ground_z']) < 1 and sample['headroom'] > 12, sample
    assert not geometry['segments'][0]['blocked']
    (OUT / 'verification.json').write_text(json.dumps({'status': 'passed',
        'scope': 'Native object compilation and native map raycast; not deployed gameplay',
        'sources': checked, 'geometry': geometry}, indent=2) + '\n')
    print('Native object compilation and tunnel geometry passed.', flush=True)


if __name__ == '__main__':
    main()

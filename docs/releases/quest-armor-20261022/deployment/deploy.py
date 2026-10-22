"""Dispatch the pinned quest-armor operator; private receipts stay on OVH."""
import argparse
import base64
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SSH = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i',
       'C:/Users/verre/.ssh/nightcap_ovh', '-o', 'BatchMode=yes',
       '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes',
       'ubuntu@135.148.47.202']


def run(source, timeout=180):
    result = subprocess.run(SSH + ['sudo -n python3 -'], input=source,
                            text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-3500:])
    return json.loads(result.stdout)


def payload():
    manifest = json.loads((HERE.parent/'manifest.json').read_text())
    reference = json.loads((HERE.parent/'production-reference.json').read_text())
    catalog = json.loads((ROOT/'docs/items/quest-armor-catalog.json').read_text())
    scripts = manifest['scripts'] + manifest['compatibility_scripts']
    for entry in scripts:
        entry['payload'] = base64.b64encode((ROOT/'server-mods/quests'/entry['path']).read_bytes()).decode()
    targets = {i+600000 for f in catalog['families'] for ids in f['scripts'].values() for i in ids}
    return {'scripts': scripts, 'targets': [r for r in reference['items'] if r['id'] in targets],
            'npcs': reference['npcs'],
            'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['probe', 'apply', 'rollback', 'verify'])
    args = parser.parse_args()
    control = (ROOT/'docs/ops/waypoint-crystal-20261022/deployment/world_control.py').read_text()
    source = 'DATA='+repr(payload())+'\nCONTROL='+repr(control)+'\nACTION='+repr(args.action)+'\n'
    source += (HERE/'remote.py').read_text()
    report = run(source)
    destination = HERE/(args.action+'.json')
    with destination.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2); f.write('\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()

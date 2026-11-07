"""Deliver only the approved signed loot payload; preserve services and controls."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'augment-audit-20261106'))
from probe import SSH

SIGNED = ROOT / 'eq-client-dll/build/advanced-loot-release/signed-v2'
STAGE = '/opt/nightcap/releases/advanced-loot-client-2026110605-v1'


def remote(code):
    result = subprocess.run(SSH + ['sudo -n python3 -'], input=code,
                            text=True, encoding='utf-8', capture_output=True, timeout=240)
    if result.returncode:
        raise RuntimeError(result.stderr[-2500:] + result.stdout[-1200:])
    return json.loads(result.stdout)


def main(action):
    receipt = json.loads((HERE / 'signed-candidate.json').read_text())
    assert receipt['release'] == 2026110605 and receipt['changed_assets'] == 3
    files = {name: (SIGNED / name).read_bytes() for name in (
        'channel.json', 'previous-channel.json', 'dinput8.dll',
        'nightcap-patch-sites.json', 'uifiles/nightcap/equi_petinfowindow.xml')}
    for name in ('publish.py', 'test_publish.py'):
        files[name] = (HERE / name).read_bytes()
    pins = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    assert pins == json.loads((HERE / 'publication-payload.json').read_text())['files']
    if action == 'probe':
        code = (HERE / 'publish.py').read_text().split("if __name__ == '__main__':")[0]
        result = remote(code + f'''
root=PUBLIC.parent.parent
wiki=PUBLIC/'wiki/current'
assert wiki.is_symlink()
wiki_release=wiki.readlink().name
print(json.dumps(dict(status='healthy read-only preflight',services=services(),
 free_bytes=shutil.disk_usage(root).free,channel_sha256=sha((PUBLIC/'channel.json').read_bytes()),
 stage_exists=Path({STAGE!r}).exists(),wiki_release=wiki_release,
 wiki_manifest=json.loads((root/'website-history'/wiki_release/'manifest.json').read_text()),
 config_sha256=sha((root/'nginx.conf').read_bytes()))))
''')
        assert result['channel_sha256'] == receipt['previous_channel_sha256']
        assert not result['stage_exists']
    elif action == 'stage':
        encoded = {name: base64.b64encode(data).decode() for name, data in files.items()}
        result = remote(f'''from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess
stage=Path({STAGE!r});assert not stage.exists()
assert shutil.disk_usage('/opt/nightcap').free>2*{sum(map(len, files.values()))}+350*1024**2
os.umask(0o077);stage.mkdir(mode=0o700);files={encoded!r};pins={pins!r}
for name,raw in files.items():
 data=base64.b64decode(raw,validate=True);assert hashlib.sha256(data).hexdigest()==pins[name]
 path=stage/name;path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
for path in sorted([q for q in stage.rglob('*') if q.is_dir()]+[stage],key=lambda q:len(q.parts),reverse=True):
 fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
fd=os.open(stage.parent,os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
tests=subprocess.run(['python3','-B','-m','unittest','test_publish'],cwd=stage,capture_output=True,text=True,timeout=90)
assert tests.returncode==0,tests.stderr[-2200:]
print(json.dumps(dict(status='staged_not_published',files=len(pins),linux_tests=tests.stderr.strip().splitlines()[-1],pins=pins)))
''')
    else:
        baseline = json.loads((HERE / 'client-preflight.json').read_text())
        staged = json.loads((HERE / 'client-staged.json').read_text())
        assert staged['pins'] == pins
        result = remote(f'''from pathlib import Path
import fcntl,hashlib,importlib.util,json
stage=Path({STAGE!r});pins={pins!r}
for name,pin in pins.items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==pin
spec=importlib.util.spec_from_file_location('publisher',stage/'publish.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
with (p.PUBLIC.parent.parent/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert p.services()=={baseline['services']!r},'Service baseline changed; hold publication'
 result=p.publish(stage,p.PUBLIC)
 assert result['services_before']==result['services_after']=={baseline['services']!r}
 p.replace((json.dumps(result,indent=2)+chr(10)).encode(),stage/'published.json')
print(json.dumps(result))
''')
    name = {'probe': 'client-preflight.json', 'stage': 'client-staged.json',
            'publish': 'client-published.json'}[action]
    (HERE / name).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'action': action, 'status': result.get('status', 'published'),
                      'release': 2026110605, 'files': len(pins),
                      'free_bytes': result.get('free_bytes')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('probe', 'stage', 'publish'))
    main(parser.parse_args().action)

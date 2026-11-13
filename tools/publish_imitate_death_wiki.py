"""Publish only the verified Imitate Death guide delta after native activation."""
import hashlib
import json
from pathlib import Path
import subprocess
from quick_buff_remote import run
from capture_lantern_content import SSH

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/releases/imitate-death-20261112/deployment'
ART = ROOT / 'artifacts/imitate-death-20261112'
RELEASE = '20261112-imitate-death-v1'
PREVIOUS = '20261112-quick-buff-v2'

if __name__ == '__main__':
    candidate = json.loads((HERE / 'wiki-candidate.json').read_text(encoding='utf-8'))
    assert candidate['public_source_reproduced'] and candidate['preserved_files'] == 610
    wiki = ART / 'wiki-source/wiki'
    archive = ART / (RELEASE + '.tar.gz')
    paths = [archive, archive.with_suffix('.json')] + [wiki / n for n in ('update.py', 'deploy.py', 'test_update.py', 'test_deploy.py', 'nginx.conf')]
    pins = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    upload = '/home/ubuntu/wiki-imitate-death-20261112-v1'
    ssh = SSH[:-1]
    subprocess.run(ssh + ['mkdir -m 700 ' + upload], check=True, timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe', *ssh[1:-1], *map(str, paths), ssh[-1] + ':' + upload + '/'], check=True, timeout=300)
    code = r'''
from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess
os.umask(0o077)
root=Path('/opt/nightcap/deploy/production');upload=Path(UPLOAD);stage=Path('/opt/nightcap/releases/wiki-imitate-death-20261112-v1')
assert {p.name for p in upload.iterdir()}==set(PINS)
stage.mkdir(mode=0o700)
for name,pin in PINS.items():
 p=upload/name;assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==pin
 shutil.copyfile(p,stage/name)
tests=subprocess.run(['python3','-B','-m','unittest','test_deploy','test_update'],cwd=stage,text=True,capture_output=True,timeout=180)
assert tests.returncode==0,tests.stderr[-1800:]
path=Path('/opt/nightcap/releases/imitate-death-20261112-v1/rollout.py')
s=importlib.util.spec_from_file_location('icons',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.initialize()
proof=m.read(m.EVIDENCE/'activation/deployed.json');assert proof['gateway_open']
before={n:m.r.compact(n) for n in ('game','gateway','db','web','tunnel')}
channel=m.sha(root/'data/public/channel.json')
def guard():
 assert {n:m.r.compact(n) for n in before}==before
 assert m.sha(root/'data/public/channel.json')==channel
 m.r.running(proof['runtime']['image_id'],m.binaries());m.base.health()
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard()
 pointer=root/'data/public/wiki/current';assert pointer.is_symlink() and pointer.readlink()==Path('releases')/PREVIOUS
 config=m.sha(root/'nginx.conf');assert config=='46355a5e09bc63bc0a05713c02a315966378ef2ecbc5856bbab2140093a619c6'
 result=json.loads(subprocess.check_output(['python3',str(stage/'update.py'),str(stage/ARCHIVE),str(stage/MANIFEST),RELEASE,PREVIOUS,config],timeout=240))
 guard()
result.update(linux_tests=tests.stderr.strip().splitlines()[-1],changed_existing=CHANGED,preserved_files=610,source_reproduced=True)
print(json.dumps(result,indent=2))
'''
    prefix = '\n'.join(k + '=' + repr(v) for k, v in {'PINS': pins, 'UPLOAD': upload, 'RELEASE': RELEASE,
                       'PREVIOUS': PREVIOUS, 'ARCHIVE': archive.name, 'MANIFEST': archive.with_suffix('.json').name,
                       'CHANGED': candidate['changed_existing']}.items()) + '\n'
    result = run(prefix + code)
    (HERE / 'wiki-publication.json').write_text(result, encoding='utf-8')
    print(result, end='')

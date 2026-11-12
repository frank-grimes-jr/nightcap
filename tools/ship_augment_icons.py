"""Package exact reviewed bytes; upload privately without changing the runtime."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
from capture_lantern_content import SSH
from augment_icon_remote import run

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/items/augment-icons-20261112'
ART = ROOT / 'artifacts/augment-icons-20261112'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    payload = ART / 'payload-v1'; payload.mkdir(exist_ok=False)
    (payload / 'bin').mkdir()
    proof = json.loads((HERE / 'native-build.json').read_text(encoding='utf-8'))
    probe = json.loads((ART / 'production-probe.json').read_text(encoding='utf-8'))
    assert proof['status'] == 'PASS' and len(proof['dependency_closures']) == 3
    for name in ('common/item_instance.cpp', 'zone/client_packet.cpp'):
        normalized = (ROOT / 'server-mods/code' / name).read_text(encoding='utf-8').encode('utf-8')
        assert hashlib.sha256(normalized).hexdigest() == proof['source_sha256'][name]
    for name in ('zone', 'world', 'shared_memory'):
        subprocess.run(['docker', 'cp', 'akk-stack-eqemu-server-1:/tmp/nightcap-augment-icons-20261112-v2/candidate-' + name + '.stripped',
                        str(payload / 'bin' / name)], check=True, capture_output=True)
        assert sha(payload / 'bin' / name) == proof['shipping']['candidate-' + name]
    for name in ('rollout.py', 'repair.py', 'native-build.json', 'repair-rehearsal.json'):
        (payload / name).write_bytes((HERE / name).read_bytes())
    capture = '/opt/nightcap/releases/augment-icons-20261112-v1/capture-1794503428249604294.json'
    capture_pin = json.loads(run('from pathlib import Path\nimport json,hashlib\np=Path(' + repr(capture) + ')\nprint(json.dumps({"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}))'))['sha256']
    files = {p.relative_to(payload).as_posix(): sha(p) for p in payload.rglob('*') if p.is_file()}
    manifest = {'owner_authorization': 'Deploy the fix and repair the affected item icons, preserving the augments and all other item data.',
                'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'source_hashes': proof['source_sha256'], 'base_image_id': probe['game']['image_id'],
                'base_hashes': probe['image_files'], 'prior_operator_sha256': probe['release_operator_sha256'],
                'capture': capture, 'capture_sha256': capture_pin, 'files': files,
                'binaries': {name: proof['shipping']['candidate-' + name] for name in ('zone', 'world', 'shared_memory')}}
    (payload / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    archive = ART / 'release-v1.tar.gz'
    with tarfile.open(archive, 'x:gz') as handle:
        for path in sorted(payload.rglob('*')):
            if path.is_file():
                info = handle.gettarinfo(str(path), path.relative_to(payload).as_posix())
                info.mode = 0o755 if path.parent.name == 'bin' else 0o600
                with path.open('rb') as source:
                    handle.addfile(info, source)
    upload = '/home/ubuntu/augment-icons-20261112-v1.tar.gz'
    ssh = SSH[:-1]
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe', *ssh[1:-1], str(archive), ssh[-1] + ':' + upload], check=True, timeout=600)
    code = r'''
from pathlib import Path
import hashlib,json,os,tarfile
os.umask(0o077)
stage=Path('/opt/nightcap/releases/augment-icons-20261112-v1')
upload=Path('/home/ubuntu/augment-icons-20261112-v1.tar.gz')
assert hashlib.sha256(upload.read_bytes()).hexdigest()==ARCHIVE_PIN
assert not (stage/'manifest.json').exists(),'Staging already exists; do not overwrite'
with tarfile.open(upload) as archive:
 entries=archive.getmembers();assert {e.name for e in entries}==set(FILES)|{'manifest.json'}
 for member in entries:
  target=stage/member.name
  assert member.isfile() and not member.issym() and not member.islnk() and target.resolve().is_relative_to(stage) and not target.exists()
  target.parent.mkdir(mode=0o700,exist_ok=True)
  with target.open('xb') as output:
   data=archive.extractfile(member).read();output.write(data);output.flush();os.fsync(output.fileno())
  if member.name in FILES:assert hashlib.sha256(data).hexdigest()==FILES[member.name]
  os.chmod(target,0o755 if member.name.startswith('bin/') else 0o600)
print(json.dumps({'status':'STAGED','manifest_sha256':hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest(),'runtime_changed':False}))
'''
    result = run('ARCHIVE_PIN=' + repr(sha(archive)) + '\nFILES=' + repr(files) + '\n' + code)
    (HERE / 'staged.json').write_text(result, encoding='utf-8')
    print(result, end='')

"""Publish the reviewed wiki through its existing guarded atomic updater."""
import hashlib
import json
import subprocess
from pathlib import Path
from remote import SSH, run

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGE = '/opt/nightcap/releases/thj-parity-20261018/wiki'
RELEASE = '20261018-thj-parity-v1'
FILES = [ROOT.parent/'thj-parity-wiki-20261018.tar.gz',
         ROOT.parent/'thj-parity-wiki-20261018.tar.json',
         ROOT/'wiki/update.py', ROOT/'wiki/deploy.py']


def main():
    manifest = json.loads(FILES[1].read_text(encoding='utf-8'))
    assert len(manifest) == 465
    pins = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in FILES}
    # A fresh upload directory makes accidental replacement an error.
    run("import os,pwd\nfrom pathlib import Path\np=Path('/home/ubuntu/thj-parity-wiki-upload')\np.mkdir(exist_ok=False)\np.chmod(0o755)\nu=pwd.getpwnam('ubuntu')\nos.chown(p,u.pw_uid,u.pw_gid)\n")
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe', *SSH[1:-1],
                    *map(str, FILES), SSH[-1]+':/home/ubuntu/thj-parity-wiki-upload/'], check=True)
    source = f'''
import hashlib,json,shutil,subprocess
from pathlib import Path
upload=Path('/home/ubuntu/thj-parity-wiki-upload');stage=Path({STAGE!r})
pins={pins!r}
assert {{p.name for p in upload.iterdir()}}==set(pins)
for name,digest in pins.items():
    p=upload/name
    assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest
stage.mkdir(exist_ok=False)
for name,digest in pins.items():
    shutil.copyfile(upload/name,stage/name)
    assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
result=subprocess.check_output(['python3',str(stage/'update.py'),str(stage/'thj-parity-wiki-20261018.tar.gz'),str(stage/'thj-parity-wiki-20261018.tar.json'),{RELEASE!r},'20261018-loot-quality-v1','03ef62717aad29884d3c1a60d800b19d0ee9cc7024fec7313d0263f37fbd046c'])
print(result.decode())
'''
    output = run(source, timeout=900)
    report = json.loads(output)
    assert report['result'] == 'PASS' and report['files'] == 465
    with (HERE/'wiki-publication.json').open('xb') as f:f.write(output)
    print(output.decode())


if __name__ == '__main__':main()

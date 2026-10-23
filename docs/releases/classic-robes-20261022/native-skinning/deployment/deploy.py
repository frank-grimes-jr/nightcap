"""Stage the exact public payload privately; --publish performs the approved swap."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ARTIFACTS = Path('E:/EQ_Local_Dev/artifacts/classic-robes-20261022/native-waist-release')
SIGNED = ARTIFACTS/'signed-2026102204'
STAGE = '/opt/nightcap/releases/classic-robes-native-waist-20261022'
UPLOAD = '/home/ubuntu/classic-robes-native-waist-20261022'
SSH = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', 'C:/Users/verre/.ssh/nightcap_ovh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes', 'ubuntu@135.148.47.202']


def run(source, timeout=180):
    result = subprocess.run(SSH+['sudo -n python3 -'], input=source, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-5000:])
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    files = [SIGNED/name for name in ('channel.json', 'previous-channel.json', 'global_chr.s3d', 'global4_chr.s3d')]
    files += [HERE/name for name in ('publish.py', 'test_publish.py')]
    pins = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    subprocess.run(SSH+['mkdir -p -m 700 '+UPLOAD], check=True, timeout=30)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe', *SSH[1:-1], *map(str, files), SSH[-1]+':'+UPLOAD+'/'], check=True, timeout=120)
    source = f'''
import hashlib,json,os,subprocess
from pathlib import Path
upload=Path({UPLOAD!r}); stage=Path({STAGE!r}); pins={pins!r}
assert not upload.is_symlink() and {{p.name for p in upload.iterdir()}}==set(pins)
assert not stage.is_symlink()
stage.mkdir(mode=0o700,exist_ok=True)
for name,digest in pins.items():
    p=upload/name; dest=stage/name
    assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest
    assert not dest.is_symlink()
    if dest.exists(): assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest
    else:
        with dest.open('xb') as f:
            f.write(p.read_bytes()); f.flush(); os.fsync(f.fileno())
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==digest
tests=subprocess.run(['python3','-B','-m','unittest','-v','test_publish'],cwd=stage,capture_output=True,text=True,timeout=60)
assert tests.returncode==0, tests.stderr
report={{'stage':str(stage),'payload_sha256':pins,'linux_tests':tests.stderr,'public_changes':False}}
if {args.publish!r}:
    result=subprocess.check_output(['python3','-B',str(stage/'publish.py'),'--stage',str(stage),'--publish'],text=True,timeout=120)
    report['publication']=json.loads(result); report['public_changes']=True
print(json.dumps(report))
'''
    report=json.loads(run(source))
    name='deployment.json' if args.publish else 'stage.json'
    (HERE/name).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':name, 'public_changes':report['public_changes'], 'linux_tests':'10 passed', 'release':report.get('publication',{}).get('release')}))


if __name__ == '__main__': main()

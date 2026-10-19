"""Owner-authorized catalog-only publication; never uploads signing material."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ARTIFACTS = Path('E:/EQ_Local_Dev/artifacts/client-contract-20261019')
SSH = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', 'C:/Users/verre/.ssh/nightcap_ovh',
       '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes',
       'ubuntu@135.148.47.202']
STAGE = '/opt/nightcap/releases/client-contract-20261019'


def main():
    files = {'channel.json': ARTIFACTS/'channel.json',
             'nightcap-patch-sites.json': ARTIFACTS/'nightcap-patch-sites.json',
             'previous-channel.json': HERE/'previous-channel.json',
             'publish.py': HERE/'publish.py'}
    payload = {name: {'data': base64.b64encode(path.read_bytes()).decode(),
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
               for name, path in files.items()}
    source = f'''
import base64,hashlib,json,os,subprocess
from pathlib import Path
stage=Path({STAGE!r})
payload={payload!r}
assert not stage.is_symlink()
stage.mkdir(mode=0o700,exist_ok=True)
for name,record in payload.items():
    data=base64.b64decode(record['data'])
    assert hashlib.sha256(data).hexdigest()==record['sha256']
    target=stage/name
    assert not target.is_symlink()
    if target.exists():
        assert hashlib.sha256(target.read_bytes()).hexdigest()==record['sha256'],name
    else:
        with target.open('xb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
result=subprocess.run(['python3',str(stage/'publish.py'),'--stage',str(stage),'--publish'],capture_output=True,text=True,timeout=180)
if result.returncode:raise RuntimeError(result.stderr[-3000:])
print(result.stdout)
'''
    result = subprocess.run(SSH+['sudo -n python3 -'], input=source, text=True,
                            capture_output=True, timeout=210)
    if result.returncode:
        raise RuntimeError(result.stderr[-3500:])
    report = json.loads(result.stdout)
    assert report['release'] == 2026101901
    assert report['services_before'] == report['services_after']
    (HERE/'published.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'release':report['release'], 'channel_sha256':report['channel_sha256'],
                      'changed_assets':report['changed_assets'], 'preserved_assets':report['preserved_assets'],
                      'services_unchanged':True}))


if __name__ == '__main__':
    main()

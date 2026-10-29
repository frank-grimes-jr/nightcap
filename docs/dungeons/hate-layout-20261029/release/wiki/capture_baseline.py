"""Read only the current wiki publication identity and public file manifest."""
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
SSH = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', 'C:/Users/verre/.ssh/nightcap_ovh',
       '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes',
       'ubuntu@135.148.47.202']
PREVIOUS = '20261028-bazaar-owner-qa-v1'


def remote(code):
    result = subprocess.run(SSH + ['sudo -n python3 -'], input=code, text=True,
                            capture_output=True, timeout=240)
    if result.returncode:
        raise RuntimeError(result.stderr[-3500:])
    return json.loads(result.stdout)


def main():
    result = remote('''from pathlib import Path
import json,hashlib
base=Path('/opt/nightcap/deploy/production')
pointer=base/'data/public/wiki/current';assert pointer.is_symlink()
release=pointer.readlink().name
print(json.dumps({'release':release,'manifest':json.loads((base/'website-history'/release/'manifest.json').read_text()),'config_sha256':hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()}))
''')
    assert result['release'] == PREVIOUS, 'Reconcile changed public baseline'
    assert len(result['manifest']) == 499
    (HERE / 'wiki-baseline.json').write_text(json.dumps(result['manifest'], indent=2) + '\n', encoding='utf-8')
    (HERE / 'baseline-state.json').write_text(json.dumps({k: v for k, v in result.items() if k != 'manifest'}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'release': result['release'], 'files': len(result['manifest'])}))


if __name__ == '__main__':
    main()

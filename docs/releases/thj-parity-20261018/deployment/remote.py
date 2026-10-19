"""Run reviewed remote Python without shell interpolation."""
import argparse
import subprocess
from pathlib import Path

SSH = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', 'C:/Users/verre/.ssh/nightcap_ovh',
       '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-o', 'StrictHostKeyChecking=yes',
       'ubuntu@135.148.47.202']


def run(source, timeout=900):
    result = subprocess.run(SSH + ['sudo -n python3 -'], input=source.encode(),
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace')[-3500:])
    return result.stdout


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--timeout', type=int, default=900)
    a = p.parse_args()
    output = run(a.source.read_text(), a.timeout)
    if a.output:
        with a.output.open('xb') as f:
            f.write(output)
        print('Saved', len(output), 'bytes to', a.output)
    else:
        print(output.decode())

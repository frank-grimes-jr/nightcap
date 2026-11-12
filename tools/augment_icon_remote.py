"""Execute reviewed task scripts over the established SSH transport; no raw logs."""
import argparse
import json
from pathlib import Path
import subprocess
from capture_lantern_content import SSH

ROOT = Path(__file__).resolve().parents[1]


def run(script, timeout=600):
    result = subprocess.run(SSH, input=script, text=True, encoding='utf-8', capture_output=True, timeout=timeout)
    if result.returncode:
        error = ROOT / 'artifacts/augment-icons-20261112/remote-error.txt'
        error.parent.mkdir(parents=True, exist_ok=True)
        error.write_text(result.stdout + '\n' + result.stderr, encoding='utf-8')
        raise RuntimeError(f'Remote action failed ({result.returncode}); private diagnostic: {error}')
    return result.stdout


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('script', type=Path)
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()
    print(run(args.script.read_text(encoding='utf-8'), args.timeout), end='')

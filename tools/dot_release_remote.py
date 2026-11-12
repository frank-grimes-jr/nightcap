"""Pinned-host task transport; retain private diagnostics, omit credentials."""
import argparse
from pathlib import Path
import subprocess
from capture_lantern_content import SSH

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'artifacts/dot-no-initial-damage-20261112'


def run(script, timeout=600):
    result = subprocess.run(SSH, input=script, text=True, encoding='utf-8',
                            capture_output=True, timeout=timeout)
    if result.returncode:
        ART.mkdir(parents=True, exist_ok=True)
        (ART / 'remote-error.txt').write_text(result.stdout + '\n' + result.stderr, encoding='utf-8')
        raise RuntimeError(f'Remote action failed ({result.returncode}); inspect {ART / "remote-error.txt"}')
    return result.stdout


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('script', type=Path)
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args()
    print(run(args.script.read_text(encoding='utf-8'), args.timeout), end='')

"""Run a fixed, staged one-shot action and retain logs; never retry automatically."""
import argparse
from pathlib import Path
from quick_buff_remote import run

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'activate', 'open'))
    args = parser.parse_args()
    code = 'import runpy,sys\nsys.argv=["rollout.py",' + repr(args.action) + ']\nrunpy.run_path("/opt/nightcap/releases/quick-buff-20261112-v2/rollout.py",run_name="__main__")\n'
    result = run(code, timeout=1800)
    path = ROOT / 'docs/releases/quick-buff-20261112/hotkey-fix' / (args.action + '.log')
    path.write_text(result.rstrip() + '\n', encoding='utf-8')
    print(result[-2200:], end='')

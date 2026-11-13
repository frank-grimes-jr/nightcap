"""Pinned-host task transport; preserve failures privately, never print credentials."""
import argparse
from pathlib import Path
import subprocess
from capture_lantern_content import SSH
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts/quick-buff-20261112'
def run(script,timeout=600):
    result=subprocess.run(SSH,input=script,text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    if result.returncode:
        ART.mkdir(parents=True,exist_ok=True)
        path=ART/'remote-error.txt';path.write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        raise RuntimeError(f'Remote action failed ({result.returncode}); private diagnostic: {path}')
    return result.stdout
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('script',type=Path);p.add_argument('--timeout',type=int,default=600);a=p.parse_args()
    print(run(a.script.read_text(encoding='utf-8'),a.timeout),end='')

"""Run a named reviewed release script over SSH; save output locally."""
import argparse,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
SSH=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes',os.environ['NIGHTCAP_DEPLOY_SSH_TARGET'],'sudo -n python3 -']
p=argparse.ArgumentParser();p.add_argument('script');p.add_argument('--output');a=p.parse_args()
result=subprocess.run(SSH,input=(HERE/a.script).read_bytes(),capture_output=True,timeout=900)
if result.returncode:raise RuntimeError((result.stdout+result.stderr).decode()[-5000:])
if a.output:(HERE/a.output).write_bytes(result.stdout)
print(result.stdout.decode()[-2500:])

"""Start a single recorded action. Polling logs never replays a deployment."""
import argparse
import json
from probe import SSH, HERE, remote
from stage import STAGE

def main():
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=('preflight','activate','open'))
    p.add_argument('--start',action='store_true')
    args=p.parse_args()
    code="""
from pathlib import Path
import json,subprocess
d=Path('/opt/nightcap/releases')/STAGE
log=d/(ACTION+'.log');unit='nightcap-'+STAGE+'-'+ACTION
if START:
 with log.open('x') as f: f.write('Starting '+ACTION+'\\n')
 subprocess.run(['systemd-run','--unit='+unit,'--property=WorkingDirectory='+str(d),'--property=StandardOutput=append:'+str(log),'--property=StandardError=append:'+str(log),'/usr/bin/python3','-B',str(d/'rollout.py'),ACTION],check=True,stdout=subprocess.DEVNULL)
state=subprocess.check_output(['systemctl','show',unit,'--property=LoadState,ActiveState,SubState,Result,ExecMainStatus'],text=True)
files=sorted(str(p.relative_to(d)) for p in (d/'evidence').rglob('*.json')) if (d/'evidence').exists() else []
print(json.dumps(dict(state=state.splitlines(),receipts=files,log=log.read_text()[-1300:] if log.exists() else '')))
"""
    report=json.loads(remote('STAGE='+repr(STAGE)+'\nACTION='+repr(args.action)+'\nSTART='+repr(args.start)+'\n'+code,timeout=90))
    print(json.dumps(report))
if __name__=='__main__':main()

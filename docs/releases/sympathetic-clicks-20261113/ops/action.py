"""Start one scoped systemd unit or inspect its existing outcome."""
import argparse
import json
import time
from probe import STAGE, call

def action(name,start=False,rechecked=False):
    return json.loads(call("""
from pathlib import Path
import json,subprocess
root=Path('/opt/nightcap/releases')/STAGE
label=ACTION+('-wiki-rechecked' if RECHECKED else '')
unit='nightcap-'+STAGE+'-'+label
log=root/(label+'.log')
if RECHECKED:
 assert ACTION=='activate' and (root/'evidence/wiki-reconciliation.json').is_file()
if START:
 with log.open('x') as f:f.write('Starting '+ACTION+'\\n')
 subprocess.run(['systemd-run','--unit='+unit,'--property=WorkingDirectory='+str(root),
    '--property=StandardOutput=append:'+str(log),'--property=StandardError=append:'+str(log),
    '/usr/bin/python3','-B',str(root/'release.py'),ACTION],check=True,stdout=subprocess.DEVNULL)
state=subprocess.check_output(['systemctl','show',unit,'--property=LoadState,ActiveState,Result,ExecMainStatus'],text=True)
print(json.dumps(dict(state=state.splitlines(),receipts=sorted(str(p.relative_to(root)) for p in (root/'evidence').rglob('*.json')),
                      log=log.read_text()[-1500:] if log.is_file() else '')))
""",STAGE=STAGE,ACTION=name,START=start,RECHECKED=rechecked))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('preflight','activate','publish','open','recover-closed'))
    parser.add_argument('--start',action='store_true')
    parser.add_argument('--watch',action='store_true')
    parser.add_argument('--wiki-rechecked',action='store_true')
    args=parser.parse_args()
    outcome=action(args.action,args.start,args.wiki_rechecked)
    while args.watch and 'ActiveState=active' in outcome['state']:
        time.sleep(15)
        outcome=action(args.action,rechecked=args.wiki_rechecked)
    print(json.dumps(outcome,indent=2))

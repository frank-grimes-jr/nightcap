"""Run one guarded action and retain its observed receipt; never replay silently."""
import argparse
import json
import subprocess
from inventory_release_support import HERE,ART,SSH,STAGE,remote,save


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate','publish-client','open'))
    action=parser.parse_args().action
    log=ART/(action+'.log')
    with log.open('x',encoding='utf-8') as output:
        p=subprocess.run(SSH+['sudo -n python3 '+STAGE+'/rollout.py '+action],stdout=output,stderr=subprocess.STDOUT,text=True,encoding='utf-8',timeout=1800)
    if p.returncode:raise RuntimeError('Release action stopped; inspect '+str(log)+' and remote receipts before retry. '+log.read_text(encoding='utf-8')[-800:])
    receipts={'preflight':'evidence/preflight.json','activate':'evidence/activation/verified-closed.json',
              'publish-client':'client/published.json','open':'evidence/activation/paired-deployed.json'}
    value=remote('import json\nfrom pathlib import Path\nprint(json.dumps(json.loads(Path('+repr(STAGE+'/'+receipts[action])+').read_text())))')
    save(ART/(action+'-receipt.json'),value)
    print(json.dumps({'action':action,'status':'observed_success','receipt':receipts[action]}))


if __name__=='__main__':main()

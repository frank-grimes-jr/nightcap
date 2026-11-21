"""Stage checked-in gameplay data and invoke the content-only release operator."""
import gzip
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'docs/releases/classic-raid-augments-20261112'))
from probe import remote

STAGE='classic-equipment-paths-20261121-v1'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def stage(source,candidate=False):
    assert subprocess.check_output(['git','rev-parse','HEAD' if candidate else 'origin/main'],cwd=ROOT,text=True).strip()==source
    fields=['ID','HP','Mana','HealAmt','SpellDmg','DamageShield','Slots','AugType','Worn','Focus']
    code='#include "common/item_data.h"\n#include <cstdio>\n#include <cstddef>\nint main(){printf("%zu",sizeof(EQ::ItemData));'+''.join('printf(" %zu",offsetof(EQ::ItemData,'+f+'));' for f in fields)+'}'
    cmd='cd /tmp/nightcap-raid-augments-shipping-20261112-v3 && clang++ -std=c++20 -Isource -xc++ - -o /tmp/nightcap-prismatic-layout && /tmp/nightcap-prismatic-layout'
    layout=list(map(int,subprocess.check_output(['docker','exec','-i','akk-stack-eqemu-server-1','sh','-c',cmd],input=code.encode()).split()))
    assert layout[:2]==[1332,440]
    data={}
    for path in [HERE/'release.py',ROOT/'docs/items/classic-equipment-paths/catalog.py',ROOT/'docs/items/classic-equipment-paths/targets.json.gz',ROOT/'docs/items/classic-equipment-paths/policy.json',ROOT/'docs/items/classic-equipment-paths/effects.json',ROOT/'docs/items/classic-equipment-paths/zone_catalog.py',ROOT/'docs/items/classic-equipment-paths/soltemple.json.gz']:
        data[path.name]=subprocess.check_output(['git','show',source+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
    prior=json.loads((HERE/'baseline.json').read_bytes())
    manifest=dict(source=source,base_hashes=prior['base_hashes'],services=prior['services'],files={k:digest(v) for k,v in data.items()},stock_operator=prior['stock_operator'],titles_receipt=prior['titles_receipt'],image=prior['image'],binaries=prior['binaries'],caches=prior['caches'],client=prior['client'],channel=prior['channel'],layout=dict(zip(['size']+fields,layout,strict=True)))
    data['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    sourcecode="""import os,hashlib,base64,gzip
from pathlib import Path
os.umask(0o077)
folder=Path('/opt/nightcap/releases')/stage
folder.mkdir(exist_ok=True,mode=0o700)
for name,enc in files.items():
 assert Path(name).name==name
 raw=gzip.decompress(base64.b64decode(enc,validate=True))
 path=folder/name
 if path.exists():assert not path.is_symlink() and path.read_bytes()==raw
 else:
  with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(stage)
"""
    print(remote('stage='+repr(STAGE)+'\nfiles='+repr({k:base64.b64encode(gzip.compress(v,mtime=0)).decode() for k,v in data.items()})+'\n'+sourcecode))
    (HERE/'staged.json').write_bytes(data['manifest.json'])

def action(name,start):
    assert name in ['preflight','activate','verify']
    code="""from pathlib import Path
import subprocess,json
folder=Path('/opt/nightcap/releases')/stage
cmd=['/usr/bin/python3','-B',str(folder/'release.py'),action]
if action=='verify':
 print(subprocess.check_output(cmd,text=True))
else:
 unit='nightcap-'+stage+'-'+action
 log=folder/(action+'.log')
 if start:
  subprocess.run(['systemd-run','--unit='+unit,'--property=WorkingDirectory='+str(folder),'--property=StandardOutput=append:'+str(log),'--property=StandardError=append:'+str(log),*cmd],check=True)
 state=subprocess.check_output(['systemctl','show',unit,'--property=ActiveState,Result,ExecMainStatus'],text=True)
 print(json.dumps(dict(state=state.splitlines(),log=log.read_text()[-1400:] if log.exists() else '', receipts=[str(p.relative_to(folder)) for p in (folder/'evidence').rglob('*.json')])))
"""
    out=remote('stage='+repr(STAGE)+'\naction='+repr(name)+'\nstart='+repr(start)+'\n'+code,timeout=900)
    if name=='verify':(HERE/'production-verified.json').write_bytes((json.dumps(json.loads(out),indent=2)+'\n').encode())
    print(out)

if __name__=='__main__':
    cli=argparse.ArgumentParser()
    cli.add_argument('action',choices=('stage','preflight','activate','verify','status'))
    cli.add_argument('--source')
    cli.add_argument('--start',action='store_true')
    cli.add_argument('--candidate',action='store_true',help='Isolated rehearsal only; activation prohibited')
    args=cli.parse_args()
    if args.candidate:
        assert args.action in ('stage','preflight','status')
        STAGE='classic-equipment-paths-20261121-candidate-v2'
    if args.action=='stage':stage(args.source,args.candidate)
    elif args.action=='status':
        code="""from pathlib import Path
import subprocess,json
p=Path('/opt/nightcap/releases')/stage
state=subprocess.check_output(['systemctl','show','nightcap-'+stage+'-preflight','--property=ActiveState,Result,ExecMainStatus'],text=True)
log=p/'preflight.log';print(json.dumps(dict(state=state.splitlines(),log=log.read_text()[-2200:] if log.exists() else '')))
"""
        print(remote('stage='+repr(STAGE)+'\n'+code))
    else:
        assert args.action=='verify' or args.start,'Use explicit status for read-only polling'
        action(args.action,args.start)

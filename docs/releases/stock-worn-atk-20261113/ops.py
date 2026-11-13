"""Pinned-host transport for the content-only stock ATK release."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PRIOR=ROOT/'docs/releases/classic-raid-augments-20261112'
sys.path.insert(0,str(PRIOR))
from probe import remote
STAGE='stock-worn-atk-20261113-v1'
SOURCE='690d67f376d367d9111a978543b623789d5e0c6f'

def digest(data):return hashlib.sha256(data).hexdigest()
def save(name,data):(HERE/name).write_bytes((json.dumps(data,indent=2)+'\n').encode())
def call(code,timeout=600,**params):return remote('\n'.join(k+'='+repr(v) for k,v in params.items())+'\n'+code,timeout=timeout)

def stage():
    before=json.loads(call("""
from pathlib import Path
import importlib.util,json,shutil
path=Path('/opt/nightcap/releases/classic-raid-augments-20261112-v2/rollout.py')
s=importlib.util.spec_from_file_location('base',path);op=importlib.util.module_from_spec(s);s.loader.exec_module(op);op.initialize()
g=op.r.compact('game');d=op.read(path.parent/'evidence/activation/deployed.json')
assert g['image_id']==d['image'] and op.r.compact('gateway')['running']
print(json.dumps(dict(game=g,image=g['image_id'],players=op.a.prior.players(),channel=op.sha(op.ROOT/'data/public/channel.json'),wiki=str((op.ROOT/'data/public/wiki/current').readlink()),prior_operator=op.sha(path),free=shutil.disk_usage(op.ROOT).free)))
"""))
    assert before['prior_operator']==digest((PRIOR/'rollout.py').read_bytes().replace(b'\r\n',b'\n'))
    assert before['image']==json.loads((PRIOR/'deployed.json').read_bytes())['game']['image_id']
    save('production-before.json',before)
    layout_source='#include "common/item_data.h"\n#include <cstddef>\n#include <cstdio>\nint main(){printf("%zu %zu %zu %zu",sizeof(EQ::ItemData),offsetof(EQ::ItemData,ID),offsetof(EQ::ItemData,Attack),sizeof(EQ::ItemData::Attack));}'
    shell='cd /tmp/nightcap-raid-augments-shipping-20261112-v3 && clang++ -std=c++20 -Isource -xc++ - -o /tmp/nightcap-atk-layout-20261113 && /tmp/nightcap-atk-layout-20261113'
    values=list(map(int,subprocess.check_output(['docker','exec','-i','akk-stack-eqemu-server-1','sh','-c',shell],input=layout_source.encode()).split()))
    assert values[:2]==[1332,440] and values[3]==4
    item=ROOT/'docs/items/stock-worn-atk'
    data={n:(item/n).read_bytes() for n in ('forward.sql.gz','rollback.sql.gz','changes.csv','production-items.json.gz')}
    data['release.py']=(HERE/'release.py').read_bytes().replace(b'\r\n',b'\n')
    manifest=dict(source=SOURCE,authorization='Push to prod',image=before['image'],channel=before['channel'],prior_operator=before['prior_operator'],layout=dict(zip(('size','ID','Attack','width'),values)),files={k:digest(v) for k,v in data.items()})
    data['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    result=call("""
import base64,hashlib,os,fcntl
from pathlib import Path
os.umask(0o077);root=Path('/opt/nightcap/deploy/production')
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 stage=Path('/opt/nightcap/releases')/NAME;stage.mkdir(mode=0o700)
 for name,encoded in DATA.items():
  path=stage/name;raw=base64.b64decode(encoded,validate=True);assert path.parent==stage and hashlib.sha256(raw).hexdigest()==PINS[name]
  with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(stage)
""",NAME=STAGE,DATA={k:base64.b64encode(v).decode() for k,v in data.items()},PINS={k:digest(v) for k,v in data.items()})
    save('staged.json',manifest);print(result,before['players'],'players')

def action(name,start):
    print(call("""
from pathlib import Path
import json,subprocess
stage=Path('/opt/nightcap/releases')/NAME
log=stage/(ACTION+'.log');unit='nightcap-'+NAME+'-'+ACTION
if START:
 with log.open('x') as f:f.write('Starting '+ACTION+'\\n')
 subprocess.run(['systemd-run','--unit='+unit,'--property=WorkingDirectory='+str(stage),'--property=StandardOutput=append:'+str(log),'--property=StandardError=append:'+str(log),'/usr/bin/python3','-B',str(stage/'release.py'),ACTION],check=True,stdout=subprocess.DEVNULL)
state=subprocess.check_output(['systemctl','show',unit,'--property=LoadState,ActiveState,Result,ExecMainStatus'],text=True)
print(json.dumps(dict(state=state.splitlines(),receipts=sorted(str(p.relative_to(stage/'evidence')) for p in (stage/'evidence').rglob('*.json')),log=log.read_text()[-950:] if log.exists() else '')))
""",NAME=STAGE,ACTION=name,START=start))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('stage','preflight','activate'));parser.add_argument('--start',action='store_true');args=parser.parse_args()
    if args.action=='stage':stage()
    else:action(args.action,args.start)

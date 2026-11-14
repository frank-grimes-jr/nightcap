"""Read running image and cache preimages after any preceding maintenance."""
from pathlib import Path
import sys,json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'docs/releases/classic-raid-augments-20261112'))
from probe import remote
q="""import importlib.util,json,subprocess
from pathlib import Path
path=Path('/opt/nightcap/releases/stock-worn-atk-20261113-v1/release.py')
s=importlib.util.spec_from_file_location('stock',path);op=importlib.util.module_from_spec(s);s.loader.exec_module(op);op.initialize()
game=op.r.compact('game');gw=op.r.compact('gateway')
out=dict(game=game,gateway=gw)
receipt=path.parent.parent/'titles-live-20261114-v1/evidence/activation/deployed.json'
if gw['running'] and game['health']=='healthy' and receipt.is_file():
 bins={k[4:]:v for k,v in op.r.image_hashes(game['image_id']).items() if k.startswith('bin/')}
 runtime=op.r.running(game['image_id'],bins)
 assert not any(runtime['errors'].values())
 assert json.loads(receipt.read_bytes())['gateway_open']
 out.update(client=json.loads(receipt.read_bytes())['client_release'],titles_receipt=op.sha(receipt),image=game['image_id'],binaries=bins,workers=sum(r[0]=='zone' for r in runtime['processes']),channel=op.sha(op.ROOT/'data/public/channel.json'),caches=op.h.caches(),stock_operator=op.sha(path),players=op.a.prior.players())
else:
 out['active_units']=subprocess.check_output(['systemctl','list-units','--no-legend','nightcap-*'],text=True).splitlines()
print(json.dumps(out))
"""
if __name__=='__main__':
 out=json.loads(remote(q));print(out)
 if 'image' not in out:sys.exit(2)
 assert out['workers']==12
 (HERE/'baseline.json').write_text(json.dumps(out,indent=2)+'\n')

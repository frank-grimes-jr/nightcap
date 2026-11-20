from pathlib import Path
import subprocess,json,sys
W=Path('E:/EQ_Local_Dev/_worktrees/aa-availability')
sys.path.insert(0,str(W/'docs/releases/classic-raid-augments-20261112'))
from probe import remote
A=Path(__file__).resolve().parent
q="""import importlib.util,json
from pathlib import Path
path=Path('/opt/nightcap/releases/stock-worn-atk-20261113-v1/release.py')
s=importlib.util.spec_from_file_location('stock',path);op=importlib.util.module_from_spec(s);s.loader.exec_module(op);op.initialize()
game=op.r.compact('game')
out=dict(image=game['image_id'],services={k:op.r.compact(k) for k in ('game','gateway','db','web','tunnel')},base_hashes=op.r.image_hashes(game['image_id']),caches=op.h.caches(),channel=op.sha(op.ROOT/'data/public/channel.json'),stock_operator=op.sha(path),players=op.a.prior.players())
out['rules']=op.op.sql("SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name IN ('Character:RestRegenTimeToActivate','Character:RestRegenRaidTimeToActivate') ORDER BY ruleset_id,rule_name")
out['wiki']=str((op.ROOT/'data/public/wiki/current').readlink())
print(json.dumps(out))
"""
data=json.loads(remote(q));(A/'production-before.json').write_text(json.dumps(data,indent=2))
print({k:data[k] for k in ('players','wiki')})
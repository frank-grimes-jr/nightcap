"""Read current production identities; no state or player data changes."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'docs/releases/classic-raid-augments-20261112'))
from probe import remote

CODE = '''import importlib.util,json,shutil,datetime
from pathlib import Path
path=Path('/opt/nightcap/releases/stock-worn-atk-20261113-v1/release.py')
s=importlib.util.spec_from_file_location('stock',path)
op=importlib.util.module_from_spec(s);s.loader.exec_module(op);op.initialize()
game=op.r.compact('game')
out=dict(captured_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 image=game['image_id'],services={k:op.r.compact(k) for k in ('game','gateway','db','web','tunnel')},
 base_hashes=op.r.image_hashes(game['image_id']),caches=op.h.caches(),
 channel=op.sha(op.ROOT/'data/public/channel.json'),stock_operator=op.sha(path),
 players=op.a.prior.players(),free=shutil.disk_usage(op.ROOT).free)
out['wiki']=str((op.ROOT/'data/public/wiki/current').readlink())
print(json.dumps(out))
'''

if __name__ == '__main__':
    report = json.loads(remote(CODE))
    build = json.loads((HERE / 'build.json').read_bytes())
    assert report['base_hashes']['bin/zone'] == build['baseline']['zone'], 'Live native baseline changed; rebuild required'
    assert report['free'] >= 3 * 1024**3, 'Insufficient release/backup headroom'
    (HERE / 'production-before.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('captured_utc','players','free','image','wiki')}))

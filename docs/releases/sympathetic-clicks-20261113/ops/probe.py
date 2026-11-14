"""Capture the current public release identities and two-click preimages."""
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
prior_probe = ROOT / 'docs/releases/classic-raid-augments-20261112/probe.py'
spec = importlib.util.spec_from_file_location('raid_probe', prior_probe)
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)

STAGE = 'sympathetic-clicks-20261113-v1'
PREVIOUS = 'stock-worn-atk-20261113-v1'
BOOT = """
import importlib.util, json, pathlib, shutil
from pathlib import Path
stages = Path('/opt/nightcap/releases')
path = stages / 'stock-worn-atk-20261113-v1/release.py'
spec = importlib.util.spec_from_file_location('stock_atk', path)
stock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stock)
stock.initialize()
r, a, op = stock.r, stock.a, stock.op
"""

def call(code, **kwargs):
    header = '\n'.join(k + '=' + repr(v) for k, v in kwargs.items())
    return transport.remote(header + '\n' + code, timeout=1200)

def write(name, data):
    (HERE / name).write_bytes((json.dumps(data, indent=2) + '\n').encode())

def main():
    result = json.loads(call(BOOT + """
released = stock.read(stock.EVIDENCE/'activation/deployed.json')
services = {n:r.compact(n) for n in ('game','gateway','db','web','tunnel')}
game = services['game']
assert released['gateway_open'] and released['runtime']['image_id']==game['image_id']
assert services['gateway']['running'] and game['health']=='healthy'
report = dict(services=services, base_hashes=r.image_hashes(game['image_id']), players=a.prior.players(),
              prior_operator=stock.sha(path), prior_receipt=stock.sha(stock.EVIDENCE/'activation/deployed.json'),
              channel=stock.sha(stock.ROOT/'data/public/channel.json'),
              wiki=str((stock.ROOT/'data/public/wiki/current').readlink()),
              caches=stock.h.caches(), free=shutil.disk_usage(stock.ROOT).free,
              items=op.sql('SELECT id,Name,clickeffect,clicktype,casttime,maxcharges,focuseffect FROM items WHERE id IN (610150,610338) ORDER BY id').splitlines(),
              markers=op.sql('SELECT id,name FROM spells_new WHERE id IN (44379,44380)').splitlines(),
              descriptions=op.sql('SELECT id,type FROM db_str WHERE id IN (44379,44380)').splitlines())
print(json.dumps(report))
"""))
    assert result['base_hashes']['bin/zone'].startswith('a0506a16') and not result['markers'] and not result['descriptions']
    write('production-before.json', result)
    print(json.dumps({k: result[k] for k in ('players','items','channel','free','wiki')}, indent=2))

if __name__ == '__main__':
    main()

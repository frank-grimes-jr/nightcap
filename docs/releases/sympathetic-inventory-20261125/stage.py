"""Capture the currently running build and signed channel for this release."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

stage=Path(__file__).resolve().parent
previous=stage.parent/'classic-equipment-paths-20261121-v1'
load=lambda path: json.loads(path.read_bytes())
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()
base=load(previous/'manifest.json')
stock=stage.parent/'stock-worn-atk-20261113-v1/release.py'
assert sha(stock)==base['stock_operator']
spec=importlib.util.spec_from_file_location('stock_release',stock)
op=importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)
op.initialize()
r=op.r
services={k:r.compact(k) for k in ('game','gateway','web','tunnel','db')}
image=services['game']['image_id']
hashes=r.image_hashes(image)
root=Path('/opt/nightcap/deploy/production')
channel=root/'data/public/channel.json'
manifest=dict(source=sys.argv[1],stock_operator=base['stock_operator'],titles_receipt=base['titles_receipt'],
    layout=base['layout'],click_layout=load(stage.parent/'sympathetic-clicks-20261113-v1/manifest.json')['layout'],
    image=image,base_hashes=hashes,binaries={k:hashes['bin/'+k] for k in base['binaries']},
    files={n:sha(stage/n) for n in ('release.py','before.sql','verify.sql','forward.sql','rollback.sql','spells.sql')},
    services=services,caches=op.h.caches(),channel=sha(channel),client=json.loads(base64.b64decode(load(channel)['manifest']))['release'])
with (stage/'manifest.json').open('x') as out:
    json.dump(manifest,out,indent=2)

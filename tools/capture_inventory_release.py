"""Capture current native/client/wiki release identities read-only; no player rows."""
import base64
import hashlib
from inventory_release_support import ROOT,HERE,ART,remote,save


def main():
    result=remote('''from pathlib import Path
import base64,hashlib,importlib.util,json,shutil
from urllib.parse import urlsplit
root=Path('/opt/nightcap/deploy/production');public=root/'data/public'
prior=Path('/opt/nightcap/releases/dot-no-initial-damage-20261112-v2/rollout.py')
spec=importlib.util.spec_from_file_location('inventory_read_only_baseline',prior);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=m.initialize();services={n:r.r.compact(n) for n in ('game','gateway','db','web','tunnel')}
raw=(public/'channel.json').read_bytes();manifest=json.loads(base64.b64decode(json.loads(raw)['manifest']))
assets={}
for f in manifest['files']:
 if f['path'] not in ('dinput8.dll','nightcap-patch-sites.json','nightcap-patches.cfg','uifiles/nightcap/equi_inventory.xml'):continue
 p=public/urlsplit(f['url']).path.lstrip('/');assert p.resolve().is_relative_to(public.resolve()) and not p.is_symlink()
 data=p.read_bytes();assert len(data)==f['size'] and hashlib.sha256(data).hexdigest()==f['sha256']
 assets[f['path']]=base64.b64encode(data).decode()
wiki=public/'wiki/current';assert wiki.is_symlink()
wiki_release=wiki.readlink().name
history=root/'website-history'/wiki_release
out={'status':'read_only_current_baseline','services':services,'players':r.a.prior.players(),
 'base_image_id':services['game']['image_id'],'base_hashes':r.r.image_hashes(services['game']['image_id']),
 'prior_operator_sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),
 'client_release':manifest['release'],'client_channel_sha256':hashlib.sha256(raw).hexdigest(),
 'channel_base64':base64.b64encode(raw).decode(),'assets_base64':assets,
 'wiki_release':wiki_release,'wiki_manifest':json.loads((history/'manifest.json').read_text()),
 'free_bytes':shutil.disk_usage(root).free}
print(json.dumps(out))
''')
    dest=ART/'baseline-assets';dest.mkdir(parents=True,exist_ok=True)
    for name,raw in result.pop('assets_base64').items():
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(raw))
    raw=base64.b64decode(result.pop('channel_base64'))
    assert hashlib.sha256(raw).hexdigest()==result['client_channel_sha256']
    assert raw==(ART/'channel.json').read_bytes(),'Client baseline changed since audit'
    save(ART/'release-baseline.json',result)
    print({k:result[k] for k in ('status','players','base_image_id','client_release','wiki_release','free_bytes')})


if __name__=='__main__':main()

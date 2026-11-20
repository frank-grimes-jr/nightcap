"""Read current channel, retained runtime assets and website identities."""
import base64
from support import ART,HERE,remote,save,sha
result=remote("""from pathlib import Path
import base64,hashlib,json,shutil,subprocess
from urllib.parse import urlsplit
root=Path('/opt/nightcap/deploy/production');public=root/'data/public'
raw=(public/'channel.json').read_bytes()
manifest=json.loads(base64.b64decode(json.loads(raw)['manifest']))
assets={}
for f in manifest['files']:
 if f['path'] not in ('uifiles/nightcap/equi_inventory.xml','dinput8.dll','nightcap-patch-sites.json','nightcap-patches.cfg'):continue
 p=public/urlsplit(f['url']).path.lstrip('/')
 assert p.resolve().is_relative_to(public.resolve()) and not p.is_symlink()
 b=p.read_bytes();assert len(b)==f['size'] and hashlib.sha256(b).hexdigest()==f['sha256']
 assets[f['path']]=base64.b64encode(b).decode()
services={}
for name in ('game','gateway','db','web','tunnel'):
 cid=subprocess.check_output(['docker','compose','ps','-aq',name],cwd=root,text=True).strip()
 row=json.loads(subprocess.check_output(['docker','inspect',cid]))[0];state=row['State']
 assert state['Running'] and not state.get('OOMKilled')
 if name in ('game','db'):assert state['Health']['Status']=='healthy'
 services[name]={k:row[k] for k in ('Id','Image','RestartCount')}
 services[name]['state']={k:state[k] for k in ('Running','StartedAt','OOMKilled')}
wiki=public/'wiki/current';assert wiki.is_symlink();release=wiki.readlink().name
print(json.dumps(dict(release=manifest['release'],channel=base64.b64encode(raw).decode(),assets=assets,
 channel_sha256=hashlib.sha256(raw).hexdigest(),services=services,free_bytes=shutil.disk_usage(root).free,
 wiki_release=release,wiki_manifest=json.loads((root/'website-history'/release/'manifest.json').read_bytes()),
 config_sha256=hashlib.sha256((root/'nginx.conf').read_bytes()).hexdigest(),config_inode=(root/'nginx.conf').stat().st_ino)))
""")
raw=base64.b64decode(result.pop('channel'))
assert raw==(ART/'channel.json').read_bytes(),'Channel changed since candidate; review instead of overwriting'
for name,encoded in result.pop('assets').items():
 p=ART/'baseline-assets'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(encoded))
assert sha(ART/'baseline-assets/uifiles/nightcap/equi_inventory.xml')==sha(ART/'before.xml')
save(HERE/'baseline.json',result)
print({k:result[k] for k in ('release','channel_sha256','wiki_release','free_bytes')})

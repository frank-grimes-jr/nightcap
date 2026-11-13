from pathlib import Path
import fcntl,hashlib,importlib.util,json,re
root=Path('/opt/nightcap/deploy/production')
s=importlib.util.spec_from_file_location('published_wiki',Path('/opt/nightcap/releases/wiki-dot-no-initial-damage-20261112-v2/deploy.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with (root/'.deployment.lock').open('r') as outer:
 fcntl.flock(outer,fcntl.LOCK_SH|fcntl.LOCK_NB)
 with (root/'website-history/.lock').open('r') as lock:
  fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
  p=root/'data/public/wiki/current';assert p.is_symlink(); pointer=p.readlink();assert re.fullmatch(r'releases/\d{8}-[a-z0-9-]+',str(pointer))
  release=pointer.name;manifest_path=root/'website-history'/release/'manifest.json';manifest=json.loads(manifest_path.read_text())
  before=m.services();assert len(before)==5
  config=m.sha((root/'nginx.conf').read_bytes());channel=m.sha((root/'data/public/channel.json').read_bytes());inode=(root/'nginx.conf').stat().st_ino
  m.verify(manifest)
  assert p.readlink()==pointer and m.services()==before and m.sha((root/'nginx.conf').read_bytes())==config
  print(json.dumps(dict(status='PASS',release=release,pointer=str(pointer),manifest=manifest,config_sha256=config,config_inode=inode,channel_sha256=channel,services=before,scope='Read-only current origin reproduction baseline; no gameplay or wiki changes'),indent=2))

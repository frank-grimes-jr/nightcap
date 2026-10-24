"""Publish the paired player documentation after verified gameplay activation."""
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
def remote(source):
 result=subprocess.run(SSH+['sudo -n python3 -'],input=source,text=True,capture_output=True,timeout=300)
 if result.returncode:raise RuntimeError(result.stderr[-3000:])
 return result.stdout
WIKI=Path('E:/EQ_Local_Dev/_worktrees/hole-keyless-wiki/wiki')
ART=Path('E:/EQ_Local_Dev/artifacts')
RELEASE='20261024-hole-keyless-v1'

def main():
 before=json.loads(remote("""from pathlib import Path
import hashlib,json
base=Path('/opt/nightcap/deploy/production')
p=Path('/opt/nightcap/backups/hole-keyless-passage-20261024/result.json')
assert p.exists() and json.loads(p.read_text())['health_passed']
name=(base/'data/public/wiki/current').readlink().name
print(json.dumps({'wiki':name,'manifest':json.loads((base/'website-history'/name/'manifest.json').read_text()),'config_sha256':hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()}))
"""))
 assert before['wiki']=='20261023-camil-chapterhouse-v1','Review any concurrent publication first'
 archive=ART/'hole-keyless-wiki-20261024-matched.tar.gz';manifest=archive.with_suffix('.json')
 after=json.loads(manifest.read_text());assert len(after)==483
 added=set(after)-set(before['manifest']);assert not added
 assert set(before['manifest'])<=set(after)
 changed={n for n,h in before['manifest'].items() if after[n]!=h}
 allowed={'index.html','features.html','dungeon-modes.html','recent-changes.html','travel.html','zone-hole.html','all-pages.html','search-index.json','sitemap.xml'}
 assert changed<=allowed,changed-allowed
 report={'previous':before['wiki'],'release':RELEASE,'files':len(after),'added':sorted(added),'changed':sorted(changed),'preserved':len(after)-len(added)-len(changed)}
 (HERE/'wiki-package-review.json').write_text(json.dumps(report,indent=2)+'\n')
 files=[archive,manifest,WIKI/'update.py',WIKI/'deploy.py']
 pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 upload='/home/ubuntu/hole-keyless-wiki-20261024'
 subprocess.run(SSH+['mkdir -m 700 '+upload],check=True)
 subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,files),SSH[-1]+':'+upload+'/'],check=True,timeout=180)
 source=f'''from pathlib import Path
import contextlib,fcntl,hashlib,io,json,shutil,sys,types
upload=Path({upload!r});stage=Path('/opt/nightcap/releases/hole-keyless-wiki-20261024')
pins={pins!r};base=Path('/opt/nightcap/deploy/production')
assert {{p.name for p in upload.iterdir()}}==set(pins)
stage.mkdir(mode=0o700,exist_ok=False)
for name,digest in pins.items():
 p=upload/name;assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest
 shutil.copyfile(p,stage/name)
sys.path.insert(0,str(stage));import update
with (base/'website-history/.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 buffer=io.StringIO()
 with contextlib.redirect_stdout(buffer):
  update.main(types.SimpleNamespace(archive=stage/{archive.name!r},manifest=stage/{manifest.name!r},release={RELEASE!r},expected_release={before['wiki']!r},expected_config_sha={before['config_sha256']!r}))
 result=json.loads(buffer.getvalue());(stage/'published.json').write_text(json.dumps(result,indent=2)+'\\n')
 print(json.dumps(result))
'''
 result=json.loads(remote(source));(HERE/'wiki-publication.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()

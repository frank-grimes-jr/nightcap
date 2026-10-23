"""Publish verified AA guidance with existing guarded wiki/player-site publishers."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
WIKI=Path('C:/Users/verre/.codex/worktrees/aa-level-wiki/EQ_Local_Dev')
ART=Path('E:/EQ_Local_Dev/artifacts/aa-level-progression-20261023')
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh',
     '-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
RELEASE='20261023-aa-level-v1'
def remote(source,timeout=240):
    p=subprocess.run(SSH+['sudo -n python3 -'],input=source,text=True,capture_output=True,timeout=timeout)
    if p.returncode: raise RuntimeError('Inspect remote receipts before retry: '+p.stderr[-2500:])
    return p.stdout
def main():
    before=json.loads(remote("""
from pathlib import Path
import hashlib,json
base=Path('/opt/nightcap/deploy/production')
wiki=(base/'data/public/wiki/current').readlink().name
guide=(base/'data/public/player-site/current').readlink().name
manifest=json.loads((base/'website-history'/wiki/'manifest.json').read_text())
guide_files={n:hashlib.sha256((base/'data/public/player-site/current'/n).read_bytes()).hexdigest() for n in ['index.html','site-assets/site.css','site-assets/moon.svg','site-assets/traders-at-dusk.png','site-assets/master-of-three.png']}
print(json.dumps({'wiki':wiki,'guide':guide,'wiki_manifest':manifest,'guide_manifest':guide_files,'config_sha256':hashlib.sha256((base/'nginx.conf').read_bytes()).hexdigest()}))
"""))
    wiki=ART/'wiki-live-v1.tar.gz'; guide=ART/'guide-live-v1.tar.gz'
    wm=json.loads(wiki.with_suffix('.json').read_text()); gm=json.loads(guide.with_suffix('.json').read_text())
    expected=json.loads((OUT/'guides-before.json').read_text(encoding='utf-8'))
    assert before==expected,'Published guide/config baseline drift'
    assert set(wm)==set(before['wiki_manifest']) and len(wm)==467
    review=json.loads((OUT/'guide-package-review.json').read_text(encoding='utf-8'))
    assert wm==review['wiki_manifest'] and gm==review['guide_manifest'],'Reviewed package drift'
    changed={n for n in wm if wm[n]!=before['wiki_manifest'][n]}
    assert {n for n in gm if gm[n]!=before['guide_manifest'][n]}=={'index.html'}
    files=[wiki,wiki.with_suffix('.json'),guide,guide.with_suffix('.json'),
           WIKI/'wiki/update.py',WIKI/'wiki/deploy.py',ROOT/'deploy/production/player-site-deploy.py']
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload='/home/ubuntu/aa-level-guides-20261023'
    # Fixed new dedicated upload directory; never reuse an uncertain attempt.
    p=subprocess.run(SSH+['mkdir -m 700 '+upload],capture_output=True,text=True,timeout=30)
    if p.returncode: raise RuntimeError(p.stderr)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,files),SSH[-1]+':'+upload+'/'],check=True,timeout=120)
    source=f"""
from pathlib import Path
import hashlib,json,shutil,subprocess
upload=Path({upload!r});stage=Path('/opt/nightcap/releases/aa-level-guides-20261023')
pins={pins!r};base=Path('/opt/nightcap/deploy/production')
assert {{p.name for p in upload.iterdir()}}==set(pins)
stage.mkdir(mode=0o700,exist_ok=False)
for name,digest in pins.items():
 p=upload/name
 assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest
 shutil.copyfile(p,stage/name)
 assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
config=(base/'nginx.conf').read_bytes()
assert hashlib.sha256(config).hexdigest()=={before['config_sha256']!r}
(stage/'current-nginx.conf').write_bytes(config)
import contextlib,fcntl,importlib.util,io,sys,types
sys.path.insert(0,str(stage))
import update
spec=importlib.util.spec_from_file_location('player_site',stage/'player-site-deploy.py')
player=importlib.util.module_from_spec(spec);spec.loader.exec_module(player)
def captured(fn,*args):
 buffer=io.StringIO()
 with contextlib.redirect_stdout(buffer):fn(*args)
 return json.loads(buffer.getvalue())
with (base/'website-history/.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert (base/'data/public/wiki/current').readlink()==Path('releases')/{before['wiki']!r}
 assert (base/'data/public/player-site/current').readlink().name=={before['guide']!r}
 expected_guide={before['guide_manifest']!r}
 for name,digest in expected_guide.items():assert hashlib.sha256((base/'data/public/player-site/current'/name).read_bytes()).hexdigest()==digest
 assert (base/'nginx.conf').read_bytes()==config
 wiki=captured(update.main,types.SimpleNamespace(archive=stage/{wiki.name!r},manifest=stage/{wiki.with_suffix('.json').name!r},release={RELEASE!r},expected_release={before['wiki']!r},expected_config_sha={before['config_sha256']!r}))
 sys.argv=['player-site-deploy.py','stage',str(stage/{guide.name!r}),str(stage/{guide.with_suffix('.json').name!r}),'20261023-aa-level-guide-v1',{before['config_sha256']!r},str(stage/'current-nginx.conf')]
 guide_stage=captured(player.main)
 sys.argv=['player-site-deploy.py','activate','20261023-aa-level-guide-v1']
 guide_live=captured(player.main)
 report={{'wiki':wiki,'guide_stage':guide_stage,'guide':guide_live,'config_unchanged':(base/'nginx.conf').read_bytes()==config}}
 (stage/'published.json').write_text(json.dumps(report,indent=2)+chr(10))
 print(json.dumps(report))

"""
    report=json.loads(remote(source,timeout=420).splitlines()[-1])
    report['changed_wiki_files']=sorted(changed)
    (OUT/'guides-publication.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()

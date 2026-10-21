"""Publish verified AA guidance with existing guarded wiki/player-site publishers."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent.parent
ART=Path('E:/EQ_Local_Dev/artifacts/aa-point-cost-40000-20261021')
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh',
     '-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
RELEASE='20261021-aa-pacing-v1'
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
    wiki=ART/'wiki20261021-aa-pacing-v1.tar.gz'; guide=ART/'guide20261021-aa-pacing-v1.tar.gz'
    wm=json.loads(wiki.with_suffix('.json').read_text()); gm=json.loads(guide.with_suffix('.json').read_text())
    assert before['wiki']=='20261019-thj-behaviors-live-v1','Review newer wiki before publication'
    assert set(wm)==set(before['wiki_manifest']) and len(wm)==465
    changed={n for n in wm if wm[n]!=before['wiki_manifest'][n]}
    assert changed <= {'index.html','features.html','multiclass.html','getting-started.html','commands.html','recent-changes.html','unreleased.html','search-index.json'},changed
    old_index=subprocess.check_output(['git','show','059fd49:index.html'],cwd=ROOT)
    # Git stores LF, while the historical package may have CRLF.
    assert before['guide_manifest']['index.html'] in {
        hashlib.sha256(old_index).hexdigest(),
        hashlib.sha256(old_index.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()
    },'Private guide source drift; inspect before replacing'
    assert {n for n in gm if gm[n]!=before['guide_manifest'][n]}=={'index.html'}
    (OUT/'guides-before.json').write_text(json.dumps(before,indent=2)+'\n')
    files=[wiki,wiki.with_suffix('.json'),guide,guide.with_suffix('.json'),
           ROOT/'wiki/update.py',ROOT/'wiki/deploy.py',ROOT/'deploy/production/player-site-deploy.py']
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    upload='/home/ubuntu/aa-pacing-guides-20261021'
    # Fixed new dedicated upload directory; never reuse an uncertain attempt.
    p=subprocess.run(SSH+['mkdir -m 700 '+upload],capture_output=True,text=True,timeout=30)
    if p.returncode: raise RuntimeError(p.stderr)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,files),SSH[-1]+':'+upload+'/'],check=True,timeout=120)
    source=f"""
from pathlib import Path
import hashlib,json,shutil,subprocess
upload=Path({upload!r});stage=Path('/opt/nightcap/releases/aa-pacing-guides-20261021')
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
wiki=subprocess.check_output(['python3',str(stage/'update.py'),str(stage/{wiki.name!r}),str(stage/{wiki.with_suffix('.json').name!r}),{RELEASE!r},{before['wiki']!r},{before['config_sha256']!r}],timeout=180,text=True)
print('WIKI '+wiki,flush=True)
assert (base/'data/public/player-site/current').readlink().name=={before['guide']!r}
guide_stage=subprocess.check_output(['python3',str(stage/'player-site-deploy.py'),'stage',str(stage/{guide.name!r}),str(stage/{guide.with_suffix('.json').name!r}),'20261021-aa-pacing-guide-v1',{before['config_sha256']!r},str(stage/'current-nginx.conf')],timeout=120,text=True)
guide_live=subprocess.check_output(['python3',str(stage/'player-site-deploy.py'),'activate','20261021-aa-pacing-guide-v1'],timeout=120,text=True)
print('GUIDE '+guide_stage+guide_live,flush=True)
print(json.dumps({{'wiki':json.loads(wiki),'guide_stage':json.loads(guide_stage),'guide':json.loads(guide_live),'config_unchanged':(base/'nginx.conf').read_bytes()==config}}))
"""
    report=json.loads(remote(source,timeout=420).splitlines()[-1])
    report['changed_wiki_files']=sorted(changed)
    (OUT/'guides-publication.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()

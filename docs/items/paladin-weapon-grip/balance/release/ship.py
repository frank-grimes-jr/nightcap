"""Stage the approved exact server/quest package and preflight; never activate."""
from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
ART=ROOT/'artifacts/paladin-grip-release-20261028'
STAGE='/opt/nightcap/releases/paladin-progression-20261028-v1'
UPLOAD='/home/ubuntu/paladin-progression-20261028-v1.tar.gz'
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def remote(code,timeout=900):
    p=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,capture_output=True,timeout=timeout)
    if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-6000:])
    return json.loads(p.stdout)

def main(baseline, capture):
    import sys
    sys.path.insert(0,str(ROOT/'tools'))
    import paladin_grip_preflight as guard
    reference=json.loads(capture.read_text(encoding='utf-8'));guard.validate_fresh(reference)
    base=json.loads(baseline.read_text(encoding='utf-8'))
    assert sha(ART/'bundle/manifest.json')==json.loads((HERE/'bundle.json').read_text())['manifest_sha256']
    bundle=json.loads((ART/'bundle/manifest.json').read_text())
    for path,digest in bundle['source_sha256'].items():assert sha(ROOT/'server-mods/code'/path)==digest,path
    signed=json.loads((ART/'client-signed/verification.json').read_text())
    assert signed['previous_channel_sha256']==base['client_channel_sha256']
    assert sha(ART/'client-signed/channel.json')==signed['channel_sha256']
    package=ART/'server-package';package.mkdir(exist_ok=False)
    sources={n:ART/'bundle'/n for n in bundle['files'] if n.startswith(('bin/','quests/'))}
    assert len(sources)==10
    sources['rollout.py']=HERE/'rollout.py'
    for name,path in sources.items():
        if name!='rollout.py':
            assert sha(path)==bundle['files'][name]['sha256'],name
            assert path.stat().st_size==bundle['files'][name]['size'],name
        if name.startswith('quests/'):
            assert path.read_bytes()==(ROOT/'server-mods'/name).read_bytes(),name
        target=package/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
    files={n:sha(package/n) for n in sources}
    m={k:base[k] for k in ['base_image_id','base_hashes','client_channel_sha256']}
    m.update(helpers={k:{'path':v['path'],'sha256':v['sha256']} for k,v in base['helpers'].items()},
             contract={k:base['contract'][k] for k in ['path','sha256']},
             files=files,candidate_hashes={n:h for n,h in files.items() if n.startswith('bin/')},
             zone_sha256=files['bin/zone'],quest_preimages={n:reference['scripts'][n]['sha256'] for n in guard.QUESTS},
             runtime_preimage=base['runtime'],client_channel_new_sha256=signed['channel_sha256'],
             source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             owner_live_qa_authorized=True,authorization='AUTHORIZATION.md',reference_observed_utc=reference['observed_utc'])
    (package/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    archive=ART/'server-package.tar.gz'
    with tarfile.open(archive,'x:gz',compresslevel=1) as tar:
        for name in [*files,'manifest.json']:
            data=(package/name).read_bytes();info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o755 if name.startswith('bin/') else 0o600;tar.addfile(info,io.BytesIO(data))
    ready=remote(f"""from pathlib import Path
import json,shutil
assert not Path({STAGE!r}).exists() and not Path({UPLOAD!r}).exists(),'Existing attempt; inspect'
assert shutil.disk_usage('/opt/nightcap').free>={sum((package/n).stat().st_size for n in files if n.startswith('bin/'))*3+672*1024**2}
print(json.dumps({{'ready':True}}))
""")
    assert ready['ready']
    subprocess.run([str(Path(SSH[0]).with_name('scp.exe')),*SSH[1:-1],str(archive),SSH[-1]+':'+UPLOAD],check=True,timeout=180)
    result=remote(f"""from pathlib import Path
import hashlib,json,tarfile,subprocess,shutil
upload=Path({UPLOAD!r});stage=Path({STAGE!r});expected={list(files)+['manifest.json']!r}
assert hashlib.sha256(upload.read_bytes()).hexdigest()=={sha(archive)!r}
stage.mkdir(mode=0o700,parents=True,exist_ok=False)
with tarfile.open(upload,'r:gz') as tar:
 members=tar.getmembers();assert len(members)==len(expected) and {{m.name for m in members}}==set(expected)
 for member in members:
  assert member.isfile();dest=stage/member.name;assert dest.resolve().is_relative_to(stage)
  dest.parent.mkdir(mode=0o700,parents=True,exist_ok=True);dest.write_bytes(tar.extractfile(member).read());dest.chmod(member.mode)
assert hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest()=={sha(package/'manifest.json')!r}
for name,digest in json.loads((stage/'manifest.json').read_text())['files'].items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
# Delete only this exact authenticated transfer; local and extracted copies remain.
assert upload.resolve()==Path({UPLOAD!r});upload.unlink()
with (stage/'preflight.log').open('x') as log:p=subprocess.run(['python3',str(stage/'rollout.py'),'preflight'],stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0,(stage/'preflight.log').read_text()[-6000:]
p=json.loads((stage/'evidence/preflight.json').read_text())
print(json.dumps({{'result':'PASS','stage':str(stage),'image':p['image'],'checks':p['checks'],'manifest_sha256':p['manifest_sha256'],'free_bytes':shutil.disk_usage(stage).free,'production_activated':False}}))
""")
    (HERE/'preflight-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);a=p.parse_args();main(a.baseline,a.capture)

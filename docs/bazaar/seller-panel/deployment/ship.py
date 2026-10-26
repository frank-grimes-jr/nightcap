"""Stage the verified zone candidate and run preflight only; never activate."""
import hashlib,io,json,os,subprocess,tarfile,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
ART=ROOT/'docs/bazaar/private/seller-panel/package'
STAGE='/opt/nightcap/releases/bazaar-grip-20261026'
UPLOAD='/home/ubuntu/bazaar-grip-20261026.tar.gz'
spec=importlib.util.spec_from_file_location('configured_remote',ROOT/'docs/quests/camil-chapterhouse/deployment/remote.py')
configured=importlib.util.module_from_spec(spec);spec.loader.exec_module(configured);SSH=list(configured.SSH)
if os.environ.get('NIGHTCAP_DEPLOY_SSH_TARGET'):SSH[-1]=os.environ['NIGHTCAP_DEPLOY_SSH_TARGET']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def remote(code):
    p=subprocess.run(SSH+['sudo -n python3 -'],input=code.encode(),capture_output=True,timeout=900)
    if p.returncode:raise RuntimeError((p.stdout+p.stderr).decode()[-6000:])
    return json.loads(p.stdout)

def main():
    build=json.loads((ROOT/'docs/bazaar/private/seller-panel/integrated-build.json').read_text())
    assert build['status']=='complete integrated zone/world/shared_memory build passed; not installed'
    for name,digest in build['source_files'].items():
        path=ROOT/'server-mods/code'/name
        if path.is_file():assert hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,name
    base=json.loads((ROOT/'docs/bazaar/private/seller-panel/production-before.json').read_text())
    proof=json.loads((ROOT/'docs/bazaar/private/seller-panel/runtime-identity.json').read_text())
    assert set(proof)=={'zone','world','shared_memory'}
    ART.mkdir(exist_ok=False);(ART/'bin').mkdir()
    for name,result in proof.items():
        assert result['status']=='PASS' and result['original_sha256']==build['binaries'][name]
        binary=ART/'bin'/name
        subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-paladin-grip-20261026-v1/runtime-bin/'+name,str(binary)],check=True)
        assert sha(binary)==result['sha256']
    candidates={'bin/'+n:result['sha256'] for n,result in proof.items()}
    m={k:base[k] for k in ('base_image_id','base_hashes','helpers','client_channel_sha256','contract')}
    m.update(zone_sha256=candidates['bin/zone'],candidate_hashes=candidates,source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),owner_live_qa_authorized=True,files={**candidates,'rollout.py':sha(HERE/'rollout.py')},runtime_identity=proof)
    (ART/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    package=ART/'bazaar-grip-20261026.tar.gz'
    with tarfile.open(package,'x:gz',compresslevel=1) as tar:
        for name,p in [(n,ART/n) for n in candidates]+[('rollout.py',HERE/'rollout.py'),('manifest.json',ART/'manifest.json')]:
            data=p.read_bytes();entry=tarfile.TarInfo(name);entry.size=len(data);entry.mode=0o755 if name.startswith('bin/') else 0o600;tar.addfile(entry,io.BytesIO(data))
    guard=remote(f"""from pathlib import Path
import json
assert not Path({STAGE!r}).exists() and not Path({UPLOAD!r}).exists(),'Existing staging attempt; inspect'
print(json.dumps({{'ready':True}}))
""")
    assert guard['ready']
    subprocess.run([str(Path(SSH[0]).with_name('scp.exe')),*SSH[1:-1],str(package),SSH[-1]+':'+UPLOAD],check=True,timeout=180)
    result=remote(f"""from pathlib import Path
import hashlib,json,tarfile,subprocess,shutil
upload=Path({UPLOAD!r});stage=Path({STAGE!r})
assert hashlib.sha256(upload.read_bytes()).hexdigest()=={sha(package)!r}
stage.mkdir(mode=0o700,parents=True,exist_ok=False)
with tarfile.open(upload,'r:gz') as tar:
 members=tar.getmembers();assert {{m.name for m in members}}=={{'bin/zone','bin/world','bin/shared_memory','rollout.py','manifest.json'}} and len(members)==5
 for member in members:
  assert member.isfile()
  dest=stage/member.name;assert dest.resolve().is_relative_to(stage)
  dest.parent.mkdir(mode=0o700,exist_ok=True);dest.write_bytes(tar.extractfile(member).read());dest.chmod(member.mode)
manifest=json.loads((stage/'manifest.json').read_text())
for n,h in manifest['files'].items():assert hashlib.sha256((stage/n).read_bytes()).hexdigest()==h
assert hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest()=={sha(ART/'manifest.json')!r}
# This exact task upload has a verified local package and verified extracted copy.
assert upload.resolve()==Path({UPLOAD!r});upload.unlink()
with (stage/'preflight.log').open('x') as log:r=subprocess.run(['python3',str(stage/'rollout.py'),'preflight'],stdout=log,stderr=subprocess.STDOUT)
if r.returncode:raise RuntimeError((stage/'preflight.log').read_text()[-5000:])
p=json.loads((stage/'evidence/preflight.json').read_text())
print(json.dumps({{'result':'PASS','stage':str(stage),'image':p['image'],'checks':p['checks'],'manifest_sha256':p['manifest_sha256'],'free_bytes':shutil.disk_usage(stage).free,'production_activated':False}}))
""")
    (HERE.parent/'preflight-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()

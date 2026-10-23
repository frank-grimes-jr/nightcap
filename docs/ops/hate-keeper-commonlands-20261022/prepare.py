"""Build a local immutable package from verified inputs; no production writes."""
import argparse,ast,hashlib,json,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
ARTIFACTS=Path('E:/EQ_Local_Dev/artifacts/hate-keeper-commonlands-20261022')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--name',default='package');args=parser.parse_args()
    assert args.name.replace('-','').isalnum(),'Use a fresh simple package name'
    build=json.loads((HERE/'build-manifest.json').read_text())
    for name,digest in build['candidate_sources'].items():
        assert hashlib.sha256((ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,name
    ast.parse((HERE/'rollout.py').read_text())
    remote="""import hashlib,importlib.util,json
from pathlib import Path
path=Path('/opt/nightcap/releases/classic-dungeons-rewards-20261022/rollout.py')
spec=importlib.util.spec_from_file_location('prior',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.initialize()
r=module.r;image=r.compact('game')['image_id']
print(json.dumps({'base_image_id':image,'base_hashes':r.image_hashes(image),'prior_operator_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
"""
    ssh=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
    probe=json.loads(subprocess.check_output(ssh,input=remote,text=True))
    assert probe['base_hashes']['bin/zone']==build['baseline_zone_sha256'],'Production baseline drift'
    ARTIFACTS.mkdir(exist_ok=True);stage=ARTIFACTS/args.name;stage.mkdir(exist_ok=False)
    def copy(source,name):
        dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes().replace(b'\r\n',b'\n'))
    for name in ('rollout.py','preimages.json'):copy(HERE/name,name)
    copy(ROOT/'docs/dungeons/runtime-contract.json','runtime-contract.json')
    for name in ('hate_keeper.py','content_patch.py','pok_hub_migration.py','pok_hub.py'):copy(ROOT/'tools'/name,'tools/'+name)
    (stage/'bin').mkdir()
    subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-hate-keeper-build-v1/zone',str(stage/'bin/zone')],check=True)
    assert sha(stage/'bin/zone')==build['zone_sha256']
    subprocess.run(['python','-B','-c','import hate_keeper; assert hate_keeper.PRIVATE["zone_id"]==76'],cwd=stage/'tools',check=True)
    manifest={**probe,'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'zone_sha256':build['zone_sha256'],'files':{p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*') if p.is_file()},
              'source_status':'reviewed candidate; main/live approval required','build_sources':build['candidate_sources']}
    (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    archive=ARTIFACTS/(args.name+'.tar.gz')
    def permissions(info):
        info.mode=0o755 if info.name=='bin/zone' else 0o600
        info.uid=info.gid=0;info.uname=info.gname='root';return info
    with tarfile.open(archive,'x:gz',compresslevel=1) as tar:
        for path in stage.rglob('*'):
            if path.is_file():tar.add(path,arcname=path.relative_to(stage).as_posix(),filter=permissions)
    (HERE/'package-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    receipt={'package':str(archive),'sha256':sha(archive),'bytes':archive.stat().st_size,'production_changed':False}
    (HERE/'package.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()

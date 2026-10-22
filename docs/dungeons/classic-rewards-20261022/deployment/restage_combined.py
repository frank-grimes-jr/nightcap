"""Replace the un-preflighted candidate zone, retain new live baseline/client."""
import argparse,gzip,hashlib,json,shutil,subprocess
from upload import ARTIFACTS,HERE,SSH,STAGE
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--uploaded',action='store_true');args=parser.parse_args()
    old_folder=ARTIFACTS/'deployment-package-v2'
    previous=json.loads((old_folder/'manifest.json').read_text())
    original_sha=sha(old_folder/'manifest.json')
    build=json.loads((HERE/'combined-build-manifest.json').read_text())
    probe=json.loads((ARTIFACTS/'live-probe.json').read_text())
    root=HERE.parents[3]
    for name,digest in build['candidate_sources'].items():assert sha(root/'server-mods/code'/name)==digest,name
    assert build['baseline_zone_sha256']==probe['base_hashes']['bin/zone']
    assert all(build['other_binaries'][n]['baseline']==probe['base_hashes']['bin/'+n] for n in ('world','shared_memory'))
    zone=ARTIFACTS/'combined-zone';assert sha(zone)==build['zone_sha256']
    manifest={**previous,'base_hashes':probe['base_hashes'],'base_image_id':probe['services']['game']['image_id'],
              'client_channel_sha256':probe['channel_sha256'],'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()}
    manifest['binaries']={**previous['binaries'],'zone':build['zone_sha256']}
    manifest['files']={**previous['files'],'bin/zone':build['zone_sha256']}
    archive=ARTIFACTS/'combined-zone.gz'
    if not archive.exists():
        with zone.open('rb') as src,gzip.open(archive,'xb',compresslevel=1) as dst:shutil.copyfileobj(src,dst)
    remote='/home/ubuntu/classic-combined-zone-20261022.gz'
    if not args.uploaded:subprocess.run(['scp',*SSH[1:-1],str(archive),SSH[-1]+':'+remote],check=True,timeout=300)
    code='stage_name='+repr(STAGE)+'\narchive_name='+repr(remote)+'\narchive_sha='+repr(sha(archive))+'\nprevious_manifest='+repr(previous)+'\nmanifest='+repr(manifest)+'\n'+r'''
import gzip,hashlib,json,os,shutil
from pathlib import Path
stage=Path(stage_name);archive=Path(archive_name)
assert not (stage/'evidence').exists()
assert json.loads((stage/'manifest.json').read_text())==previous_manifest
assert hashlib.sha256(archive.read_bytes()).hexdigest()==archive_sha
previous=json.loads((stage/'manifest.json').read_text())
assert hashlib.sha256((stage/'bin/zone').read_bytes()).hexdigest()==previous['files']['bin/zone']
for name,digest in manifest['files'].items():
    if name!='bin/zone':assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
tmp=stage/'bin/zone.combined';assert not tmp.exists()
with gzip.open(archive,'rb') as src,tmp.open('xb') as dst:shutil.copyfileobj(src,dst)
assert hashlib.sha256(tmp.read_bytes()).hexdigest()==manifest['files']['bin/zone']
tmp.chmod(0o755);os.replace(tmp,stage/'bin/zone')
tmp=stage/'manifest.combined.json';tmp.write_text(json.dumps(manifest,indent=2)+'\n');tmp.chmod(0o600);os.replace(tmp,stage/'manifest.json')
archive.unlink()
print(json.dumps({'stage':str(stage),'zone_sha256':manifest['binaries']['zone'],'free_bytes':shutil.disk_usage(stage).free}))
'''
    result=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,capture_output=True,timeout=120)
    if result.returncode:raise RuntimeError(result.stderr[-1800:])
    (HERE/'package-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ARTIFACTS/'combined-staging-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(result.stdout)
if __name__=='__main__':main()

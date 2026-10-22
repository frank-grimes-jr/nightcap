"""Upload only the locally created, hash-pinned release package; no player data."""
import argparse,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ARTIFACTS=Path('E:/EQ_Local_Dev/artifacts/classic-dungeon-options-20261022')
SSH=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
STAGE='/opt/nightcap/releases/classic-dungeons-rewards-20261022'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('package');parser.add_argument('--extract-only',action='store_true');args=parser.parse_args()
    path=ARTIFACTS/args.package;assert path.parent==ARTIFACTS and path.name.endswith('.tar.gz')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    remote='/home/ubuntu/'+path.name
    if not args.extract_only:subprocess.run(['scp',*SSH[1:-1],str(path),SSH[-1]+':'+remote],check=True,timeout=300)
    source='archive='+repr(remote)+'\nexpected='+repr(digest)+'\nstage_name='+repr(STAGE)+'\n'+r'''
import hashlib,json,os,shutil,tarfile
from pathlib import Path,PurePosixPath
archive=Path(archive);stage=Path(stage_name)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected
assert not stage.exists();os.umask(0o077)
with tarfile.open(archive) as tar:
    members=tar.getmembers();assert all(m.isfile() and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts for m in members)
    assert len({m.name for m in members})==len(members)
    manifest=json.load(tar.extractfile('manifest.json'))
    assert {m.name for m in members}==set(manifest['files'])|{'manifest.json'}
    assert shutil.disk_usage(stage.parent).free>=sum(m.size for m in members)+2400*1024**2
    stage.mkdir(mode=0o700)
    for m in members:
        target=stage/m.name;target.parent.mkdir(parents=True,exist_ok=True)
        with tar.extractfile(m) as src,target.open('xb') as dst:shutil.copyfileobj(src,dst)
        mode=0o755 if m.name.startswith('bin/') or m.name=='cache_check' else 0o600
        assert m.mode==mode;target.chmod(mode)
        if m.name!='manifest.json':assert hashlib.sha256(target.read_bytes()).hexdigest()==manifest['files'][m.name]
archive.unlink()
print(json.dumps({'stage':str(stage),'files':len(members),'free_bytes':shutil.disk_usage(stage).free}))
'''
    result=subprocess.run(SSH+['sudo -n python3 -'],input=source,text=True,capture_output=True,timeout=120)
    if result.returncode:raise RuntimeError(result.stderr[-2000:])
    report=json.loads(result.stdout);(HERE/'staging.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()

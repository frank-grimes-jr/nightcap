"""Authenticate built artifacts, refresh reviewed operators and seal upload archive."""
import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=ROOT.parent/'thj-parity-production-stage'
BUNDLE=ROOT.parent/'thj-parity-test-bundle'


def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    tested=json.loads((BUNDLE/'manifest.json').read_text())
    for name,record in tested['files'].items():
        assert sha(BUNDLE/name)==record['sha256'] and (BUNDLE/name).stat().st_size==record['bytes'],name
    built=json.loads((HERE.parent/'evidence/native-build-manifest.json').read_text())
    for name,digest in built['requested_sources'].items():
        assert hashlib.sha256((ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,name
    for name in ('world','zone','shared_memory'):
        assert sha(OUT/'bin'/name)==built[name+'_sha256']==tested['files']['server/bin/'+name]['sha256']
    for p in (OUT/'content').glob('*.sql'):
        assert sha(p)==tested['files']['content/'+p.name]['sha256']
    for p in (OUT/'client/assets').rglob('*'):
        if p.is_file(): assert sha(p)==tested['files']['client-delta/'+p.relative_to(OUT/'client/assets').as_posix()]['sha256']
    old=json.loads((OUT/'manifest.json').read_text())
    for name,digest in old['files'].items():
        assert sha(OUT/name)==digest,'Staging drift before refresh: '+name
    shutil.copyfile(HERE/'rollout.py',OUT/'rollout.py')
    shutil.copyfile(HERE/'prepare_client.py',OUT/'client/prepare.py')
    old['source_ref']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    subprocess.run(['git','diff','--exit-code','origin/test','--','server-mods','config','tools'],cwd=ROOT,check=True)
    old['files']={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json'}
    (OUT/'manifest.json').write_text(json.dumps(old,indent=2)+'\n')
    shutil.copyfile(OUT/'manifest.json',HERE/'manifest.json')
    target=ROOT.parent/'thj-parity-production-final.tar.gz'
    with tarfile.open(target,'x:gz',compresslevel=3) as archive:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():
                info=archive.gettarinfo(p,arcname=p.relative_to(OUT).as_posix());info.mode=0o755 if p.parent==OUT/'bin' else 0o600
                with p.open('rb') as f: archive.addfile(info,f)
    report={'path':str(target),'bytes':target.stat().st_size,'sha256':sha(target),'source_ref':old['source_ref'],
            'tested_bundle_sha256':sha(BUNDLE/'manifest.json'),'native_manifest_sha256':sha(HERE.parent/'evidence/native-build-manifest.json')}
    (HERE/'upload.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()

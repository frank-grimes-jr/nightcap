"""Verify the first build, then rebuild reviewed final inputs in isolation."""
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path('/tmp/nightcap-thj-behaviors-v1');INPUT=Path('/tmp/nightcap-thj-behaviors-final-input')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def fingerprints(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '.git' not in p.parts}
def run(command,label):
    print(label,flush=True)
    with (ROOT/(label+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:print((ROOT/(label+'.log')).read_text()[-12000:],flush=True);raise RuntimeError(label)
def main():
    previous=ROOT/('final-manifest.json' if (ROOT/'final-manifest.json').exists() else 'manifest.json')
    prior=json.loads(previous.read_text());source=ROOT/'source'
    assert fingerprints(source)==prior['source_files'],'Prior build inputs drifted'
    for binary in ('world','zone','shared_memory'):assert sha(ROOT/'build/bin'/binary)==prior[binary+'_sha256']
    expected=json.loads((INPUT/'expected.json').read_text())
    for name,digest in expected.items():
        incoming=INPUT/'source'/name;assert sha(incoming)==digest
        if not (source/name).exists() or sha(source/name)!=digest:shutil.copyfile(incoming,source/name)
    before=fingerprints(source)
    run(['cmake','--build',str(ROOT/'build'),'--target','world','zone','shared_memory','-j2'],'final-build')
    for binary in ('world','zone','shared_memory'):
        run(['ldd',str(ROOT/'build/bin'/binary)],'final-ldd-'+binary)
        assert 'not found' not in (ROOT/('final-ldd-'+binary+'.log')).read_text()
    assert fingerprints(source)==before,'Build inputs changed'
    result=dict(prior,source_files=before,requested_sources=expected,initial_manifest_sha256=sha(ROOT/'manifest.json'),previous_manifest_sha256=sha(previous),status='built_not_installed')
    for binary in ('world','zone','shared_memory'):result[binary+'_sha256']=sha(ROOT/'build/bin'/binary)
    (ROOT/'final-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_files','requested_sources')}),flush=True)
if __name__=='__main__':main()

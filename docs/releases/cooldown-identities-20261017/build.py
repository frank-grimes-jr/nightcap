"""Build the integrated release from the fingerprinted deployed source, without installing."""
import hashlib,json,shutil,subprocess
from pathlib import Path

BASE=Path('/tmp/nightcap-october-17-build-v2')
ROOT=Path('/tmp/nightcap-cooldown-identities-build-v1')
INPUT=Path('/tmp/nightcap-cooldown-identities-input')

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def fingerprints(root):
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '.git' not in p.parts}
def run(args,name,cwd=None):
    print(name,flush=True)
    with (ROOT/(name+'.log')).open('w') as log:
        result=subprocess.run(args,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        print((ROOT/(name+'.log')).read_text()[-12000:],flush=True)
        raise RuntimeError(name+' failed')
def main():
    baseline=json.loads((BASE/'manifest.json').read_text())
    assert sha(BASE/'build/bin/zone')==baseline['zone_sha256']=='3c1d74926cb7cff032a3ee8c48c210e37740156e7e36cc0eeddd07f847e88d1a'
    assert fingerprints(BASE/'source')==baseline['source_files']
    ROOT.mkdir(exist_ok=False)
    source=ROOT/'source';shutil.copytree(BASE/'source',source)
    expected=json.loads((INPUT/'expected-sources.json').read_text())
    # Only reviewed inputs use canonical LF; retained files outside the delta
    # remain byte-identical, including production-only hardening.
    for name in expected:
        p=source/name
        if p.exists():p.write_bytes(p.read_bytes().replace(b'\r\n',b'\n'))
    run(['patch','--batch','--fuzz=0','-p1','-i',str(INPUT/'source.patch')],'patch',source)
    before=fingerprints(source)
    changed={n:h for n,h in before.items() if baseline['source_files'].get(n)!=h}
    assert changed==expected,'Unexpected source delta'
    assert set(baseline['source_files'])<=set(before),'Source removal'
    (ROOT/'input-sources.json').write_text(json.dumps(before,indent=2)+'\n')
    run(['cmake','-S',str(source),'-B',str(ROOT/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo',
         '-DCMAKE_CXX_COMPILER=/usr/bin/clang++','-DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache',
         '-DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake',
         '-DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed','-DVCPKG_MANIFEST_MODE=OFF',
         '-DEQEMU_BUILD_PERL=ON','-DEQEMU_BUILD_LUA=ON'],'configure')
    run(['cmake','--build',str(ROOT/'build'),'--target','zone','-j2'],'build')
    run(['ldd',str(ROOT/'build/bin/zone')],'ldd')
    assert 'not found' not in (ROOT/'ldd.log').read_text()
    assert fingerprints(source)==before and fingerprints(BASE/'source')==baseline['source_files']
    result={'status':'built_not_installed','source_files':before,'changed_sources':changed,
            'baseline_manifest_sha256':sha(BASE/'manifest.json'),'baseline_zone_sha256':baseline['zone_sha256'],
            'zone_sha256':sha(ROOT/'build/bin/zone'),'item_abi_changed':False,'full_zone_rebuild':True,
            'owner_gameplay_accepted':False}
    (ROOT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_files','changed_sources')}),flush=True)
if __name__=='__main__':main()

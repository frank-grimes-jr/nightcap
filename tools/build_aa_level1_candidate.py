"""Build the level-1 AA correction from the exact retained AA QA source."""
import hashlib, json, shlex, shutil, subprocess
from pathlib import Path

BASE = Path('/tmp/nightcap-item-upgrades-release-build-20261012')
LIVE = Path('/tmp/nightcap-aa-build-20261013-v3')
INPUT = Path('/tmp/nightcap-aa-level1-input-20261013')
OUT = Path('/tmp/nightcap-aa-level1-build-20261013')
CHANGED = ['common/nightcap_aa_policy.h', 'zone/aa.cpp']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprints(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git','build','build-tests','vcpkg'}.intersection(p.relative_to(root).parts)}
def run(name,args,cwd=None):
    print(name,flush=True)
    with (OUT/(name+'.log')).open('w') as f:
        r=subprocess.run(args,cwd=cwd,stdout=f,stderr=subprocess.STDOUT)
    if r.returncode:
        print((OUT/(name+'.log')).read_text()[-7000:],flush=True)
        raise RuntimeError(name+' failed')
def main():
    prior=json.loads((LIVE/'manifest.json').read_text())
    expected=json.loads((INPUT/'input.json').read_text())
    assert fingerprints(LIVE/'source')==prior['source_files']
    assert sha(LIVE/'zone')==prior['binaries']['zone']==expected['live_zone_sha256']
    assert all(sha(INPUT/n)==h for n,h in expected['files'].items())
    assert all(sha(Path(n))==h for n,h in prior['final_link_inputs'].items())
    OUT.mkdir(exist_ok=False)
    source=OUT/'source';shutil.copytree(LIVE/'source',source)
    for n in CHANGED: shutil.copyfile(INPUT/n,source/n)
    before=fingerprints(source)
    assert sorted(n for n,h in before.items() if prior['source_files'].get(n)!=h)==CHANGED
    assert set(before)==set(prior['source_files'])
    link=list(prior['link_command']); old_output=link[link.index('-o')+1]
    retained={str((BASE/'build/zone'/a).resolve()):sha((BASE/'build/zone'/a).resolve())
              for a in link[1:] if not a.startswith('-') and a!=old_output and (BASE/'build/zone'/a).is_file()}
    args=[a.replace(str(LIVE/'source'),str(source)) for a in prior['compile_commands']['aa.cpp']]
    obj=OUT/'aa.cpp.o';args[args.index('-o')+1]=str(obj)
    run('compile-aa',args,BASE/'build')
    old=str(LIVE/'aa.cpp.o');assert link.count(old)==1;link[link.index(old)]=str(obj)
    link[link.index('-o')+1]=str(OUT/'zone')
    run('link',link,BASE/'build/zone')
    assert all(sha(Path(n))==h for n,h in retained.items())
    assert fingerprints(LIVE/'source')==prior['source_files'] and fingerprints(source)==before
    run('ldd',['ldd',str(OUT/'zone')]);assert 'not found' not in (OUT/'ldd.log').read_text()
    run('native-policy-tests',['python3',str(INPUT/'verify_aa_tbs_native.py'),str(source),str(OUT/'native-tests')])
    final={str((BASE/'build/zone'/a).resolve()):sha((BASE/'build/zone'/a).resolve())
           for a in link[1:] if not a.startswith('-') and a!=str(OUT/'zone') and (BASE/'build/zone'/a).is_file()}
    manifest={'status':'built_not_installed','base_manifest_sha256':sha(LIVE/'manifest.json'),
              'source_files':before,'changed_source_files':CHANGED,'added_source_files':[],
              'binaries':{**prior['binaries'],'zone':sha(OUT/'zone')},'compile_commands':{'aa.cpp':args},
              'link_command':link,'unchanged_link_inputs':retained,'final_link_inputs':final}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'status':manifest['status'],'zone_sha256':manifest['binaries']['zone']}),flush=True)
if __name__=='__main__':main()

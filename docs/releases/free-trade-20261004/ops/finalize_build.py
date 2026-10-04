"""Apply reviewed follow-ups in the same fresh task build, with fresh mtimes."""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
BASE=Path('/tmp/nightcap-blessing-lifetime-build-20261004')
OUT=Path('/tmp/nightcap-free-trade-build-20261004')
INPUT=Path('/tmp/nightcap-free-trade-final-input-20261004')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprints(root):
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not {'.git','build','build-tests','vcpkg'}.intersection(p.relative_to(root).parts)}
initial=json.loads((OUT/'manifest.json').read_text())
assert fingerprints(OUT/'source')==initial['source_files']
base=json.loads((BASE/'manifest.json').read_text())
assert fingerprints(BASE/'source')==base['source_files']
candidate=OUT/'reviewed-files';candidate.mkdir(exist_ok=False)
changed=json.loads((INPUT/'changed.json').read_text())
for name in changed:
    dest=candidate/name;dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes((BASE/'source'/name).read_bytes().replace(b'\r\n',b'\n'))
subprocess.run(['patch','--batch','--forward','--fuzz=0','-p1','-i',str(INPUT/'changes.patch')],cwd=candidate,check=True)
inputs=json.loads((INPUT/'inputs.json').read_text())
for name,h in inputs.items():
    src=INPUT/'overlay'/name;assert sha(src)==h
    dest=candidate/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(src.read_bytes())
updated=[]
for p in candidate.rglob('*'):
    if not p.is_file():continue
    dest=OUT/'source'/p.relative_to(candidate)
    if not dest.exists() or dest.read_bytes()!=p.read_bytes():
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(p.read_bytes()) # deliberately never preserve source mtimes
        updated.append(p.relative_to(candidate).as_posix())
assert set(updated)=={'zone/client_packet.cpp','zone/gm_commands/sell_all.cpp','zone/command.cpp'},updated
before=fingerprints(OUT/'source')
assert {n for n,h in before.items() if base['source_files'].get(n)!=h}==set(inputs)|set(changed)
with (OUT/'reviewed-build.log').open('w') as log:
    p=subprocess.run(['cmake','--build',str(OUT/'build'),'--target',*initial['built_targets'],'-j','4'],stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0,'Reviewed build failed; inspect reviewed-build.log'
assert fingerprints(OUT/'source')==before
shutil.copyfile(OUT/'manifest.json',OUT/'initial-manifest.json')
result={**initial,'source_files':before,'binaries':{n:sha(OUT/'build/bin'/n) for n in initial['built_targets']},
        'changed_source_files':sorted(set(inputs)|set(changed)),
        'review_followup_files':updated,'review_patch_sha256':sha(INPUT/'changes.patch'),
        'initial_manifest_sha256':sha(OUT/'initial-manifest.json')}
(OUT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'binaries':result['binaries'],'review_followups':updated}),flush=True)

"""Finish the already fresh, isolated build after reviewed fixes; never install it."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from build_living_economy import source_fingerprints
from check_living_economy_binary import verify_world

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--overlay',type=Path,required=True);p.add_argument('--build-root',type=Path,required=True)
p.add_argument('--previous-manifest',type=Path,help='Recorded manifest for an already finalized candidate before reviewed integration')
a=p.parse_args();root=a.build_root.resolve()
if root.parent!=Path('/tmp') or not root.name.startswith('nightcap-market-zone-hunt-'):
    raise ValueError('Only this feature isolated build is permitted')
source=root/'source';prior=a.previous_manifest.resolve() if a.previous_manifest else root/'manifest.json'
if prior.parent!=root or prior.name not in ('manifest.json','final-manifest.json'):
    raise ValueError('Previous manifest must belong to this isolated build')
previous=json.loads(prior.read_text());previous_hash=hashlib.sha256(prior.read_bytes()).hexdigest()
if source_fingerprints(source)!=previous['source_files']:
    raise ValueError('Candidate source changed outside the recorded build')
changed=[]
for f in a.overlay.rglob('*'):
    if not f.is_file(): continue
    rel=f.relative_to(a.overlay);target=source/rel;data=f.read_bytes()
    if target.exists() and target.read_bytes()==data: continue
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);changed.append(str(rel))
before=source_fingerprints(source)
targets=['world','zone','shared_memory','loginserver','ucs']
with (root/'final-build.log').open('w') as log:
    result=subprocess.run(['cmake','--build',str(root/'build'),'--target',*targets,'-j','4'],stdout=log,stderr=subprocess.STDOUT)
if result.returncode:
    lines=(root/'final-build.log').read_text().splitlines()
    print('\n'.join(x for x in lines if 'error:' in x.lower())[-5000:]);print('\n'.join(lines[-12:]))
    raise SystemExit(result.returncode)
if before!=source_fingerprints(source): raise RuntimeError('Source changed during final build')
verify_world((root/'build/bin/world').read_bytes())
binaries={name:hashlib.sha256((root/'build/bin'/name).read_bytes()).hexdigest() for name in targets}
manifest=dict(status='built_not_installed',source_files=before,binaries=binaries,reviewed_fix_files=changed,
              previous_manifest_sha256=previous_hash,
              provenance='Fresh isolated build created for this feature, followed by dependency-tracked reviewed fixes; no pre-existing release objects imported.')
(root/'final-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status=manifest['status'],binaries=binaries)))

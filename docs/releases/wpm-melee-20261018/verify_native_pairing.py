"""Read-only fingerprint verification of the isolated full/diagnostic builds."""
import hashlib
import json
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

root=Path('/tmp/nightcap-wpm-pet-v1')
runtime=Path('/tmp/nightcap-balance-wpm-20261018')
manifest=json.loads((root/'manifest.json').read_text())
diagnostic=json.loads((runtime/'native-build-manifest.json').read_text())
for name,digest in manifest['source_files'].items():assert sha(root/'source'/name)==digest,name
for name in ('zone','world','shared_memory'):assert sha(root/'build/bin'/name)==manifest[name+'_sha256']
assert sha(runtime/'balance-zone')==diagnostic['binary_sha256']
native=adapters=dependencies=0
for name,digest in diagnostic['objects'].items():
    path=Path(name)
    if not path.is_absolute():path=(root/'build/zone'/path).resolve()
    assert sha(path)==digest,name
    if path.is_relative_to(root/'build'):native+=1
    elif path.is_relative_to(runtime):adapters+=1
    elif path.is_relative_to(Path('/home/eqemu/code/build/vcpkg_installed/x64-linux/lib')):dependencies+=1
    else:raise AssertionError('Unexpected diagnostic object '+name)
report={'status':'passed','retained_source_files':len(manifest['source_files']),
        'native_objects_and_libraries':native,'diagnostic_objects':adapters,'dependency_libraries':dependencies,
        'zone_sha256':manifest['zone_sha256'],'diagnostic_sha256':diagnostic['binary_sha256'],
        'scope':'All current candidate sources, paired binaries and linked diagnostic objects match their manifests; no install'}
(runtime/'native-pairing.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))

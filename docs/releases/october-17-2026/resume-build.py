"""Resume the same full compilation after the qualified Pet gate correction."""
import hashlib,json,shutil,sys
from pathlib import Path
sys.path.insert(0,'/tmp/nightcap-october-17-input')
import build as b

before=json.loads((b.ROOT/'input-sources.json').read_text())
assert b.fingerprints(b.ROOT/'source')==before
name='zone/aa_recommendations.inc';p=b.ROOT/'source'/name
old=p.read_bytes();assert old.count(b'case Pet:')==1
p.write_bytes(old.replace(b'case Pet:',b'case nightcap::recommended_aa::Pet:'))
expected=json.loads((b.INPUT/'expected-sources.json').read_text())
baseline=json.loads((b.BASE/'manifest.json').read_text())
after=b.fingerprints(b.ROOT/'source')
assert {n:h for n,h in after.items() if before.get(n)!=h}=={name:expected[name]}
changed={n:h for n,h in after.items() if baseline['source_files'].get(n)!=h}
assert changed==expected and b.fingerprints(b.BASE/'source')==baseline['source_files']
shutil.copyfile(b.ROOT/'build.log',b.ROOT/'first-compile-failure.log')
b.run(['cmake','--build',str(b.ROOT/'build'),'--target','zone','-j2'],'build')
b.run(['ldd',str(b.ROOT/'build/bin/zone')],'ldd')
assert 'not found' not in (b.ROOT/'ldd.log').read_text()
assert b.fingerprints(b.ROOT/'source')==after
result={'status':'built_not_installed','source_files':after,'changed_sources':changed,
        'baseline_manifest_sha256':b.sha(b.BASE/'manifest.json'),'baseline_zone_sha256':baseline['zone_sha256'],
        'zone_sha256':b.sha(b.ROOT/'build/bin/zone'),'item_abi_changed':False,'full_zone_rebuild':True,
        'compile_repair':'Qualify recommendation Pet gate; reproduced and fixed in native fixture',
        'owner_gameplay_accepted':False}
(b.ROOT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('source_files','changed_sources')}),flush=True)

"""Prepare a stripped zone copy; prove every mapped byte and runtime header retained."""
from pathlib import Path
import json,subprocess,hashlib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
build=json.loads((HERE/'native-build.json').read_text())
out=HERE/'private/payload';out.mkdir(parents=True,exist_ok=True)
code='IDENTITY='+repr((ROOT/'tools/elf_runtime_identity.py').read_text())+'\nBUILD='+repr(build)+'\n'+'''
from pathlib import Path
import hashlib,json,subprocess
ns={'__name__':'identity'};exec(IDENTITY,ns)
root=Path(BUILD['candidate_root']);source=root/'zone';target=root/'zone.ship'
assert hashlib.sha256(source.read_bytes()).hexdigest()==BUILD['zone_sha256']
assert not target.exists(),'Existing package: verify receipt before reusing'
subprocess.run(['strip','--strip-debug','-o',str(target),str(source)],check=True)
report=ns['verify'](source,target)
assert 'not found' not in subprocess.check_output(['ldd',str(target)],text=True)
(root/'shipping-identity.json').write_text(json.dumps(report,indent=2)+'\\n')
print(json.dumps(report))
'''
result=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input=code,text=True,encoding='utf-8',capture_output=True,check=True)
identity=json.loads(result.stdout)
subprocess.run(['docker','cp','akk-stack-eqemu-server-1:'+build['candidate_root']+'/zone.ship',str(out/'zone')],check=True)
assert hashlib.sha256((out/'zone').read_bytes()).hexdigest()==identity['sha256']
(HERE/'native-identity.json').write_text(json.dumps(identity,indent=2)+'\n')
print(json.dumps(identity))

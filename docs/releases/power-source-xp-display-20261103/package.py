"""Strip the built zone; prove every mapped byte and runtime header retained; copy it out."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEST = '/tmp/nightcap-power-source-xp-display-20261103-v1'

def main(out):
    code = 'IDENTITY=' + repr((ROOT/'tools/elf_runtime_identity.py').read_text()) + '\nDEST=' + repr(DEST) + '\n' + '''
from pathlib import Path
import json,subprocess
ns={'__name__':'identity'};exec(IDENTITY,ns)
root=Path(DEST);source=root/'build/bin/zone';target=root/'shipping/zone'
assert not target.exists(),'Existing package: verify receipt before reusing'
target.parent.mkdir()
subprocess.run(['strip','--strip-debug','-o',str(target),str(source)],check=True)
report=ns['verify'](source,target)
assert 'not found' not in subprocess.check_output(['ldd',str(target)],text=True)
(root/'shipping-identity.json').write_text(json.dumps(report,indent=2)+'\\n')
print(json.dumps(report))
'''
    result = subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'], input=code, text=True,
                            encoding='utf-8', capture_output=True, check=True)
    identity = json.loads(result.stdout)
    subprocess.run(['docker','cp','akk-stack-eqemu-server-1:'+DEST+'/shipping/zone', out], check=True)
    assert hashlib.sha256(Path(out).read_bytes()).hexdigest() == identity['sha256']
    (HERE/'native-identity.json').write_text(json.dumps(identity, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(identity))

if __name__ == '__main__':
    main(sys.argv[1])

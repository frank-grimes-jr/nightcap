"""Strip world/zone/shared_memory; prove every mapped byte and runtime header retained; copy them out."""
import hashlib, json, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEST = '/tmp/nightcap-power-source-xp-20261103-v1'
NAMES = ('world', 'zone', 'shared_memory')

def main(out):
    code = 'IDENTITY=' + repr((ROOT/'tools/elf_runtime_identity.py').read_text()) + '\nDEST=' + repr(DEST) + \
           '\nNAMES=' + repr(NAMES) + '\n' + '''
from pathlib import Path
import json,subprocess
ns={'__name__':'identity'};exec(IDENTITY,ns)
root=Path(DEST);(root/'shipping').mkdir()  # fails on an existing package: verify its receipt instead
reports={}
for name in NAMES:
    source=root/'build/bin'/name;target=root/'shipping'/name
    subprocess.run(['strip','--strip-debug','-o',str(target),str(source)],check=True)
    reports[name]=ns['verify'](source,target)
    assert 'not found' not in subprocess.check_output(['ldd',str(target)],text=True)
(root/'shipping-identity.json').write_text(json.dumps(reports,indent=2)+'\\n')
print(json.dumps(reports))
'''
    result = subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'], input=code, text=True,
                            encoding='utf-8', capture_output=True, check=True)
    reports = json.loads(result.stdout)
    Path(out).mkdir(parents=True)
    for name in NAMES:
        subprocess.run(['docker','cp',f'akk-stack-eqemu-server-1:{DEST}/shipping/{name}', str(Path(out)/name)], check=True)
        assert hashlib.sha256((Path(out)/name).read_bytes()).hexdigest() == reports[name]['sha256'], name
    (HERE/'native-identity.json').write_text(json.dumps(reports, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({n: r['sha256'] for n, r in reports.items()}))

if __name__ == '__main__':
    main(sys.argv[1])

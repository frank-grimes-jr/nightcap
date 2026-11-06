"""Reproduce retained baseline, then link candidate objects; never install or restart."""
import json
import subprocess
from augment_audit import OUT, ROOT
from compile_augment_audit import LIVE, DEST

REMOTE = r'''
from pathlib import Path
import hashlib,json,shlex,subprocess,shutil
live=Path(LIVE);dest=Path(DEST)
work=dest/'link-debug-v1';work.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
evidence=json.loads((dest/'evidence.json').read_text())
assert evidence['status']=='PASS'
assert shutil.disk_usage(dest).free>3*1024**3,'Insufficient local candidate build space'
for unit in evidence['compiles']:assert sha(dest/(unit['unit']+'.o'))==unit['object_sha256']
for name,pin in evidence['files'].items():assert sha(live/'source'/name)==pin['base_sha256']
shipping=live/'shipping/zone'
assert sha(shipping)=='335cbce1d046565da3ad013261080de4df5032703719a2b2d8348f73f1830dd1'
recipe=live/'build/zone/CMakeFiles/zone.dir/link.txt';cwd=live/'build/zone'
args=shlex.split(recipe.read_text());assert args[0]=='/usr/bin/clang++' and args.count('-o')==1
inputs={}
for arg in args[1:]:
 if arg.endswith(('.o','.a')) or '.so' in arg and not arg.startswith('-'):
  path=(cwd/arg).resolve();assert path.is_file(),str(path);inputs[str(path)]=sha(path)
assert len(inputs)>100
manifest=dest/'link-inputs.json';manifest.write_text(json.dumps(inputs,indent=2)+'\n')
for label,replace in [('baseline',False),('candidate',True)]:
 command=args.copy();command[command.index('-o')+1]=str(work/(label+'-zone'))
 if replace:
  for unit in evidence['compiles']:
   old='CMakeFiles/zone.dir/'+unit['unit']+'.o';assert command.count(old)==1
   command[command.index(old)]=str(dest/(unit['unit']+'.o'))
 with (work/(label+'-link.log')).open('x') as log:
  p=subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
 assert p.returncode==0,label+' link failed'
 binary=work/(label+'-zone');stripped=work/(label+'-zone.stripped')
 subprocess.run(['strip','--strip-debug','-o',str(stripped),str(binary)],check=True)
 if not replace:
  assert sha(binary)==sha(live/'build/bin/zone'),'Unstripped retained baseline mismatch'
  assert sha(stripped)==sha(shipping),'Shipping baseline mismatch'
 identity={'__name__':'identity'};exec(IDENTITY,identity);assert identity['verify'](binary,stripped)['status']=='PASS'
 evidence[label]={'unstripped_sha256':sha(binary),'stripped_sha256':sha(stripped),'bytes':stripped.stat().st_size}
for path,pin in inputs.items():assert sha(Path(path))==pin,'Retained link input changed'
symbols=subprocess.check_output(['nm','-C',str(work/'candidate-zone')],text=True)
for symbol in ('NightcapHunt::CanDropAugment(', 'NightcapHunt::OutputShieldBlock('):assert symbol in symbols
evidence.update(link='PASS',link_inputs=len(inputs),link_manifest_sha256=sha(manifest),
 scope='isolated candidate link; byte-reproduced retained live baseline; no installation, production writes or player QA')
(dest/'linked-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps(evidence))
'''


if __name__ == '__main__':
    p = subprocess.run(['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'python3', '-'],
        input=f'LIVE={LIVE!r}\nDEST={DEST!r}\nIDENTITY={(ROOT / "tools/elf_runtime_identity.py").read_text()!r}\n' + REMOTE,
        text=True, encoding='utf-8', capture_output=True, timeout=600)
    if p.returncode:
        raise RuntimeError(p.stderr[-3000:])
    data = json.loads(p.stdout)
    (OUT / 'native-link.json').write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({k: data[k] for k in ('link', 'link_inputs', 'baseline', 'candidate', 'scope')}))

"""Resume the isolated candidate build using final reviewed source; never install."""
import hashlib,json,os,signal,subprocess,tempfile
from pathlib import Path
BASE=Path('/tmp/nightcap-october-17-build-v2')
ROOT=Path('/tmp/nightcap-cooldown-identities-build-v1')
INPUT=Path('/tmp/nightcap-cooldown-identities-final-input')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprints(root):
 return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '.git' not in p.parts}
def run(args,name):
 print(name,flush=True)
 with (ROOT/(name+'.log')).open('w') as f: r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT)
 if r.returncode: print((ROOT/(name+'.log')).read_text()[-12000:],flush=True);raise RuntimeError(name)
def main():
 baseline=json.loads((BASE/'manifest.json').read_text())
 assert fingerprints(BASE/'source')==baseline['source_files']
 # Stop only our superseded compilation and its descendants. No runtime process.
 needle='cmake --build '+str(ROOT/'build')
 targets=[]
 for row in subprocess.check_output(['ps','-eo','pid,args'],text=True).splitlines():
  parts=row.strip().split(None,1)
  if len(parts)==2 and parts[1].startswith(needle): targets.append(int(parts[0]))
 def descendants(pid):
  p=Path(f'/proc/{pid}/task/{pid}/children')
  children=[int(x) for x in p.read_text().split()] if p.exists() else []
  return [pid]+[child for c in children for child in descendants(c)]
 for pid in targets:
  for child in reversed(descendants(pid)):
   try: os.kill(child,signal.SIGTERM)
   except ProcessLookupError: pass
 if targets:
  import time; time.sleep(2)
 expected=json.loads((INPUT/'expected-sources.json').read_text())
 source=ROOT/'source'
 stage=Path(tempfile.mkdtemp(prefix='reviewed-patch-',dir=ROOT))
 for name in expected:
  p=stage/name
  p.parent.mkdir(parents=True,exist_ok=True)
  p.write_bytes((BASE/'source'/name).read_bytes().replace(b'\r\n',b'\n'))
 with (ROOT/'final-patch.log').open('w') as f:
  subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(INPUT/'source.patch')],cwd=stage,stdout=f,stderr=subprocess.STDOUT,check=True)
 for name,digest in expected.items():
  assert sha(stage/name)==digest
  if sha(source/name)!=digest: (source/name).write_bytes((stage/name).read_bytes())
 before=fingerprints(source)
 changed={n:h for n,h in before.items() if baseline['source_files'].get(n)!=h}
 assert changed==expected,'source delta mismatch'
 run(['cmake','--build',str(ROOT/'build'),'--target','zone','-j3'],'final-build')
 run(['ldd',str(ROOT/'build/bin/zone')],'final-ldd')
 assert 'not found' not in (ROOT/'final-ldd.log').read_text()
 assert fingerprints(source)==before and fingerprints(BASE/'source')==baseline['source_files']
 result={'status':'built_not_installed','source_files':before,'changed_sources':changed,
 'baseline_manifest_sha256':sha(BASE/'manifest.json'),'baseline_zone_sha256':baseline['zone_sha256'],
 'zone_sha256':sha(ROOT/'build/bin/zone'),'item_abi_changed':False,'full_zone_target_rebuilt':True,
 'build_history':'Fresh candidate configure; superseded compiles stopped, final reviewed delta applied to exact baseline in a staging directory, only differing files refreshed, final target rebuilt with dependency tracking.',
 'owner_gameplay_accepted':False}
 (ROOT/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['source_files','changed_sources']}),flush=True)
if __name__=='__main__':main()

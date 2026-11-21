"""Stage the paired native/content release; candidate mode permits rehearsal only."""
from pathlib import Path
import argparse,hashlib,io,json,subprocess,sys,tarfile
A=Path('E:/EQ_Local_Dev/artifacts/classic-focus-coverage-20261120');W=Path('E:/EQ_Local_Dev/_worktrees/classic-focus-coverage');D=W/'docs/releases/classic-focus-coverage-20261120';I=W/'docs/items/classic-focus-coverage'
sys.path.insert(0,str(D));import ops as ctl
sys.path.insert(0,str(W/'tools'));from capture_lantern_content import SSH
def sha(raw):return hashlib.sha256(raw).hexdigest()
def stage(candidate):
 ref='HEAD' if candidate else 'origin/main'
 rev=subprocess.check_output(['git','rev-parse',ref],cwd=W,text=True).strip()
 if not candidate:assert rev==json.loads((A/'duration-main.json').read_bytes())['mergeCommit']['oid']
 paths={'release.py':D/'release.py','catalog.py':I/'catalog.py','production.json.gz':I/'production.json.gz','policy.json':I/'policy.json','effects.json':I/'effects.json','build.json':I/'correction-build.json'}
 data={n:subprocess.check_output(['git','show',rev+':'+p.relative_to(W).as_posix()],cwd=W) for n,p in paths.items()}
 build=json.loads(data['build.json']);before=json.loads((I/'runtime.json').read_bytes())
 data['bin/zone']=(A/'zone').read_bytes();assert sha(data['bin/zone'])==build['binaries']['zone']
 assert build['baseline']['zone']==before['binaries']['zone']
 full=subprocess.check_output(['git','show',rev+':server-mods/code/zone/spell_effects.cpp'],cwd=W)
 assert sha(full.replace(b'\r\n',b'\n'))==build['after_source'], 'Merged source differs from compiled unit'
 m={k:before[k] for k in ('image','base_hashes','binaries','caches','services','client','channel','stock_operator','titles_receipt')}
 m.update(source=rev,target_binaries=build['binaries'],files={n:sha(v) for n,v in data.items()},layout=json.loads((D/'staged.json').read_bytes())['layout'])
 data['manifest.json']=(json.dumps(m,indent=2)+'\n').encode()
 archive=A/(ctl.STAGE+'.tar.gz')
 assert not archive.exists(),'Immutable package already exists'
 with tarfile.open(archive,'w:gz') as t:
  for n,v in data.items():
   entry=tarfile.TarInfo(n);entry.size=len(v);t.addfile(entry,io.BytesIO(v))
 upload='/home/ubuntu/'+archive.name
 subprocess.run(SSH[:-1]+['test ! -e '+upload+' && test ! -e /opt/nightcap/releases/'+ctl.STAGE],check=True)
 subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-2],str(archive),SSH[-2]+':'+upload],check=True,timeout=600)
 code='''from pathlib import Path
import hashlib,tarfile,os
os.umask(0o077)
p=Path(upload);assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
folder=Path('/opt/nightcap/releases')/stage
assert not folder.exists();folder.mkdir(mode=0o700)
with tarfile.open(p) as t:
 members=t.getmembers();assert len(members)==len(pins) and {m.name for m in members}==set(pins)
 for member in members:
  assert member.isfile() and (Path(member.name).name==member.name or member.name=='bin/zone')
  raw=t.extractfile(member).read();assert hashlib.sha256(raw).hexdigest()==pins[member.name]
  target=folder/member.name;target.parent.mkdir(exist_ok=True,mode=0o700)
  with target.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  target.chmod(0o755 if member.name=='bin/zone' else 0o600)
print(stage)
'''
 print(ctl.remote('upload='+repr(upload)+'\nstage='+repr(ctl.STAGE)+'\ndigest='+repr(sha(archive.read_bytes()))+'\npins='+repr({n:sha(v) for n,v in data.items()})+'\n'+code))
 (D/('correction-candidate-staged.json' if candidate else 'paired-staged.json')).write_bytes(data['manifest.json'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','preflight','activate','verify','status']);p.add_argument('--candidate',action='store_true');p.add_argument('--start',action='store_true');p.add_argument('--job',choices=['preflight','activate'],default='preflight');a=p.parse_args()
 ctl.STAGE='classic-focus-coverage-20261120-correction-candidate' if a.candidate else 'classic-focus-coverage-20261120-v2'
 assert not a.candidate or a.action in ('stage','preflight','status')
 if a.action=='stage':stage(a.candidate)
 elif a.action=='status':
  print(ctl.remote('stage='+repr(ctl.STAGE)+'\njob='+repr(a.job)+'\n'+'''from pathlib import Path
import subprocess,json
p=Path('/opt/nightcap/releases')/stage
state=subprocess.check_output(['systemctl','show','nightcap-'+stage+'-'+job,'--property=ActiveState,Result,ExecMainStatus'],text=True)
log=p/(job+'.log');print(json.dumps(dict(state=state.splitlines(),log=log.read_text()[-2200:] if log.exists() else '')))
'''))
 else:
  assert a.action=='verify' or a.start,'Use explicit status for read-only polling'
  ctl.action(a.action,a.start)

from pathlib import Path
import json,sys,hashlib,io,subprocess,tarfile
A=Path(__file__).resolve().parent
W=A.parents[1]/'_worktrees/aa-availability'
D=W/'docs/audits/aa-availability-20261120'
sys.path.insert(0,str(W/'docs/releases/classic-raid-focus-20261114'))
import ops as ctl
sys.path.insert(0,str(W/'tools'))
from capture_lantern_content import SSH
ctl.STAGE='aa-availability-20261120-v1';ctl.HERE=D
def sha(data):return hashlib.sha256(data).hexdigest()
def stage():
 rev=subprocess.check_output(['git','rev-parse','origin/main'],cwd=W,text=True).strip()
 assert rev==json.loads((A/'duration-main.json').read_bytes())['mergeCommit']['oid']
 assert json.loads((D/'validation.json').read_bytes())['result']=='PASS'
 before=json.loads((A/'production-before.json').read_bytes())
 data={n:subprocess.check_output(['git','show',rev+':docs/audits/aa-availability-20261120/'+n],cwd=W) for n in ('release.py','build.json')}
 build=json.loads(data['build.json'])
 for n,v in build['binaries'].items():
  raw=(A/n).read_bytes();assert sha(raw)==v and before['base_hashes']['bin/'+n]==build['baseline'][n];data['bin/'+n]=raw
 m={k:before[k] for k in ('base_hashes','channel','stock_operator','services','image','caches')}
 m.update(source=rev,before=before['rules'].strip().splitlines(),binaries=build['binaries'],files={n:sha(v) for n,v in data.items()})
 data['manifest.json']=json.dumps(m,indent=2).encode()
 archive=A/(ctl.STAGE+'.tar.gz')
 with tarfile.open(archive,'w:gz') as tar:
  for n,v in data.items():
   ent=tarfile.TarInfo(n);ent.size=len(v);tar.addfile(ent,io.BytesIO(v))
 upload='/home/ubuntu/'+archive.name
 subprocess.run(SSH[:-1]+['test ! -e '+upload+' && test ! -e /opt/nightcap/releases/'+ctl.STAGE],check=True)
 subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-2],str(archive),SSH[-2]+':'+upload],check=True,timeout=600)
 source=(W/'docs/releases/thj-combat-20261113/ops/control.py').read_text()
 extract=source.split('    code = """',1)[1].split('"""',1)[0].replace("m.name=='bin/zone'","m.name in ('bin/zone','bin/world')")
 print(ctl.remote('upload='+repr(upload)+'\nstage='+repr(ctl.STAGE)+'\nexpected='+repr(sha(archive.read_bytes()))+'\npins='+repr({k:sha(v) for k,v in data.items()})+'\n'+extract))
if __name__=='__main__':
 if sys.argv[1]=='stage':stage()
 elif sys.argv[1]=='activate-authorized-drain':
  print(ctl.remote('stage='+repr(ctl.STAGE)+'\n'+"""import subprocess,json
from pathlib import Path
p=Path('/opt/nightcap/releases')/stage
assert not (p/'evidence/activation').exists()
assert json.loads((p/'preflight.json').read_text())['result']=='PASS'
subprocess.run(['systemd-run','--unit=nightcap-'+stage+'-activate','--property=WorkingDirectory='+str(p),'--property=StandardOutput=append:'+str(p/'activate.log'),'--property=StandardError=append:'+str(p/'activate.log'),'/usr/bin/python3','-B',str(p/'release.py'),'activate-authorized-drain'],check=True)
print('Started owner-authorized admission drain')
"""))
 else:ctl.action(sys.argv[1],'--start' in sys.argv)



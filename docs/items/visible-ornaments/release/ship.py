"""Stage the main revision and execute one bounded operation on the production host."""
import gzip
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

here=Path(__file__).resolve().parent
repo=here.parents[3]
art=Path('E:/EQ_Local_Dev/artifacts/visible-ornaments-20261121')
sys.path.insert(0,str(repo/'docs/releases/classic-raid-augments-20261112'))
from probe import SSH,remote

stage='visible-ornaments-20261121-v1'
def digest(data):return hashlib.sha256(data).hexdigest()

def upload():
    revision=subprocess.check_output(['git','rev-parse','origin/main'],cwd=repo,text=True).strip()
    def source(p):
        return subprocess.check_output(['git','show',revision+':'+p],cwd=repo)
    before=json.loads((art/'production-before.json').read_bytes())
    build=json.loads((here/'build.json').read_bytes())
    files={'activate.py':source('docs/items/visible-ornaments/release/activate.py'),
           '998946.pl':source('server-mods/quests/ecommons/998946.pl'),
           'build.json':source('docs/items/visible-ornaments/release/build.json'),
           'content.sql.gz':gzip.compress((art/'production.sql').read_bytes(),mtime=0)}
    for n in ('world','zone'):
        data=(art/('shipping-'+n)).read_bytes()
        assert digest(data)==build['binaries'][n] and build['baseline'][n]==before['base_hashes']['bin/'+n]
        files['bin/'+n]=data
    manifest={k:before[k] for k in ('image','services','base_hashes','caches','channel','stock_operator')}
    manifest.update(source=revision,binaries=build['binaries'],donors=137799,designs=14768,files={n:digest(d) for n,d in files.items()})
    files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    archive=art/(stage+'.tar.gz')
    with tarfile.open(archive,'w:gz') as tar:
        for n,d in files.items():
            item=tarfile.TarInfo(n);item.size=len(d);tar.addfile(item,io.BytesIO(d))
    dest='/home/ubuntu/'+archive.name
    subprocess.run(SSH[:-1]+['test ! -e '+dest+' && test ! -e /opt/nightcap/releases/'+stage],check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-2],str(archive),SSH[-2]+':'+dest],check=True,timeout=600)
    controller=(repo/'docs/releases/thj-combat-20261113/ops/control.py').read_text()
    extraction=controller.split('    code = """',1)[1].split('"""',1)[0]
    result=remote('upload='+repr(dest)+'\nstage='+repr(stage)+'\nexpected='+repr(digest(archive.read_bytes()))+'\npins='+repr({n:digest(d) for n,d in files.items()})+'\n'+extraction)
    print(result.strip())
    (art/'manifest.json').write_bytes(files['manifest.json'])

def action(name):
    assert name in ('preflight','activate','activate-authorized-drain','verify','status','occupancy')
    code="""import subprocess,json
from pathlib import Path
folder=Path('/opt/nightcap/releases')/stage
if name in ('verify','occupancy'):
 if name=='verify':print(subprocess.check_output(['python3','-B',str(folder/'activate.py'),'verify'],text=True))
 else:
  import importlib.util
  path=folder.parent/'stock-worn-atk-20261113-v1/release.py'
  spec=importlib.util.spec_from_file_location('stock',path);s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s);s.initialize()
  print(s.a.prior.players())
elif name=='status':
 for n in ('preflight','activate','activate-authorized-drain'):
  unit='nightcap-'+stage+'-'+n
  print(n,subprocess.check_output(['systemctl','show',unit,'-p','ActiveState,Result,ExecMainStatus'],text=True))
  log=folder/(n+'.log')
  if log.exists():print(log.read_text(errors='replace')[-1900:])
 for p in (folder/'preflight.json',folder/'activation/deployed.json'):
  if p.exists():print(p.name,p.read_text())
else:
 log=folder/(name+'.log')
 with log.open('x'):pass
 subprocess.run(['systemd-run','--unit=nightcap-'+stage+'-'+name,
  '--property=WorkingDirectory='+str(folder),'--property=StandardOutput=append:'+str(log),
  '--property=StandardError=append:'+str(log),'python3','-B',str(folder/'activate.py'),name],check=True)
"""
    result=remote('name='+repr(name)+'\nstage='+repr(stage)+'\n'+code)
    if name=='verify':
        (here/'production-verified.json').write_text(json.dumps(json.loads(result),indent=2)+'\n')
    print(result.strip())

if __name__=='__main__':
    if sys.argv[1]=='stage':upload()
    else:action(sys.argv[1])

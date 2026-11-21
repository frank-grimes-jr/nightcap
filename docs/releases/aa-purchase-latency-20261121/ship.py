"""Stage the merged binary release and invoke one-shot maintenance actions."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARTIFACTS = Path('E:/EQ_Local_Dev/artifacts')
STAGE = 'aa-purchase-latency-20261121-v1'
sys.path.insert(0, str(ROOT / 'docs/releases/classic-raid-augments-20261112'))
from probe import remote, SSH


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stage():
    revision = subprocess.check_output(['git','rev-parse','origin/main'], cwd=ROOT, text=True).strip()
    before = json.loads((HERE / 'production-before.json').read_bytes())
    files = {name: subprocess.check_output(
        ['git','show',revision+':docs/releases/aa-purchase-latency-20261121/'+name], cwd=ROOT)
        for name in ('release.py','build.json')}
    build = json.loads(files['build.json'])
    for name,pin in build['stages']['candidate']['sources'].items():
        source = subprocess.check_output(['git','show',revision+':server-mods/code/zone/'+name], cwd=ROOT)
        assert sha(source) == pin, name
    files['bin/zone'] = (ARTIFACTS / 'aa-purchase-latency-zone').read_bytes()
    assert sha(files['bin/zone']) == build['binaries']['zone']
    assert before['base_hashes']['bin/zone'] == build['baseline']['zone']
    manifest = {key:before[key] for key in ('image','services','base_hashes','caches','channel','stock_operator')}
    manifest.update(source=revision, binaries=build['binaries'], files={name:sha(raw) for name,raw in files.items()})
    files['manifest.json'] = (json.dumps(manifest,indent=2)+'\n').encode()
    archive = ARTIFACTS / (STAGE+'.tar.gz')
    with tarfile.open(archive,'w:gz') as container:
        for name,raw in files.items():
            member=tarfile.TarInfo(name);member.size=len(raw)
            container.addfile(member,io.BytesIO(raw))
    upload='/home/ubuntu/'+archive.name
    subprocess.run(SSH[:-1]+['test ! -e '+upload+' && test ! -e /opt/nightcap/releases/'+STAGE],check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-2],str(archive),SSH[-2]+':'+upload],check=True,timeout=600)
    # Reuse the reviewed path-constrained, digest-checked immutable extractor.
    controller=(ROOT/'docs/releases/thj-combat-20261113/ops/control.py').read_text(encoding='utf-8')
    extraction=controller.split('    code = """',1)[1].split('"""',1)[0]
    result=remote('upload='+repr(upload)+'\nstage='+repr(STAGE)+'\nexpected='+repr(sha(archive.read_bytes()))+
                  '\npins='+repr({name:sha(raw) for name,raw in files.items()})+'\n'+extraction)
    (HERE/'staged.json').write_bytes(files['manifest.json'])
    print(result.strip())


def action(name,start):
    code='''from pathlib import Path
import json,subprocess
folder=Path('/opt/nightcap/releases')/stage
command=['/usr/bin/python3','-B',str(folder/'release.py'),action]
if action=='verify':
 print(subprocess.check_output(command,text=True))
else:
 unit='nightcap-'+stage+'-'+action
 log=folder/(action+'.log')
 if start:
  if action=='activate-authorized-drain':
   assert not (folder/'evidence/activation').exists()
   assert json.loads((folder/'preflight.json').read_bytes())['result']=='PASS'
  with log.open('x') as stream:stream.write('')
  subprocess.run(['systemd-run','--unit='+unit,'--property=WorkingDirectory='+str(folder),
   '--property=StandardOutput=append:'+str(log),'--property=StandardError=append:'+str(log),*command],check=True)
 state=subprocess.check_output(['systemctl','show',unit,'--property=LoadState,ActiveState,Result,ExecMainStatus'],text=True)
 print(json.dumps(dict(state=state.splitlines(),log=log.read_text()[-2400:] if log.exists() else '',
  receipts=sorted(str(p.relative_to(folder)) for p in (folder/'evidence').rglob('*.json')))))
'''
    result=remote('stage='+repr(STAGE)+'\naction='+repr(name)+'\nstart='+repr(start)+'\n'+code,timeout=600)
    if name=='verify':
        data=json.loads(result)
        assert data['gateway_open'] and data['workers']==12 and not any(data['errors'].values())
        (HERE/'production-verified.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(result)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('stage','preflight','activate-authorized-drain','verify'))
    parser.add_argument('--start',action='store_true')
    args=parser.parse_args()
    if args.action=='stage':stage()
    else:action(args.action,args.start)

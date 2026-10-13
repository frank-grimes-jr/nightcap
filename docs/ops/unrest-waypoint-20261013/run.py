"""Stage and run the owner-approved, committed Unrest release on OVH."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
REMOTE='/opt/nightcap/releases/unrest-waypoint-20261013'
SSH=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes',
     '-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']

def run(action):
    if action=='stage':
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        subprocess.run(['git','merge-base','--is-ancestor',revision,'origin/main'],cwd=ROOT,check=True)
        assert not subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip(),'Uncommitted release files'
        files={
          'rollout.py':HERE/'ops/rollout.py',
          'runtime_ops.py':ROOT/'docs/releases/zone-loot-20261009/ops/runtime_ops.py',
          **{'tools/'+name:ROOT/'tools'/name for name in ('unrest_waypoint.py','content_patch.py','pok_hub_migration.py','pok_hub.py')},
        }
        payload={name:path.read_text(encoding='utf-8').replace('\r\n','\n').encode() for name,path in files.items()}
        manifest={'source_commit':revision,'files':{name:hashlib.sha256(data).hexdigest() for name,data in payload.items()}}
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
            for name,data in payload.items():
                info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o600
                archive.addfile(info,io.BytesIO(data))
        code='ARCHIVE='+repr(base64.b64encode(buffer.getvalue()).decode())+'\nMANIFEST='+repr(manifest)+'\n'+r'''
import base64,hashlib,io,json,os,sys,tarfile
from pathlib import Path
os.umask(0o077)
stage=Path('/opt/nightcap/releases/unrest-waypoint-20261013')
stage.mkdir(mode=0o700)
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(ARCHIVE)),mode='r:gz') as archive:
 for member in archive.getmembers():
  assert member.isfile() and member.name in MANIFEST['files']
  path=stage/member.name
  assert path.resolve().is_relative_to(stage)
  data=archive.extractfile(member).read()
  assert hashlib.sha256(data).hexdigest()==MANIFEST['files'][member.name]
  path.parent.mkdir(exist_ok=True,mode=0o700)
  with path.open('xb') as output:output.write(data)
sys.path[:0]=[str(stage),str(stage/'tools')]
import runtime_ops as r
import unrest_waypoint as content
before=content.capture(r.sql);content.desired(before)
(stage/'reviewed-before.json').write_text(json.dumps(before,indent=2)+'\n')
MANIFEST['files']['reviewed-before.json']=hashlib.sha256((stage/'reviewed-before.json').read_bytes()).hexdigest()
MANIFEST['map_sha256']=hashlib.sha256((r.ROOT/'data/server/maps/base/unrest.map').read_bytes()).hexdigest()
(stage/'manifest.json').write_text(json.dumps(MANIFEST,indent=2)+'\n')
print(json.dumps({'staged':str(stage),'source_commit':MANIFEST['source_commit'],'captured_tables':list(before['rows'])}))
'''
        subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,check=True)
    else:
        subprocess.run(SSH+['sudo -n python3 '+REMOTE+'/rollout.py '+action],check=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['stage','preflight','activate','report'])
    run(parser.parse_args().action)

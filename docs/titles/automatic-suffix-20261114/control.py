"""Immutable package transport and durable action/status controls."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ART=ROOT/'artifacts/titles-live-20261114/automatic'
STAGE='titles-automatic-suffix-20261114-v1'
sys.path.insert(0,str(ROOT/'tools'))
from quick_buff_remote import run as remote
from capture_lantern_content import SSH
sha=lambda data:hashlib.sha256(data).hexdigest()


def stage(revision):
    assert re.fullmatch('[0-9a-f]{40}',revision)
    before=json.loads((ART/'before.json').read_bytes());build=json.loads((HERE/'shipping-candidate.json').read_bytes())
    assert all(v['running'] for v in before['services'].values())
    assert before['base_hashes']['bin/zone']==build['baseline']
    files={'release.py':(HERE/'release.py').read_bytes().replace(b'\r\n',b'\n'),
           'build.json':(HERE/'shipping-candidate.json').read_bytes(),'bin/zone':(ART/'shipping-v2/zone').read_bytes()}
    assert sha(files['bin/zone'])==build['zone']
    manifest=dict(stage=STAGE,source_revision=revision,files={n:sha(b) for n,b in files.items()},
        base_image_id=before['services']['game']['image_id'],base_hashes=before['base_hashes'],baseline_services=before['services'],
        client_release=2026111301,client_channel_sha256=before['channel'],prior_operator=before['prior_operator'],
        prior_receipt=before['prior_receipt'],prior_manifest=before['prior_manifest'],title_operator=before['title_operator'],
        maintenance=before['maintenance'],binaries={'zone':build['zone']})
    files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    archive=ART/(STAGE+'.tar.gz')
    with tarfile.open(archive,'w:gz') as tar:
        for name,data in files.items():
            entry=tarfile.TarInfo(name);entry.size=len(data);tar.addfile(entry,io.BytesIO(data))
    upload='/home/ubuntu/'+archive.name
    subprocess.run(SSH[:-1]+['test ! -e '+upload+' && test ! -e /opt/nightcap/releases/'+STAGE],check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-2],str(archive),SSH[-2]+':'+upload],check=True,timeout=600)
    previous=(ROOT/'docs/releases/thj-combat-20261113/ops/control.py').read_text(encoding='utf8')
    extract=previous.split('    code = """',1)[1].split('"""',1)[0]
    print(remote('upload='+repr(upload)+'\nstage='+repr(STAGE)+'\nexpected='+repr(sha(archive.read_bytes()))+
        '\npins='+repr({n:sha(b) for n,b in files.items()})+'\n'+extract))
    (HERE/'staged.json').write_text(json.dumps(manifest,indent=2)+'\n')


def retained():
    path=ROOT/'docs/releases/thj-combat-20261113/ops';sys.path.insert(0,str(path))
    spec=importlib.util.spec_from_file_location('automatic_title_transport',path/'control.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.STAGE=STAGE;module.HERE=HERE;module.ARTIFACTS=ART
    module.write=lambda name,data:(HERE/name).write_text(json.dumps(data,indent=2)+'\n')
    return module


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','deploy','verify','recover-closed']);p.add_argument('--revision');p.add_argument('--start',action='store_true');a=p.parse_args()
    if a.action=='stage':stage(a.revision)
    elif a.action=='verify':retained().verify()
    else:retained().action(a.action,a.start)

"""Exact immutable stage transport and durable title operation controls."""
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
ART=ROOT/'artifacts/titles-live-20261114'
sys.path.insert(0,str(ROOT/'tools'))
from quick_buff_remote import run as remote
from capture_lantern_content import SSH
STAGE='titles-live-20261114-v1'
sha=lambda b:hashlib.sha256(b).hexdigest()


def stage(revision):
    assert re.fullmatch('[0-9a-f]{40}',revision)
    before=json.loads((ART/'before-after-prismatic.json').read_bytes())
    assert all(v['running'] for v in before['services'].values())
    files={name:(HERE/name).read_bytes().replace(b'\r\n',b'\n') for name in ('release.py','schema.py','schema-expected.json')}
    files.update({'setup.sql':(ROOT/'docs/titles/setup.sql').read_bytes().replace(b'\r\n',b'\n'),
        'build.json':(HERE/'shipping-candidate.json').read_bytes(),
        'commands-before.json':(json.dumps([json.loads(x) for x in before['commands'].splitlines() if x.strip()],indent=2)+'\n').encode(),
        'bin/zone':(ART/'zone').read_bytes()})
    build=json.loads(files['build.json'])
    assert sha(files['bin/zone'])==build['zone'] and build['baseline']==before['base_hashes']['bin/zone']
    m=dict(stage=STAGE,source_revision=revision,files={n:sha(b) for n,b in files.items()},
        client_release=2026111301,client_channel_sha256=before['channel'],prior_operator=before['prior_operator'],
        prior_receipt=before['prior_receipt'],prismatic_receipt=before['prismatic_receipt'],maintenance=before['maintenance'],
        base_image_id=before['services']['game']['image_id'],base_hashes=before['base_hashes'],
        baseline_services=before['services'],binaries={'zone':build['zone']})
    files['manifest.json']=(json.dumps(m,indent=2)+'\n').encode()
    archive=ART/(STAGE+'.tar.gz')
    with tarfile.open(archive,'w:gz') as tar:
        for name,data in files.items():
            item=tarfile.TarInfo(name);item.size=len(data);tar.addfile(item,io.BytesIO(data))
    upload='/home/ubuntu/'+archive.name
    subprocess.run(SSH[:-1]+['test ! -e '+upload+' && test ! -e /opt/nightcap/releases/'+STAGE],check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-2],str(archive),SSH[-2]+':'+upload],check=True,timeout=600)
    # Reuse the reviewed path-checked exclusive extraction and fsync code.
    previous=(ROOT/'docs/releases/thj-combat-20261113/ops/control.py').read_text()
    extract=previous.split('    code = """',1)[1].split('"""',1)[0]
    print(remote('upload='+repr(upload)+'\nstage='+repr(STAGE)+'\nexpected='+repr(sha(archive.read_bytes()))+
        '\npins='+repr({n:sha(b) for n,b in files.items()})+'\n'+extract).strip())
    (HERE/'staged.json').write_text(json.dumps(m,indent=2)+'\n')


def old_control():
    path=ROOT/'docs/releases/thj-combat-20261113/ops'
    sys.path.insert(0,str(path))
    spec=importlib.util.spec_from_file_location('retained_transport',path/'control.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.STAGE=STAGE;module.HERE=HERE;module.ARTIFACTS=ART
    module.write=lambda name,data:(HERE/name).write_text(json.dumps(data,indent=2)+'\n')
    return module


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('stage','deploy','verify','recover-closed'));p.add_argument('--revision');p.add_argument('--start',action='store_true');a=p.parse_args()
    if a.action=='stage':stage(a.revision)
    elif a.action=='verify':old_control().verify()
    else:old_control().action(a.action,a.start)

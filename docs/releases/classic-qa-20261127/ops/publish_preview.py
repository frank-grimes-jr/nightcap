"""Stage the signed Hailstone launcher plus its source and advance its independent channel."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

from build_desktop import OUT, ORIGINAL, PUBLISH, RELEASE, ROOT
from capture import SSH
from upload import INSTALL


def sha(data):
    return hashlib.sha256(data).hexdigest()


def public(path):
    url='https://play.nightcapgame.org/'+path
    request=urllib.request.Request(url,headers={'User-Agent':'Nightcap-Release-Verification/0.8','Cache-Control':'no-cache'})
    with urllib.request.urlopen(request,timeout=120) as response:
        assert response.status==200 and response.url==url
        return response.read()


def main(action):
    pins=json.loads((OUT/'release.json').read_bytes())
    previous=json.loads((ORIGINAL/'release.json').read_bytes())['channel']
    pub=OUT/'desktop-release'
    pub.mkdir(exist_ok=True)
    payload=[pub/'nightcap-desktop.exe',pub/'nightcap-hailstone-source.zip']
    src=[next(PUBLISH.rglob('nightcap-desktop.exe')),OUT/'nightcap-hailstone-source.zip']
    for origin,target in zip(src,payload):
        shutil.copyfile(origin,target)
    shutil.copyfile(PUBLISH/'launcher-channel.json', pub/'launcher-channel.json')
    shutil.copyfile(OUT/'release.json',pub/'release.json')
    op=(ROOT/'docs/qa/cairnwright-hailstone/publish_launcher.py').read_text()
    op,n=re.subn(r'(?m)^PARENT = "[0-9a-f]{64}"$',lambda _:f'PARENT = "{previous}"',op)
    assert n==1
    assert op.count('RELEASE = 2026112202')==1
    (pub/'publish_launcher.py').write_text(op.replace('RELEASE = 2026112202','RELEASE = '+RELEASE))
    names=[p.name for p in payload]+['launcher-channel.json','release.json','publish_launcher.py']
    manifest={name:sha((pub/name).read_bytes()) for name in names}
    path=pub/'manifest.json'
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    pin=sha(path.read_bytes())
    folder='/opt/nightcap/releases/classic-qa-20261127-'+pin[:12]
    descriptor=json.loads(base64.b64decode(json.loads((pub/'launcher-channel.json').read_bytes())['Channel']))
    assert descriptor['release']==int(RELEASE) and descriptor['sha256']==pins['desktop']
    assert manifest['nightcap-desktop.exe']==pins['desktop'] and manifest['nightcap-hailstone-source.zip']==pins['source']
    if action=='upload':
        assert sha(public('launcher-channel.json'))==previous
        with tempfile.TemporaryFile() as archive:
            with tarfile.open(fileobj=archive,mode='w:gz',compresslevel=1) as tar:
                for name in names+['manifest.json']:
                    tar.add(pub/name,arcname=name,recursive=False)
            archive.seek(0)
            cmd=shlex.join(['sudo','-n','python3','-c',INSTALL,pin,*names,'manifest.json'])
            subprocess.run([*SSH,cmd],stdin=archive,check=True)
    elif action in ('files','switch'):
        if action=='switch':
            for file,key in zip(payload,('desktop','source')):
                assert sha(public(f'launcher/{RELEASE}/{file.name}'))==pins[key]
        subprocess.run([*SSH,shlex.join(['sudo','-n','python3',folder+'/publish_launcher.py',action])],check=True)
    else:
        online=public('launcher-channel.json')
        assert sha(online)==pins['channel']
        for file,key in zip(payload,('desktop','source')):
            assert sha(public(f'launcher/{RELEASE}/{file.name}'))==pins[key]
        receipt=dict(release=int(RELEASE),**pins,previous=previous,https_verified=True)
        (OUT/'public-verified.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['upload','files','switch','verify'])
    main(p.parse_args().action)


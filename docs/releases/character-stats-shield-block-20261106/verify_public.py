"""Verify signed inventory and served XML/pair; retained files were hashed by publisher."""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request
from urllib.parse import urlsplit
import base64

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ART=ROOT/'artifacts/character-stats-shield-block'


def download(url,limit):
    request=urllib.request.Request(url,headers={'User-Agent':'NightcapLauncher/0.6.0','Accept-Encoding':'identity'})
    with urllib.request.urlopen(request,timeout=60) as response:
        target=urlsplit(response.url)
        assert target.scheme=='https' and target.hostname=='play.nightcapgame.org'
        data=response.read(limit+1)
        assert len(data)<=limit
        return data


def main():
    code=(HERE/'verify.go').read_bytes();entry=ROOT/'eq-launcher/cmd/shield-block-verify'
    if entry.exists():assert (entry/'main.go').read_bytes()==code
    else:entry.mkdir();(entry/'main.go').write_bytes(code)
    try:
        p=subprocess.run(['go','run','./cmd/shield-block-verify','-previous',str(ART/'previous-channel.json'),
            '-expected',str(ART/'signed/channel.json')],cwd=ROOT/'eq-launcher',capture_output=True,text=True,check=True)
        result=json.loads(p.stdout)
    finally:
        assert (entry/'main.go').read_bytes()==code
        (entry/'main.go').unlink();entry.rmdir()
    expected=(ART/'signed/channel.json').read_bytes()
    assert download('https://play.nightcapgame.org/channel.json',2*1024**2)==expected
    manifest=json.loads(base64.b64decode(json.loads(expected)['manifest']))
    total=0;verified=[]
    for f in manifest['files']:
        if f['path'] not in ('uifiles/nightcap/equi_inventory.xml','dinput8.dll','nightcap-patch-sites.json'):continue
        data=download(f['url'],f['size'])
        assert len(data)==f['size'] and hashlib.sha256(data).hexdigest()==f['sha256']
        if f['path']!='uifiles/nightcap/equi_inventory.xml':assert data==(ART/'baseline-assets'/f['path']).read_bytes()
        total+=len(data);verified.append(f['path'])
    assert len(verified)==3
    publication=json.loads((HERE/'client-published.json').read_text())
    assert publication['preserved_assets']==147 and publication['services_before']==publication['services_after']
    result.update(hosted=True,hosted_files_verified=verified,verified_bytes=total,
        verification_scope='All148 signed descriptors/history; served changed XML plus unchanged DLL/catalog matching preflight-verified baseline; publisher hashes all147 retained files',
        retained_proxy_catalog_pair='same authenticated/preflight-verified bytes',owner_pixel_acceptance=False)
    (HERE/'client-public-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(release=result['release'],signature=result['signature'],hosted_files=len(verified),retained=147)))


if __name__=='__main__':main()

"""Verify every authorized public wiki file, security headers and private denials."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/quick-buff-20261112'
ART=ROOT/'artifacts/quick-buff-20261112'
BASE='https://wiki.nightcapgame.org/'
def get(name):
    request=urllib.request.Request(BASE+urllib.parse.quote(name,safe='/'),headers={'User-Agent':'NightcapLauncher/0.7.0','Accept-Encoding':'identity'})
    return urllib.request.urlopen(request,timeout=60)
def verify(row):
    name,pin=row
    with get(name) as response:
        assert response.status==200
        assert response.headers.get('X-Content-Type-Options')=='nosniff',name
        assert response.headers.get('Content-Security-Policy'),name
        digest=hashlib.sha256();count=0
        while data:=response.read(131072):
            count+=len(data);assert count<32*1024**2;digest.update(data)
        assert digest.hexdigest()==pin,name
    return count
if __name__=='__main__':
    pins=json.loads((ART/'20261112-quick-buff-v1.tar.json').read_text(encoding='utf-8'))
    with ThreadPoolExecutor(max_workers=8) as pool:counts=list(pool.map(verify,pins.items()))
    denials={}
    for name in ('README.md','content-review.json','articles/combat.json','catalog.json','.git/config'):
        try:
            with get(name) as response:status=response.status
        except urllib.error.HTTPError as error:status=error.code
        assert status in (403,404),(name,status);denials[name]=status
    report=dict(status='PASS',release='20261112-quick-buff-v1',files=len(pins),verified_bytes=sum(counts),
        all_public_sha256_and_security_headers=True,private_denials=denials,owner_gameplay_acceptance='OPEN')
    (OUT/'wiki-public-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

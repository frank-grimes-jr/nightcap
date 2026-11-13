"""Verify all published title-preview release hashes/headers and private denials."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'docs/titles/wiki-release'
ART=ROOT/'artifacts/titles-wiki-20261112'
RELEASE='20261112-earned-titles-v1'


def get(name):
    request=urllib.request.Request('https://wiki.nightcapgame.org/'+urllib.parse.quote(name,safe='/'),
        headers={'User-Agent':'NightcapLauncher/0.7.0','Accept-Encoding':'identity'})
    return urllib.request.urlopen(request,timeout=60)


def verify(row):
    name,pin=row
    with get(name) as response:
        assert response.status==200,name
        assert response.headers.get('X-Content-Type-Options')=='nosniff',name
        assert "script-src 'self'" in response.headers.get('Content-Security-Policy',''),name
        data=response.read(32*1024**2)
        assert hashlib.sha256(data).hexdigest()==pin,name
    return len(data)


def main():
    pins=json.loads((ART/(RELEASE+'.tar.json')).read_text(encoding='utf-8'))
    assert len(pins)==614
    with ThreadPoolExecutor(max_workers=8) as pool:
        counts=list(pool.map(verify,pins.items()))
    denials={}
    for name in ('README.md','content-review.json','articles/titles.json','catalog.json','.git/config'):
        try:
            with get(name) as response:
                status=response.status
        except urllib.error.HTTPError as error:
            status=error.code
        assert status in (403,404),(name,status)
        denials[name]=status
    report=dict(status='PASS',release=RELEASE,files=len(pins),verified_bytes=sum(counts),
        all_public_sha256_and_security_headers=True,private_denials=denials,
        title_availability='Not released preview',title_gameplay_acceptance='OPEN',title_runtime='not activated')
    (HERE/'public-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()

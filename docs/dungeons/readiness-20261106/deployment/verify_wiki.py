"""Verify every canonical public HTTPS file and private-route denial after publication."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RELEASE='20261106-dungeon-readiness-v1'
manifest=json.loads((ROOT/'artifacts/dungeon-readiness'/(RELEASE+'.tar.json')).read_text())
publication=json.loads((HERE/'wiki-publication.json').read_text())
assert publication['result']=='PASS' and publication['files']==len(manifest)==510


def check(entry):
    name,expected=entry
    request=Request('https://wiki.nightcapgame.org/'+name,headers={'Cache-Control':'no-cache','User-Agent':'NightcapReleaseVerification/1.0'})
    with urlopen(request,timeout=40) as response:
        digest=hashlib.sha256(response.read()).hexdigest()
        assert response.status==200 and digest==expected,(name,response.status,'Public bytes mismatch')
        assert response.headers.get('X-Content-Type-Options')=='nosniff'
        assert "script-src 'self'" in response.headers.get('Content-Security-Policy','')
    return name


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=6) as pool:verified=list(pool.map(check,manifest.items()))
    private=['/channel.json','/launcher-channel.json','/nightcap-friends.zip','/guide.html','/.env']
    denials={}
    for path in private:
        try:
            with urlopen('https://wiki.nightcapgame.org'+path,timeout=30) as response:status=response.status
        except HTTPError as error:status=error.code
        # Origin checks require404. Cloudflare may reject a private request
        # earlier with403; neither response exposes the route.
        assert status in (403,404),(path,status)
        denials[path]=status
    report=dict(status='PASS',release=RELEASE,files=len(verified),private_denials=len(private),private_statuses=denials,security_headers=True,
                scope='All510canonical HTTPS hashes; five private routes denied403/404 (origin404 verified separately); no gameplay/player acceptance inferred')
    (HERE/'wiki-public-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

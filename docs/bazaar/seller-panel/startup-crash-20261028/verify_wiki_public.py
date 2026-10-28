"""Verify the complete public wiki and private-source denials over HTTPS."""
import concurrent.futures
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError

HERE=Path(__file__).resolve().parent
ORIGIN='https://wiki.nightcapgame.org/'


def probe(path):
    try:r=urlopen(Request(ORIGIN+path,headers={'User-Agent':'NightcapLauncher/0.6.0','Accept-Encoding':'identity'}),timeout=45)
    except HTTPError as e:r=e
    with r:return r.status,hashlib.sha256(r.read()).hexdigest(),r.headers


def main():
    manifest=json.loads((Path('E:/EQ_Local_Dev/artifacts/client-crash-20261028/wiki/20261028-bazaar-startup-hotfix-v1.tar.json')).read_text())
    def verify(pair):
        path,digest=pair;status,actual,headers=probe(path)
        assert status==200 and actual==digest,(path,status)
        assert headers.get('X-Content-Type-Options')=='nosniff' and "script-src 'self'" in headers.get('Content-Security-Policy',''),path
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(verify,manifest.items()))
    denied=['.env','articles/features.json','content-review.json','catalog.json','wiki/current/index.html']
    for path in denied:assert probe(path)[0]==404,path
    report={'result':'PASS','release':'20261028-bazaar-startup-hotfix-v1','files':len(manifest),'sha256_and_security_headers':True,'private_routes_denied':denied,'verified_at':datetime.now(timezone.utc).isoformat()}
    (HERE/'wiki-public-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))


if __name__=='__main__':main()

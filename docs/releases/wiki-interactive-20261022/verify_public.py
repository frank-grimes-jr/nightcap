"""Verify all public wiki hashes, response policy and private-source denials."""
import concurrent.futures
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HOST = 'https://wiki.nightcapgame.org/'


def probe(path):
    req = Request(HOST+path, headers={'User-Agent':'NightcapLauncher/0.6.0', 'Accept-Encoding':'identity'})
    try:response = urlopen(req, timeout=45)
    except HTTPError as error:response = error
    with response:
        assert response.url.startswith(HOST), 'Unexpected redirected host'
        return response.status, hashlib.sha256(response.read()).hexdigest(), response.headers


def main():
    manifest = json.loads((Path('E:/EQ_Local_Dev/artifacts/wiki-interactive-20261022/20261022-interactive-handbook-v1.tar.json')).read_text(encoding='utf-8'))
    assert len(manifest) == 465
    def verify(entry):
        path, expected = entry
        status, digest, headers = probe(path)
        assert status == 200 and digest == expected, (path, status, digest)
        assert headers.get('X-Content-Type-Options') == 'nosniff', path
        assert "script-src 'self'" in headers.get('Content-Security-Policy',''), path
        return path
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        verified = list(pool.map(verify, manifest.items()))
    denied = ['.env','articles/item-upgrades.json','content-review.json','catalog.json','wiki/current/index.html']
    for path in denied:assert probe(path)[0] == 404, path
    report = {'result':'PASS','release':'20261022-interactive-handbook-v1',
              'verified_at':datetime.now(timezone.utc).isoformat(),
              'files':len(verified),'sha256_and_security_headers':True,'private_routes_denied':denied}
    with (HERE/'wiki-public-verification.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report))


if __name__ == '__main__':main()

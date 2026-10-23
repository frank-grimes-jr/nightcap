"""Verify the owner-confirmed wiki release on the public origin."""
import concurrent.futures
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
HOST = 'https://wiki.nightcapgame.org/'
RELEASE = '20261022-hate-keeper-confirmed-v1'


def probe(path):
    req = Request(HOST + path, headers={'User-Agent': 'NightcapLauncher/0.6.0', 'Accept-Encoding': 'identity'})
    try:
        response = urlopen(req, timeout=45)
    except HTTPError as error:
        response = error
    with response:
        assert response.url.startswith(HOST), 'Unexpected redirected host'
        return response.status, hashlib.sha256(response.read()).hexdigest(), response.headers


def main():
    manifest = json.loads((Path('E:/EQ_Local_Dev/artifacts/hate-keeper-commonlands-20261022') / (RELEASE + '.tar.json')).read_text(encoding='utf-8'))
    assert len(manifest) == 466

    def verify(entry):
        path, expected = entry
        status, digest, headers = probe(path)
        assert status == 200 and digest == expected, (path, status, digest)
        assert headers.get('X-Content-Type-Options') == 'nosniff', path
        assert "script-src 'self'" in headers.get('Content-Security-Policy', ''), path
        return path

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        verified = list(pool.map(verify, manifest.items()))
    denied = ['.env', 'articles/item-upgrades.json', 'content-review.json', 'catalog.json', 'wiki/current/index.html']
    for path in denied:
        assert probe(path)[0] == 404, path
    report = {'result': 'PASS', 'release': RELEASE, 'verified_at': datetime.now(timezone.utc).isoformat(),
              'files': len(verified), 'sha256_and_security_headers': True, 'private_routes_denied': denied}
    (HERE / 'wiki-public-verification-confirmed.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()

"""Verify every public file hash/header and the private-source denials."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from publish_wiki import HERE, ART, RELEASE
ORIGIN = 'https://wiki.nightcapgame.org/'


def probe(path):
    try:
        result = urlopen(Request(ORIGIN + path, headers={'User-Agent': 'NightcapLauncher/0.6.0', 'Accept-Encoding': 'identity'}), timeout=45)
    except HTTPError as error:
        result = error
    with result:
        return result.status, hashlib.sha256(result.read()).hexdigest(), result.headers


def main():
    manifest = json.loads((ART / (RELEASE + '.tar.json')).read_text())
    def verify(pair):
        path, digest = pair
        status, actual, headers = probe(path)
        assert status == 200 and actual == digest, (path, status)
        assert headers.get('X-Content-Type-Options') == 'nosniff'
        assert "script-src 'self'" in headers.get('Content-Security-Policy', '')
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(verify, manifest.items()))
    denied = ['.env', 'articles/features.json', 'content-review.json', 'catalog.json', 'wiki/current/index.html']
    for path in denied:
        assert probe(path)[0] == 404, path
    report = dict(result='PASS', release=RELEASE, files=len(manifest),
                  sha256_and_security_headers=True, private_routes_denied=denied,
                  verified_at=datetime.now(timezone.utc).isoformat())
    (HERE / 'wiki-public-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()

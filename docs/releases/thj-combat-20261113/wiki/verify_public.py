"""Verify the effective public release, canonical versioned assets and private exclusions."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
import re
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from prepare import ART, BASE, HERE, PREVIOUS, RELEASE, save

ORIGIN = 'https://wiki.nightcapgame.org/'

def probe(path):
    request = Request(ORIGIN + path, headers={'User-Agent': 'NightcapWikiPublicationCheck/1.0', 'Accept-Encoding': 'identity'})
    for attempt in range(3):
        try:
            try:
                response = urlopen(request, timeout=45)
            except HTTPError as error:
                if error.code >= 500:
                    raise
                response = error
            with response:
                assert response.geturl() == ORIGIN + path
                body = response.read()
                if response.headers.get('Content-Encoding') == 'gzip':
                    body = gzip.decompress(body)
                return response.status, body, response.headers
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            sleep(attempt + 1)

def verify(predecessor):
    release, directory = (PREVIOUS, BASE) if predecessor else (RELEASE, ART)
    manifest = json.loads((directory / (release + '.tar.json')).read_bytes())
    code, home, _ = probe('')
    assert code == 200 and hashlib.sha256(home).hexdigest() == manifest['index.html']
    version = re.search(rb'assets/wiki\.css\?v=([a-f0-9]+)', home)[1].decode()
    def check(row):
        name, expected = row
        route = name + '?v=' + version if name in ('assets/wiki.css', 'assets/search.js') else name
        status, body, headers = probe(route)
        assert status == 200 and hashlib.sha256(body).hexdigest() == expected, route
        assert headers['X-Content-Type-Options'] == 'nosniff' and "script-src 'self'" in headers['Content-Security-Policy'], route
        return name
    with ThreadPoolExecutor(max_workers=6) as pool:
        files = len(list(pool.map(check, manifest.items())))
    denied = {path:probe(path)[0] for path in ('.env','articles/features.json','content-review.json','catalog.json','wiki/current/index.html')}
    assert all(status in (403,404) for status in denied.values())
    report = dict(result='PASS', release=release, files=files, canonical_root=True, hashes_and_headers=True,
                  asset_version=version, versioned_assets=2, private_status=denied,
                  verified_at=datetime.now(timezone.utc).isoformat())
    save(HERE / ('predecessor-https.json' if predecessor else 'public-verification.json'), report)
    print(report)
if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predecessor', action='store_true')
    verify(parser.parse_args().predecessor)

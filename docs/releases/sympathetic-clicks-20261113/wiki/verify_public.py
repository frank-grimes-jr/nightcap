"""Check canonical HTTPS bytes, privacy headers and the two public named camps."""
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

from prepare import ART, HERE, PARENT, PREVIOUS, RELEASE, save

ORIGIN = 'https://wiki.nightcapgame.org/'
CAMPS = {
    610338: ('Runed Lava Pendant', 'soldunga', 'lava elemental'),
    610150: ('Moonstone Ring', 'gukbottom', 'frenzied ghoul'),
}


def probe(path):
    request = Request(ORIGIN + path, headers={'User-Agent': 'NightcapLauncher/0.6.0', 'Accept-Encoding': 'identity'})
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


def loot():
    status, body, _ = probe('loot-data/current/index.json')
    assert status == 200
    index = json.loads(body)
    revision = index['snapshot']
    assert index['era'] == 0 and re.fullmatch('[0-9a-f]{16}', revision)
    assert index['base_url'] == '/loot-data/' + revision + '/'
    details = {}
    for key, (name, zone, npc) in CAMPS.items():
        assert any(row['id'] == key for row in index['items'])
        path = f'loot-data/{revision}/item-{key}.json'
        status, body, _ = probe(path)
        assert status == 200, path
        row = json.loads(body)
        assert row['id'] == key and name.casefold() in row['name'].casefold() and row['era'] == 0
        assert row['classes'] == 65535 and row['slots'] & (32 if key == 610338 else 98304)
        sources = [s for s in row['sources'] if s['zone'] == zone and npc in s['npc'].replace('_', ' ').casefold()]
        assert sources and all(s['rate'][1] > 0 and s['locations'] for s in sources), (row['name'], row['sources'])
        details[key] = dict(name=row['name'], sources=[s['npc'] for s in sources], zone=zone,
                            sha256=hashlib.sha256(body).hexdigest(), route=ORIGIN + path)
        assert not {'focuseffect', 'clickeffect'} & row.keys()
    return dict(snapshot=revision, captured_at=index['captured_at'], targets=details,
                effect_fields='Omitted by the existing public loot capture and projection. The Equipment guide documents both clicks and the retained ring focus.')


def verify(predecessor=False):
    release, folder = (PREVIOUS, PARENT) if predecessor else (RELEASE, ART)
    manifest = json.loads((folder / (release + '.tar.json')).read_bytes())
    status, homepage, _ = probe('')
    assert status == 200 and hashlib.sha256(homepage).hexdigest() == manifest['index.html']
    asset_version = re.search(rb'assets/wiki\.css\?v=([a-f0-9]+)', homepage)[1].decode()
    def check(pair):
        path, pin = pair
        if path in ('assets/wiki.css', 'assets/search.js'):
            path += '?v=' + asset_version
        status, body, headers = probe(path)
        assert status == 200 and hashlib.sha256(body).hexdigest() == pin, (path, status)
        assert headers['X-Content-Type-Options'] == 'nosniff' and "script-src 'self'" in headers['Content-Security-Policy']
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(check, manifest.items()))
    check(('', manifest['index.html']))
    denied = ['.env', 'articles/features.json', 'content-review.json', 'catalog.json', 'wiki/current/index.html']
    private = {path: probe(path)[0] for path in denied}
    assert all(status in (403,404) for status in private.values()), private
    report = dict(result='PASS', release=release, files=len(manifest), canonical_root_verified=True,
                  hashes_and_headers=True, versioned_assets=2, asset_version=asset_version, denied=private, loot=loot(), player_qa='open',
                  verified_at=datetime.now(timezone.utc).isoformat())
    save(HERE / ('predecessor-https.json' if predecessor else 'public-verification.json'), report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--check-camps', action='store_true', help='Read current public acquisition data only.')
    modes.add_argument('--predecessor', action='store_true', help='Verify the current complete public preimage before publishing.')
    args = parser.parse_args()
    if args.check_camps:
        print(json.dumps(loot(), indent=2))
    else:
        verify(args.predecessor)

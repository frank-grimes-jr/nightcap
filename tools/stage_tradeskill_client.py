"""Stage the four reviewed tradeskill client assets; does not sign or publish.

Merge this delta into the latest signed game inventory for an authorized release.
The protected client is read-only. Existing unrelated assets must be retained.
"""
import argparse
import hashlib
import json
from pathlib import Path
from client_gameplay_assets import ui_xml

ROOT = Path(__file__).resolve().parents[1]
CLIENT_SHA = '2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    client, output = args.client.resolve(), args.output.resolve()
    if output == client or client in output.parents or output in client.parents:
        raise ValueError('Output must be separate from the original client')
    image = (client / 'eqgame.exe').read_bytes()
    if len(image) != 8774656 or hashlib.sha256(image).hexdigest() != CLIENT_SHA:
        raise ValueError('Unsupported exact client')
    files = {
        'dinput8.dll': (ROOT / 'eq-client-dll/build/dinput8.dll').read_bytes(),
        'nightcap-patches.cfg': (ROOT / 'eq-client-dll/config/nightcap-patches.cfg').read_bytes(),
        'nightcap-patch-sites.json': (ROOT / 'eq-client-dll/config/patch-sites.json').read_bytes(),
        'uifiles/nightcap/equi_tradeskillwnd.xml': ui_xml(
            (client / 'uifiles/default/EQUI_TradeskillWnd.xml').read_bytes(), 'tradeskill'),
    }
    if b'tradeskill_repeat=1' not in files['nightcap-patches.cfg']:
        raise ValueError('Tradeskill hook not enabled')
    catalog = json.loads(files['nightcap-patch-sites.json'])
    if 'tradeskill_repeat' not in catalog['required_features']:
        raise ValueError('Missing required tradeskill catalog feature')
    audit = {'status': 'staged_not_signed_or_installed', 'kind': 'delta_not_full_game_inventory',
             'proxy_version': catalog['proxy_version'], 'exact_client_sha256': CLIENT_SHA,
             'files': {name: {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                       for name, data in files.items()}}
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        path = output / 'files' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (output / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()

"""Fail closed on drift in a fresh SELECT-only production reference capture."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT/'docs/items/paladin-weapon-grip/balance/production-reference-complete.json'
STAT_REFERENCE = ROOT/'docs/items/paladin-weapon-grip/balance/assessment/public-stats-reference.json'
STAT_FIELDS = ('accuracy','astr','awis','heroic_str','heroic_wis','healamt','spelldmg','proclevel2')
QUESTS = ('paw/v0/Brother_Hayle.lua', 'southkarana/#Brother_Hayle.lua', 'airplane/Inte_Akera.lua',
          'fearplane/Irak_Altil.lua', 'hohonora/#Irak_Altil.lua',
          'ecommons/Epic_Forgemaster.pl', 'poknowledge/Epic_Forgemaster.pl')
UNCHANGED = ()
EXPECTED_DISPATCH = {
    'paw/Brother_Hayle':'paw/v0/Brother_Hayle.lua',
    'southkarana/#Brother_Hayle':'southkarana/#Brother_Hayle.lua',
    'airplane/Inte_Akera':'airplane/Inte_Akera.lua',
    'fearplane/Irak_Altil':'fearplane/Irak_Altil.lua',
    'hohonora/#Irak_Altil':'hohonora/#Irak_Altil.lua',
    'ecommons/Epic_Forgemaster':'ecommons/Epic_Forgemaster.pl',
    'poknowledge/Epic_Forgemaster':'poknowledge/Epic_Forgemaster.pl',
}


def profiles():
    text = (ROOT/'server-mods/code/common/paladin_weapon_grip.h').read_text(encoding='utf-8')
    rows = re.findall(r'\{(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*\d+,\s*\d+\}', text)
    result = {int(r[0]): tuple(map(int, r[1:])) for r in rows}
    if len(rows) != 10 or len(result) != 10:
        raise ValueError('Expected ten unique reviewed profiles')
    return result


def validate(capture):
    if capture.get('environment') != 'production' or capture.get('read_only') is not True:
        raise ValueError('Expected SELECT-only production capture')
    reference = json.loads(REFERENCE.read_text(encoding='utf-8'))
    stats = {r['id']: r for r in json.loads(STAT_REFERENCE.read_text(encoding='utf-8'))['items']}
    items = {row['id']: row for row in capture['items']}
    for id in profiles():
        row = items[id]
        original = next(r for r in reference['items'] if r['id'] == id)
        damage, delay = original['damage'], original['delay']
        if (row['damage'],row['delay'],row['itemtype'],row['slots'],row['classes']) != (damage,delay,1,8192,4):
            raise ValueError(f'Canonical weapon drift: {id}')
        if any(row.get(field) != original[field] for field in original):
            raise ValueError(f'Canonical weapon drift: {id}')
        if any(row.get(field) != stats[id][field] for field in STAT_FIELDS):
            raise ValueError(f'Canonical support-stat drift: {id}')
    for path in QUESTS + UNCHANGED:
        row = capture['scripts'][path]
        if hashlib.sha256(row['source'].encode()).hexdigest() != row['sha256']:
            raise ValueError(f'Invalid script digest: {path}')
        if row['sha256'] != reference['scripts'][path]['sha256']:
            raise ValueError(f'Quest preimage drift: {path}')
    helper = capture['helpers']['lua_modules/items.lua']
    if (hashlib.sha256(helper['source'].encode()).hexdigest() != helper['sha256'] or
            helper['sha256'] != reference['helpers']['lua_modules/items.lua']['sha256']):
        raise ValueError('Tier-aware quest helper drift')
    if capture['precedence'] != {key:[path] for key,path in EXPECTED_DISPATCH.items()}:
        raise ValueError('Quest precedence drift')
    if set(capture.get('dispatch',{})) != set(EXPECTED_DISPATCH):
        raise ValueError('Missing seven-script quest dispatch evidence')
    for key, path in EXPECTED_DISPATCH.items():
        resolutions = capture['dispatch'][key]
        expected_versions = {'v0':[path]}
        # The captured Paw v1 directory has no Brother Hayle quest. The approved
        # reward is explicitly Paw v0; do not install it into the later version.
        if key == 'paw/Brother_Hayle':
            expected_versions['v1'] = []
        if (not resolutions or {row['version'] for row in resolutions} != set(expected_versions)
                or any(row['selected'] != expected_versions[row['version']] for row in resolutions)):
            raise ValueError(f'Quest dispatch drift: {key}')
    if capture['recipe_references']:
        raise ValueError('New recipe consumers require review')
    return {'canonical_weapons':10,'reward_scripts':4,'epic_compatibility_scripts':3,'dispatch_paths':7,'result':'PASS'}


def validate_fresh(capture, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    observed = datetime.datetime.fromisoformat(capture['observed_utc'])
    if observed.tzinfo is None:
        raise ValueError('Capture must have a UTC-aware timestamp')
    age = (now-observed).total_seconds()
    if age < -300 or age > 3600:
        raise ValueError('Capture must be from the last hour; recapture before release')
    return validate(capture)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True,help='Fresh capture; do not substitute historical evidence at release')
    args = parser.parse_args()
    print(json.dumps(validate_fresh(json.loads(args.capture.read_text(encoding='utf-8')))))

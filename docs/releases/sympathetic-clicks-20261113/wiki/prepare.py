"""Build the Classic click guide from the last authenticated public wiki source."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ART = ROOT / 'artifacts/sympathetic-prod/official-wiki-ste'
PARENT_SOURCE = ROOT.parent / 'wiki-simple-ste'
PARENT = PARENT_SOURCE / 'artifacts/wiki-simple-ste-20261113'
PREVIOUS = '20261113-wiki-simple-ste-v1'
RELEASE = '20261113-sympathetic-clicks-v1'
SLUG = 'stock-sympathetic'
SOURCE = 'docs/items/sympathetic-clicks/README.md'


def save(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def edit(wiki):
    """Apply the reviewed additions independently to the two different source trees."""
    equipment = (
        '<h2 id="stock-sympathetic">Classic sympathetic clicks</h2>'
        '<p>Any class can use these two Ascended items. Only the Ascended copies grant the buffs. '
        'You can also make them with the ordinary <a href="item-upgrades.html#normal-items">Reforging Box recipes</a>.</p>'
        '<ol><li>Equip the item.</li><li>Right-click it to start the two-second cast.</li>'
        '<li>After the cast, put your usual gear back on.</li></ol>'
        '<p>Both buffs can stay active together. Use the same item again to refresh its buff.</p>'
        '<ul><li><strong>Sympathetic Strike I.</strong> A lava elemental in Solusek’s Eye drops the '
        '<a href="loot-finder.html?item=610338">Runed Lava Pendant (Ascended)</a>. '
        'Cast a single-target direct damage spell from a spell gem. The base mana cost must be at least 10 before mana preservation. '
        'If the spell lands fully, the target takes one extra hit. An eligible lifetap deals extra damage without increasing its healing.</li>'
        '<li><strong>Sympathetic Healing I.</strong> A frenzied ghoul in Lower Guk drops the '
        '<a href="loot-finder.html?item=610150">Moonstone Ring (Ascended)</a>. The ring keeps Extended Range II. '
        'Cast a single-target direct heal from a spell gem. The spell must have a base mana cost above zero. '
        'The same target receives one extra heal. If a worn sympathetic focus delivers a direct heal on this cast, the worn effect takes precedence.</li></ul>'
        '<p>Each bonus equals 5% of the largest eligible hit or heal from the cast. Round down to a maximum of 48. '
        'A 40-point heal gives 2 extra before overheal. A 960-point hit gives 48 extra before target protections.</p>'
        '<p>Area spells, spells with a duration and partial resists cannot activate either buff. '
        'Pet casts, item clicks and triggered casts also give no bonus.</p>')
    feature_text = '<a href="equipment.html#stock-sympathetic">Classic sympathetic clicks</a> — Two Ascended jewelry pieces grant extra damage or healing on eligible spells.'
    changes = (
        '<h2 id="stock-sympathetic">November 13 · Classic sympathetic clicks</h2>'
        '<p>The Ascended Runed Lava Pendant now grants Sympathetic Strike I. The Ascended Moonstone Ring grants Sympathetic Healing I. '
        'Exit EverQuest. Select Play in the Nightcap launcher to get the new spell descriptions. '
        'See <a href="equipment.html#stock-sympathetic">item sources, eligible spells and bonus amounts</a>.</p>')
    for name, block in [('equipment', equipment), ('features', feature_text), ('recent-changes', changes)]:
        file = wiki / 'articles' / (name + '.json')
        data = json.loads(file.read_bytes())
        if name == 'equipment':
            anchor = '<h2 id="stock-worn-atk">'
        elif name == 'features':
            if '<li id="combat">' in data['body']:
                anchor = '<li id="combat">'
                block = '<li>'+block+'</li>'
            else:
                anchor = '<p><a href="combat.html">Read the combat rules'
                block = '<p>'+block+'</p>'
        else:
            anchor = None
        if block in data['body']:
            continue
        if anchor:
            assert data['body'].count(anchor) == 1
            data['body'] = data['body'].replace(anchor, block + anchor)
        else:
            data['body'] = block + data['body']
        if SOURCE not in data['sources']:
            data['sources'].append(SOURCE)
        if name == 'equipment':
            for word in ('sympathetic', 'Runed Lava Pendant', 'Moonstone Ring'):
                if word not in data['keywords']:
                    data['keywords'].append(word)
        data['reviewed_at'] = data['updated'] = '2026-11-13'
        save(file, data)
    file = wiki / 'articles/unreleased.json'
    data = json.loads(file.read_bytes())
    marker = '<h2 id="stock-sympathetic">'
    if marker in data['body']:
        before, section = data['body'].split(marker)
        assert section.startswith('Classic sympathetic clicks · test candidate</h2><p>')
        end = section.index('</p>') + len('</p>')
        data['body'] = before + section[end:]
        data['sources'] = [s for s in data['sources'] if s != SOURCE]
        save(file, data)


def prepare():
    base = json.loads((PARENT / (PREVIOUS + '.tar.json')).read_bytes())
    assert len(base) == 631
    checkout = ART / 'wiki-source'
    if not checkout.exists():
        shutil.copytree(PARENT_SOURCE/'wiki', checkout/'wiki', ignore=shutil.ignore_patterns('dist', '__pycache__'))
    for rel in ('config/classic-raid-augments.json', 'config/zone-hunt-rates.json',
                'docs/releases/wiki-simple-ste-20261113/public-contract.json'):
        (checkout/rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PARENT_SOURCE/rel, checkout/rel)
    site = checkout / 'wiki'
    for name in ('equipment', 'features', 'recent-changes', 'unreleased'):
        rel = Path('wiki/articles') / (name + '.json')
        shutil.copyfile(PARENT_SOURCE / rel, checkout / rel)
    cmd = [sys.executable, '-B', '-X', 'utf8']
    def build(*args):
        subprocess.run(cmd + ['build.py', *args], cwd=site, check=True)
        return {p.relative_to(site/'dist').as_posix(): sha(p) for p in (site/'dist').rglob('*') if p.is_file()}
    assert build() == base, 'The retained source must reproduce every previous public byte.'
    edit(site)
    subprocess.run(cmd + ['-m', 'unittest', 'test_wiki', 'test_refresh', 'test_public_language', 'test_loot_model', 'test_loot_refresh'], cwd=site, check=True)
    archive = ART / (RELEASE + '.tar.gz')
    if archive.exists():
        after = build()
        assert json.loads((ART / (RELEASE + '.tar.json')).read_bytes()) == after
    else:
        after = build('--package', str(archive))
    assert set(after) == set(base)
    changes = sorted(k for k in base if base[k] != after[k])
    assert changes == ['equipment.html', 'features.html', 'recent-changes.html', 'search-index.json'], changes
    for test in ('test_search.cjs', 'test_equipment.cjs', 'test_loot_finder.cjs', 'test_experience.cjs'):
        subprocess.run(['node', test], cwd=site, check=True)
    index = json.loads((site / 'dist/search-index.json').read_bytes())
    equipment = next(row for row in index if row['slug'] == 'equipment')
    assert 'Moonstone Ring' in json.dumps(equipment, ensure_ascii=False)
    receipt = dict(release=RELEASE, predecessor=PREVIOUS, previous_manifest_sha256=sha(PARENT/(PREVIOUS+'.tar.json')),
                   exact_predecessor_reproduced=True, files=len(after), retained=len(base)-len(changes),
                   changed=changes, package_sha256=sha(archive), manifest_sha256=sha(ART/(RELEASE+'.tar.json')))
    save(HERE / 'candidate.json', receipt)
    print(receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edit-repository', action='store_true')
    if parser.parse_args().edit_repository:
        edit(ROOT / 'wiki')
    else:
        prepare()

"""Prepare approved release prose; publication waits for paired activation."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ARTICLES = ROOT / 'wiki/articles'


def replace_section(body, identity, replacement, level=2):
    pattern = rf'<h{level} id="{identity}">.*?(?=<h[23]\b|$)'
    result, count = re.subn(pattern, replacement + '\n', body, flags=re.S)
    assert count == 1, (identity, count)
    return result


def main():
    assert not (HERE / 'article-review.json').exists(), 'Article preparation already recorded; review edits instead of replaying'
    before = {p.name: p.read_bytes() for p in ARTICLES.glob('*.json')}
    data = {name: json.loads(value) for name, value in before.items()}
    changes = {}
    d = data['dungeon-modes.json']
    d['body'] = d['body'].replace(
        '; private Hate entrance: <code>-374.8,-337.08,2</code>',
        '; new-layout Keeper: <code>656,-409,2</code>; original-run Keeper: <code>-374.8,-337.08,2</code>')
    d['body'] = d['body'].replace('<td>hateplane / 50</td>', '<td>Plane of Hate (both layouts) / 50</td>')
    d['body'] = replace_section(d['body'], 'hate-layout-preview', '''<h2 id="hate-layout-preview">Plane of Hate layout — live testing</h2>
<p>New Raid and Grind runs from the East Commonlands Keeper use a ground-level Plane of Hate layout. The Keeper is still at <code>/loc -1570,-346,3</code>. You must be level 46 to enter. Fully exit EverQuest and press Play in the launcher to install the paired terrain and creature models before entering.</p>
<p>Existing unexpired runs remain in the original layout, with their enemies, corpses, timers and earned progress intact. Return to your current run through the Keeper; joining an existing group run follows its layout. Ordinary spell travel keeps its original destination. To start a new-layout run, use the Commonlands Keeper after your original run has ended.</p>
<p>The same four bosses, NPC strength, ordinary and epic loot, Book of Souls, experience, Hunt rewards and Raid/Grind completion rewards remain. The Hunt catalog still labels that reward family <code>hateplane</code>. Enemy placement and patrol routes have changed, so pull spacing and difficulty still need player testing.</p>
<div class="table-wrap"><table><caption>New-layout landmarks, in /loc order Y,X,Z</caption><thead><tr><th scope="col">Landmark</th><th scope="col">/loc</th></tr></thead><tbody><tr><td>Arrival</td><td><code>656,-393,2</code></td></tr><tr><td>Instance Keeper</td><td><code>656,-409,2</code></td></tr><tr><td>Magi P’Tasa</td><td><code>365.2,-361.9,3</code></td></tr><tr><td>Hand of the Maestro</td><td><code>-43,-93,3</code></td></tr><tr><td>Maestro of Rancor</td><td><code>-386,-173,3</code></td></tr><tr><td>Innoruuk</td><td><code>-765,-451,3</code></td></tr><tr><td>Book of Souls</td><td><code>313,-673,3</code></td></tr></tbody></table></div>
<p>All four bosses and the book have ground-level routes from the arrival point. RoF2 rendering, doors, actual pulls, complete runs and reconnect recovery remain open player checks.</p>''')
    changes['dungeon-modes.json'] = 'New Keeper destination, legacy-run continuity, both-layout reward identity, paired update and exact new landmarks; retain old anchors.'
    d = data['features.json']
    section = '''<h3 id="hate-layout-preview">Plane of Hate layout — live testing</h3><p>New Keeper runs place Nightcap’s existing Hate encounters on ground-level routes, preserving loot and earned rewards. Existing runs keep their original layout. <a href="dungeon-modes.html#hate-layout-preview">Entry, landmarks and testing</a>.</p>'''
    d['body'], count = re.subn(r'<h3 id="hate-layout-preview">.*?</p>', '', d['body'], flags=re.S)
    assert count == 1
    match = re.search(r'<h3[^>]*>Raid &amp; Grind dungeons</h3>.*?(?=<h3)', d['body'], re.S)
    assert match
    d['body'] = d['body'][:match.end()] + section + d['body'][match.end():]
    changes['features.json'] = 'Move the preserved Hate anchor into custom adventures and link the installed-layout guide.'
    data['unreleased.json']['body'] = replace_section(data['unreleased.json']['body'], 'hate-layout-preview', '''<h2 id="hate-layout-preview">Plane of Hate layout — live testing</h2><p>The paired Hate server and client update is installed for testing. New Keeper runs use ground-level routes while existing runs remain in the original layout. Nightcap encounters, loot and earned rewards are preserved. Rendering, routes, pulls and full-run acceptance remain open. <a href="dungeon-modes.html#hate-layout-preview">Current entry and testing guide</a>.</p>''')
    changes['unreleased.json'] = 'Mark only Hate as installed with unresolved player acceptance; preserve every unrelated preview boundary.'
    data['recent-changes.json']['body'] = replace_section(data['recent-changes.json']['body'], 'hate-layout-20261029', '''<h2 id="hate-layout-20261029">October 29: Plane of Hate ground-level layout — live testing</h2><p>New Raid and Grind runs from the East Commonlands Keeper now use the newer Hate layout, with Nightcap’s existing encounters, NPC strength, loot, epic items, Hunt drops, experience and completion rewards preserved. Existing unexpired runs remain usable in the original layout. Fully exit EverQuest and update through launcher Play before entering. Player rendering, pathing and balance checks remain open. <a href="dungeon-modes.html#hate-layout-preview">Entry, landmarks and testing</a>.</p>''')
    changes['recent-changes.json'] = 'Replace the unreleased October29 note with the approved paired-release scope and outstanding QA; preserve historical entries.'
    data['travel.json']['body'] += '\n<h2 id="hate-layout">Plane of Hate runs</h2><p>Use the level-46 Hate Keeper in East Commonlands at <code>/loc -1570,-346,3</code> for a new Raid or Grind run in the ground-level layout. Existing unexpired runs and groups continue in their original layout; ordinary spell travel retains its original destination. Update through launcher Play with EverQuest fully closed first. <a href="dungeon-modes.html#hate-layout-preview">Keeper locations and route details</a>.</p>'
    changes['travel.json'] = 'Distinguish new private entry from original runs and unchanged spell destinations; explain client update.'
    data['zone-hunt.json']['body'] += '\n<h2 id="hate-layout">Hate rewards across both layouts</h2><p>The new private Hate layout uses the original Plane of Hate Hunt family, approved enemy list and drop chances. The catalog’s <a href="zone-hateplane.html">hateplane rewards</a> apply to both layouts; this update does not add a second Hunt family or change forging. <a href="dungeon-modes.html#hate-layout-preview">Dungeon entry and testing</a>.</p>'
    changes['zone-hunt.json'] = 'Explain the retained hateplane catalog identity and unchanged family/chances in new private Hate.'
    reference = 'docs/dungeons/hate-layout-20261029/release/; paired activation and publication receipts required before public release; owner gameplay acceptance remains open'
    for name in changes:
        d = data[name]
        d['updated'] = d['reviewed_at'] = '2026-10-29'
        d['sources'] = [s for s in d['sources'] if 'docs/dungeons/hate-layout-20261029/' not in s] + [reference]
        (ARTICLES / name).write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    review = dict(date='2026-10-29', status='prepared approved release prose; publication gated on verified runtime/client activation',
        whole_wiki_article_count=len(data), articles=[])
    for name, d in sorted(data.items()):
        review['articles'].append(dict(path='wiki/articles/' + name, title=d['title'],
            before_sha256=hashlib.sha256(before[name]).hexdigest(),
            after_sha256=hashlib.sha256((ARTICLES / name).read_bytes()).hexdigest(),
            decision=changes.get(name, 'No change: reviewed scope; no altered class, economy, command, quest, UI, reward value or other release boundary.')))
    review['catalogs'] = 'Preserved exact catalog values and generated item/zone identities; owning Hate guides explain the same original Hunt family in both layouts.'
    review['home_commands_launcher'] = 'Home goals, commands and launcher instructions remain accurate; existing fully-exit/update guidance retained.'
    (HERE / 'article-review.json').write_text(json.dumps(review, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'reviewed': len(data), 'changed_articles': list(changes)}))


if __name__ == '__main__':
    main()

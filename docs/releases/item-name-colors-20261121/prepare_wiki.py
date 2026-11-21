"""Prepare only the item-color guide delta; never publish or advance the ledger."""
import json
import shutil
import subprocess
import sys
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = Path('E:/EQ_Local_Dev/artifacts/aa-purchase-latency-20261121/wiki')
OUT = ROOT / 'artifacts/item-name-colors/wiki-release/wiki'
EVIDENCE = Path(__file__).resolve().parent
GUIDE = ('<h2 id="item-name-colors">Item name colors</h2>'
    '<p>Usable item names show their quality: Regular is green, Polished is blue, Exalted is purple, and Ascended is orange.</p>'
    '<p>These colors appear in item inspection, Advanced loot and Bazaar seller listings. Hunt rewards use orange for Ascension.</p>'
    '<p>Native equipment restriction warnings still apply. A quality color does not change which items you can equip.</p>')
LOOT = '<p>Item names use the <a href="equipment.html#item-name-colors">quality colors</a> in the loot list and item rule details.</p>'
NEWS = ('<h2 id="item-name-colors-20261121">November 21, 2026: Item name colors</h2>'
    '<p>Item inspection, Advanced loot and Bazaar seller listings share quality colors: green, blue, purple and orange.</p>'
    '<p>Read the <a href="equipment.html#item-name-colors">color guide</a>. Equipment restriction warnings still apply.</p>')

def edit(wiki):
    for slug, extra, marker in [('equipment', GUIDE, 'item-name-colors'),
            ('advanced-loot', LOOT, 'equipment.html#item-name-colors'),
            ('recent-changes', NEWS, 'item-name-colors-20261121')]:
        path = wiki / 'articles' / (slug + '.json')
        data = json.loads(path.read_text(encoding='utf-8'))
        if marker in data['body']:
            continue
        if slug == 'equipment':
            anchor = '<h2 id="item-tiers">'
            assert data['body'].count(anchor) == 1
            data['body'] = data['body'].replace(anchor, extra + anchor)
        else:
            data['body'] = extra + data['body']
        data.setdefault('sources', []).append('docs/releases/item-name-colors-20261121/README.md; client candidate, unpublished, player QA open')
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__':
    for name in ('config', 'docs'):
        if not (OUT.parent / name).exists():
            shutil.copytree(BASE.parent / name, OUT.parent / name)
    if not OUT.exists():
        shutil.copytree(BASE, OUT, ignore=shutil.ignore_patterns('dist', '__pycache__'))
    # Reproduce the authenticated current publication before applying our delta.
    if 'item-name-colors' not in json.loads((OUT/'articles/equipment.json').read_bytes())['body']:
        subprocess.run([sys.executable, '-B', str(OUT/'build.py')],check=True)
        baseline = json.loads((EVIDENCE/'baseline.json').read_bytes())['wiki_manifest']
        actual = {p.relative_to(OUT/'dist').as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (OUT/'dist').rglob('*') if p.is_file()}
        assert actual == baseline, 'current public wiki reproduction drift'
        print('Reproduced all',len(actual),'current public wiki files')
    edit(OUT)
    edit(ROOT / 'wiki')
    reviews = []
    for path in sorted((BASE / 'articles').glob('*.json')):
        changed = path.name in {'equipment.json', 'advanced-loot.json', 'recent-changes.json'}
        reviews.append({'article': path.name, 'decision': 'color guidance updated' if changed else
            'no impact: no mechanics, acquisition, commands, stats, rates or reward definitions change'})
    report = {'status': 'candidate only; not published', 'baseline': '20261121-aa-purchase-latency-v1',
        'baseline_source': str(BASE), 'candidate_source': str(OUT), 'articles': reviews,
        'generated_catalogs': 'unchanged: item and zone values, rewards, drop rates and names unchanged',
        'home_features_commands': 'existing owning-guide links retained; this is a display correction',
        'ledger': 'historical source drift requires review; no unrelated fingerprint advance',
        'publication': 'recheck then-current public source and release authorization before publishing'}
    (EVIDENCE / 'wiki-review.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('Prepared three-article delta over the recorded current public source; no publication.')

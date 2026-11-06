"""Prepare only unpublished candidate notes and scoped wiki-impact evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
note = ('<h2 id="keeper-readiness-20261106">Instance Keeper entry repair — Not released</h2>'
        '<p>A tested server correction is prepared for Raid and Grind requests rejected after the November6 '
        'augment update. It restores existing entry behavior and preserves earned run progress. '
        'Deployment and player entry verification remain pending; no client update is needed.</p>')
articles = sorted((ROOT / 'wiki/articles').glob('*.json'))
review = []
for path in articles:
    data = json.loads(path.read_text(encoding='utf-8'))
    changed = path.stem in ('unreleased', 'recent-changes')
    review.append(dict(slug=data['slug'], decision='unpublished candidate note' if changed else 'no change',
                       reason='Repair restores existing documented Keeper entry; commands, rewards, balance, release labels and saved progress remain.'))
    if changed and 'keeper-readiness-20261106' not in data['body']:
        data['body'] = note+data['body']
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
catalog = json.loads((ROOT / 'wiki/catalog.json').read_text(encoding='utf-8'))
report = dict(date='2026-11-06', status='local candidate; no publication', articles=review,
              generated_catalog=dict(zones=len(catalog['zones']), items=len(catalog['items']), chapterhouse='retained',
                                     decision='No item, zone, acquisition, chance, command, stat or unlock changes; retain generated values/pages.'),
              home_features_commands='No new feature or command; keep existing guide links, summaries and candidate labels. No repeated announcements.',
              source_drift='Historical global ledger remains REVIEW REQUIRED; not advanced.',
              public_release='Existing verified augment-display publication remains unchanged; these candidate notes are unpublished.')
(HERE / 'wiki-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps(dict(articles=len(review), changed=['unreleased','recent-changes'], publication=False)))

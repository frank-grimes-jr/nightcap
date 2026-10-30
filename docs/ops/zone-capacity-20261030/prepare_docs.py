"""Record candidate-only wiki impact without publishing or advancing its ledger."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
source='docs/ops/zone-capacity-20261030/README.md; tested candidate, not deployed'
fragments={
 'travel':'<h2 id="zoning-capacity">Travel capacity correction — not released</h2><p>A tested server update is awaiting activation to prevent the reported return to the source zone after travelling through many areas. It adds zone capacity and shortens empty retention only in reviewed travel areas. Current live behaviour is unchanged; see <a href="unreleased.html#zoning-capacity">In development</a>.</p>',
 'unreleased':'<h2 id="zoning-capacity">Travel capacity correction — not released</h2><p>The fix for running out of available zones during extended travel is tested but not installed. Activation is pending server disk headroom and maintenance approval. Dungeon progression, rewards and encounter-specific timers are preserved by the candidate. In-game travel and return-state checks remain pending.</p>',
 'recent-changes':'<h2 id="zoning-capacity-20261030">October 30 — travel capacity candidate</h2><p><strong>Not released.</strong> A tested correction addresses the reported bounce back from Plane of Fear after travelling through many zones. It increases zone capacity and adjusts only reviewed empty travel-zone timers. Server activation and player acceptance remain pending; <a href="unreleased.html#zoning-capacity">details</a>.</p>'}
records=[]
for path in sorted((ROOT/'wiki/articles').glob('*.json')):
    data=json.loads(path.read_text(encoding='utf-8'))
    slug=data['slug']
    records.append({'slug':slug,'impact':'candidate travel status' if slug in fragments else
                    'no released mechanic, command, reward, catalog or home summary change'})
    if slug in fragments:
        if 'id="zoning-capacity' not in data['body']:
            data['body'] += '\n'+fragments[slug]
            data['updated']='2026-10-30'
            data.setdefault('sources',[]).append(source)
            path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
review={'source_ref':'989a464c345fb2c3799f5b769090442039a1d35e plus working tree',
        'articles_reviewed':len(records),'articles':records,
        'generated_catalog':'All source catalogs unchanged; no item/zone values or release promotions.',
        'Features':'Capacity bug fix, not a new gameplay feature; no directory entry needed.',
        'publication':'Not published; explicit candidate labels remain.',
        'ledger':'Historical drift remains review-required; no blanket advance.'}
(HERE/'wiki-review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
print(f'Reviewed impact across {len(records)} authored articles; three candidate notes; no publication.')

"""Reconcile the prepared wiki candidate only after a verified live receipt."""
import json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
WIKI=Path('E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki/wiki')
affected=('dungeon-modes','tunnel','travel','features','index','unreleased','recent-changes')
receipt=json.loads((HERE/'deployment.json').read_text());assert receipt['gateway_open'] and receipt['contract']=={'schema':39,'content':499}
notice='<p class="notice" id="hate-commonlands-candidate"><strong>Live testing — Hate Keeper in Commonlands:</strong> Find the Plane of Hate Keeper in East Commonlands at <code>/loc -1570,-346,3</code>, between Mirielle and Khalure in the travel area. Raid, Grind and return entry lead to Hate; private Hate instances retain an entrance Keeper. Public and private Hate entry require level 46; GM status is no longer required. The server update is installed. In-game visibility, travel and gameplay acceptance remain open.</p>'
for name in affected:
    path=WIKI/'articles'/(name+'.json');article=json.loads(path.read_text(encoding='utf-8'))
    article['body'],count=re.subn(r'<p class="notice" id="hate-commonlands-candidate">.*?</p>',lambda _:notice,article['body'],count=1)
    assert count==1
    article['body']=article['body'].replace('all 21 entrance Keepers','all 21 dungeon Keepers')
    if name=='dungeon-modes':
        old='<tr><td>Plane of Hate</td><td><code>-374.8,-337.08,2.0</code></td></tr>'
        assert old in article['body']
        article['body']=article['body'].replace(old,'<tr><td>Plane of Hate (East Commonlands)</td><td><code>-1570,-346,3</code>; private Hate entrance: <code>-374.8,-337.08,2</code></td></tr>')
        article['body']=article['body'].replace('Each Keeper has Raid, Grind, Enter, Join, Status, Claim Rewards and Reset.','Hate’s public Keeper is in East Commonlands; its private instances retain the entrance Keeper. Each Keeper has Raid, Grind, Enter, Join, Status, Claim Rewards and Reset.')
    article['sources']=[s for s in article['sources'] if not s.startswith('docs/ops/hate-keeper-commonlands-20261022/')]
    article['sources'].append('docs/ops/hate-keeper-commonlands-20261022/deployment.json and README.md; main PR299 and live server verified; owner gameplay acceptance open')
    path.write_text(json.dumps(article,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
ledger=json.loads((WIKI/'content-review.json').read_text(encoding='utf-8'))
ledger['supplemental_evidence']=[s for s in ledger['supplemental_evidence'] if not s.startswith('Hate Keeper Commonlands candidate:')]
ledger['supplemental_evidence'].append('Hate Keeper relocation: owner-authorized main PR299/a736fb0 and paired live server release verified; all12 workers and39 schema/499 content checks passed. All22 guides/432 generated routes reviewed; seven guides plus search updated for live placement, level46 and private Keeper continuity.384 Hunt catalog values, commands, Build Lab and handbook preserved. Owner native QA open. Source/deployment evidence in hate-keeper-commonlands checkout, docs/ops/hate-keeper-commonlands-20261022/.')
# Keep the main Build Lab review base: this supplemental review names the exact
# gameplay branch. A later publisher must reconcile both source histories.
(WIKI/'content-review.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Seven live Keeper guides updated; publication pending.')

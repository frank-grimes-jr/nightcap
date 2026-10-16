"""Prepare a preimage-checked wiki update; never publish the website."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wiki',type=Path,required=True)
    parser.add_argument('--preview',type=Path,required=True)
    args=parser.parse_args()
    out=ROOT/'docs/dungeons/wiki-update';out.mkdir(exist_ok=True)
    source=args.wiki
    source_note='docs/dungeons/{SPEC,README,QA}.md and catalog.json; dungeon candidate, not deployed'
    edits={}
    def article(slug):
        obj=json.loads((source/'articles'/f'{slug}.json').read_text(encoding='utf-8'))
        obj['sources'].append(source_note);obj['updated']='2026-10-16'
        edits['articles/'+slug+'.json']=obj
        return obj
    notice='<p class="notice"><strong>Not released:</strong> <a href="dungeon-modes.html">Raid and Grind dungeon modes</a> are a test candidate. Existing private instances keep their current behavior until a separate release.</p>'
    article('unreleased')['body']='<h2 id="dungeons">Raid and Grind dungeons</h2>'+notice+article_body('summary')+json.loads((source/'articles/unreleased.json').read_text(encoding='utf-8'))['body']
    article('travel')['body']+=notice
    article('features')['body']+=notice
    recent=article('recent-changes')
    recent['body']=recent['body'].replace('<ul>','<ul><li><a href="dungeon-modes.html">Raid and Grind dungeons</a> have a candidate guide and open test checklist; the modes and rewards are not released.</li>',1)
    edits['articles/dungeon-modes.json']=dict(slug='dungeon-modes',title='Raid & Grind dungeon candidate',
        summary='Seven private dungeons, personal boss checklists and shared rewards; not released.',
        body=article_body('full'),category='World',status='Not released',updated='2026-10-16',
        sources=[source_note],keywords=['raid','grind','dungeon rewards','Instance Keeper','Gynok Moltor','Lady Vox','Lord Nagafen'])
    ledger=json.loads((source/'content-review.json').read_text(encoding='utf-8'))
    ledger['supplemental_evidence'].append('Dungeon candidate: all maintained articles and generated catalog routes assessed in docs/dungeons/wiki-review.md. Existing release availability and live catalog stats retained; candidate pages only. Publication pending.')
    edits['content-review.json']=ledger
    preimages={};patch=[]
    for relative,obj in edits.items():
        path=source/relative
        old=path.read_bytes() if path.exists() else None
        preimages[relative]=hashlib.sha256(old).hexdigest() if old is not None else None
        new=json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
        target=out/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(new,encoding='utf-8')
        patch.extend(difflib.unified_diff((old.decode('utf-8') if old else '').splitlines(True),new.splitlines(True),
                     fromfile='a/wiki/'+relative if old else '/dev/null',tofile='b/wiki/'+relative))
    (out/'preimages.json').write_text(json.dumps(preimages,indent=2)+'\n')
    (out/'wiki.patch').write_text(''.join(patch),encoding='utf-8')
    shutil.copytree(source,args.preview,ignore=shutil.ignore_patterns('dist','__pycache__'),dirs_exist_ok=True)
    for relative in edits:shutil.copyfile(out/relative,args.preview/relative)
    print('Prepared six wiki files and a complete isolated preview; publication not performed.')

def article_body(kind):
    summary='<p>The candidate adds Raid and Grind choices to Befallen, Unrest, High Keep, Najena, Cazic-Thule, Permafrost and Nagafen’s Lair. Each run lasts twelve hours and allows up to six characters. Testing and balance acceptance remain open.</p>'
    if kind=='summary':return summary
    return '<p class="notice"><strong>Not released.</strong> This guide describes a test candidate. Production activation and player acceptance are pending.</p>'+summary+'''
<h2 id="modes">Choose a mode</h2><table><thead><tr><th>Rule</th><th>Grind</th><th>Raid</th></tr></thead><tbody><tr><td>Enemies</td><td>Normal stats and respawns</td><td>35% more HP, 15% more damage; defeated enemies do not return</td></tr><tr><td>Bosses</td><td>Required bosses available initially</td><td>Final boss unlocks after all required minibosses</td></tr><tr><td>Personal reward</td><td>One Normal item</td><td>One item: 90% Polished, 10% Ascended</td></tr></tbody></table>
<h2 id="credit">Earn your own checklist</h2><p>The creator chooses the mode. Hail the entrance Keeper for Raid, Grind, Enter, Join, Status, Claim Rewards and Reset. Tasks display the boss checklist and deadline; Status also shows permanent completion counts. Stay enrolled, connected and within 200 units of your party’s encounter, including vertical distance. Owned-pet kills count for the owner’s party. Missed kills never receive retroactive credit. Grind respawns offer another opportunity; Raid deaths are permanent for that run.</p>
<h2 id="rewards">Shared rewards and exclusive drops</h2><p>Twenty-four shared designs include eight armor pieces, eight weapon families, six accessories and two weight-reduction bags. Every dungeon uses these designs at its equipment band: Befallen 20; Unrest/Najena 30; High Keep/Cazic-Thule 40; Permafrost/Nagafen’s Lair 50. Selection does not filter by class. Rewards are permanent, tradeable, non-lore and have zero merchant resale. Dungeon rewards cannot be converted by existing forging recipes.</p><p>Raid final bosses also drop one, two or three distinct exclusive designs with 80%, 18% and 2% chances. Each independently rolls Polished or Ascended at 90%/10%. Examples include Moltor’s Graveblade, Rucksif’s Mourning Mantle, McCabe’s Hidden Treasury, Vox’s Hoarfrost Satchel and Nagafen’s Emberfang. These shared corpse drops use normal loot controls and are additional to native loot and personal completion rewards.</p><p>Weapon delay stays fixed between qualities. Bags have six, eight or ten slots and up to 100% weight reduction. Rewards are selected durably; reconnecting cannot change them. There is one personal completion reward per character per run. A full inventory leaves an earned claim at the Keeper.</p>
<h2 id="recovery">Keep progress through interruptions</h2><p>Progress and the original deadline survive reconnects and restarts. Abandoning the task removes its display, not earned credit. Only the creator can confirm a reset, and no player, pending entry or recoverable player corpse may remain inside. Earned claims survive reset and expiry. Classic Cazic-Thule restoration applies only to managed private instances; High Keep keeps normal faction consequences.</p>
<h2 id="testing">Testing still required</h2><p>All seven dungeons in both modes need in-game checks. Cazic-Thule paths and doors, inventory/loot recovery and demanding solo/small-group balance remain open. Lady Vox and Lord Nagafen explicitly require level-50 gameplay acceptance. Existing live reward catalog pages retain their released stats; these candidate items are not added to the live equipment catalog.</p>
'''

if __name__=='__main__':main()

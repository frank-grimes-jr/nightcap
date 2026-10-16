"""Replace candidate wiki notices after verified deployment; never publish."""
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
    evidence=json.loads((ROOT/'docs/dungeons/deployment/production-verification.json').read_text())
    assert evidence['status']=='healthy' and evidence['gateway_open'] and evidence['enabled_revision']==2026101601
    output=ROOT/'docs/dungeons/wiki-update'
    old_notice='<p class="notice"><strong>Not released:</strong> <a href="dungeon-modes.html">Raid and Grind dungeon modes</a> are a test candidate. Existing private instances keep their current behavior until a separate release.</p>'
    new_notice='<p class="notice"><strong>Live testing:</strong> <a href="dungeon-modes.html">Raid and Grind dungeon modes</a> are available from all seven entrance Keepers. Existing legacy runs keep their original behavior until expiry or reset. Gameplay and balance acceptance remain open.</p>'
    edits={}
    for slug in ('unreleased','travel','features','recent-changes','dungeon-modes','equipment','item-upgrades','index','getting-started'):
        relative='articles/'+slug+'.json'
        article=json.loads((args.wiki/relative).read_text(encoding='utf-8'))
        article['sources']=[s for s in article['sources'] if not s.startswith('docs/dungeons/')]
        article['sources'].append('docs/dungeons/deployment/production-verification.json and QA.md; deployed October 16 for live QA, owner acceptance pending')
        article['updated']='2026-10-16'
        body=article['body']
        if slug in ('travel','features'):
            assert old_notice in body or new_notice in body
            body=body.replace(old_notice,new_notice)
            if slug=='travel':
                body=body.replace('Hail to enter or join your group leader;','Hail to choose Raid or Grind, enter, or join your group leader;')
                body=body.replace('Resets ask for confirmation and discard that instance’s kills and progress.','Only the creator can confirm a reset, with no players, pending entries or recoverable corpses inside. Earned reward claims and permanent completion counts survive reset and expiry.')
            else:
                row='<section class="feature-row"><h3>Raid or Grind in seven private dungeons</h3><div><p>Choose normal respawning enemies or harder enemies with permanent deaths. Earn personal boss-checklist rewards; Raid final bosses add exclusive loot.</p><a href="dungeon-modes.html">Choose your dungeon mode →</a></div></section>'
                marker='<h2 id="adventuring">Prepare in the tunnel, then explore</h2><div class="feature-list">'
                assert marker in body
                if row not in body:body=body.replace(marker,marker+row)
        elif slug=='unreleased':
            if body.startswith('<h2 id="dungeons">'):
                body=body[body.index('<h2 id="journal">'):]
        elif slug=='recent-changes':
            body=body.replace('have a candidate guide and open test checklist; the modes and rewards are not released.','are deployed for live testing with personal boss checklists, shared rewards and exclusive Raid drops. Gameplay and balance acceptance remain open.')
        elif slug=='dungeon-modes':
            article.update(title='Raid & Grind dungeons',summary='Seven private dungeons, personal boss checklists and shared rewards, available for live testing.',status='Live testing')
            body=body.replace('<p class="notice"><strong>Not released.</strong> This guide describes a test candidate. Production activation and player acceptance are pending.</p>',new_notice)
            body=body.replace('The candidate adds Raid and Grind choices to','Raid and Grind choices are available in')
            body=body.replace('Existing live reward catalog pages retain their released stats; these candidate items are not added to the live equipment catalog.','The equipment index covers the separate zone-hunt catalog; dungeon rewards use the designs and bands described here. Existing forging recipes do not upgrade these rewards.')
        elif slug=='equipment':
            section='<h2 id="dungeon-rewards">Dungeon completion rewards</h2><p><a href="dungeon-modes.html">Raid and Grind dungeons</a> have 24 shared reward designs and three exclusive Raid designs per dungeon. Grind grants Normal; Raid grants Polished or Ascended. These permanent, tradeable, non-lore items have zero merchant resale and no existing forging recipe. Their bags have up to ten slots and 100% weight reduction.</p>'
            if section not in body:body+=section
            body=body.replace('Zone-hunt rewards and the supported divine summoned-hammer families have no merchant resale value.','Zone-hunt rewards, dungeon rewards and the supported divine summoned-hammer families have no merchant resale value.')
        elif slug=='item-upgrades':
            body=body.replace('Nightcap has two tier families:','Nightcap has two forgeable tier families:')
            section='<p><a href="dungeon-modes.html">Dungeon rewards</a> use Normal, Polished and Ascended qualities but have no conversion through these recipes. Earn their qualities through Grind or Raid completion and Raid final-boss drops.</p>'
            if section not in body:body+=section
        elif slug=='index':
            marker='<section><h2>New in Nightcap</h2>'
            section='<p><a href="dungeon-modes.html"><strong>Raid or Grind in seven private dungeons.</strong></a> Complete personal boss checklists for new rewards, with exclusive Raid drops. Available for live testing.</p>'
            assert marker in body
            if section not in body:body=body.replace(marker,marker+section)
        elif slug=='getting-started':
            body=body.replace('or hunt <a href="zones.html">zone rewards</a>.','hunt <a href="zones.html">zone rewards</a>, or choose a <a href="dungeon-modes.html">Raid or Grind dungeon run</a>.')
        article['body']=body;edits[relative]=article
    ledger=json.loads((args.wiki/'content-review.json').read_text(encoding='utf-8'))
    ledger['supplemental_evidence']=[v for v in ledger['supplemental_evidence'] if not v.startswith(('Dungeon candidate:','Dungeon deployment:'))]
    ledger['supplemental_evidence'].append('Dungeon deployment: verified production release 2026101601, all maintained articles and generated routes assessed in docs/dungeons/wiki-review.md. Live testing guide replaces unreleased notices; owner gameplay and website publication remain pending.')
    edits['content-review.json']=ledger
    preimages={};patch=[]
    for relative,obj in edits.items():
        old=(args.wiki/relative).read_bytes();preimages[relative]=hashlib.sha256(old).hexdigest()
        new=json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
        target=output/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(new,encoding='utf-8')
        patch.extend(difflib.unified_diff(old.decode('utf-8').splitlines(True),new.splitlines(True),fromfile='a/wiki/'+relative,tofile='b/wiki/'+relative))
    (output/'preimages.json').write_text(json.dumps(preimages,indent=2)+'\n')
    (output/'wiki.patch').write_text(''.join(patch),encoding='utf-8')
    shutil.copytree(args.wiki,args.preview,ignore=shutil.ignore_patterns('dist','__pycache__'),dirs_exist_ok=True)
    for relative in edits:shutil.copyfile(output/relative,args.preview/relative)
    print('Staged ten verified-deployment wiki updates; publication not performed.')

if __name__=='__main__':main()

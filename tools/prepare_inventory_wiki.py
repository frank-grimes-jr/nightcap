"""Reproduce current public wiki exactly, then change only Inventory guidance."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from inventory_release_support import ROOT,HERE,ART,save

PREVIOUS='20261112-earned-titles-v1'
RELEASE='20261112-inventory-combat-v1'
SOURCE=Path('E:/EQ_Local_Dev/_worktrees/earned-titles/artifacts/titles-wiki-20261112/wiki-source-v2')
CHANGED=['equipment','augment-audit','features','recent-changes']


def pins(folder):
    return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}


def update(article):
    name=article['slug'];body=article['body']
    assert 'id="inventory-combat-summary"' not in body
    if name=='equipment':
        body+='''\n<h2 id="inventory-combat-summary">Combat stats and heroic attributes in Inventory</h2>
<p>The main <strong>Inventory</strong> tab shows AC, MIT, AVD, ATK, DMG and HEAL above your attributes. MIT is the mitigation AC rating used by the server. AVD is the server defense rating used for the hit check, not the item Avoidance bonus or a percentage chance to dodge. <strong>Auto</strong> indicates an automatic-avoidance effect; sitting and other attack checks still apply. AC remains the conventional client display. ATK is your attack rating; DMG and HEAL are Spell Damage and Healing Amount bonuses, not damage or healing per cast.</p>
<p>Each attribute has a <strong>green current value</strong>, a <strong>white /cap</strong> and a <strong>yellow/gold signed heroic total</strong>. The cap is the actual server cap, including heroic allowance. Heroics are already included in the current value and cap: do not add the yellow number again. No heroic bonus displays as <strong>+0</strong>. Missing or stale server totals show <strong>--</strong> while refreshing.</p>
<p>Fully exit EverQuest and use normal launcher <strong>Play</strong> to install client update <strong>2026111202</strong>. The Inventory information column is wider to keep the normal font readable; scrolling remains available for smaller saved windows. The separate Stats tab retains equipped secondary bonuses, focus potential and the single Shield Block total. This release is in <strong>Live testing</strong>; player checks of placement, gear/buff refresh, zoning and skin reload remain open.</p>'''
    elif name=='augment-audit':
        body+='\n<p>The main <strong>Inventory</strong> tab now shows combat ratings, attribute caps and yellow/gold heroic totals. These heroic totals are already included in the green values. Use <strong>Stats</strong> for the secondary bonuses and focus details below. <a href="equipment.html#inventory-combat-summary">Reading the Inventory combat summary</a>.</p>'
    elif name=='features':
        body+='\n<p><a href="equipment.html#inventory-combat-summary">Inventory combat summary</a>: front-page combat ratings, actual attribute caps and yellow/gold heroic totals, with the normal font and the detailed Stats tab retained. Live testing.</p>'
    elif name=='recent-changes':
        body='<h2 id="inventory-combat-summary">November 12: Inventory combat stats, caps and heroics — Live testing</h2><p>Signed client <strong>2026111202</strong> with proxy <strong>0.13.6</strong> adds the combat summary and current/cap/heroic attributes to the main Inventory tab. MIT and AVD use the server combat ratings. Heroic mechanics and item balance are unchanged. Fully exit EQ and press launcher Play. Visible player acceptance remains open. <a href="equipment.html#inventory-combat-summary">Instructions</a>.</p>\n'+body
    article['body']=body;article['updated']=article['reviewed_at']='2026-11-12'
    article.setdefault('sources',[]).append('docs/releases/heroic-stats-inventory-20261112/: owner-authorized paired release; native visual/player acceptance open')
    return article


def main():
    baseline=json.loads((ART/'release-baseline.json').read_text())
    assert baseline['wiki_release']==PREVIOUS
    destination=ART/'wiki-source';assert not destination.exists()
    shutil.copytree(SOURCE,destination,ignore=shutil.ignore_patterns('dist','__pycache__'))
    wiki=destination/'wiki';sys.path.insert(0,str(wiki));import build
    before=pins(build.build());assert before==baseline['wiki_manifest'],'Current public source does not reproduce'
    reviewed=[]
    for path in sorted((wiki/'articles').glob('*.json')):
        article=json.loads(path.read_text(encoding='utf-8'))
        reviewed.append({'article':article['slug'],'status':article.get('status'),
            'assessment':'Inventory instructions/status/history updated' if article['slug'] in CHANGED else 'No change to guide, access, commands, gameplay or rewards'})
        if article['slug'] in CHANGED:
            article=update(article);raw=json.dumps(article,ensure_ascii=False,indent=2)+'\n'
            path.write_text(raw,encoding='utf-8',newline='\n')
            # Port only the same scoped fragment into current repository guides.
            target=ROOT/'wiki/articles'/path.name
            current=json.loads(target.read_text(encoding='utf-8'));current=update(current)
            target.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    run=subprocess.run([sys.executable,'-X','utf8','-B','-m','unittest','test_wiki','test_refresh'],cwd=wiki,capture_output=True,text=True,encoding='utf-8',timeout=240)
    (HERE/'wiki-tests.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8');assert run.returncode==0,run.stderr[-2000:]
    after=pins(build.build());assert set(after)==set(before)
    changed=sorted(p for p in before if before[p]!=after[p])
    assert set(changed)=={n+'.html' for n in CHANGED}|{'search-index.json'},changed
    build.package(wiki/'dist',ART/(RELEASE+'.tar.gz'))
    save(HERE/'wiki-candidate.json',{'status':'PREPARED_NOT_PUBLISHED','release':RELEASE,'previous_release':PREVIOUS,
        'public_source_reproduced':True,'files':len(after),'changed_existing':changed,'added':[],'removed':[],
        'preserved_files':len(before)-len(changed),'authored_articles_reviewed':len(reviewed),
        'native_visual_QA':'OPEN','publication':'pending'})
    save(HERE/'wiki-impact.json',{'reviewed':reviewed,'home':'Existing equipment path stays valid; no extra announcement',
        'commands':'No player command needed; existing detailed Stats and augstats remain',
        'catalogs':'No item/zone stats, acquisition, reward or balance changes',
        'release_labels':'Live testing after matched server/client publication; title preview remains Not released',
        'global_refresh':'Unrelated source drift remains review-required; no ledger advance'})
    print({'status':'PREPARED','files':len(after),'preserved':len(before)-len(changed),'changed':changed})


if __name__=='__main__':main()

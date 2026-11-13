"""Reproduce the current public wiki before the scoped live-testing delta."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/quick-buff-20261112'
ART=ROOT/'artifacts/quick-buff-20261112'
OLD=Path('E:/EQ_Local_Dev/_worktrees/augment-item-icons/artifacts/augment-icons-20261112')
RELEASE='20261112-quick-buff-v1'
NOTES={
 'combat':'<h2 id="quick-buff-hotkey">Quick Buff hotkey</h2><p>Quick Buff is an activated AA. Memorize the buff spells you want, select Quick Buff in the AA window, and choose <strong>Make Hotkey</strong>. Press it to cast eligible memorized buffs immediately on yourself for <strong>50% of maximum mana</strong> once per use, with <strong>no reuse delay</strong>. You must have the full mana cost available. Group and pet buffs retain normal delivery; direct heals and attacks are skipped. Normal spell ownership, level, instruments/reagents, range and stacking apply. A completion failure does not refund the activation cost. All three existing earned ranks use the same action, replacing passive buff casting-speed reduction. Fully exit EverQuest and use launcher Play for the paired hotkey text. Released for live testing; gameplay and balance acceptance remain open.</p>',
 'multiclass':'<h2 id="quick-buff-hotkey">Quick Buff</h2><p>All existing earned Quick Buff ranks now activate the same instant memorized-buff hotkey. It costs 50% of maximum mana once per use and has no reuse delay. Held-class spell access and current-level requirements remain; primary and secondary Bard songs retain native instrument requirements without starting a new pulse or melody. <a href="combat.html#quick-buff-hotkey">Make the hotkey and use it</a>. Gameplay and balance checks remain in live testing.</p>',
 'unreleased':'<h2 id="quick-buff-hotkey">Quick Buff hotkey — live testing</h2><p>The activated Quick Buff hotkey is deployed for testing: immediate eligible memorized buffs, 50% maximum mana once, no reuse delay and normal group/pet delivery. Fully exit EverQuest and use launcher Play. <a href="combat.html#quick-buff-hotkey">Instructions and limits</a>. Player and balance acceptance remain open.</p>',
 'recent-changes':'<h2 id="quick-buff-20261112">November 12: Quick Buff hotkey — live testing</h2><p>Quick Buff replaces passive buff haste with an activated hotkey that immediately casts eligible memorized buffs for 50% maximum mana with no reuse delay. Earned ranks, spell access, reagents and normal group/pet delivery remain. Full game exit and launcher Play install the paired text. <a href="combat.html#quick-buff-hotkey">Hotkey instructions</a>. Native gameplay and balance acceptance remain open.</p>',
 'features':'<h3 id="quick-buff-preview">Quick Buff hotkey</h3><p>Instantly cast your memorized buffs for 50% maximum mana with no reuse delay. <a href="combat.html#quick-buff-hotkey">Quick Buff instructions</a>. Released for live testing.</p>'}
def files(folder):return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
if __name__=='__main__':
    dest=ART/'wiki-source';shutil.copytree(OLD/'wiki-source',dest)
    wiki=dest/'wiki';sys.path.insert(0,str(wiki));import build
    out=build.build();baseline=json.loads((OLD/'20261112-augment-icons-v1.tar.json').read_text(encoding='utf-8'))
    assert files(out)==baseline,'Current public source not reproduced'
    for name,note in NOTES.items():
        for directory in (wiki,ROOT/'wiki'):
            p=directory/'articles'/(name+'.json');d=json.loads(p.read_text(encoding='utf-8'))
            body=d['body'];body=re.sub(r'<h[23] id="quick-buff-(?:hotkey|preview|20261112)">.*?(?=<h[23] |\Z)','',body,flags=re.S)
            if name=='features':body=body.replace('<h2 id="custom-world">',note+'\n<h2 id="custom-world">',1)
            elif name=='recent-changes':body=note+'\n'+body
            else:body=body.rstrip()+'\n'+note
            d['body']=body;d['updated']=d['reviewed_at']='2026-11-12'
            d['sources']=[s for s in d['sources'] if 'quick-buff-20261112/' not in s]+['docs/releases/quick-buff-20261112/README.md; owner-authorized live testing; acceptance open']
            p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    out=build.build();current=files(out);changed=sorted(n for n in current if current[n]!=baseline[n])
    assert set(current)==set(baseline) and set(changed)=={n+'.html' for n in NOTES}|{'search-index.json'}
    build.package(out,ART/(RELEASE+'.tar.gz'))
    report=dict(result='prepared_not_published',baseline_release='20261112-augment-icons-v1',release=RELEASE,
        files=len(current),changed_existing=changed,preserved_files=len(current)-len(changed),public_source_reproduced=True,
        whole_wiki_review='All42authored sources, Home, commands, catalogs and generated item/zone impacts assessed; only five owning/status/history guides plus search change')
    (OUT/'wiki-candidate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

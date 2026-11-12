"""Reproduce the current public wiki before the scoped live-testing delta."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/quick-buff-20261112/hotkey-fix'
ART=ROOT/'artifacts/quick-buff-20261112'
OLD=ART
RELEASE='20261112-quick-buff-v2'
NOTES={
 'combat':'<h3 id="quick-buff-hotkey-ready">Creating the hotkey</h3><p>Relog after the hotkey availability fix, select your earned Quick Buff rank in the AA window and choose <strong>Make Hotkey</strong>. Generic AA details may show one second, but Quick Buff has no reuse delay and the hotkey is immediately ready after use. Each use still requires and costs 50% of maximum mana.</p>',
 'recent-changes':'<h2 id="quick-buff-hotkey-fix-20261112">November 12: Quick Buff hotkey creation fixed — live testing</h2><p>Fixed the disabled Make Hotkey button for players who own Quick Buff. Relog to refresh the AA window, then create the hotkey. No additional client download is needed. Instant memorized buffs, 50% maximum-mana cost and no reuse delay remain. Generic AA details may show one second while the hotkey remains immediately ready. <a href="combat.html#quick-buff-hotkey-ready">Hotkey instructions</a>. Visible gameplay and balance acceptance remain open.</p>'}

def files(folder):return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
if __name__=='__main__':
    dest=ART/'wiki-source-v2';shutil.copytree(OLD/'wiki-source',dest)
    wiki=dest/'wiki';shutil.copyfile(ROOT/'wiki/test_wiki.py',wiki/'test_wiki.py');sys.path.insert(0,str(wiki));import build
    out=build.build();baseline=json.loads((OLD/'20261112-quick-buff-v1.tar.json').read_text(encoding='utf-8'))
    assert files(out)==baseline,'Current public source not reproduced'
    for name,note in NOTES.items():
        for directory in (wiki,ROOT/'wiki'):
            p=directory/'articles'/(name+'.json');d=json.loads(p.read_text(encoding='utf-8'))
            body=d['body'];assert 'quick-buff-hotkey-fix-20261112' not in body and 'quick-buff-hotkey-ready' not in body
            if name=='features':body=body.replace('<h2 id="custom-world">',note+'\n<h2 id="custom-world">',1)
            elif name=='recent-changes':body=note+'\n'+body
            else:body=body.rstrip()+'\n'+note
            d['body']=body;d['updated']=d['reviewed_at']='2026-11-12'
            d['sources']=[s for s in d['sources'] if 'quick-buff-20261112/' not in s]+['docs/releases/quick-buff-20261112/README.md; owner-authorized live testing; acceptance open']
            p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    out=build.build();current=files(out);changed=sorted(n for n in current if current[n]!=baseline[n])
    assert set(current)==set(baseline) and set(changed)=={n+'.html' for n in NOTES}|{'search-index.json'}
    build.package(out,ART/(RELEASE+'.tar.gz'))
    report=dict(result='prepared_not_published',baseline_release='20261112-quick-buff-v1',release=RELEASE,
        files=len(current),changed_existing=changed,preserved_files=len(current)-len(changed),public_source_reproduced=True,
        whole_wiki_review='All42authored sources, Home, commands, catalogs and generated item/zone impacts assessed; only Combat instructions, Change Log and search change')
    (OUT/'wiki-candidate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

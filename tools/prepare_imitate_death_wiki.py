"""Reproduce current public output, then prepare the authorized live-testing note."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/imitate-death-20261112/deployment'
ART=ROOT/'artifacts/imitate-death-20261112'
OLD=Path('E:/EQ_Local_Dev/_worktrees/quick-buff-hotkey/artifacts/quick-buff-20261112')
RELEASE='20261112-imitate-death-v1'
NOTES={
 'combat':'<details class="guide-topic" id="imitate-death"><summary>Imitate Death without cooldown</summary><div class="topic-body"><p>Earned Monk Imitate Death has no ability reuse delay. An old saved cooldown no longer blocks it. Relog, select Imitate Death in the AA window and choose <strong>Make Hotkey</strong>. The hotkey is immediately ready after use; generic AA details may show a nominal one second. Monk access, existing spell effects and normal standing/casting checks still apply. The basic Feign Death skill keeps its own reuse. No client update is required. Gameplay and balance acceptance remain in live testing.</p></div></details>',
 'recent-changes':'<h2 id="imitate-death">November 12: Imitate Death without cooldown — live testing</h2><p>Removed Imitate Death\'s ability cooldown and retired its old saved wait. Earned Monk access, existing effects and ordinary casting checks remain. Relog to refresh the AA window; no client update is required. <a href="combat.html#imitate-death">Hotkey instructions and limits</a>. Gameplay and balance acceptance remain open.</p>'}

def files(folder):
    return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}

if __name__=='__main__':
    ART.mkdir(exist_ok=True,parents=True)
    dest=ART/'wiki-source';shutil.copytree(OLD/'wiki-source-v2',dest)
    wiki=dest/'wiki';sys.path.insert(0,str(wiki));import build
    baseline=json.loads((OLD/'20261112-quick-buff-v2.tar.json').read_text(encoding='utf-8'))
    assert files(build.build())==baseline,'Current public wiki must reproduce exactly'
    for name,note in NOTES.items():
        for directory in (wiki,ROOT/'wiki'):
            path=directory/'articles'/(name+'.json');d=json.loads(path.read_text(encoding='utf-8'))
            body=d['body']
            body=re.sub(r'<details class="guide-topic" id="imitate-death-candidate">.*?</details>','',body,flags=re.S)
            body=re.sub(r'<h2 id="imitate-death-candidate">.*?</p>\s*','',body,flags=re.S)
            assert 'id="imitate-death"' not in body
            d['body']=note+'\n'+body if name=='recent-changes' else body.rstrip()+'\n'+note
            d['updated']=d['reviewed_at']='2026-11-12'
            d['sources']=[s for s in d['sources'] if 'imitate-death-20261112/' not in s]+['docs/releases/imitate-death-20261112/deployment/; owner-authorized live deployment; gameplay acceptance open']
            path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    out=build.build();current=files(out)
    changed=sorted(n for n in current if current[n]!=baseline[n])
    assert set(current)==set(baseline) and set(changed)=={'combat.html','recent-changes.html','search-index.json'}
    build.package(out,ART/(RELEASE+'.tar.gz'))
    report=dict(result='prepared_not_published',baseline_release='20261112-quick-buff-v2',release=RELEASE,
                files=len(current),changed_existing=changed,preserved_files=len(current)-len(changed),public_source_reproduced=True,
                whole_wiki_review='All 42 authored sources and generated item/zone/catalog/Home/Features/commands impacts reviewed; only Combat, Change Log and search change. Live-testing labels preserved; owner QA open.')
    (OUT/'wiki-candidate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

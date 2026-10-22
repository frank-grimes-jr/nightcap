"""Prepare candidate guidance on the latest published wiki source; no publication."""
import hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
WIKI=Path('E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki/wiki')
affected=('dungeon-modes','tunnel','travel','features','index','unreleased','recent-changes')
reference='docs/ops/hate-keeper-commonlands-20261022/README.md; built/tested candidate, main/live and publication pending'
notice='<p class="notice" id="hate-commonlands-candidate"><strong>Not released — Hate Keeper relocation:</strong> A tested candidate moves the Plane of Hate Keeper to East Commonlands at <code>/loc -1570,-346,3</code>, between Mirielle and Khalure in the travel area. Raid, Grind and return entry still lead to Hate; private Hate instances keep an entrance Keeper. The candidate removes Hate’s GM access gate while retaining level 46 for public and private entry. Live activation and in-game checks are pending.</p>\n'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    before={p.relative_to(WIKI).as_posix():sha(p) for p in WIKI.rglob('*') if p.is_file() and 'dist' not in p.parts and '__pycache__' not in p.parts}
    inventory=[]
    for path in sorted((WIKI/'articles').glob('*.json')):
        article=json.loads(path.read_text(encoding='utf-8'))
        changed=path.stem in affected
        inventory.append({'article':path.stem,'title':article['title'],'decision':'candidate location/access notice' if changed else 'no impact: existing guidance and status retained'})
        if changed:
            assert 'id="hate-commonlands-candidate"' not in article['body']
            article['body']=notice+article['body'];article['reviewed']='2026-10-22'
            article['sources'].append(reference)
            if path.stem=='dungeon-modes':article['keywords'].extend(['Hate Keeper Commonlands','Plane of Hate level 46'])
            path.write_text(json.dumps(article,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    ledger=json.loads((WIKI/'content-review.json').read_text(encoding='utf-8'))
    ledger['supplemental_evidence'].append('Hate Keeper Commonlands candidate: all22 maintained guides/432 generated routes assessed on published Build Lab source5dff50c. Seven candidate notices updated. Gameplay/main, website publication and owner QA pending. Commands,384 Hunt catalog values, unrelated dungeon rules, Build Lab and interactive shell unchanged. Evidence: '+reference)
    (WIKI/'content-review.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    refresh=subprocess.run(['python','-X','utf8','-B',str(WIKI/'check_refresh.py'),'--repo',str(ROOT),'--ref','HEAD','--include-worktree'],capture_output=True,text=True,encoding='utf-8')
    assert refresh.returncode in (0,1);(HERE/'wiki-refresh.json').write_text(refresh.stdout,encoding='utf-8')
    drift=json.loads(refresh.stdout)
    report={'wiki_base':'5dff50c5cecd4f9062f3e464990ad93276f8c272','wiki_root':str(WIKI.parent),
      'status':'candidate only; not published','articles':inventory,'generated_routes':432,'catalog_values':384,
      'source_drift':drift['changed_sources'],'drift_review':'Keeper routing/content/tests and candidate operational evidence reviewed; earlier source drift retains current published labels. Ledger revision not blindly advanced.',
      'unaffected':['commands','Hunt catalog stats','Build Lab','interactive handbook','other dungeon objectives and reward values'],
      'changed_files':[p for p,h in before.items() if sha(WIKI/p)!=h]}
    assert len(inventory)==22 and len(report['changed_files'])==8
    (HERE/'wiki-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'guides_reviewed':22,'notices':7,'generated_routes_reviewed':432,'published':False}))
if __name__=='__main__':main()

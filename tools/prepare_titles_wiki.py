"""Reproduce the authenticated public source, then add only title-preview content."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT/'docs/titles/wiki-release'
ART = ROOT/'artifacts/titles-wiki-20261112'
OLD = Path('E:/EQ_Local_Dev/_worktrees/dot-no-initial-damage/artifacts/dot-no-initial-damage-20261112')
PREVIOUS = '20261112-dot-ticks-v2'
RELEASE = '20261112-earned-titles-v1'
GUIDES = ['index','features','commands','unreleased','recent-changes','dungeon-modes',
          'combat','multiclass','adventure-journal','tradeskills']


def files(folder):
    return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob('*') if p.is_file()}


def original(revision, slug):
    return json.loads(subprocess.check_output(['git','show',revision+':wiki/articles/'+slug+'.json'],
                                              cwd=ROOT,encoding='utf-8'))


def main():
    before = json.loads((HERE/'baseline.json').read_text(encoding='utf-8'))
    assert before['status']=='PASS' and before['release']==PREVIOUS
    baseline = before['manifest']
    assert baseline==json.loads((OLD/(PREVIOUS+'.tar.json')).read_text(encoding='utf-8'))
    destination = ART/'wiki-source-v2'
    if destination.exists():
        # Resume only an untouched baseline clone after a preparation guard stop.
        def inputs(folder):
            return {p:pin for p,pin in files(folder).items()
                    if 'dist' not in Path(p).parts and '__pycache__' not in Path(p).parts}
        assert inputs(destination)==inputs(OLD/'wiki-source-v2'), 'Prepared source changed; inspect instead of replaying'
    else:
        shutil.copytree(OLD/'wiki-source-v2',destination)
    wiki = destination/'wiki'
    sys.path.insert(0,str(wiki))
    import build
    assert files(build.build())==baseline, 'Authenticated current public source does not reproduce'
    (HERE/'source-reproduction.json').write_text(json.dumps(dict(status='PASS',release=PREVIOUS,
        files=len(baseline),source=str(OLD/'wiki-source-v2'),
        manifest_sha256=hashlib.sha256(json.dumps(baseline,sort_keys=True).encode()).hexdigest()),indent=2)+'\n',encoding='utf-8')

    for slug in GUIDES:
        print('Adding title context: '+slug,flush=True)
        base, added = original('423f9c3b',slug), original('caaaf784',slug)
        path = wiki/'articles'/(slug+'.json')
        published = json.loads(path.read_text(encoding='utf-8'))
        body = published['body']
        assert 'id="earned-titles' not in body, slug
        if slug=='features':
            start=added['body'].index('<section class="feature-row" id="earned-titles">')
            end=added['body'].index('</section>',start)+len('</section>')
            fragment=added['body'][start:end]
            assert added['body'][:start]+added['body'][end:]==base['body']
            anchor=base['body'][start:start+100]
            assert body.count(anchor)==1, (slug,'ambiguous insertion anchor')
            body=body.replace(anchor,fragment+anchor,1)
        else:
            assert added['body'].startswith(base['body']),slug
            fragment=added['body'][len(base['body']):]
            assert fragment.startswith('<') and 'titles.html' in fragment,slug
            if slug=='recent-changes':
                fragment=fragment.replace('gameplay activation, native client QA and public publication are pending.',
                    'earning these titles still requires server activation and native client QA. This guide is a preview.')
            body+=fragment
        published['body']=body
        published['updated']=published['reviewed_at']='2026-11-12'
        published['sources']=list(dict.fromkeys(published['sources']+[
            'docs/titles/wiki-release/: owner-authorized preview publication; title runtime remains disabled and player QA open']))
        path.write_text(json.dumps(published,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

    shutil.copyfile(ROOT/'wiki/articles/titles.json',wiki/'articles/titles.json')
    # Current tests add the fifteenth Features row; no public runtime/code changes.
    shutil.copyfile(ROOT/'wiki/test_wiki.py',wiki/'test_wiki.py')
    run = subprocess.run([sys.executable,'-X','utf8','-B','-m','unittest','test_wiki','test_refresh'],
                         cwd=wiki,capture_output=True,text=True,encoding='utf-8',timeout=240)
    (HERE/'release-tests.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
    assert run.returncode==0,run.stderr[-3000:]
    current = files(build.build())
    added = sorted(set(current)-set(baseline))
    removed = sorted(set(baseline)-set(current))
    changed = sorted(p for p in baseline if p in current and current[p]!=baseline[p])
    expected = {slug+'.html' for slug in GUIDES}|{'all-pages.html','sitemap.xml','search-index.json'}
    assert added==['titles.html'] and not removed
    assert set(changed)==expected,changed
    assert all(current[p]==baseline[p] for p in baseline if p not in expected)
    build.package(wiki/'dist',ART/(RELEASE+'.tar.gz'))
    report = dict(status='PREPARED',release=RELEASE,previous_release=PREVIOUS,
        public_source_reproduced=True,files=len(current),added=added,removed=removed,
        changed_existing=changed,preserved_files=len(baseline)-len(changed),
        authoring_articles_reviewed=len(list((wiki/'articles').glob('*.json'))),
        player_status='Titles Not released; server not activated; native player QA OPEN',
        whole_wiki_review='New titles directory plus owning guides/navigation/history. Unrelated guides, all existing item/zone values, acquisitions, catalog, client and service behavior preserved. No source-ledger advance.')
    (HERE/'candidate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()

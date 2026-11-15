"""Reproduce the published Titles site and stage the automatic/suffix guide delta."""
import html
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=ROOT/'artifacts/titles-live-20261114/wiki'
ART=ROOT/'artifacts/titles-live-20261114/automatic/wiki'
PREVIOUS='20261114-titles-active-v1'
RELEASE='20261114-titles-automatic-suffix-v1'


def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')


def transform(article):
    slug=article['slug'];body=article['body'];before=body
    if slug=='commands':
        body=body.replace('The command also checks your existing dungeon, story and skill progress.',
            'Titles unlock automatically. This command is an optional progress list.')
    elif slug=='features':
        old='Select cosmetic titles for kills, dungeon completion and skill mastery.'
        body=body.replace(old,old+' Matching prefixes and suffixes unlock automatically, with a notification.')
    elif slug in ['combat','dungeon-modes','multiclass','tradeskills']:
        start=body.index('<h2 id="earned-titles">');end=body.find('<h2 ',start+1)
        if end<0:end=len(body)
        block=body[start:end]
        sentence={
            'combat':'Qualifying kills unlock titles automatically, with a chat message and a new-title alert.',
            'dungeon-modes':'Completion titles unlock automatically after your personal full clear is recorded.',
            'multiclass':'Mastery titles unlock automatically when your saved skill reaches its legal cap.',
            'tradeskills':'Mastery titles unlock automatically and include matching prefix and suffix choices.'}[slug]
        assert block.count('</p>')==1
        body=body[:start]+block.replace('</p>',' '+sentence+'</p>')+body[end:]
    elif slug=='adventure-journal':
        old='Recorded completion qualifies when you open the Titles window or use #titles.'
        assert body.count(old)==1
        body=body.replace(old,'Finishing the final chapter unlocks it automatically, with a notification.')
    if body!=before:
        article['body']=body;article['reviewed_at']=article['updated']='2026-11-14'
        article['sources']=list(dict.fromkeys(article['sources']+['docs/titles/automatic-suffix-20261114/: automatic milestones and paired title placements']))
    return body!=before


def main():
    sys.path.insert(0,str(ROOT/'tools'))
    import prepare_titles_wiki as helpers
    baseline=json.loads((BASE/(PREVIOUS+'.tar.json')).read_bytes())
    ART.mkdir(parents=True,exist_ok=True)
    dest=ART/'wiki-source';assert not dest.exists(),'Inspect prior candidate instead of overwriting it'
    shutil.copytree(BASE/'wiki-source',dest,ignore=shutil.ignore_patterns('dist','__pycache__'))
    site=dest/'wiki';cmd=[sys.executable,'-B','-X','utf8']
    subprocess.run(cmd+['build.py'],cwd=site,check=True)
    assert helpers.files(site/'dist')==baseline
    (site/'articles/titles.json').write_bytes((ROOT/'wiki/articles/titles.json').read_bytes())
    for name in ['commands','features','combat','dungeon-modes','multiclass','tradeskills','adventure-journal']:
        path=site/'articles'/(name+'.json');article=json.loads(path.read_bytes())
        assert transform(article),name
        save(path,article)
    path=site/'articles/recent-changes.json';article=json.loads(path.read_bytes())
    article['body']='<h2 id="titles-automatic-suffix">November 14: automatic titles and matching suffixes</h2><p>Titles now unlock automatically when earned, with a chat message and a new-title alert. Every prefix also unlocks a matching suffix through the same achievement. Existing awards gain their matching suffix without another grind. Login and zoning automatically check recorded goals. <code>#titles</code> remains an optional progress list. <a href="titles.html">Title names and requirements</a>.</p>'+article['body']
    article['updated']=article['reviewed_at']='2026-11-14';save(path,article)
    subprocess.run(cmd+['-m','unittest','test_wiki','test_refresh','test_public_language','test_loot_model','test_loot_refresh'],cwd=site,check=True)
    archive=ART/(RELEASE+'.tar.gz')
    subprocess.run(cmd+['build.py','--package',str(archive)],cwd=site,check=True)
    after=helpers.files(site/'dist');assert set(after)==set(baseline)
    changed=sorted(n for n in baseline if baseline[n]!=after[n])
    expected={n+'.html' for n in ['titles','commands','features','combat','dungeon-modes','multiclass','tradeskills','adventure-journal','recent-changes']}|{'search-index.json'}
    assert set(changed)==expected,changed
    gen_spec=importlib.util.spec_from_file_location('automatic_title_catalog',ROOT/'tools/earned_titles.py')
    gen=importlib.util.module_from_spec(gen_spec);gen_spec.loader.exec_module(gen)
    page=(site/'dist/titles.html').read_text(encoding='utf8')
    for title in gen.catalog()[0]:
        assert page.count('<tr><td>'+html.escape(title['name'])+'</td>')==1
        assert '<td>'+html.escape(gen.suffix_name(title))+'</td>' in page
    for test in ['test_search.cjs','test_equipment.cjs','test_loot_finder.cjs','test_experience.cjs']:
        subprocess.run(['node',test],cwd=site,check=True)
    from hashlib import sha256
    sha=lambda p:sha256(p.read_bytes()).hexdigest()
    save(HERE/'wiki-candidate.json',dict(result='PASS',release=RELEASE,predecessor=PREVIOUS,
        exact_predecessor_reproduced=True,files=len(after),changed=changed,retained=len(after)-len(changed),
        package_sha256=sha(archive),manifest_sha256=sha(archive.with_suffix('.json')),
        previous_manifest_sha256=sha(BASE/(PREVIOUS+'.tar.json')),achievements=77,prefixes=76,suffixes=77))


if __name__=='__main__':main()

"""Reproduce the current public site and stage only title activation guidance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ART=ROOT/'artifacts/titles-live-20261114/wiki'
BASE=ROOT.parent/'thj-bow-live/artifacts/thj-combat-wiki'
PREVIOUS='20261113-archery-backstab-v2'
RELEASE='20261114-titles-active-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def save(path,obj):path.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
def files(folder):return {p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}


def activate(article):
    """Change only title-specific wording, retaining unrelated candidate labels."""
    b=article['body'];old=b
    if article['slug']=='index':
        b=b.replace('celebrate dragon victories, Classic completion and skill mastery. <strong>Not released.</strong>',
                    'celebrate dragon victories, Classic completion and skill mastery. <strong>Available.</strong>')
    elif article['slug']=='features':
        needle='Slayer ranks, dragon victories, Classic Raid completion and skill mastery become permanent cosmetic choices. <strong>Not released.</strong>'
        b=b.replace(needle,needle.replace('Not released.','Available.'))
    elif article['slug']=='unreleased':
        b=b.replace('Implemented candidate; tracking, unlocks and command are not enabled on the live server.',
                    'Tracking, unlocks and the command are active. See the Titles guide.')
    elif article['slug']=='commands':
        b=b.replace('Earned titles (Not released)','Earned titles').replace('The planned <code>#titles','The <code>#titles')
        b=b.replace('This command is unavailable until activation.','The command also checks your existing dungeon, story and skill progress.')
    elif article['slug'] in ['dungeon-modes','combat','multiclass','adventure-journal','tradeskills']:
        # The owning fragment is last in authored source, with a stable anchor.
        start=b.index('<h2 id="earned-titles">');end=b.find('<h2 ',start+1)
        if end<0:end=len(b)
        fragment=b[start:end].replace(' (Not released)','').replace('The planned ','The ').replace('Planned ','')
        fragment=fragment.replace('New general kill totals begin when tracking is activated.',
            'New general kill totals count qualifying kills from activation on November 14, 2026.')
        fragment=fragment.replace('Recorded completion can qualify when titles are activated; no new campaign reward is currently available.',
            'Recorded completion qualifies when you open the Titles window or use #titles.')
        fragment=fragment.replace('This candidate does not change current dungeon rewards.','These cosmetic titles add no combat bonuses.')
        b=b[:start]+fragment+b[end:]
    if b!=old:
        article['body']=b;article['updated']=article['reviewed_at']='2026-11-14'
        article['sources'].append('docs/titles/deployment-20261114/: title activation evidence; native player QA remains open')
    return b!=old


def main():
    ART.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((ROOT/'artifacts/titles-live-20261114/wiki-before.json').read_bytes())
    manifest=json.loads((BASE/(PREVIOUS+'.tar.json')).read_bytes())
    assert baseline['release']==PREVIOUS and baseline['manifest']==manifest
    dest=ART/'wiki-source'
    assert not dest.exists(),'Existing candidate: inspect rather than overwrite'
    shutil.copytree(BASE/'wiki-source',dest,ignore=shutil.ignore_patterns('dist','__pycache__'))
    site=dest/'wiki';python=[sys.executable,'-B','-X','utf8']
    subprocess.run(python+['build.py'],cwd=site,check=True)
    assert files(site/'dist')==manifest,'Current public source does not reproduce'
    spec=importlib.util.spec_from_file_location('title_catalog',ROOT/'tools/earned_titles.py')
    gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
    title=gen.outputs()['wiki/articles/titles.json']
    (site/'articles/titles.json').write_text(title,encoding='utf8',newline='\n')
    for name in ['index','features','commands','unreleased','dungeon-modes','combat','multiclass','adventure-journal','tradeskills']:
        path=site/'articles'/(name+'.json');article=json.loads(path.read_bytes())
        if activate(article):save(path,article)
    path=site/'articles/recent-changes.json';article=json.loads(path.read_bytes())
    article['body']='<h2 id="titles-active">November 14: earned titles available</h2><p>The <a href="titles.html">77 cosmetic titles</a> and <code>#titles</code> are available. Open the Titles window to check existing completion and skill goals. New slayer totals start now. Nagafen earns Flamebreaker; defeating both Nagafen and Vox earns Dragonslayer. Newly earned titles notify you and never replace your selected title.</p>'+article['body']
    article['updated']=article['reviewed_at']='2026-11-14';save(path,article)
    subprocess.run(python+['-m','unittest','test_wiki','test_refresh','test_public_language','test_loot_model','test_loot_refresh'],cwd=site,check=True)
    archive=ART/(RELEASE+'.tar.gz')
    subprocess.run(python+['build.py','--package',str(archive)],cwd=site,check=True)
    after=files(site/'dist');assert after.keys()==manifest.keys()
    changed=sorted(n for n in manifest if manifest[n]!=after[n])
    assert set(changed)=={'titles.html','commands.html','combat.html','adventure-journal.html','recent-changes.html','search-index.json'},changed
    for test in ['test_search.cjs','test_equipment.cjs','test_loot_finder.cjs','test_experience.cjs']:
        subprocess.run(['node',test],cwd=site,check=True)
    save(HERE/'wiki-candidate.json',dict(release=RELEASE,predecessor=PREVIOUS,exact_predecessor_reproduced=True,
        changed=changed,files=len(after),retained=len(after)-len(changed),package_sha256=sha(archive),
        manifest_sha256=sha(archive.with_suffix('.json')),previous_manifest_sha256=sha(BASE/(PREVIOUS+'.tar.json'))))


if __name__=='__main__':main()

"""Prepare the scoped wiki release on the matching published Inventory source."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ART=ROOT/'artifacts/classic-raid-augments-20261112-v1'
PREVIOUS='20261112-inventory-combat-v1'
RELEASE='20261112-raid-augments-v1'
ORIGIN=Path('E:/EQ_Local_Dev/_worktrees/heroic-stats-inventory/artifacts/heroic-stats')

def pins(folder):
    return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}

def main():
    destination=ART/'wiki-source'
    assert not destination.exists()
    baseline=json.loads((ORIGIN/(PREVIOUS+'.tar.json')).read_bytes())
    shutil.copytree(ORIGIN/'wiki-source',destination,ignore=shutil.ignore_patterns('dist','__pycache__'))
    wiki=destination/'wiki'
    sys.path.insert(0,str(wiki))
    import build
    assert pins(build.build())==baseline
    shutil.copyfile(ROOT/'wiki/raid_augment_catalog.py',wiki/'raid_augment_catalog.py')
    (destination/'config').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'config/classic-raid-augments.json',destination/'config/classic-raid-augments.json')
    guide=ROOT/'wiki/articles/classic-raid-augments.json'
    shutil.copyfile(guide,wiki/'articles'/guide.name)
    catalog=wiki/'catalog.py'
    src=catalog.read_text(encoding='utf8')
    assert src.count('    return articles\n')==1
    catalog.write_text(src.replace('    return articles\n','    from raid_augment_catalog import add_raid_rewards\n    return add_raid_rewards(articles)\n'),encoding='utf8',newline='\n')
    for slug in ('features','augment-audit','equipment','recent-changes'):
        path=wiki/'articles'/(slug+'.json')
        article=json.loads(path.read_bytes())
        assert 'classic-raid-augments.html' not in article['body']
        new=json.loads((ROOT/'wiki/articles'/(slug+'.json')).read_bytes())
        link_pos=new['body'].index('href="classic-raid-augments.html"')
        start=new['body'].rindex('<p>',0,link_pos)
        end=new['body'].index('</p>',link_pos)+4
        if slug=='recent-changes':
            start=new['body'].rindex('<h2',0,start)
            article['body']=new['body'][start:end]+article['body']
        else:
            article['body']+=new['body'][start:end]
        article['updated']=article['reviewed_at']='2026-11-12'
        article['sources'].append('config/classic-raid-augments.json')
        path.write_text(json.dumps(article,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    # A new process loads the new catalog module.
    subprocess.run([sys.executable,'-B','-X','utf8',str(wiki/'build.py'),'--package',str(ART/(RELEASE+'.tar.gz'))],cwd=wiki,check=True)
    after=pins(wiki/'dist')
    added=set(after)-set(baseline);removed=set(baseline)-set(after)
    assert added=={'classic-raid-augments.html',*(f'item-{i}.html' for i in range(963200,963216))} and not removed
    changed=sorted(n for n in baseline if baseline[n]!=after[n])
    allowed={'all-pages.html','index.html','items.html','search-index.json','sitemap.xml','features.html','augment-audit.html','equipment.html','recent-changes.html',
        *('zone-'+z+'.html' for z in ('permafrost','soldungb','kedge','hole','fearplane','hateplane','hateplaneb','airplane'))}
    assert set(changed)<=allowed and all('item-'+str(i)+'.html' in (wiki/'dist/classic-raid-augments.html').read_text(encoding='utf8') for i in range(963200,963216)),changed
    result=dict(release=RELEASE,previous=PREVIOUS,files=len(after),preserved=len(baseline)-len(changed),changed=changed,added=sorted(added),removed=sorted(removed))
    (HERE/'wiki-candidate.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(result)
if __name__=='__main__':main()

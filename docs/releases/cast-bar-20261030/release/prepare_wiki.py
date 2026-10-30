"""Append approved notes to the authenticated current public wiki package."""
import hashlib,io,json,re,sys,tarfile
from pathlib import Path
from capture import HERE,ROOT,PRIVATE
sys.path.insert(0,str(ROOT/'wiki'))
import build

SOURCE=Path('E:/EQ_Local_Dev/_worktrees/public-cazic-classic')
RELEASE='20261030-cast-bar-v1'
PREVIOUS='20261030-public-cazic-v1'

def render(a):
    headings=[(m[0] or m[2],m[1] or m[3]) for m in re.findall(r'<h2 id="([^"]+)">(.+?)</h2>|<details class="guide-topic" id="([^"]+)"><summary>(.+?)</summary>',a['body'])]
    toc='<nav class="contents" aria-label="On this page"><strong>On this page</strong><ol>'+''.join(f'<li><a href="#{id}">{title}</a></li>' for id,title in headings[:6])+'</ol>'+('<details><summary>More topics</summary><ol>'+''.join(f'<li><a href="#{id}">{title}</a></li>' for id,title in headings[6:])+'</ol></details>' if len(headings)>6 else '')+'</nav>' if len(headings)>1 else ''
    if a['slug'] in ['features','recent-changes']:toc=''
    return build.render(a['title'],a['summary'],a['body'],a['slug'],a['category'],a['status'],a['updated'],toc)

def main():
    out=PRIVATE/'wiki'
    assert not out.exists(),'Prepared package exists; inspect it instead of replaying'
    baseline=json.loads((HERE/'baseline.json').read_bytes())
    assert baseline['wiki_release']==PREVIOUS
    before=baseline['wiki_manifest']
    archive=SOURCE/'work/public-ct-wiki'/f'{PREVIOUS}.tar.gz'
    with tarfile.open(archive,'r:gz') as tar:
        files={m.name:tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
    assert len(files)==499 and {n:hashlib.sha256(b).hexdigest() for n,b in files.items()}==before
    additions={
      'launcher':'<h2 id="cast-bar-repair">Spell casting bar timing</h2><p>Client update <strong>2026103002</strong> corrects spell bars that stayed full until the final instant, including level-1 Wizard nukes. Fully exit EverQuest and press Play in the normal launcher to update. Server cast times, instant DoTs and existing Bard timing are unchanged. Visible casting and interruption checks remain under live testing.</p>',
      'recent-changes':'<h2 id="cast-bar-repair-20261030">October 30: spell casting bar timing — live testing</h2><p>Client update <strong>2026103002</strong> corrects casting bars that stayed full until the final instant. Fully exit EverQuest and use launcher Play before testing. Normal server cast times, instant DoTs and Bard timing are unchanged; the Ancient Attunement label repair remains included. Visible gameplay checks remain open. <a href="launcher.html#cast-bar-repair">Update instructions</a>.</p>'}
    search=json.loads(files['search-index.json'])
    for slug,note in additions.items():
        a=json.loads((SOURCE/'wiki/articles'/f'{slug}.json').read_bytes())
        html=files[slug+'.html'].decode('utf-8');newline='\r\n' if '\r\n' in html else '\n'
        assert render(a)==html.replace('\r\n','\n'),f'Published {slug} template/source mismatch'
        a['body']+='\n'+note+'\n';a['updated']='2026-10-30'
        a['sources'].append('docs/releases/cast-bar-20261030/README.md')
        (ROOT/'wiki/articles'/f'{slug}.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        files[slug+'.html']=render(a).replace('\n',newline).encode('utf-8')
        row=next(x for x in search if x['slug']==slug)
        row.update({k:a[k] for k in ['title','summary','category','status']})
        row.update(keywords=a.get('keywords',[]),text=re.sub(r'\s+',' ',build.plain(a['body'])))
    # The pending cast note was never public. Remove it from source, retaining
    # the current published Cazic/Hate candidates and every other release label.
    for slug in ['unreleased','travel','dungeon-modes','features']:
        source=(SOURCE/'wiki/articles'/f'{slug}.json').read_bytes()
        assert render(json.loads(source))==files[slug+'.html'].decode('utf-8').replace('\r\n','\n'),f'Published {slug} source mismatch'
        (ROOT/'wiki/articles'/f'{slug}.json').write_bytes(source)
    files['search-index.json']=json.dumps(search,ensure_ascii=False).encode('utf-8')
    manifest={n:hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())}
    changed={n for n in before if before[n]!=manifest[n]}
    assert changed=={'launcher.html','recent-changes.html','search-index.json'}
    out.mkdir(exist_ok=False)
    path=out/f'{RELEASE}.tar.gz'
    with tarfile.open(path,'x:gz',compresslevel=9) as tar:
        for name,data in sorted(files.items()):
            entry=tarfile.TarInfo(name);entry.size=len(data);entry.mode=0o644;tar.addfile(entry,io.BytesIO(data))
    path.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (HERE/'wiki-baseline.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
    (HERE/'baseline-state.json').write_text(json.dumps({'release':PREVIOUS,'config_sha256':baseline['config_sha256']},indent=2)+'\n',encoding='utf-8')
    report=dict(status='prepared_not_published',release=RELEASE,previous=PREVIOUS,files=499,changed=sorted(changed),preserved=496,archive_bytes=path.stat().st_size,expanded_bytes=sum(map(len,files.values())),package_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),reviewed_articles=[dict(slug=p.stem,source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),impact='release notes' if p.stem in additions else 'preserve current public behavior/labels') for p in sorted((SOURCE/'wiki/articles').glob('*.json'))],catalog_impact='No item, zone, command, reward, home or feature changes',owner_gameplay_acceptance='pending')
    (HERE/'wiki-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='reviewed_articles'}))

if __name__=='__main__':main()

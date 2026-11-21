"""Reproduce the current public wiki, then prepare only this release note."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BEFORE=Path('E:/EQ_Local_Dev/artifacts/classic-defense-coverage-20261121')
ART=Path('E:/EQ_Local_Dev/artifacts/aa-purchase-latency-20261121')
SITE=ART/'wiki'
RELEASE='20261121-aa-purchase-latency-v1'
PREVIOUS='20261121-classic-defense-v1'


def main():
    ART.mkdir(exist_ok=True)
    if not SITE.exists():
        shutil.copytree(BEFORE/'wiki',SITE,ignore=shutil.ignore_patterns('dist','__pycache__','*.tar.gz','*.tar.json'))
    for name in ('config','docs'):
        if not (ART/name).exists():shutil.copytree(BEFORE/name,ART/name)
    subprocess.run([sys.executable,'-B',str(SITE/'build.py')],check=True)
    previous=json.loads((BEFORE/(PREVIOUS+'.tar.json')).read_bytes())
    assert all(hashlib.sha256((SITE/'dist'/name).read_bytes()).hexdigest()==pin for name,pin in previous.items())
    path=SITE/'articles/recent-changes.json'
    article=json.loads(path.read_bytes())
    assert 'id="aa-purchase-latency"' not in article['body']
    article['body']=('<h2 id="aa-purchase-latency">November 21, 2026: AA purchase responsiveness</h2>'
        '<p>Reduced repeated window refreshes when purchasing AA ranks. Costs, earned ranks '
        'and cooldown deadlines are unchanged. Reconnect after server maintenance; no client '
        'download is needed. In-game confirmation of the reported freeze remains open. '
        'See <a href="multiclass.html">Multiclass &amp; progression</a>.</p>'+article['body'])
    article['updated']='2026-11-21'
    article['sources'].append('docs/releases/aa-purchase-latency-20261121/; deploy before publication, owner visible QA open')
    raw=(json.dumps(article,ensure_ascii=False,indent=2)+'\n').encode()
    path.write_bytes(raw)
    (ROOT/'wiki/articles/recent-changes.json').write_bytes(raw)
    pending=ROOT/'wiki/articles/unreleased.json'
    data=json.loads(pending.read_bytes())
    data['body'],count=re.subn(r'<h2 id="aa-purchase-latency">.*?</h2><p>.*?</p>\n?', '',data['body'],count=1)
    assert count==1
    data['sources']=[s for s in data['sources'] if 'aa-purchase-latency' not in s]
    pending.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    archive=ART/(RELEASE+'.tar.gz')
    subprocess.run([sys.executable,'-B',str(SITE/'build.py'),'--package',str(archive)],check=True)
    manifest=json.loads(archive.with_suffix('.json').read_bytes())
    changed=sorted(n for n,pin in manifest.items() if previous.get(n)!=pin)
    assert set(previous)==set(manifest) and changed==['recent-changes.html','search-index.json']
    result=dict(release=RELEASE,previous=PREVIOUS,files=len(manifest),changed=changed,
                preserved=len(manifest)-len(changed),published=False,
                review='All44authored pages plus Home/Features/commands and generated catalogs reviewed; no mechanics, acquisition, values, or guide steps change. Retain historical ledger drift.')
    (HERE/'wiki-candidate-release.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()

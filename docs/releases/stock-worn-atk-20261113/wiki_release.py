"""Apply the same stock ATK guidance to the repo and the reproduced official wiki."""
import csv
import hashlib
import html
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ART=ROOT/'artifacts/stock-worn-atk-prod'
PREVIOUS='20261112-raid-augments-v1'
RELEASE='20261113-stock-worn-atk-v1'
ORIGIN=Path('E:/EQ_Local_Dev/_worktrees/classic-raid-augments-production/artifacts/classic-raid-augments-20261112-v1')

def edit(wiki):
    families={}
    with (ROOT/'docs/items/stock-worn-atk/changes.csv').open(encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            entry=families.setdefault((row['name'],int(row['base_id'])),{'Normal':int(row['before_atk'])})
            assert entry['Normal']==int(row['before_atk'])
            entry[row['tier']]=int(row['after_atk'])
    assert len(families)==135
    table=''.join('<tr><td>'+html.escape(n) + (f' (base ID {i})' if sum(other==n for other,_ in families)>1 else '')+'</td>'+''.join(f'<td>{v[k]}</td>' for k in ('Normal','Polished','Exalted','Ascended'))+'</tr>' for (n,i),v in sorted(families.items()))
    contribution=('<h2 id="stock-worn-atk">Worn ATK on stock gear</h2><p>The 135 families below gain ATK as they improve in quality. The item window shows its full value. If your character is below an item’s recommended level, the server reduces its contribution before adding it to your worn ATK. The base worn cap is 250. Applicable item, spell and AA bonuses can raise the cap.</p>'
        '<p>For example, an Ascended Armguard of Shadows lists 53 ATK. It contributes up to 44 at level 50 and 53 at its recommended level of 60. If your other gear already reaches the cap, equipping more worn ATK adds zero. The Inventory ATK rating also includes skills, STR and other bonuses.</p>'
        '<details><summary>Compare all 135 families by quality</summary><div class="table-scroll"><table><thead><tr><th>Equipment</th><th>Normal</th><th>Polished</th><th>Exalted</th><th>Ascended</th></tr></thead><tbody>'+table+'</tbody></table></div></details>')
    blocks={'equipment':contribution,'recent-changes':'<h2 id="stock-worn-atk">November 13 · Stock equipment ATK</h2><p>Polished, Exalted and Ascended versions of 135 stock families now use updated worn ATK. <a href="equipment.html#stock-worn-atk">See all item values and how the cap works</a>.</p>'}
    for slug,block in blocks.items():
        file=wiki/'articles'/(slug+'.json');d=json.loads(file.read_bytes())
        assert 'id="stock-worn-atk"' not in d['body']
        d['body']=block+d['body'] if slug=='recent-changes' else d['body']+block
        d['sources'].append('docs/items/stock-worn-atk/changes.csv')
        d['reviewed_at']=d['updated']='2026-11-13'
        file.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
    file=wiki/'articles/unreleased.json';d=json.loads(file.read_bytes())
    marker='<h2 id="stock-worn-atk">'
    if marker in d['body']:
        a,b=d['body'].split(marker);assert b.count('</p>')==1 and b.endswith('</p>')
        d['body']=a;d['sources']=[s for s in d['sources'] if s!='docs/items/stock-worn-atk/README.md']
        file.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())

def pins(folder):return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}

def main():
    dest=ART/'wiki-source'
    if not dest.exists():shutil.copytree(ORIGIN/'wiki-source',dest,ignore=shutil.ignore_patterns('dist','__pycache__'))
    previous=json.loads((ORIGIN/(PREVIOUS+'.tar.json')).read_bytes())
    wiki=dest/'wiki'
    def build(*args):subprocess.run([sys.executable,'-B','-X','utf8',str(wiki/'build.py'),*args],cwd=wiki,check=True)
    build();assert pins(wiki/'dist')==previous
    edit(wiki)
    subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','test_wiki','test_refresh'],cwd=wiki,check=True)
    build('--package',str(ART/(RELEASE+'.tar.gz')))
    after=pins(wiki/'dist')
    assert set(after)==set(previous)
    changes=sorted(p for p in after if after[p]!=previous[p])
    assert set(changes)=={'equipment.html','recent-changes.html','search-index.json'}
    text=(wiki/'dist/equipment.html').read_text(encoding='utf8');assert text.count('Compare all 135')==1 and 'Armguard of Shadows</td><td>50</td><td>51</td><td>52</td><td>53</td>' in text
    edit(ROOT/'wiki')
    data=dict(release=RELEASE,previous=PREVIOUS,files=len(after),preserved=len(after)-len(changes),changed=changes,exact_base_reproduced=True,table_families=135)
    (HERE/'wiki-candidate.json').write_bytes((json.dumps(data,indent=2)+'\n').encode())
    print(data)
if __name__=='__main__':main()

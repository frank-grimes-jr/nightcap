"""Check the prepared real title article, catalog, links and browser search code."""
import html
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'docs/titles/wiki-release'
ART=ROOT/'artifacts/titles-wiki-20261112'
WIKI=ART/'wiki-source-v2/wiki'


def main():
    spec=importlib.util.spec_from_file_location('title_catalog',ROOT/'tools/earned_titles.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    titles,_=module.catalog()
    article=json.loads((WIKI/'articles/titles.json').read_text(encoding='utf-8'))
    expected=json.loads(module.outputs()['wiki/articles/titles.json'])
    assert article==expected and article['status']=='Not released'
    page=(WIKI/'dist/titles.html').read_text(encoding='utf-8')
    assert len(re.findall(r'<tr><td>',page))==len(titles)==77
    for title in titles:
        assert page.count('<td>'+html.escape(title['name'])+'</td>')==1,title['name']
        assert html.escape(title['description']) in page,title['name']
    for name in ['index','features','commands','unreleased','dungeon-modes','combat','multiclass','adventure-journal','tradeskills','all-pages']:
        assert 'href="titles.html' in (WIKI/'dist'/(name+'.html')).read_text(encoding='utf-8'),name
    code=(WIKI/'test_search.cjs').read_text(encoding='utf-8')
    code=code.replace('__dirname',json.dumps(str(WIKI)))
    code=code.replace("  let result = await search('#zoneforge');",'''  for (const query of ['Titles','#titles','Dragonslayer']) {
    const found = await search(query);
    assert.equal(found.results[0].children[0].href,'titles.html',query);
    assert.match(found.results[0].children[1].textContent,/Not released/);
  }
  let result = await search('#zoneforge');''')
    script=ART/'title-search-check.cjs';script.write_text(code,encoding='utf-8')
    checks=[]
    for target in [script,WIKI/'test_equipment.cjs',WIKI/'test_experience.cjs']:
        run=subprocess.run(['node',str(target)],capture_output=True,text=True,encoding='utf-8')
        assert run.returncode==0,run.stderr
        checks.append({'test':target.name,'output':run.stdout.strip()})
    report=dict(status='PASS',exact_titles=77,generated_article_matches=True,
        all_titles_have_exact_requirements=True,title_context_links=True,
        top_title_search_queries=['Titles','#titles','Dragonslayer'],node_checks=checks)
    (HERE/'content-checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS:77 exact title requirements, preview labels, guide links, title search and existing search/equipment/experience checks')


if __name__=='__main__':
    main()

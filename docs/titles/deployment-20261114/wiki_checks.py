"""Check the staged real title catalog, context and browser search behavior."""
import html
import importlib.util
import json
import re
import subprocess
from wiki import ROOT,ART,HERE,save

site=ART/'wiki-source/wiki'
spec=importlib.util.spec_from_file_location('earned_catalog',ROOT/'tools/earned_titles.py')
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
article=json.loads((site/'articles/titles.json').read_bytes())
assert article==json.loads(gen.outputs()['wiki/articles/titles.json']) and article['status']=='Live testing'
page=(site/'dist/titles.html').read_text(encoding='utf8')
assert len(re.findall('<tr><td>',page))==77
for row in gen.catalog()[0]:
    assert page.count('<td>'+html.escape(row['name'])+'</td>')==1
    assert html.escape(row['description']) in page
assert 'unavailable until activation' not in (site/'dist/commands.html').read_text(encoding='utf8')
assert 'New general kill totals count qualifying kills from activation on November 14, 2026.' in (site/'dist/combat.html').read_text(encoding='utf8')
code=(site/'test_search.cjs').read_text(encoding='utf8').replace('__dirname',json.dumps(str(site)))
marker="  let result = await search('#zoneforge');"
assert code.count(marker)==1
code=code.replace(marker,"""  for (const query of ['Titles','#titles','Dragonslayer']) {
    const found = await search(query);
    assert.equal(found.results[0].children[0].href,'titles.html',query);
  }
"""+marker)
target=ART/'title-search-check.cjs';target.write_text(code,encoding='utf8')
subprocess.run(['node',str(target)],check=True)
save(HERE/'wiki-content-checks.json',dict(result='PASS',exact_titles=77,generated_article_matches=True,
    title_queries=['Titles','#titles','Dragonslayer'],ordinary_search_controls=True))

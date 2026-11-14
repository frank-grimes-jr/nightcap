"""Keep current-main authored title context aligned with the scoped public release."""
from wiki import ROOT,ART,activate,save
import json

for name in ['index','features','commands','unreleased','dungeon-modes','combat','multiclass','adventure-journal','tradeskills']:
    path=ROOT/'wiki/articles'/(name+'.json');article=json.loads(path.read_bytes())
    if activate(article):save(path,article)
path=ROOT/'wiki/articles/recent-changes.json';article=json.loads(path.read_bytes())
assert 'id="titles-active"' not in article['body']
body=json.loads((ART/'wiki-source/wiki/articles/recent-changes.json').read_bytes())['body']
article['body']=body[:body.index('<h2 ',1)]+article['body']
article['updated']=article['reviewed_at']='2026-11-14';save(path,article)

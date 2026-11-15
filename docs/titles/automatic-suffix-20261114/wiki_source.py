"""Align current-main title guide fragments without publishing its whole mirror."""
import json
from wiki import ROOT,ART,transform,save

for name in ['commands','combat','dungeon-modes','multiclass','tradeskills','adventure-journal']:
    path=ROOT/'wiki/articles'/(name+'.json');article=json.loads(path.read_bytes())
    assert transform(article),name
    save(path,article)
path=ROOT/'wiki/articles/features.json';article=json.loads(path.read_bytes())
needle='Slayer ranks, dragon victories, Classic Raid completion and skill mastery become permanent cosmetic choices.'
assert article['body'].count(needle)==1
article['body']=article['body'].replace(needle,needle+' Matching prefixes and suffixes unlock automatically, with a notification.')
article['updated']=article['reviewed_at']='2026-11-14';save(path,article)
path=ROOT/'wiki/articles/index.json';article=json.loads(path.read_bytes())
needle='celebrate dragon victories, Classic completion and skill mastery.'
assert article['body'].count(needle)==1
article['body']=article['body'].replace(needle,needle+' Matching prefix and suffix choices unlock automatically.')
article['updated']=article['reviewed_at']='2026-11-14';save(path,article)
path=ROOT/'wiki/articles/recent-changes.json';article=json.loads(path.read_bytes())
body=json.loads((ART/'wiki-source/wiki/articles/recent-changes.json').read_bytes())['body']
assert 'id="titles-automatic-suffix"' not in article['body']
article['body']=body[:body.index('<h2 ',1)]+article['body']
article['updated']=article['reviewed_at']='2026-11-14';save(path,article)

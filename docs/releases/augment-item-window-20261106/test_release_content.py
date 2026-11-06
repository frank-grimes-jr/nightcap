"""Validate the exact scoped public guide projection before publication."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[3]
WIKI=ROOT/'artifacts/augment-item-window/wiki-source/wiki'
BEFORE=Path('E:/EQ_Local_Dev/_worktrees/augment-audit-20261106/artifacts/augment-audit-release/reproduced/wiki/dist')


class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=[];self.links=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.append(d['id'])
        self.links += [d[k] for k in ('href','src') if k in d]


class ReleaseContent(unittest.TestCase):
    def test_exact_route_and_change_scope(self):
        hashes=lambda folder:{p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
        old,new=hashes(BEFORE),hashes(WIKI/'dist')
        self.assertEqual(set(old),set(new));self.assertEqual(len(new),510)
        allowed={n+'.html' for n in ('augment-audit','equipment','commands','features','recent-changes','all-pages')}|{'search-index.json','sitemap.xml'}
        self.assertLessEqual({n for n in new if new[n]!=old[n]},allowed)

    def test_all_links_and_unique_ids(self):
        out=WIKI/'dist';pages={p.name:Page(p.read_text(encoding='utf-8')) for p in out.glob('*.html')}
        self.assertEqual(len(pages),503)
        for name,page in pages.items():
            self.assertEqual(len(page.ids),len(set(page.ids)),name)
            for link in page.links:
                url=urlsplit(link)
                if url.scheme or url.netloc:continue
                target=unquote(url.path) or name
                self.assertTrue((out/target).is_file(),(name,link))
                if url.fragment:self.assertIn(unquote(url.fragment),pages[target].ids,(name,link))

    def test_equipped_totals_stacking_and_live_qa_boundary(self):
        article=json.loads((WIKI/'articles/augment-audit.json').read_text(encoding='utf-8'))
        for phrase in ('#augstats','separately from Shielding','strongest','+1 percentage point','Ascension gives +2','Bagged augments','live testing'):
            self.assertIn(phrase,article['body'])
        self.assertEqual(article['status'],'Live testing')
        self.assertNotIn('Description and equipped totals — Not released',article['body'])


if __name__=='__main__':unittest.main()

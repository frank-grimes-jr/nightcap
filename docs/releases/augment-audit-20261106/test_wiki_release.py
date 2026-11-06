"""Public-release projection and all generated links/anchors; no deployment calls."""
import html.parser
import json
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[3]
WIKI=ROOT/'artifacts/augment-audit-release/wiki-source/wiki'
sys.path.insert(0,str(WIKI))
import build


class Page(html.parser.HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=[];self.links=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        for k in ('href','src'):
            if k in a:self.links.append(a[k])


class WikiRelease(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=build.build();cls.articles={a['slug']:a for a in build.load_articles()}
        cls.pages={p.name:Page(p.read_text(encoding='utf-8')) for p in cls.out.glob('*.html')}

    def test_all_local_links_and_unique_anchors(self):
        for name,page in self.pages.items():
            self.assertEqual(len(page.ids),len(set(page.ids)),name)
            for raw in page.links:
                url=urlsplit(raw)
                if url.scheme or url.netloc:continue
                target=unquote(url.path) or name
                self.assertTrue((self.out/target).is_file(),(name,raw))
                if url.fragment:self.assertIn(unquote(url.fragment),self.pages[target].ids,(name,raw))

    def test_enabled_pools_and_no_invented_wearables(self):
        data=json.loads((WIKI/'catalog.json').read_text(encoding='utf-8'))
        self.assertEqual(len(data['zones']),50);self.assertEqual(len(data['items']),392)
        for zone in ('cazicthule','hateplaneb'):
            rows=[i for i in data['items'] if i['zone']==zone]
            self.assertEqual(len(rows),4)
            self.assertEqual({i['kind'] for i in rows},{'Augment'})
            self.assertIn('Augment-only pool',self.articles['zone-'+zone]['body'])
        self.assertEqual(len([i for i in data['items'] if i['kind']=='Gear']),192)

    def test_public_stats_follow_installed_afterimages(self):
        after={int(r['after']['id']):r['after'] for r in json.loads((ROOT/'docs/audits/augments-20261106/item-preimages.json').read_text())}
        data=json.loads((WIKI/'catalog.json').read_text(encoding='utf-8'))
        for i in data['items']:
            if i['kind']!='Augment':continue
            for field,label in [('spelldmg','Spell Damage'),('healamt','Healing Amount'),('avoidance','Avoidance')]:
                if int(after[i['id']][field]):self.assertEqual(i['stats'][label],int(after[i['id']][field]))
        self.assertEqual(self.articles['augment-audit']['status'],'Live testing')
        self.assertNotIn('Not released',self.articles['augment-audit']['body'])
        self.assertNotIn('Disabled; candidate enables',self.articles['augment-audit']['body'])

    def test_existing_public_artwork_is_unchanged(self):
        baseline=json.loads((ROOT/'docs/releases/augment-audit-20261106/wiki-baseline.json').read_text())['manifest']
        import hashlib
        for name,pin in baseline.items():
            if name.startswith('assets/'):
                self.assertEqual(hashlib.sha256((self.out/name).read_bytes()).hexdigest(),pin,name)

    def test_build_lab_changes_only_reviewed_item_projection(self):
        import html
        prior=Path('E:/EQ_Local_Dev/_worktrees/wiki-hunt-rates-live/wiki/dist/build-lab.html').read_text(encoding='utf-8')
        current=(self.out/'build-lab.html').read_text(encoding='utf-8')
        parse=lambda s:json.loads(html.unescape(re.search(r'data-lab="([^"]+)"',s)[1]))
        before,after=parse(prior),parse(current)
        old_items,new_items=before.pop('items'),after.pop('items')
        self.assertEqual(before,after,'Build Lab model/spells changed outside the item catalog')
        old_gear={i['id']:i for i in old_items if i['kind']=='Gear'}
        new_gear={i['id']:i for i in new_items if i['kind']=='Gear'}
        self.assertEqual(old_gear,new_gear)
        self.assertEqual(set(i['id'] for i in new_items)-set(i['id'] for i in old_items),{b+t for b in (940344,940592) for t in range(4)})


if __name__=='__main__':unittest.main()

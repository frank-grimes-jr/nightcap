"""Content/release invariants and complete generated-site link checks."""
import html.parser
import json
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
import build


class Page(html.parser.HTMLParser):
    def __init__(self, data):
        super().__init__()
        self.ids, self.links, self.assets, self.tags = [], [], [], []
        self.feed(data)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag in ['img', 'script'] and 'src' in attrs:
            self.assets.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') in ['stylesheet', 'icon']:
            self.assets.append(attrs['href'])


class WikiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = build.build()
        cls.articles = {a['slug']:a for a in build.load_articles()}
        cls.pages = {p.name:Page(p.read_text(encoding='utf-8')) for p in cls.out.glob('*.html')}

    def test_every_local_link_asset_and_anchor(self):
        for name, page in self.pages.items():
            self.assertEqual(len(page.ids), len(set(page.ids)), name+' duplicate IDs')
            self.assertEqual(page.tags.count('h1'), 1, name)
            for raw in page.links + page.assets:
                url = urlsplit(raw)
                if url.scheme or url.netloc:
                    continue
                target = unquote(url.path) or name
                self.assertTrue((self.out / target).is_file(), f'{name} -> {raw}')
                if url.fragment:
                    self.assertIn(unquote(url.fragment), self.pages[target].ids, f'{name} -> {raw}')

    def test_only_enabled_reward_catalog(self):
        data = json.loads((build.ROOT/'catalog.json').read_text(encoding='utf-8'))
        self.assertEqual(len(data['zones']),48)
        self.assertEqual(len(data['items']),384)
        self.assertEqual(len({i['id'] for i in data['items']}),384)
        for z in data['zones']:
            items = [i for i in data['items'] if i['zone']==z['slug']]
            self.assertEqual(len(items),8,z['slug'])
            for kind in ['Augment','Gear']:
                self.assertEqual(sorted(i['tier'] for i in items if i['kind']==kind),[0,1,2,3])
        self.assertNotIn('highpass', [z['slug'] for z in data['zones']])

    def test_equipment_groups_variants_and_keeps_every_item_reachable(self):
        catalog = (self.out/'items.html').read_text(encoding='utf-8')
        self.assertEqual(catalog.count('data-equipment-row '), 96)
        ids = set(re.findall(r'href="item-(\d+)\.html"', catalog))
        data = json.loads((build.ROOT/'catalog.json').read_text(encoding='utf-8'))
        self.assertEqual(ids, {str(i['id']) for i in data['items']})
        for control in ['equipment-query', 'equipment-slot', 'equipment-level', 'equipment-zone', 'equipment-reset']:
            self.assertIn(control, self.pages['items.html'].ids)
        directory = (self.out/'all-pages.html').read_text(encoding='utf-8')
        equipment = directory.split('id="category-2"')[1].split('id="category-3"')[0]
        self.assertNotIn('href="item-', equipment)
        self.assertIn('href="items.html"', equipment)
        self.assertIn('href="equipment.html"', equipment)
        self.assertIn('href="zone-hunt.html"', equipment)
        self.assertIn('selectFamilies', (self.out/'assets/search.js').read_text(encoding='utf-8'))

    def test_current_mechanics_and_unreleased_labels(self):
        self.assertIn('<strong>10%',self.articles['multiclass']['body'])
        self.assertIn('1,000,000 AA experience',self.articles['multiclass']['body'])
        self.assertNotIn('plus 1%',self.articles['multiclass']['body'])
        self.assertIn('10%',self.articles['commands']['body'])
        self.assertNotIn('40%',self.articles['commands']['body'])
        self.assertEqual(self.articles['unreleased']['status'],'Not released')
        self.assertIn('not installed',self.articles['unreleased']['body'])
        self.assertIn('no merchant resale value',self.articles['zone-hunt']['body'])
        self.assertIn('nighttime undead',self.articles['zone-kithicor']['body'])

    def test_features_and_updated_guides_are_reachable(self):
        for name, page in self.pages.items():
            self.assertIn('features.html', page.links, name)
        features = self.articles['features']['body']
        for target in ['multiclass','item-upgrades','tradeskills','pets','combat','travel','equipment','launcher']:
            self.assertIn(target+'.html',features)
        self.assertIn('4 identical Polished',self.articles['item-upgrades']['body'])
        self.assertIn('Craft All',self.articles['tradeskills']['body'])
        self.assertIn('Temporary AA effects',self.articles['combat']['body'])
        self.assertIn('LORE restrictions are disabled',self.articles['equipment']['body'])
        self.assertNotIn('all 72',self.articles['waypoints']['body'])

    def test_generated_reward_pages_use_current_upgrade_costs(self):
        rewards = [a for slug,a in self.articles.items() if re.fullmatch(r'item-\d+|zone-(?!hunt$)[a-z0-9-]+',slug)]
        self.assertEqual(len(rewards),432)
        for a in rewards:
            self.assertRegex(a['body'],r'[Ff]our (?:identical )?Polished',a['slug'])
            self.assertNotIn('exchange three identical eligible copies',a['body'])

    def test_search_index_has_all_articles_without_internal_sources(self):
        index = json.loads((self.out/'search-index.json').read_text(encoding='utf-8'))
        self.assertEqual({a['slug'] for a in index},set(self.articles))
        self.assertNotIn('sources',index[0])
        self.assertTrue(all(a['text'] for a in index))

    def test_public_payload_excludes_private_material(self):
        forbidden = re.compile(r'135\.148\.47\.202|/opt/nightcap|C:/Users|\.ssh/|BEGIN .*PRIVATE KEY|scrypt|account_password|docs/releases/|github.com/frank-grimes',re.I)
        for p in self.out.rglob('*'):
            if p.is_file() and p.suffix != '.png':
                self.assertIsNone(forbidden.search(p.read_text(encoding='utf-8')),str(p))
        self.assertFalse((self.out/'catalog.json').exists())
        self.assertFalse((self.out/'articles').exists())

    def test_package_is_exact_and_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)/'wiki.tar.gz'
            manifest = build.package(self.out,dest)
            self.assertEqual(set(manifest),{p.relative_to(self.out).as_posix() for p in self.out.rglob('*') if p.is_file()})
            with self.assertRaises(ValueError):
                build.package(self.out,dest)


if __name__ == '__main__':
    unittest.main()

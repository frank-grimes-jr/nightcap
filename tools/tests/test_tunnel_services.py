import copy
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tunnel_services import plan, stock_catalog, starter_items, CLASSES, STATS, PORTABLE
import generate_living_economy

ROOT=Path(__file__).resolve().parents[2]


class TunnelServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads((ROOT/'docs/releases/tunnel-services-starters/catalog.json').read_bytes())
        cls.layout=plan(cls.source)

    def test_every_legal_spell_component_and_all_instrument_families_are_available(self):
        stock=set(self.layout['stock']['general'])
        for spell in self.source['spells']:
            for i in range(1,5):
                item=int(spell[f'components{i}'])
                if item>0:self.assertIn(item,stock,spell['name'])
        self.assertTrue({13073,13068,10015,13080,13070,13076,13005,13006,13009,13000,13001,13011,13012}<=stock)

    def test_missing_reagent_fails_closed(self):
        source=copy.deepcopy(self.source)
        source['items']=[i for i in source['items'] if i['id']!='13073']
        with self.assertRaisesRegex(ValueError,'component'):stock_catalog(source)

    def test_no_free_unreviewed_spell_components(self):
        prices={int(i['id']):int(i['price']) for i in self.source['items']}
        prices.update(self.layout['stock']['price_overrides'])
        self.assertEqual(self.layout['stock']['price_overrides'],{12832:100})
        self.assertTrue(all(prices[i]>0 for i in self.layout['stock']['general']))
        source=copy.deepcopy(self.source)
        next(i for i in source['items'] if i['id']=='13073')['price']='0'
        with self.assertRaisesRegex(ValueError,'Unpriced'):stock_catalog(source)

    def test_retired_baseline_generator_cannot_rewrite_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'candidate'
            with patch.object(generate_living_economy,'read_sql',side_effect=AssertionError('must not reach database')):
                with self.assertRaisesRegex(ValueError,'retired'):
                    generate_living_economy.generate(out)
            self.assertFalse(out.exists())

    def test_tradeskill_coverage_and_merchant_capacity(self):
        stock=self.layout['stock']['tradeskills']
        self.assertEqual(len(stock),12)
        for skill,item in PORTABLE.items():self.assertIn(item,stock[skill],skill)
        self.assertTrue({17500,17501,17502,17903}<=set(stock['Research']))
        self.assertTrue({13100,13101}<=set(stock['Fishing']))
        for npc in self.layout['npcs']:
            if npc['role']=='merchant':
                self.assertLessEqual(len(npc['stock']),150)
                self.assertEqual(len(npc['stock']),len(set(npc['stock'])))
        for skill,items in stock.items():
            actual=[i for n in self.layout['npcs'] if n.get('skill')==skill for i in n['stock']]
            self.assertEqual(sorted(actual),items)
        self.assertEqual({s['name'] for s in self.layout['stations']},{'Forge','Kiln','Pottery Wheel','Oven','Brewing Barrel','Loom'})

    def test_restricted_merchant_rows_do_not_become_public_stock(self):
        source=copy.deepcopy(self.source)
        sample=next(r for r in source['stock'] if not r['min_status'] or r['min_status']=='0')
        for restriction,value in [('min_status','80'),('level_required','51'),('bucket_name','quest'),('min_expansion','1'),('content_flags','Future')]:
            source['stock']=[*self.source['stock'],dict(sample,item='900099',**{restriction:value})]
            stock=stock_catalog(source)
            self.assertTrue(all(900099 not in v for v in stock['tradeskills'].values()))

    def test_exactly_one_trainer_per_class_and_visible_irregular_clusters(self):
        trainers=[n for n in self.layout['npcs'] if n['role']=='trainer']
        self.assertEqual(sorted(n['class_id'] for n in trainers),list(range(20,36)))
        self.assertGreater(len({n['position']['heading'] for n in trainers}),12)
        self.assertEqual(len([n for n in self.layout['npcs'] if n['role']=='walker']),8)
        points=list(self.layout['relocations'].values())+[n['position'] for n in self.layout['npcs']]+self.layout['stations']
        for i,p in enumerate(points):
            for q in points[i+1:]:self.assertGreaterEqual(math.hypot(p['x']-q['x'],p['y']-q['y']),8)
            self.assertGreater(math.hypot(p['x']+190,p['y']+1725),18,'arrival point must stay clear')

    def test_primary_class_starter_items_are_modest_and_linkable(self):
        items={int(i['id']):i for i in starter_items(self.source)}
        self.assertEqual(len(items),32)
        for cls in range(1,17):
            robe=items[998599+cls];weapon=items[998619+cls]
            self.assertEqual(int(robe['ac']),10)
            self.assertEqual(int(robe[STATS[cls-1]]),5)
            self.assertEqual(sum(int(robe[s]) for s in {'astr','asta','aagi','adex','awis','aint','acha'}),5)
            for item in (robe,weapon):
                self.assertEqual(int(item['classes']),1<<(cls-1))
                self.assertEqual(int(item['races']),65535)
                self.assertEqual(item['nodrop'],'0')
                self.assertLess(int(item['id']),1048576)
                for effect in ('clickeffect','proceffect','worneffect','focuseffect'):self.assertEqual(int(item[effect]),-1)
            self.assertGreater(int(weapon['damage']),3)
            self.assertLess(int(weapon['damage'])/int(weapon['delay']),.25)


if __name__=='__main__':unittest.main()

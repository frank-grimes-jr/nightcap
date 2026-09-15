import copy
import json
from pathlib import Path
import unittest
from pok_hub import build_plan


class PokHubPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = json.loads((Path(__file__).resolve().parents[2] / 'docs/pok/hub-stock-audit.json').read_bytes())

    def test_all_current_scrolls_and_prices_survive_correct_class_routing(self):
        plan = build_plan(self.audit)
        self.assertEqual([m['class_id'] for m in plan['merchants']], list(range(1, 17)))
        self.assertEqual(plan['invariants']['current_unique_scrolls'], 1229)
        self.assertEqual(plan['invariants']['planned_unique_scrolls'], 1229)
        self.assertEqual(plan['invariants']['maximum_merchant_slots'], 275)
        source = {i['item_id']: i for i in self.audit['stock']}
        for merchant in plan['merchants']:
            items = merchant['items']
            self.assertEqual([i['slot'] for i in items], list(range(1, len(items)+1)))
            for item in items:
                self.assertEqual(item['price'], source[item['item_id']]['price'])
                self.assertEqual(item['class_level'], source[item['item_id']]['original_class_levels'][merchant['class_id']-1])
                self.assertLessEqual(item['class_level'], 50)
        for merchant in plan['merchants']:
            if merchant['class_id'] in (1,7,9,16):
                self.assertIn('Discipline_Merchant', merchant['name'])
                self.assertIn('Tomes', merchant['lastname'])

    def test_missing_source_invalid_classes_and_duplicate_stock_are_rejected(self):
        for mutate in (
            lambda a: a.update(source_sha256='unverified'),
            lambda a: a['stock'].append(copy.deepcopy(a['stock'][0])),
            lambda a: a['stock'][0].update(original_class_levels=[]),
            lambda a: a['stock'][0].update(original_class_levels=[255]*16),
            lambda a: a['stock'][0].update(price=-1),
        ):
            audit = copy.deepcopy(self.audit)
            mutate(audit)
            with self.assertRaises(ValueError):
                build_plan(audit)

import sys
import json
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from living_economy import parse_price, prices


class Prices(unittest.TestCase):
    def page(self, values):
        return '<div id="auc_Blue"><table><tr><td>9999</td></tr></table></div>' + \
            '<div id="auc_Green"><table><tr><th>30d Avg</th><th>90d Avg</th></tr><tr>' + \
            ''.join('<td>'+v+'</td>' for v in values) + \
            '</tr></table><table><tr><td>2026-08-23</td><td>A</td><td>1500</td></tr></table></div>'

    def test_green_average_and_fallback(self):
        self.assertEqual(parse_price(self.page(['1575 &#177; 130', '1660']))['reference_pp'], 1575)
        fallback = parse_price(self.page(['?', '1,660 &#177; 430']))
        self.assertEqual((fallback['reference_pp'], fallback['window']), (1660, '90d'))
        self.assertEqual(fallback['latest_auction'], '2026-08-23')

    def test_missing_price_fails_closed(self):
        for value in ('?', '0', '-1', '9999999999'):
            with self.assertRaises(ValueError):
                parse_price(self.page([value, '?']))

    def test_spread_and_rounding(self):
        self.assertEqual(prices(1575, 8900)['sell_cp'], 1890000)
        for reference in (1, 11, 1575, 30000):
            p = prices(reference, 2000)
            self.assertLess(p['buy_cp'], p['find_cp'])
            self.assertLess(p['buy_cp'], p['sell_cp'])
            self.assertGreaterEqual(p['find_cp'], 4000)

    def test_actual_income_boost(self):
        policy = json.loads((Path(__file__).resolve().parents[2]/'docs/economy/policy.json').read_text())
        self.assertEqual(prices(1575, 8900, policy, 20)['sell_cp'], 19895000)
        self.assertEqual(prices(20, 3200, policy, 20)['find_cp'], 232000)
        policy['income_basis'] = 'vendor_payout'
        self.assertEqual(prices(1575, 8900, policy, 20)['sell_cp'], 4974000)

    def test_policy_validation_and_custom_premium(self):
        policy = json.loads((Path(__file__).resolve().parents[2]/'docs/economy/policy.json').read_text())
        policy['tunnel_premium']='1.30'
        self.assertEqual(prices(1575,8900,policy,20)['sell_cp'],21553000)
        policy['buy_fraction']='1.40'
        with self.assertRaises(ValueError): prices(1575,8900,policy,20)
        policy['buy_fraction']='0.70'
        policy['income_basis']='typo'
        with self.assertRaises(ValueError): prices(1575,8900,policy,20)


if __name__ == '__main__':
    unittest.main()

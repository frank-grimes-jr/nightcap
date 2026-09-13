from pathlib import Path
import unittest

from aa_owned_view_controls import assess, prepare
from aa_policy_preflight import read_json


class EarnedViewEvidenceTests(unittest.TestCase):
    def test_native_full_catalog_reproduces_prefix_and_spent_total_loss(self):
        docs = Path(__file__).resolve().parents[3] / 'docs/balance'
        case = read_json(docs / 'aa-owned-view-input.json')
        self.assertEqual(case, prepare(read_json(docs / 'gear-source-inputs.json')))
        result = read_json(docs / 'aa-owned-view-before.json.gz')
        manifest = read_json(docs / 'aa-owned-view-before-build.json')
        self.assertEqual(result['binary_sha256'], manifest['binary_sha256'])
        self.assertEqual(result['assessment'], assess(case, result['report']))
        self.assertEqual(result['assessment'], {
            'usable_prefix_preserved': False, 'earned_rows_preserved': True,
            'earned_plus_expended_points_preserved': False, 'wallet_unchanged': True,
        })
        steps = result['report']['aa_ownership_probe']['steps']
        self.assertEqual([s['effective_rank_count'] for s in steps], [6, 6, 0, 0, 0, 6, 6])
        self.assertEqual([s['spent_points'] for s in steps], [29, 29, 29, 5, 5, 5, 29])
        final = read_json(docs / 'aa-owned-view-final-checks.json')
        self.assertTrue(final['full_catalog_unchanged'])
        self.assertEqual(final['remaining_rows'], {
            'account': 0, 'character_data': 0, 'character_alternate_abilities': 0, 'inventory': 0,
        })

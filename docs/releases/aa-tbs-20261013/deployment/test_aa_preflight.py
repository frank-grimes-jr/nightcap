import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import aa_preflight as preflight


class PreflightTests(unittest.TestCase):
    def run_check(self, mutate=None, owned=None):
        config = json.loads((ROOT / 'config/aa-policy.json').read_text())
        catalog_bytes = (ROOT / config['catalog']).read_bytes()
        catalog = json.loads(gzip.decompress(catalog_bytes))
        if mutate:
            mutate(catalog)
        lines = [name + '\t' + json.dumps(row) for name, rows in catalog.items() for row in rows]
        for row in owned or []:
            lines.append('owned\t' + json.dumps(row))
        with tempfile.TemporaryDirectory() as d:
            stage = Path(d)
            (stage / 'aa-policy.json').write_text(json.dumps(config))
            (stage / 'aa-catalog.json.gz').write_bytes(catalog_bytes)
            with patch.object(preflight, 'STAGE', stage):
                return preflight.check(lambda _: '\n'.join(lines))

    def test_catalog_drift_stops_before_deployment(self):
        with self.assertRaisesRegex(AssertionError, 'catalog drift'):
            self.run_check(lambda t: t['aa_ranks'][0].update(cost=999))

    def test_earned_counts_and_charges_reported_without_writes(self):
        config = json.loads((ROOT / 'config/aa-policy.json').read_text())
        catalog = json.loads(gzip.decompress((ROOT / config['catalog']).read_bytes()))
        aa = {a['id']: a for a in catalog['aa_ability']}
        owned = [dict(level=10, **{'class': 1}, class2=2, class3=12,
                      aa_id=aa[28]['first_rank_id'], aa_value=4, charges=7),
                 dict(level=50, **{'class': 1}, class2=2, class3=12,
                      aa_id=aa[481]['first_rank_id'], aa_value=1, charges=0)]
        result = self.run_check(owned=owned)
        self.assertEqual(result['ownership'], {'ownership_rows': 2, 'earned_rank_count': 5,
                         'saved_charges': 7, 'partially_usable': 1, 'dormant': 1})
        self.assertFalse(result['database_modified'])

    def test_invalid_earned_identity_rejects_candidate(self):
        with self.assertRaisesRegex(AssertionError, 'Unresolvable earned AA'):
            self.run_check(owned=[dict(level=1, **{'class': 1}, class2=0, class3=0,
                                      aa_id=999999, aa_value=1, charges=0)])


if __name__ == '__main__':
    unittest.main(verbosity=2)

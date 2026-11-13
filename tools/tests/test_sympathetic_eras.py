import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sympathetic_eras import CATALOG, HEADER, header, release_caps


class SympatheticEras(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads(CATALOG.read_bytes())['expansions']

    def test_current_catalog_and_generated_native_gate(self):
        caps = release_caps(self.rows)
        self.assertEqual(HEADER.read_text(encoding='utf8'), header(caps))
        self.assertEqual(len(caps), 27)
        self.assertEqual(caps[-1][0], 'Torment of Velious')
        self.assertTrue(all((strike, heal) == (1, 1) for _, strike, heal in caps))

    def test_reviewed_lines_release_independently_and_carry_forward(self):
        rows = copy.deepcopy(self.rows)
        rows[1]['strike'] = 2
        rows[4]['healing'] = 2
        caps = release_caps(rows)
        self.assertEqual(caps[0][1:], (1, 1))
        self.assertEqual(caps[3][1:], (2, 1))
        self.assertEqual(caps[-1][1:], (2, 2))

    def test_invalid_release_cannot_silently_unlock_power(self):
        for bad in ({'id': 3}, {'name': 'Classic'}, {'strike': 3},
                    {'healing': True}, {'strike': 0}, {'heal': 2}):
            with self.subTest(bad=bad):
                rows = copy.deepcopy(self.rows)
                rows[1].update(bad)
                with self.assertRaises(ValueError):
                    release_caps(rows)


if __name__ == '__main__':
    unittest.main()

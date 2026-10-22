"""Pinned projection and public workbench contracts."""
import hashlib
import json
from pathlib import Path
import unittest
import build
import build_lab


class BuildLabTests(unittest.TestCase):
    def test_projected_data_and_original_class_access(self):
        data = json.loads((build.ROOT/'build-lab-data.json').read_text())
        self.assertEqual(len(data['spells']), 8)
        self.assertEqual(len(data['controls']), 12)
        self.assertEqual(next(s for s in data['spells'] if s['id']=='54')['classes'], [12])
        self.assertEqual(next(s for s in data['spells'] if s['id']=='6')['classes'], [11])
        self.assertEqual(set(data), {'version','level','spells','controls','contentDate','controlDate','reviewed'})

    def test_frozen_formula_and_fixture_inputs_match_review(self):
        root = build.ROOT.parent
        pins = json.loads((root/'docs/build-lab/data-provenance.json').read_text())
        for name, expected in pins.items():
            self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),expected,name)

    def test_workbench_has_no_inline_executable_script_or_external_dependency(self):
        body = build_lab.render()
        self.assertNotIn('<script',body)
        self.assertNotIn('http',body)
        for control in ['lab-optimize','lab-time','lab-save','lab-import','lab-apply-gear','lab-error']:
            self.assertIn(f'id="{control}"',body)
        article = json.loads((build.ROOT/'articles/build-lab.json').read_text())
        self.assertIn('not a universal optimal rotation',article['body'])
        self.assertIn('not auto-planned',article['body'])


if __name__ == '__main__':
    unittest.main()

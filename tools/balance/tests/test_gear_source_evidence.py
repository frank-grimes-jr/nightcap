import copy
import gzip
import json
from pathlib import Path
import unittest

from builds import load_snapshot
from gear_source_controls import verify
from release_pool_controls import summarize


class GearSourceNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]
        cls.docs = cls.root/'docs/balance'
        cls.original = cls.read('release-pool-inputs.json')
        cls.catalog = cls.read('native-aa-catalog.json')
        cls.snapshot, cls.manifest = load_snapshot(cls.root/'tools/balance/fixtures/classic-20260912-v2.json.gz')

    @classmethod
    def read(cls, name):
        raw = (cls.docs/name).read_bytes()
        return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)

    def test_all_144_source_and_haste_comparisons_verify(self):
        for stem, count in (('gear-source',108), ('gear-source-cloak',36)):
            rows = verify(self.read(stem+'-inputs.json'), self.read(stem+'.json.gz'), self.original,
                          self.snapshot, self.manifest['snapshot_sha256'], self.catalog)
            self.assertEqual(len(rows),count)

    def test_failing_death_case_changes_only_callback_evidence(self):
        before = self.read('gear-source-death-before.json.gz')
        run = self.read('gear-source-death.json.gz')['runs'][0]
        case = self.read('gear-source-death-inputs.json')['cases'][0]
        self.assertEqual(summarize(case,run['report']),run['summary'])
        report = copy.deepcopy(run['report'])
        combat = report['pet_probe']['combat']
        self.assertEqual(combat['terminal_events'][0]['hp'],-500)
        self.assertEqual(combat['trace'][-1]['player']['hp'],732)
        self.assertEqual(run['summary']['minimum_hp_percent'],0)
        combat.pop('terminal_events')
        combat['input'].pop('capture_terminal')
        report['pet_probe']['input']['combat'].pop('capture_terminal')
        self.assertEqual(report,before)

    def test_twelve_previous_build_reports_remain_byte_identical(self):
        old = {r['id']: r for r in self.read('release-pool.json.gz')['runs']}
        runs = self.read('gear-source-regression.json.gz')['runs']
        self.assertEqual(len(runs),12)
        for run in runs:
            self.assertEqual(run['native_raw_sha256'],old[run['id']]['native_raw_sha256'])
            self.assertEqual(run['report'],old[run['id']]['report'])

    def test_false_or_missing_callback_cannot_validate_rebound_death(self):
        run = self.read('gear-source-death.json.gz')['runs'][0]
        case = self.read('gear-source-death-inputs.json')['cases'][0]
        for bad in ([], [{'entity_id':1,'ms':164650,'hp':732,'max_hp':5093}]):
            report = copy.deepcopy(run['report'])
            report['pet_probe']['combat']['terminal_events'] = bad
            with self.assertRaises(ValueError):
                summarize(case,report)


if __name__ == '__main__':
    unittest.main()

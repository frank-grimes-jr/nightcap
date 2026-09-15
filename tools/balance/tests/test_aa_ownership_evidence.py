import gzip
import hashlib
import tarfile
from pathlib import Path
import unittest

from aa_ownership import transition
from aa_ownership_controls import cases, verify
from aa_policy_preflight import read_json


class AAOwnershipEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[3]
        cls.docs = cls.root / 'docs/balance'
        cls.source = cls.read('aa-policy-snapshot.json.gz')
        cls.spec = cls.read('aa-release-candidates.json')

    @classmethod
    def read(cls, name):
        return read_json(cls.docs / name)

    def test_all_196_earned_rows_and_nominal_cost_survive_both_transitions(self):
        plan = self.read('aa-ownership-plan.json')
        launch = transition(self.source, self.spec, 'launch_core', self.source['purchases'])
        later = transition(self.source, self.spec, 'later_core', launch['active_rows'], launch)
        again = transition(self.source, self.spec, 'launch_core', later['active_rows'], later)
        for key, actual in [('launch', launch), ('later', later), ('launch_again', again)]:
            self.assertEqual(actual, plan[key])
            self.assertEqual(len(actual['earned_rows']), 196)
            self.assertEqual(actual['earned_rows'], launch['earned_rows'])
            self.assertEqual(sum(p['earned_nominal_cost'] for p in actual['point_totals']), 3155)
        self.assertEqual(again['active_rows'], launch['active_rows'])

    def test_five_native_controls_reproduce_old_failure_and_pass_with_fix(self):
        expected = cases(self.read('gear-source-inputs.json'))
        for stem in ('aa-ownership-before', 'aa-ownership-after'):
            self.assertEqual(expected, self.read(stem + '-inputs.json'))
            evidence = self.read(stem + '.json.gz')
            self.assertEqual(evidence['binary_sha256'], self.read(stem + '-build.json')['binary_sha256'])
            backup = hashlib.sha256(gzip.decompress((self.docs / 'aa-projection-before.sql.gz').read_bytes())).hexdigest()
            self.assertEqual(evidence['original_tables_sha256'], backup)
            self.assertTrue(evidence['restored_exactly'])
        with self.assertRaisesRegex(ValueError, 'Profile and native ownership disagree: invalid_saved_count'):
            verify(self.read('aa-ownership-before.json.gz'), expected)
        self.assertEqual(verify(self.read('aa-ownership-after.json.gz'), expected),
                         self.read('aa-ownership-after-checks.json'))

    def test_valid_owned_rows_remain_byte_identical_while_three_stale_profiles_clear(self):
        before = {c['id']: c for c in self.read('aa-ownership-before.json.gz')['cases']}
        after = {c['id']: c for c in self.read('aa-ownership-after.json.gz')['cases']}
        for identity in ('valid_saved', 'materialized_cap'):
            self.assertEqual(after[identity], before[identity])
        for identity in ('invalid_saved_count', 'removed_before_reload', 'above_projected_cap'):
            old = before[identity]['report']['aa_ownership_probe']['steps'][-1]
            new = after[identity]['report']['aa_ownership_probe']['steps'][-1]
            self.assertTrue(old['profile'])
            self.assertEqual(new['profile'], [])
            self.assertEqual(new['effective_rank_count'], 0)
            self.assertEqual(new['stored'], old['stored'])

    def test_restored_six_rank_purchase_loads_and_saves_without_rebuying(self):
        evidence = self.read('aa-ownership-restoration.json.gz')
        launch = transition(self.source, self.spec, 'launch_core', evidence['launch']['earned_rows'])
        later = transition(self.source, self.spec, 'later_core', launch['active_rows'], launch)
        self.assertEqual(launch, evidence['launch'])
        self.assertEqual(later, evidence['later'])
        self.assertEqual(launch['active_rows'][0]['aa_value'], 3)
        self.assertEqual(later['active_rows'][0]['aa_value'], 6)
        steps = evidence['native']['report']['aa_ownership_probe']['steps']
        self.assertEqual([s['operation'] for s in steps], ['load', 'save', 'load'])
        for step in steps:
            self.assertEqual(step['effective_rank_count'], 6)
            self.assertEqual(step['unspent_points'], 17)
            self.assertEqual(step['profile'], step['stored'])
        self.assertEqual(steps[1]['spent_points'], later['point_totals'][0]['earned_nominal_cost'])
        self.assertEqual(evidence['restored_tables_sha256'],
                         self.read('aa-projection-native.json.gz')['before_tables_sha256'])

    def test_twenty_four_fights_preserve_raw_hashes_and_complete_reports(self):
        for stem, golden_name in [('aa-ownership-regression', 'gear-source-regression'),
                                  ('aa-ownership-source-regression', 'gear-source')]:
            inputs = self.read(stem + '-inputs.json')
            runs = self.read(stem + '.json.gz')['runs']
            golden = {r['id']: r for r in self.read(golden_name + '.json.gz')['runs']}
            self.assertEqual(len(runs), 12)
            self.assertEqual({r['id'] for r in runs}, {c['id'] for c in inputs['cases']})
            for run in runs:
                self.assertEqual(run['native_raw_sha256'], golden[run['id']]['native_raw_sha256'])
                self.assertEqual(run['report'], golden[run['id']]['report'])

    def test_before_after_builds_differ_only_in_aa_candidate_and_link(self):
        before = self.read('aa-ownership-before-build.json')
        after = self.read('aa-ownership-after-build.json')
        self.assertEqual({k for k in before.keys() | after.keys() if before.get(k) != after.get(k)},
                         {'objects', 'diagnostic_link_args', 'aa_candidate', 'binary_sha256'})
        old = dict(before['objects'])
        new = dict(after['objects'])
        old.pop('CMakeFiles/zone.dir/aa.cpp.o')
        candidate_object = str(Path(after['aa_candidate']['source']).with_suffix('.o')).replace('\\', '/')
        new.pop(candidate_object)
        self.assertEqual(old, new)
        with tarfile.open(self.root / 'docs/releases/server-fixes-20260913/candidate-source.tar.gz') as frozen:
            source = frozen.extractfile('zone/aa.cpp').read()
        compiled = gzip.decompress((self.docs / 'aa-ownership-candidate.cpp.gz').read_bytes())
        self.assertEqual(hashlib.sha256(compiled).hexdigest(), after['aa_candidate']['sha256'])
        self.assertEqual(source, compiled.replace(b'\r\n', b'\n'))


if __name__ == '__main__':
    unittest.main()

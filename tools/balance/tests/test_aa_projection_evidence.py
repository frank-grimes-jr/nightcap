import gzip
import hashlib
from pathlib import Path
import re
import unittest

from aa_policy_preflight import read_json
from aa_policy_projection import DATABASE, project, transaction_sql
from run_aa_projection import inputs, verify_batch


class AAProjectionEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = Path(__file__).resolve().parents[3] / 'docs/balance'
        cls.evidence = read_json(cls.docs / 'aa-projection-native.json.gz')
        cls.spec = read_json(cls.docs / 'aa-release-candidates.json')
        frozen = read_json(cls.docs / 'aa-policy-snapshot.json.gz')
        cls.clone = {key: frozen[key] for key in ('abilities', 'ranks', 'prerequisites')}
        cls.clone['purchases'] = []

    def test_recorded_inputs_and_table_changes_regenerate(self):
        matrix = read_json(self.docs / 'gear-source-inputs.json')
        catalog = read_json(self.docs / 'native-aa-catalog.json')
        self.assertEqual(inputs(matrix, self.spec, catalog), read_json(self.docs / 'aa-projection-inputs.json'))
        self.assertTrue(self.evidence['completed'])
        self.assertEqual(self.evidence['binary_sha256'], read_json(self.docs / 'pet-resist-build.json')['binary_sha256'])
        self.assertEqual([p['id'] for p in self.evidence['phases']], ['launch_core', 'later_core'])
        for phase in self.evidence['phases']:
            self.assertEqual(phase['plan'], project(self.clone, self.spec, phase['id']))
            for suffix, restore in (('apply', False), ('restore', True)):
                sql = (self.docs / f'aa-projection-{phase["id"]}-{suffix}.sql').read_text(encoding='utf-8')
                procedure = re.search(r'CREATE PROCEDURE `([^`]+)`', sql).group(1)
                self.assertEqual(sql, transaction_sql(phase['plan'], DATABASE, procedure, restore))

    def test_all_twenty_one_legal_build_readouts_preserve_stats_and_exact_catalogs(self):
        count = 0
        for phase in self.evidence['phases']:
            verify_batch(phase['original_batch']['report'], phase['projected_batch']['report'],
                         set(phase['plan']['allowed_rank_ids']))
            count += len(phase['projected_batch']['report']['builds'])
        self.assertEqual(count, 21)

    def test_fourteen_forbidden_purchases_succeed_before_and_fail_after_projection(self):
        phases = read_json(self.docs / 'aa-projection-inputs.json')
        count = 0
        for recorded, expected in zip(self.evidence['phases'], phases):
            self.assertEqual(len(recorded['controls']), 7)
            for run, case in zip(recorded['controls'], expected['controls']):
                self.assertEqual(run['id'], case['id'])
                player = run['original']['report']['builds'][0]
                self.assertEqual(player['aa_purchases'][-1]['rank_id'], case['rank_id'])
                self.assertEqual(player['aa_remaining'], 0)
                self.assertEqual(player['aa_spent'], case['input']['builds'][0]['aa_budget'])
                rejected = run['projected']
                self.assertEqual(rejected['exit_code'], 1)
                self.assertEqual(rejected['rejected_rank_id'], case['rank_id'])
                self.assertTrue(rejected['output_absent'])
                self.assertIn('Native AA purchase gate rejected rank ' + str(case['rank_id']), rejected['native_error'])
                count += 1
        self.assertEqual(count, 14)

    def test_twelve_projected_boss_reports_are_byte_identical_to_original_evidence(self):
        golden = {r['id']: r for r in read_json(self.docs / 'gear-source.json.gz')['runs']}
        phases = read_json(self.docs / 'aa-projection-inputs.json')
        count = 0
        for phase, expected in zip(self.evidence['phases'], phases):
            self.assertEqual({r['id'] for r in phase['fights']}, {c['id'] for c in expected['fights']})
            self.assertEqual(len(phase['fights']), 6)
            for run in phase['fights']:
                self.assertEqual(run['native_raw_sha256'], golden[run['id']]['native_raw_sha256'])
                self.assertEqual(run['report'], golden[run['id']]['report'])
                count += 1
        self.assertEqual(count, 12)

    def test_both_restorations_and_rejected_transaction_match_the_full_backup(self):
        raw = gzip.decompress((self.docs / 'aa-projection-before.sql.gz').read_bytes())
        expected = hashlib.sha256(raw).hexdigest()
        self.assertEqual(self.evidence['before_tables_sha256'], expected)
        for phase in self.evidence['phases']:
            self.assertTrue(phase['restored_exactly'])
            self.assertEqual(phase['restored_tables_sha256'], expected)
        rollback = read_json(self.docs / 'aa-projection-rollback-check.json')
        self.assertEqual(rollback['engines'], {'aa_ability': 'InnoDB', 'aa_ranks': 'InnoDB'})
        self.assertTrue(rollback['restored_exactly'])
        self.assertEqual(rollback['before_tables_sha256'], expected)
        self.assertEqual(rollback['after_tables_sha256'], expected)
        self.assertEqual(rollback['ability_updates_before_failure'], 1527)
        self.assertIn('AA original values changed', rollback['error'])


if __name__ == '__main__':
    unittest.main()

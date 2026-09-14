import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_aa_client_strings import audit, title_ids, load_snapshot


class ClientTitleAuditTests(unittest.TestCase):
    def snapshot(self):
        return {
            'abilities': [{'id': 7, 'first_rank_id': 100, 'enabled': 1}],
            'ranks': [{'id': 100, 'title_sid': 500, 'next_id': 101},
                      {'id': 101, 'title_sid': 501, 'next_id': -1}],
            'ownership': [{'aa_id': 100, 'saved_rows': 2}],
        }

    def test_only_nonempty_type_one_strings_resolve_titles(self):
        self.assertEqual(title_ids('500^1^Title^0\n501^2^Description^0\n502^1^^0'), {500})

    def test_empty_or_malformed_client_file_is_rejected(self):
        for value in ('', '500^2^Description^0', '500^1^Title^0\nbad row'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                title_ids(value)

    def test_missing_later_rank_title_blocks_family_with_saved_ownership(self):
        result = audit(self.snapshot(), {500})
        self.assertEqual(result['missing_title_abilities'], [
            {'ability_id': 7, 'first_rank_id': 100, 'enabled': 1,
             'missing_title_sids': [501], 'saved_rows': 2}])
        self.assertEqual(result['enabled_affected_saved_rows'], 2)

    def test_present_titles_are_kept_regardless_of_expansion_or_name(self):
        snapshot = self.snapshot()
        snapshot['abilities'][0].update(name='Unknown AA 500', expansion=21)
        self.assertEqual(audit(snapshot, {500, 501})['missing_title_abilities'], [])

    def test_disabled_family_is_reported_separately(self):
        snapshot = self.snapshot()
        snapshot['abilities'][0]['enabled'] = 0
        result = audit(snapshot, {999})
        self.assertEqual(result['enabled_affected_abilities'], 0)
        self.assertEqual(result['enabled_affected_saved_rows'], 0)
        self.assertEqual(result['missing_title_abilities'][0]['saved_rows'], 2)

    def test_unknown_ownership_is_not_silently_treated_as_unpurchased(self):
        snapshot = self.snapshot()
        snapshot['ownership'][0]['aa_id'] = 999
        with self.assertRaisesRegex(ValueError, 'ownership'):
            audit(snapshot, {500})

    def test_broken_or_cyclic_rank_chain_fails(self):
        for target in (999, 100):
            snapshot = self.snapshot()
            snapshot['ranks'][1]['next_id'] = target
            with self.subTest(target=target), self.assertRaises(ValueError):
                audit(snapshot, {500})

    def test_duplicate_rows_and_empty_catalog_fail(self):
        for group in ('abilities', 'ranks', 'ownership'):
            snapshot = self.snapshot()
            snapshot[group].append(snapshot[group][0].copy())
            with self.subTest(group=group), self.assertRaises(ValueError):
                audit(snapshot, {500})
        with self.assertRaises(ValueError):
            audit({'abilities': [], 'ranks': [], 'ownership': []}, {500})

    def export(self):
        snapshot = self.snapshot()
        lines = [group + '\t' + json.dumps(row)
                 for group, rows in snapshot.items() for row in rows]
        lines.append('summary\t' + json.dumps({k: len(v) for k, v in snapshot.items()}))
        return '\n'.join(lines)

    def test_truncated_export_fails_instead_of_reporting_no_purchases(self):
        lines = self.export().splitlines()
        for text in ('\n'.join(lines[:-1]),
                     '\n'.join(line for line in lines if not line.startswith('ownership'))):
            with self.subTest(text=text), self.assertRaises(ValueError):
                load_snapshot(text)

    def test_cli_records_hashes_and_preserves_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot, client, output = (root / name for name in ('aa.tsv', 'dbstr.txt', 'report.json'))
            snapshot.write_text(self.export(), encoding='utf-8')
            client.write_bytes(b'500^1^Known title^0\n')
            before = snapshot.read_bytes(), client.read_bytes()
            command = [sys.executable, '-B', str(Path(__file__).resolve().parents[1] / 'audit_aa_client_strings.py'),
                       '--snapshot', str(snapshot), '--dbstr', str(client), '--output', str(output)]
            subprocess.run(command, check=True, capture_output=True)
            report = json.loads(output.read_text())
            self.assertEqual(report['enabled_affected_saved_rows'], 2)
            self.assertEqual(len(report['dbstr_sha256']), 64)
            self.assertEqual(len(report['snapshot_sha256']), 64)
            command[-1] = str(client)
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(before, (snapshot.read_bytes(), client.read_bytes()))


if __name__ == '__main__':
    unittest.main()

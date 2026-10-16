"""Exercise the actual schema fingerprint SQL on disposable metadata rows."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from dungeon_contract import schema_checks
from rehearse_dungeons import query


class MetadataContract(unittest.TestCase):
    def test_only_audited_collation_alias_is_equivalent(self):
        database = json.loads((ROOT / 'docs/dungeons/rehearsal.json').read_text())['database']
        check = next(c for c in schema_checks() if c['label'] == 'instance_list/columns')
        statement = check['sql'].replace('FROM information_schema.columns', 'FROM dungeon_metadata_fixture') + ';'
        fixture = "CREATE TEMPORARY TABLE dungeon_metadata_fixture AS SELECT * FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='instance_list';"
        statements = [fixture, statement,
            "UPDATE dungeon_metadata_fixture SET collation_name='utf8mb3_general_ci' WHERE column_name='notes';", statement,
            "UPDATE dungeon_metadata_fixture SET collation_name='utf8mb4_general_ci' WHERE column_name='notes';", statement,
            "UPDATE dungeon_metadata_fixture SET collation_name='utf8_general_ci',column_type='varchar(49)' WHERE column_name='notes';", statement]
        values = query('\n'.join(statements), database).stdout.strip().splitlines()
        self.assertEqual(len(values), 4)
        self.assertEqual(values[0], values[1])
        self.assertNotEqual(values[0], values[2])
        self.assertNotEqual(values[0], values[3])


if __name__ == '__main__':
    unittest.main()

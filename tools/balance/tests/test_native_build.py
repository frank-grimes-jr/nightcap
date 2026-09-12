import unittest
from pathlib import Path

from build_native import patched_main
from builds import load_snapshot
from prepare_native import native_inputs, content_tables
from verify_native_resources import verify


class NativeBuildTests(unittest.TestCase):
    def test_native_resource_verifier_detects_corruption_and_missing_builds(self):
        builds = [{'profile':'test','tier':'Base','classes':[1],'level':50}]
        tables = {'base_data':[{'class':1,'level':50,'hp':1500,'hp_fac':5,'mana':0,'mana_fac':0}]}
        native = {'profile':'test','tier':'Base','sta':100,'int':75,'wis':75,'heroic_hp':0,
                  'heroic_mana':0,'item_hp':100,'item_mana':0,'item_percent_hp':0,'item_flat_hp':0,
                  'hp':2105,'mana':0}
        self.assertEqual(verify({'builds':[native]},builds,tables), [])
        self.assertEqual(len(verify({'builds':[native | {'hp':2106}]},builds,tables)),1)
        with self.assertRaises(ValueError):
            verify({'builds':[]},builds,tables)
        with self.assertRaises(ValueError):
            verify({'builds':[native,native]},builds,tables)

    def test_unknown_or_duplicate_startup_layout_fails_closed(self):
        for source in ('', 'int main(int argc, char **argv)\n{' * 2):
            with self.subTest(source=source), self.assertRaises(ValueError):
                patched_main(source)

    def test_content_export_rejects_missing_authoritative_table_declaration(self):
        with self.assertRaises(ValueError):
            content_tables('static std::vector<std::string> GetContentTables() { return {"account"}; }')

    def test_creation_uses_classic_database_allocation(self):
        snapshot, _ = load_snapshot(Path(__file__).parents[1]/'fixtures/classic-20260912-v2.json.gz')
        build = {'race':'Human','deity':'Agnostic','classes':[1,2,12]}
        result = native_inputs([build],snapshot['tables'])['builds'][0]
        self.assertEqual(result['creation'], {'str':85,'sta':110,'dex':75,'agi':80,'int':75,'wis':75,'cha':75})
        with self.assertRaises(ValueError):
            native_inputs([build | {'race':'Iksar'}],snapshot['tables'])
        with self.assertRaises(ValueError):
            native_inputs([build],snapshot['tables'] | {'char_create_combinations':[]})

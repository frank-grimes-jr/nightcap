import unittest
import copy
import tempfile
from pathlib import Path

from build_native import patched_main, patched_client, candidate_reusable, digest
from builds import load_snapshot
from prepare_native import native_inputs, content_tables
from verify_native_resources import verify


class NativeBuildTests(unittest.TestCase):
    def test_candidate_reuse_requires_source_object_flags_and_link_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, obj, flags, link = [root/name for name in ('mob.cpp', 'mob.o', 'flags', 'link')]
            for path in (source, obj, flags, link):
                path.write_text(path.name, encoding='utf-8')
            prior = {'mob_candidate': {'sha256': digest(source)}, 'objects': {str(obj): digest(obj)},
                     'flags_sha256': digest(flags), 'link_sha256': digest(link)}
            self.assertTrue(candidate_reusable(source, prior, 'mob', flags, link))
            for field in ('flags_sha256', 'link_sha256'):
                changed = copy.deepcopy(prior)
                changed[field] = 'changed'
                self.assertFalse(candidate_reusable(source, changed, 'mob', flags, link))
            for path in (source, obj):
                old = path.read_bytes()
                path.write_bytes(old+b'changed')
                self.assertFalse(candidate_reusable(source, prior, 'mob', flags, link))
                path.write_bytes(old)
            obj.unlink()
            self.assertFalse(candidate_reusable(source, prior, 'mob', flags, link))

    def test_runtime_attachment_preserves_real_constructor(self):
        before = '// prologue\n'
        mock = 'Client::Client() : Mob(0) {\n\tAI_Init();\n\n}\n\n'
        real = 'Client::Client(EQStreamInterface *ieqs) : Mob(0) {\n\tAI_Init();\n\n}\n\n'
        patched = patched_client(before + mock + real)
        self.assertTrue(patched.startswith(before))
        self.assertTrue(patched.endswith(real))
        self.assertEqual(patched.count('if (auto *stream = NightcapBalanceStream(this))'),1)
        with self.assertRaises(ValueError):
            patched_client(patched)
        with self.assertRaises(ValueError):
            patched_client(before + mock.replace('AI_Init();','AI_Init();\n\tChanged();') + real)

    def test_native_resource_verifier_distinguishes_aa_stages_and_policy(self):
        tables = {'base_data':[{'class':2,'level':50,'hp':1500,'hp_fac':5,'mana':1000,'mana_fac':2}]}
        build = {'profile':'test','tier':'Ascended','classes':[2],'level':50,'aa_stage':'100'}
        row = {'profile':'test','tier':'Ascended','aa_stage':'100','sta':100,'int':75,'wis':75,
               'heroic_hp':0,'heroic_mana':0,'item_hp':100,'item_mana':10,'item_percent_hp':0,
               'item_flat_hp':0,'aa_percent_hp':1000,'aa_flat_hp':50,'aa_mana':200,
               'hp':2365,'mana':1360}
        builds = [build | {'aa_policy':p} for p in ('balanced','durability_first')]
        report = {'builds':[row | {'aa_policy':p} for p in ('balanced','durability_first')]}
        self.assertEqual(verify(report,builds,tables), [])
        report['builds'][1]['aa_mana'] = 0
        self.assertEqual(len(verify(report,builds,tables)),1)
        report['builds'][1]['aa_policy'] = 'balanced'
        with self.assertRaises(ValueError):
            verify(report,builds,tables)

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

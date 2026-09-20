import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generate_spell_class_catalog import parse, generate


def spell(spell_id, levels):
    fields = ['0'] * 237
    fields[0] = str(spell_id)
    fields[104:120] = map(str, levels)
    return '^'.join(fields)+'\n'


class SpellCatalog(unittest.TestCase):
    def test_eligibility_excludes_zero_and_npc_only_spells(self):
        levels = [255]*16
        levels[12] = 17
        levels[0] = 0
        self.assertEqual(parse((spell(4,levels)+spell(5,[255]*16)).encode()),
                         [(4,tuple([255]*12+[17]+[255]*3))])

    def test_rejects_widened_or_unreviewed_source(self):
        with self.assertRaises(ValueError): generate(spell(4,[1]*16).encode())
        for raw in ('', '1^short', spell(4,[256]*16), spell(4,[1]*16)*2):
            with self.subTest(raw=raw[:20]), self.assertRaises(ValueError): parse(raw.encode())

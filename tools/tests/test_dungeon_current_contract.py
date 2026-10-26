"""The shipped guard must accept the current reviewed reward definitions."""
import json
from pathlib import Path
import re
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from dungeon_catalog import items
from dungeon_contract import predicate, render_header

class CurrentContract(unittest.TestCase):
    def test_runtime_item_predicates_match_current_compiler(self):
        contract=json.loads((ROOT/'docs/dungeons/runtime-contract.json').read_text())
        checks={c['label']:c for c in contract['content']}
        rows=[r['values'] for r in items()]
        for offset in range(0,len(rows),8):
            batch=rows[offset:offset+8]
            expected='SELECT COUNT(*) FROM `items` WHERE '+' OR '.join(predicate(r) for r in batch)
            self.assertEqual(checks[f'items/{offset}']['sql'],expected,
                             f'Item batch {offset} rejects the current reward compiler')

    def test_cache_guard_expects_loader_race_projection(self):
        # ApplyRacePolicy loads wearable player gear with every race; SQL keeps the mask.
        def races(**v):
            header=render_header([],[],[dict(values=dict(id=1,Name='x',idfile='IT63',lore='x',**v))])
            return re.search(r'i\.Races==(\d+)',header).group(1)
        self.assertEqual(races(classes=16,races=4095,slots=4),'65535')
        self.assertEqual(races(classes=16,races=4095,augtype=1),'65535')
        self.assertEqual(races(classes=16,races=4095),'4095')
        self.assertEqual(races(itemclass=1,classes=16,races=4095,slots=4),'4095')
        self.assertEqual(races(classes=0,races=4095,slots=4),'4095')
        shipped=(ROOT/'server-mods/code/common/dungeon_contract.h').read_text()
        self.assertIn('i.Races==65535',re.search(r'case 990510:[^\n]*',shipped).group(0))

if __name__=='__main__':unittest.main()

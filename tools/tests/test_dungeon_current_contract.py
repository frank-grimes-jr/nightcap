"""The shipped guard must accept the current reviewed reward definitions."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from dungeon_catalog import items
from dungeon_contract import predicate

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

if __name__=='__main__':unittest.main()

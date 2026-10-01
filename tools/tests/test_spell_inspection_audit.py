import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import client_gameplay_assets
from audit_spell_inspection import audit
from test_spell_class_catalog import spell


class SpellInspectionAudit(unittest.TestCase):
    def test_audits_every_class_and_separates_missing_spells(self):
        # A real shared spell, an AA-style marker and an NPC-only spell.
        source = (spell(11, [255, 1, 15]+[255]*13)
                  + spell(12, [254]+[255]*15)
                  + spell(13, [255]*16)).encode()
        scrolls = [dict(id=1, name='Shared', classes=65535, spell_id=11),
                   dict(id=2, name='AA', classes=1, spell_id=12),
                   dict(id=3, name='Unknown', classes=65535, spell_id=999),
                   dict(id=4, name='Blocked', classes=0, spell_id=11),
                   dict(id=5, name='NPC', classes=1, spell_id=13)]
        with patch.object(client_gameplay_assets, 'SOURCE_SHA256', hashlib.sha256(source).hexdigest()):
            result = audit(source, source, scrolls)
        self.assertEqual(result['packaged_spells'], 3)
        self.assertEqual(result['class_slots'], 48)
        self.assertEqual(result['affected_scroll_items'], 2)
        self.assertEqual(result['unusable_class_entries_removed'], 15)
        self.assertEqual(result['canonical_class_entries_restored'], 0)
        self.assertEqual(result['preserved_253_254_scroll_entries'], 1)
        self.assertEqual(result['scrolls_with_packaged_spell'], 4)
        self.assertEqual(result['affected_scrolls'][0]['after_mask'], 6)
        self.assertEqual(result['scrolls_without_packaged_spell'][0]['item_id'], 3)

    def test_rejects_class_drift_and_duplicate_items(self):
        source = spell(11, [255, 1, 15]+[255]*13).encode()
        widened = spell(11, [1]*16).encode()
        row = dict(id=1, name='Test', classes=6, spell_id=11)
        with patch.object(client_gameplay_assets, 'SOURCE_SHA256', hashlib.sha256(source).hexdigest()):
            with self.assertRaises(ValueError):
                audit(widened, source, [row])
            with self.assertRaises(ValueError):
                audit(source, source, [row, row])

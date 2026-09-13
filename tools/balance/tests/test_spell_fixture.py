"""Regression checks for dependencies the original spell-ID cutoff omitted."""
from pathlib import Path
import unittest

from builds import load_snapshot
from snapshot import validate_spell_references
from spell_content import npc_spell_profile


class SpellFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        snapshot, _ = load_snapshot(Path(__file__).parents[1] / 'fixtures/classic-20260912-v2.json.gz')
        cls.tables = snapshot['tables']
        cls.profiles = {n['id']: npc_spell_profile(n, cls.tables) for n in cls.tables['npc_types']}

    def test_all_boss_item_and_recourse_dependencies_close(self):
        validate_spell_references(self.tables)

    def test_vox_inherits_later_id_heals_with_entry_recasts(self):
        spells = {s['spell_id']:s for s in self.profiles[73057]['spells']}
        for sid, value, mana, cast, recast in ((13,7500,400,10000,10000),
                                               (1519,1380,355,3750,6000),
                                               (1518,483,167,1750,6000)):
            with self.subTest(spell=sid):
                s = spells[sid]
                self.assertEqual((s['effects'][0]['value'], s['mana_cost'], s['cast_ms'], s['recast_ms']),
                                 (value, mana, cast, recast))
        self.assertEqual({s['name'] for s in spells.values() if s['priority']==0}, {'Dragon Roar','Frosty Death'})

    def test_phinigel_uses_own_list_and_inherits_wizard_parent(self):
        profile = self.profiles[64001]
        self.assertEqual(profile['spell_list'],1346)
        self.assertEqual(len(profile['spells']),12)
        self.assertIn(2, {s['source_list'] for s in profile['spells']})
        self.assertIn('Ice Comet', {s['name'] for s in profile['spells']})

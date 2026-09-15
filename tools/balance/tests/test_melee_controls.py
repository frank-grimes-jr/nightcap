import gzip
import copy
import json
from pathlib import Path
import unittest

from melee_controls import verify, verify_case, verify_weapons

DOCS = Path(__file__).resolve().parents[3] / 'docs' / 'balance'


class MeleeControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads((DOCS/'melee-inputs.json').read_text())
        cls.evidence = json.loads(gzip.decompress((DOCS/'melee-encounters.json.gz').read_bytes()))

    def recorded(self, identity):
        case = next(c for c in self.matrix['cases'] if c['id'] == identity)
        report = next(r['report'] for r in self.evidence['runs'] if r['id'] == identity)
        return case, report

    def test_all_native_melee_cases_and_unchanged_caster_controls(self):
        previous = json.loads(gzip.decompress((DOCS/'gear-expanded-aa-encounters.json.gz').read_bytes()))
        result = verify(self.matrix, self.evidence, previous)
        self.assertEqual(len(result['summaries']), 60)
        self.assertEqual(len(result['unchanged_caster']), 6)

    def test_rejects_original_pilot_with_every_normal_swing_immune(self):
        case = json.loads((DOCS/'melee-pilot-inputs.json').read_text())['cases'][0]
        report = json.loads(gzip.decompress((DOCS/'melee-pilot-encounters.json.gz').read_bytes()))['runs'][0]['report']
        # The initial native pilot proves why observing *some* melee damage is
        # insufficient: its kicks land, but its equipped weapon never does.
        with self.assertRaisesRegex(ValueError, 'normal weapon'):
            verify_case(case, report)

    def test_repaired_native_pilot_has_weapon_damage_and_native_skill_timers(self):
        case, report = self.recorded('monk/shield/0/specials-True/32040/1729')
        summary = verify_case(case, report)
        self.assertGreater(summary['player_physical_damage_by_wire_type'][0], 0)
        self.assertGreater(summary['cooldown_starts'], 0)
        changed = copy.deepcopy(report)
        changed['encounter']['monk_actions']['requests'][0]['timer_before'] = 1
        with self.assertRaisesRegex(ValueError, 'combat-button'):
            verify_case(case, changed)
        changed = copy.deepcopy(report)
        changed['encounter']['attempts'][0]['spell'] = 732
        with self.assertRaisesRegex(ValueError, 'offensive'):
            verify_case(case, changed)

    def test_native_weapon_gate_preserves_level_race_and_nonheld_rejection(self):
        report = json.loads((DOCS/'melee-weapon-native.json').read_text())
        self.assertEqual(len(verify_weapons(report)), 15)
        for profile, item_id in (('war-clr-wiz', 662038), ('war-clr-mnk', 24587), ('war-clr-mnk', 5100)):
            changed = copy.deepcopy(report)
            row = next(r for b in changed['builds'] if b['profile'] == profile
                       for r in b['weapon_checks'] if r['id'] == item_id)
            row['native_weapon_damage'] = 1
            with self.subTest(profile=profile, item=item_id), self.assertRaises(ValueError):
                verify_weapons(changed)

    def test_native_all_aa_fight_can_avoid_every_boss_swing(self):
        case, report = self.recorded('monk/shield/all/specials-True/73057/1731')
        summary = verify_case(case, report)
        self.assertEqual(summary['result'], 'npc_death')
        self.assertEqual(summary['boss_positive_melee_events'], 0)
        changed = copy.deepcopy(report)
        npc = changed['encounter']['npc_entity_id']
        changed['encounter']['events'] = [e for e in changed['encounter']['events'] if not (
            e['type'] == 'damage' and e['source'] == npc and e['spell'] == 65535)]
        with self.assertRaisesRegex(ValueError, 'melee activity'):
            verify_case(case, changed)


if __name__ == '__main__':
    unittest.main()

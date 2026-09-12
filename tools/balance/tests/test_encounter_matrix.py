import copy
import unittest

from encounter_matrix import summarize, verify_matrix


class EncounterMatrixTests(unittest.TestCase):
    def fixture(self):
        player = dict(profile='war-clr-wiz', tier='Ascended/ring41', aa_stage='0',
                      aa_policy='common_free', aa_purchases=[{'rank_id': 100}], aa_spent=0,
                      hp=6000, mana=4800, haste=141)
        build = {k: player[k] for k in ('profile', 'tier', 'aa_stage', 'aa_policy')}
        build.update(aa_rank_ids=[100], gear_control='ring41')
        case = {'id': 'test', 'seed': 1729, 'input': {'builds': [build],
                'encounter': {'npc_id': 32040, 'duration_ms': 900000}}}
        state = {k: True for k in ('zone_loaded', 'npc_ai', 'npc_engaged', 'npc_has_spells',
                                   'can_combat', 'npc_can_attack', 'player_can_attack')}
        state.update(npc_hate_target=1, player_dead=False, player_zoning=False, player_destroying=False)
        first = dict(ms=0, player_hp=6000, player_mana=4800, npc_hp=32000, feared=False)
        last = dict(ms=10000, player_hp=5000, player_mana=1000, npc_hp=-1, feared=False)
        events = [dict(type='damage', source=s, spell=65535, damage=100) for s in (1, 2)]
        report = {'builds': [player], 'native_rng_seed': 1729, 'encounter': dict(
            npc_id=32040, player_entity_id=1, npc_entity_id=2, initial_state=state,
            trace=[first, last], events=events, result='npc_death', elapsed_ms=10000)}
        return case, report

    def test_short_kill_does_not_require_every_random_boss_spell(self):
        case, report = self.fixture()
        result = summarize(case, report)
        self.assertEqual(result['result'], 'npc_death')
        self.assertEqual(result['boss_casts'], {})

    def test_incomplete_trace_false_kill_or_no_combat_cannot_pass(self):
        case, original = self.fixture()
        mutations = [lambda r: r['encounter'].update(elapsed_ms=11000),
                     lambda r: r['encounter']['trace'][-1].update(npc_hp=10),
                     lambda r: r['encounter'].update(events=[]),
                     lambda r: r['encounter']['initial_state'].update(zone_loaded=False)]
        for mutation in mutations:
            report = copy.deepcopy(original)
            mutation(report)
            with self.assertRaises(ValueError):
                summarize(case, report)

    def test_wrong_seed_or_aa_allocation_is_rejected(self):
        case, report = self.fixture()
        report['native_rng_seed'] = 42
        with self.assertRaises(ValueError):
            summarize(case, report)
        report['native_rng_seed'] = 1729
        report['builds'][0]['aa_purchases'] = []
        with self.assertRaises(ValueError):
            summarize(case, report)

    def test_matrix_requires_every_case_and_summary_matches_trace(self):
        case, report = self.fixture()
        matrix = {'cases': [case]}
        run = {'id': case['id'], 'report': report, 'summary': summarize(case, report)}
        self.assertEqual(len(verify_matrix(matrix, {'runs': [run]})), 1)
        with self.assertRaises(ValueError):
            verify_matrix(matrix, {'runs': []})
        run['summary']['elapsed_ms'] = 1
        with self.assertRaises(ValueError):
            verify_matrix(matrix, {'runs': [run]})


if __name__ == '__main__':
    unittest.main()

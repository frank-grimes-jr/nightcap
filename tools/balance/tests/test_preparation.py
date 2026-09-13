import copy
import gzip
import json
from pathlib import Path
import unittest

from preparation_controls import prepare, verify_preparation
from active_aa_controls import verify_encounters
from encounter_matrix import summarize
import test_encounter_matrix


class PreparationTests(unittest.TestCase):
    def fixture(self):
        case, report = test_encounter_matrix.EncounterMatrixTests().fixture()
        wanted = {'spell_ids': [67], 'recover': True, 'max_duration_ms': 900000}
        case['input']['encounter']['preparation'] = wanted
        state = dict(hp=6000, max_hp=6000, mana=4800, max_mana=4800,
                     mr=25, fr=25, cr=25, buffs=[], casting=0, sitting=False)
        cost = state | {'mana': 4600, 'max_hp': 6150,
                        'buffs': [{'spell': 67, 'ticks': 999999, 'slot': 0, 'hits': 0}]}
        final = cost | {'hp': 6150, 'mana': 4800}
        preparation = dict(input=wanted, elapsed_ms=120000, final_state=final,
                           trace=[state | {'ms': 0}, cost | {'ms': 15000, 'sitting': True}, final | {'ms': 120000}],
                           actions=[dict(ms=50, spell=67, accepted=True, completed_ms=12100,
                                         completed_state=cost)])
        report['encounter'].update(preparation=preparation, combat_start_ms=120000)
        report['encounter']['trace'][0]['player_hp'] = 6150
        return case, report

    def test_prepared_native_resources_replace_unbuffed_start(self):
        case, report = self.fixture()
        verify_preparation(case, report)
        self.assertEqual(summarize(case, report)['initial_hp'], 6150)

    def test_missing_preparation_cannot_pass_as_prepared(self):
        case, report = test_encounter_matrix.EncounterMatrixTests().fixture()
        case['input']['encounter']['preparation'] = {'spell_ids': [67]}
        with self.assertRaises(ValueError):
            summarize(case, report)

    def test_mana_refill_clock_reset_missing_buff_and_unfinished_cast_fail(self):
        mutations = [lambda r: r['encounter']['trace'][0].update(player_mana=4799),
                     lambda r: r['encounter'].update(combat_start_ms=0),
                     lambda r: r['encounter']['preparation']['final_state'].update(buffs=[]),
                     lambda r: r['encounter']['preparation']['actions'][0].update(completed_ms=120001)]
        for mutation in mutations:
            case, report = self.fixture()
            mutation(report)
            with self.assertRaises(ValueError):
                verify_preparation(case, report)

    def test_prepared_matrix_preserves_all_aa_budgets_and_gear(self):
        docs = Path(__file__).resolve().parents[3] / 'docs' / 'balance'
        source = json.loads((docs / 'duration-encounter-inputs.json').read_text())
        matrix = prepare(source)
        self.assertEqual(len(matrix['cases']), 30)
        self.assertEqual({c['input']['builds'][0]['aa_stage'] for c in matrix['cases']}, {'0','100','200','500','all'})
        originals = {c['id']: c for c in source['cases']}
        for c in matrix['cases']:
            self.assertEqual(c['input']['builds'], originals[c['id'].removesuffix('-prepared')]['input']['builds'])

    def test_recorded_native_preparation_and_boss_runs(self):
        docs = Path(__file__).resolve().parents[3] / 'docs' / 'balance'
        matrix = json.loads((docs / 'preparation-inputs.json').read_text())
        evidence = json.loads(gzip.decompress((docs / 'preparation-encounters.json.gz').read_bytes()))
        self.assertEqual(len(verify_encounters(matrix, evidence)), 30)
        for run in evidence['runs']:
            self.assertEqual(run['summary']['initial_hp'] - run['report']['builds'][0]['hp'], 925)

    def test_appearance_only_sitting_regression_is_rejected(self):
        case, report = self.fixture()
        for state in report['encounter']['preparation']['trace']:
            state['sitting'] = False
        with self.assertRaisesRegex(ValueError, 'native client sitting state'):
            verify_preparation(case, report)


if __name__ == '__main__':
    unittest.main()

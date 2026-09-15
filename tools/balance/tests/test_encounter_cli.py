import unittest

from encounter_cli import distribution, run_trials


class EncounterReportTests(unittest.TestCase):
    def test_conditional_times_do_not_mix_deaths_into_kill_times(self):
        scenario = {'schema_version':1, 'status':'diagnostic',
                    'assumptions':['Analytically solvable timing control'],
                    'player':{'name':'player','hp':100,'mana':100,
                              'actions':[{'name':'nuke','effect':'damage','amount':25,
                                          'mana':10,'cast_ms':1000,'recovery_ms':1000}]},
                    'enemy':{'name':'dummy','hp':100}, 'duration_ms':10000}
        result = run_trials(scenario, 10, 123)
        self.assertEqual(result['outcomes'], {'kill':10,'death':0,'timeout':0})
        self.assertEqual(result['kill_time_ms']['median'], 7000)
        self.assertIsNone(result['death_time_ms'])
        self.assertEqual(result['remaining_player_mana']['mean'], 60)

    def test_missing_scope_or_invalid_schema_is_rejected(self):
        with self.assertRaises(ValueError):
            run_trials({'schema_version':1,'status':'diagnostic'}, 10, 1)
        with self.assertRaises(ValueError):
            run_trials({'schema_version':1,'status':'certified'}, 10, 1)

    def test_empty_and_single_observation_distributions(self):
        self.assertIsNone(distribution([]))
        self.assertEqual(distribution([35])['p90'], 35)

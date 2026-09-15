import unittest

from encounter import Action, Actor, simulate


def player(**changes):
    return Actor(**({'name': 'player', 'hp': 100, 'mana': 100,
                    'actions': (Action('nuke', 'damage', 25, 10, 1000, 0, 1000),)} | changes))


class EncounterTests(unittest.TestCase):
    def test_native_partial_amount_is_not_resisted_twice_and_cost_resolves_at_finish(self):
        a = Action('native','damage',0,mana=20,cast_ms=2000,recovery_ms=1000,
                   resolved_outcomes=((1,30,5,500,50),))
        result = simulate(player(actions=(a,)),Actor('dummy',60),seed=1,duration_ms=5000)
        self.assertEqual((result['outcome'],result['elapsed_ms']),('kill',2000))
        self.assertEqual((result['player']['mana_spent'],result['player']['damage']),(10,60))

    def test_native_raw_mana_gate_is_not_replaced_by_discounted_completion_cost(self):
        a = Action('native','damage',0,mana=20,cast_ms=1000,
                   resolved_outcomes=((1,30,1,1000,100),))
        result = simulate(player(mana=19,actions=(a,)),Actor('dummy',30),seed=1,duration_ms=5000)
        self.assertEqual((result['player']['casts'],result['enemy']['hp']),(0,30))
        self.assertGreater(result['player']['oom_checks'],0)

    def test_interrupted_native_cast_spends_no_completion_mana(self):
        a = Action('native','damage',0,mana=20,cast_ms=1000,
                   resolved_outcomes=((1,30,5,1000,100),))
        fear = Action('fear','fear',0,cast_ms=500,recast_ms=100000,duration_ms=5000)
        result = simulate(player(actions=(a,)),Actor('enemy',100,actions=(fear,)),seed=1,duration_ms=2000)
        self.assertEqual((result['player']['interrupts'],result['player']['mana_spent']),(1,0))

    def test_invalid_or_double_scaled_native_outcomes_fail(self):
        for data in ({'amount':1}, {'outcomes':((1,50),)},
                     {'resolved_outcomes':((1,10,5,1000,0),)},
                     {'resolved_outcomes':((1,10,5,-1,100),)}):
            args = {'name':'native','effect':'damage','amount':0,'cast_ms':1000,
                    'resolved_outcomes':((1,10,5,1000,100),)} | data
            with self.assertRaises(ValueError):
                Action(**args)

    def test_known_kill_time_and_mana_spending(self):
        result = simulate(player(), Actor('dummy', 100), seed=1, duration_ms=10000)
        self.assertEqual(result['outcome'], 'kill')
        self.assertEqual(result['elapsed_ms'], 7000)
        self.assertEqual(result['player']['mana'], 60)
        self.assertEqual(result['player']['damage'], 100)

    def test_mana_exhaustion_stops_casts_but_regen_can_resume(self):
        no_regen = simulate(player(mana=20), Actor('dummy', 100), seed=1, duration_ms=20000)
        self.assertEqual(no_regen['outcome'], 'timeout')
        self.assertEqual(no_regen['enemy']['hp'], 50)
        self.assertGreater(no_regen['player']['oom_checks'], 0)
        regen = simulate(player(mana=20, mana_regen=10), Actor('dummy', 100), seed=1, duration_ms=20000)
        self.assertEqual(regen['outcome'], 'kill')
        self.assertEqual(regen['elapsed_ms'], 13000)

    def test_death_cancels_same_time_heal_conservatively(self):
        p = player(hp=10, actions=(Action('heal', 'heal', 100, 10, 1000, 0, 1000, hp_below=1000),))
        e = Actor('enemy', 100, actions=(Action('blast', 'damage', 10, cast_ms=1000),))
        result = simulate(p, e, seed=1, duration_ms=3000)
        self.assertEqual(result['outcome'], 'death')
        self.assertEqual(result['player']['healing'], 0)

    def test_overhealing_is_not_counted_as_effective_healing(self):
        p = player(actions=(Action('heal', 'heal', 100, 10, 0, 1000, 0, hp_below=1000),))
        result = simulate(p, Actor('dummy', 100), seed=1, duration_ms=1000)
        self.assertEqual(result['player']['healing'], 0)
        self.assertEqual(result['player']['overheal'], 200)

    def test_enemy_healing_changes_a_kill_into_a_timeout(self):
        enemy = Actor('healer', 100, actions=(Action('heal', 'heal', 30,
                       recast_ms=2000, hp_below=800),))
        result = simulate(player(), enemy, seed=1, duration_ms=10000)
        self.assertEqual(result['outcome'], 'timeout')
        self.assertEqual(result['enemy']['hp'], 100)
        self.assertEqual(result['enemy']['healing'], 125)

    def test_fear_interrupts_cast_and_no_completion_mana_is_spent(self):
        fear = Action('roar', 'fear', 0, cast_ms=500, recast_ms=100000, duration_ms=2000)
        result = simulate(player(), Actor('enemy', 100, actions=(fear,)), seed=1, duration_ms=4000)
        self.assertEqual(result['player']['interrupts'], 1)
        self.assertEqual(result['player']['mana_spent'], 10)
        self.assertEqual(result['enemy']['hp'], 75)

    def test_fear_immunity(self):
        fear = Action('roar', 'fear', 0, cast_ms=500, recast_ms=100000, duration_ms=5000)
        result = simulate(player(fear_immune=True), Actor('enemy', 100, actions=(fear,)), seed=1, duration_ms=2000)
        self.assertEqual(result['player']['interrupts'], 0)
        self.assertEqual(result['enemy']['hp'], 75)

    def test_dot_ticks_and_refresh_replace_without_duplicate_stack(self):
        dot = Action('dot', 'dot', 10, cast_ms=0, recast_ms=100000, duration_ms=12000)
        result = simulate(player(actions=(dot,)), Actor('dummy', 100), seed=1, duration_ms=18000)
        self.assertEqual(result['enemy']['hp'], 80)
        refreshed = Action('dot', 'dot', 10, cast_ms=0, recast_ms=3000, duration_ms=12000)
        result = simulate(player(actions=(refreshed,)), Actor('dummy', 100), seed=1, duration_ms=18000)
        self.assertEqual(result['enemy']['hp'], 70)

    def test_full_resists_spend_mana(self):
        resisted = Action('nuke', 'damage', 25, 10, 1000, 0, 1000, outcomes=((1, 0),))
        result = simulate(player(actions=(resisted,)), Actor('dummy', 100), seed=1, duration_ms=2000)
        self.assertEqual(result['enemy']['hp'], 100)
        self.assertEqual(result['player']['mana_spent'], 10)
        self.assertEqual(result['player']['resists'], 1)

    def test_seed_reproduces_full_trace(self):
        a = Action('nuke', 'damage', 25, 10, 100, 0, 100, outcomes=((1, 0), (1, 50), (1, 100)))
        one = simulate(player(actions=(a,)), Actor('dummy', 100), seed=234, duration_ms=10000, trace=True)
        two = simulate(player(actions=(a,)), Actor('dummy', 100), seed=234, duration_ms=10000, trace=True)
        self.assertEqual(one, two)

    def test_zero_time_repeat_and_invalid_effect_are_rejected(self):
        with self.assertRaises(ValueError):
            Action('loop', 'damage', 1)
        with self.assertRaises(ValueError):
            Action('unknown', 'proc', 1, recast_ms=1)

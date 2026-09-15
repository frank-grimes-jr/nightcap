import unittest

from npc_casting import choose_engaged_spell


class LowRoll:
    def randint(self, low, high):
        return low


def spell(sid, kind=1, **changes):
    return {'spell_id':sid,'type':kind,'priority':1,'mana_cost':10,
            'min_hp_percent':0,'max_hp_percent':0} | changes


class NpcCastingTests(unittest.TestCase):
    def choose(self, spells, **changes):
        inputs={'now':3000,'hp':400,'max_hp':1000,'mana':100,'max_mana':100,
                'cooldowns':{},'active_self':set(),'target_rooted':False,
                'target_feared':False,'target_dispellable':False,'rng':LowRoll()}
        return choose_engaged_spell(spells, **(inputs|changes))

    def test_innates_precede_healing(self):
        result=self.choose([spell(13,2),spell(981,priority=0,mana_cost=0)])
        self.assertEqual(result,(981,0))

    def test_healing_precedes_regular_nukes_when_innate_on_cooldown(self):
        result=self.choose([spell(13,2),spell(732),spell(981,priority=0)],cooldowns={981:10000})
        self.assertEqual(result,(13,10))

    def test_hp_threshold_uses_integer_percent(self):
        self.assertEqual(self.choose([spell(13,2)],hp=509),(13,10))
        self.assertIsNone(self.choose([spell(13,2)],hp=510))

    def test_low_mana_blocks_nukes_but_not_affordable_heals(self):
        self.assertEqual(self.choose([spell(13,2,mana_cost=5),spell(732,mana_cost=5)],mana=9),(13,5))
        self.assertIsNone(self.choose([spell(732,mana_cost=5)],mana=9))

    def test_full_mana_npc_exception_and_zero_mana_ratio(self):
        self.assertEqual(self.choose([spell(861,priority=0,mana_cost=50)],mana=0,max_mana=0),(861,0))

    def test_existing_root_or_buff_avoids_recasting(self):
        self.assertIsNone(self.choose([spell(230,4)],target_rooted=True))
        self.assertIsNone(self.choose([spell(1534,1024)],active_self={1534}))

    def test_idle_buff_not_cast_during_engaged_check(self):
        self.assertIsNone(self.choose([spell(20,8)]))

    def test_unsupported_engaged_type_fails(self):
        with self.assertRaises(ValueError):
            self.choose([spell(99,64)])

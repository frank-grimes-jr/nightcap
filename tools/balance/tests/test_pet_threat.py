import copy
import json
from pathlib import Path
import unittest

from pet_threat_controls import prepare,verify
from pet_support_controls import gems_for,verify_threat


class PetThreatMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((Path(__file__).resolve().parents[3]/'docs/balance/gear-source-inputs.json').read_text(encoding='utf-8'))

    def test_each_pet_allocation_has_both_matched_strategies(self):
        matrix = prepare(self.original,'0'*64)
        self.assertEqual(len(matrix['cases']),72)
        self.assertEqual(matrix['allocations'],self.original['allocations'])
        original = {c['id']:c for c in self.original['cases']}
        for case in matrix['cases']:
            expected = original[case['paired_gear_case_id']]['input']
            actual = copy.deepcopy(case['input'])
            combat = actual['pet_probe']['combat']
            self.assertIn(combat.pop('threat_policy'),('no_slow_control','feign_on_aggro'))
            self.assertEqual(combat.pop('feign_hold_ms'),4000)
            self.assertEqual(actual,expected)

    def test_pilot_covers_zero_and_both_legal_maxima_without_changing_gear(self):
        matrix = prepare(self.original,'0'*64,True)
        self.assertEqual(len(matrix['cases']),6)
        self.assertEqual({c['input']['builds'][0]['aa_budget'] for c in matrix['cases']},{0,165,306})
        self.assertTrue(all(c['seed']==1729 and c['input']['pet_probe']['combat']['npc_id']==32040 for c in matrix['cases']))

    def test_unmatched_duration_or_power_change_is_rejected(self):
        matrix = prepare(self.original,'0'*64)
        matrix['cases'][0]['input']['builds'][0]['aa_budget'] += 1
        with self.assertRaisesRegex(ValueError,'matched combat'):
            verify(matrix,{},self.original,{})

    def test_escape_pilot_preserves_the_same_three_progression_stages(self):
        matrix=prepare(self.original,'0'*64,True,True)
        self.assertEqual(len(matrix['cases']),3)
        self.assertEqual({c['input']['builds'][0]['aa_budget'] for c in matrix['cases']},{0,165,306})
        self.assertTrue(all(c['input']['pet_probe']['combat']['threat_policy']=='feign_escape'
                            and c['input']['pet_probe']['combat']['feign_hold_ms']==1000 for c in matrix['cases']))


class PetThreatPolicyTests(unittest.TestCase):
    def fixture(self):
        return {'input':{'threat_policy':'feign_on_aggro','feign_hold_ms':4000},'player_id':1,
                'trace':[{'ms':20000,'owner_feigned':False}],
                'threat_control':{'policy':'feign_on_aggro','spell':366,'spell_min_level':16,
                                  'feign_kills_pet':False,'hold_ms':4000,'stand_requests':[]},
                'owner_actions':[{'spell':366,'target':1,'boss_target_before':1,'owner_feigned_before':False,
                                  'feign_ready_before':True,'living_pet_before':True,'reason':'aggro_feign'}]}

    def test_only_slow_gem_is_replaced_for_both_strategies(self):
        for boss in (32040,73057):
            old=gems_for(boss)
            for policy in ('no_slow_control','feign_on_aggro','feign_escape'):
                new=gems_for(boss,policy)
                self.assertEqual(len(set(new)),8)
                self.assertEqual(new[:1]+new[2:],old[:1]+old[2:])
                self.assertEqual((old[1],new[1]),(507,366))

    def test_feign_requires_native_timer_aggro_and_living_pet(self):
        verify_threat(self.fixture())
        for key,value in (('feign_ready_before',False),('living_pet_before',False),
                          ('boss_target_before',5),('target',5),('owner_feigned_before',True)):
            c=self.fixture();c['owner_actions'][0][key]=value
            with self.assertRaises(ValueError):verify_threat(c)

    def test_no_slow_control_cannot_cast_feign_or_slow(self):
        for spell in (366,507):
            c=self.fixture();c['input']['threat_policy']='no_slow_control';c['threat_control']['policy']='no_slow_control'
            c['owner_actions'][0]['spell']=spell
            with self.assertRaises(ValueError):verify_threat(c)

    def test_native_standing_requires_hold_time_and_consumed_packet(self):
        c=self.fixture()
        e={'ms':6000,'held_ms':4000,'feigned_before':True,'pending_packets_after':0,'feigned_after':False}
        c['threat_control']['stand_requests']=[e]
        verify_threat(c)
        for key,value in (('held_ms',3999),('pending_packets_after',1),('ms',20001)):
            bad=copy.deepcopy(c);bad['threat_control']['stand_requests'][0][key]=value
            with self.assertRaises(ValueError):verify_threat(bad)

    def test_escape_requires_healthy_surviving_pets_and_low_owner_hp(self):
        c=self.fixture();c['input']['threat_policy']='feign_escape';c['threat_control']['policy']='feign_escape'
        c['owner_actions'][0].update(owner_hp_percent_before=40,minimum_living_pet_hp_percent_before=80)
        verify_threat(c)
        for key,value in (('owner_hp_percent_before',40.1),('minimum_living_pet_hp_percent_before',79.9)):
            bad=copy.deepcopy(c);bad['owner_actions'][0][key]=value
            with self.assertRaises(ValueError):verify_threat(bad)


if __name__ == '__main__':
    unittest.main()

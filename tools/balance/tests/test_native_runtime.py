import copy
import unittest
import json
from pathlib import Path

from verify_native_runtime import verify
from verify_native_encounter import verify as verify_encounter


class NativeRuntimeVerificationTests(unittest.TestCase):
    def fixtures(self):
        build = {'profile':'war-clr-wiz','tier':'Ascended','aa_stage':'0',
                 'aa_policy':'balanced','aa_spent':0,'mana':4707}
        direct = {'builds':[build | {'spell_probes':[{'spell_id':9,'outcomes':[
            {'amount':2100,'mana':180,'cast_ms':3500}]}]}]}
        def state(ms,hp,mana,casting=0):
            return {'ms':ms,'hp':hp,'mana':mana,'casting':casting}
        report = {'builds':[build],'runtime_probe':{
            'clock':{'at_1000_persistent':True,'at_1000_timer':False,
                     'at_1001_timer':True,'at_2000_persistent':True,
                     'seconds':1789171201,'time':1789171201},
            'connected':True,'client_version_bit':64,'cast_accepted':True,'outgoing_packets':21,
            'trace':[state(2000,2961,4707),state(2000,2961,4707,9),state(5500,2961,4707,9),
                     state(5550,5061,4527),state(6050,5070,4533),state(12000,5070,4533)],
            'damage_control':{'client_finished_loading':True,'hp_before':5070,'hp_after':4970,'requested_damage':100}}}
        return report,direct

    def test_native_clock_cast_and_damage_control(self):
        report,direct = self.fixtures()
        self.assertTrue(verify(report,direct)['passed'])

    def test_rejects_idle_immune_or_wrong_cast_accounting(self):
        report,direct = self.fixtures()
        for area,index,field,value in [
            ('trace',3,'mana',4528),('trace',3,'hp',5060),('trace',3,'ms',5500),
            ('trace',2,'mana',4527),('trace',5,'hp',5061),
            ('damage_control',None,'hp_after',5070),
            ('damage_control',None,'client_finished_loading',False),
            ('clock',None,'at_1000_timer',True),
        ]:
            changed = copy.deepcopy(report)
            target = changed['runtime_probe'][area]
            if index is not None:
                target = target[index]
            target[field] = value
            with self.subTest(area=area,field=field,value=value), self.assertRaises(AssertionError):
                verify(changed,direct)

    def test_requires_matching_deterministic_native_reference(self):
        report,direct = self.fixtures()
        direct['builds'][0]['aa_stage'] = 'all'
        with self.assertRaises(ValueError):
            verify(report,direct)

    def test_encounter_control_rejects_idle_target_regression(self):
        root = Path(__file__).parents[3]/'docs/balance'
        report = json.loads((root/'native-encounter-nagafen-prototype.json').read_text())
        self.assertTrue(verify_encounter(report)['passed'])
        for key,value in [('zone_loaded',False),('npc_hate_target',0)]:
            changed = copy.deepcopy(report)
            changed['encounter']['initial_state'][key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError):
                verify_encounter(changed)
        report['encounter']['events'] = [e for e in report['encounter']['events'] if e['source'] != 2]
        with self.assertRaises(AssertionError):
            verify_encounter(report)

    def test_weapon_control_cannot_be_satisfied_by_stat_stick(self):
        root = Path(__file__).parents[3]/'docs/balance'
        weapon = json.loads((root/'native-encounter-melee-control.json').read_text())
        self.assertTrue(verify_encounter(weapon,require_player_melee=True)['passed'])
        caster = json.loads((root/'native-encounter-nagafen-prototype.json').read_text())
        with self.assertRaises(AssertionError):
            verify_encounter(caster,require_player_melee=True)


if __name__ == '__main__':
    unittest.main()

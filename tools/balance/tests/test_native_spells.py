import copy
import unittest

from native_spell_actions import action, summarize, verify
from native_spell_inputs import inputs


def probe():
    return {'spell_id':732,'name':'Ice Comet','npc_id':32040,'effect':'damage',
            'samples':4,'raw_mana':100,'raw_cast_ms':2000,'caster_hp':100,'caster_mana':100,
            'outcomes':[{'count':1,'amount':0,'mana':80,'cast_ms':1500,'landed_percent':0},
                        {'count':3,'amount':200,'mana':60,'cast_ms':1000,'landed_percent':50}]}


class NativeSpellTests(unittest.TestCase):
    def test_joint_samples_and_raw_start_gate_survive_adapter(self):
        a = action(probe(),recast_ms=1500,recovery_ms=1500)
        self.assertEqual(a.mana,100)
        self.assertEqual(a.resolved_outcomes,((1,0,80,1500,0),(3,200,60,1000,50)))
        s = summarize(probe())
        self.assertEqual(s['amount']['mean'],150)
        self.assertEqual(s['amount']['mean_standard_error'],50)
        self.assertEqual(s['mana']['mean'],65)
        self.assertEqual(s['full_resist_fraction'],0.25)

    def test_bad_counts_and_duplicate_bins_fail(self):
        p = probe()
        for bad in (p | {'samples':5}, p | {'outcomes':p['outcomes']*2,'samples':8}):
            with self.assertRaises(ValueError):
                summarize(bad)

    def test_coverage_and_full_resource_state_are_required(self):
        b = {'profile':'test','tier':'Ascended','aa_stage':'0','aa_policy':'common_free',
             'spell_probes':[{'spell_id':732,'npc_id':32040}]}
        i = {'builds':[b],'spell_samples':4}
        r = {'native_rng_seed':123,'native_seed_hook_calls':1,
             'builds':[b | {'hp':100,'mana':100,'spell_probes':[probe()]}]}
        self.assertEqual(len(verify(i,r)),1)
        for change in ('missing','resource','seed'):
            bad = copy.deepcopy(r)
            if change=='missing': bad['builds'][0]['spell_probes']=[]
            if change=='resource': bad['builds'][0]['spell_probes'][0]['caster_hp']=0
            if change=='seed': bad['native_seed_hook_calls']=0
            with self.assertRaises(ValueError):
                verify(i,bad)

    def test_input_generator_preserves_aa_allocation_and_targets_both_bosses(self):
        b = {'profile':'war-clr-wiz','aa_rank_ids':[1,2,3]}
        result = inputs({'builds':[b]},100)
        self.assertEqual(result['builds'][0]['aa_rank_ids'],[1,2,3])
        self.assertEqual(len(result['builds'][0]['spell_probes']),6)
        for n in (0,100001):
            with self.assertRaises(ValueError): inputs({'builds':[b]},n)

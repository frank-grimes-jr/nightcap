import unittest

from spell_content import active_npc_entries, resolved_effects, npc_spell_profile


def entry(spell, owner, **changes):
    return {'id':spell+owner*100,'spellid':spell,'npc_spells_id':owner,
            'minlevel':1,'maxlevel':255,'min_expansion':-1,'max_expansion':-1,
            'content_flags':None,'content_flags_disabled':None,'priority':1} | changes


class SpellContentTests(unittest.TestCase):
    def test_zero_list_means_no_spells(self):
        self.assertEqual(active_npc_entries(0,55,{}),[])

    def test_child_shadows_parent_before_level_filter(self):
        tables={'npc_spells':[{'id':1,'parent_list':0},{'id':2,'parent_list':1}],
                'npc_spells_entries':[entry(5,1),entry(5,2,minlevel=60),entry(6,1)]}
        self.assertEqual([r['spellid'] for r in active_npc_entries(2,55,tables)], [6])

    def test_flags_expansion_and_missing_parent(self):
        tables={'npc_spells':[{'id':1,'parent_list':0}],
                'npc_spells_entries':[entry(5,1,content_flags='later'),entry(6,1,min_expansion=1),entry(7,1)]}
        self.assertEqual([r['spellid'] for r in active_npc_entries(1,55,tables)], [7])
        tables['npc_spells'][0]['parent_list']=9
        with self.assertRaises(ValueError):
            active_npc_entries(1,55,tables)

    def test_spacers_are_ignored_but_stacking_rules_are_retained(self):
        spell={'buffdurationformula':0,'buffduration':0}
        for i in range(1,13):
            spell.update({f'effectid{i}':254,f'effect_base_value{i}':0,f'formula{i}':100,f'max{i}':0})
        spell.update(effectid1=10,effectid2=0,effect_base_value2=-700,formula2=6,max2=808,
                     effectid3=148,effect_base_value3=1)
        effects=resolved_effects(spell,50)
        self.assertEqual([(e['effect_id'],e['value']) for e in effects],[(0,-808),(148,1)])

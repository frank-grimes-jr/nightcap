"""Execute the actual AA bonus arms for newly restored Wizard/Druid access."""
import unittest
import all_class_aa as aa
from test_pet_equipment import compile_run
from test_gameplay_policies import function


class AllClassNative(unittest.TestCase):
    def test_wizard_crit_uses_maximum_in_both_orders_and_boon_adds_hot_only(self):
        native=function((aa.ROOT/'server-mods/code/zone/bonuses.cpp').read_text(),
                        'void Mob::ApplyAABonuses(')
        arms=[]
        for name in ('CriticalSpellChance','CriticalHealOverTime'):
            start=native.index('case SpellEffect::'+name+':')
            end=native.index('\n\t\tcase SpellEffect::',start+1)
            arms.append(native[start:end])
        config,tables,old,rows,ledger=aa.prepare()
        caps={397:9,398:6,389:6}
        cases=[]
        for aid,cap in caps.items():
            rid=next(r['rank_id'] for r in rows if r['ability_id']==aid and r['ordinal']==cap)
            effects=[e for e in tables['aa_rank_effects'] if e['rank_id']==rid]
            self.assertEqual(len(effects),1)
            e=effects[0]
            self.assertEqual(e['effect_id'],319 if aid==389 else 294)
            cases.append(f'const Effect e{aid}{{{e["effect_id"]},{e["base1"]},{e["base2"]}}};')
        fixture=r'''
#include <cassert>
#include <algorithm>
namespace SpellEffect {enum {CriticalSpellChance=294,CriticalHealOverTime=319};}
struct Bonus {int CriticalSpellChance=0,SpellCritDmgIncNoStack=0,CriticalHealOverTime=0;};
struct Effect {int id,base,limit;};
void apply(Bonus&b,Effect e){auto*newbon=&b;int base_value=e.base,limit_value=e.limit;switch(e.id){
// ARMS
}}
int main(){
// ROWS
Bonus a,b;apply(a,e397);apply(a,e398);apply(b,e398);apply(b,e397);
assert(a.SpellCritDmgIncNoStack==b.SpellCritDmgIncNoStack);
assert(a.SpellCritDmgIncNoStack==std::max(e397.limit,e398.limit));
assert(a.CriticalSpellChance==0);
Bonus released;apply(released,e398);assert(released.SpellCritDmgIncNoStack==e398.limit);
Bonus druid;apply(druid,e389);assert(druid.CriticalHealOverTime==16);
assert(druid.CriticalSpellChance==0 && druid.SpellCritDmgIncNoStack==0);
}
'''
        compile_run(fixture.replace('// ARMS','\n'.join(arms)).replace('// ROWS','\n'.join(cases)))


if __name__=='__main__':unittest.main()

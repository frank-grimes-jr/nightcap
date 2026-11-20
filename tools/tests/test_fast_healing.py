"""Exercise actual healing methods with deterministic boundary dependencies."""
from pathlib import Path
import unittest
from test_pet_equipment import compile_run, ROOT
from test_gameplay_policies import function

class FastHealing(unittest.TestCase):
    def test_floor_and_preservation(self):
        source=(ROOT/'server-mods/code/zone/effects.cpp').read_text()
        headers='\n'.join('#include "'+(ROOT/p).as_posix()+'"' for p in (
            'server-mods/code/common/nightcap_spell_scaling.h',
            'server-mods/code/zone/nightcap_heroic_cast.h'))
        fixture=Path(__file__).with_name('thj_spell_fixture.h').read_text().replace('spells[6000]', 'spells[65536]')
        bodies='\n'.join(function(source,s) for s in (
            'int64 Mob::GetActSpellHealing(', 'int64 Mob::GetExtraSpellAmt(',
            'int64 Mob::GetNightcapHeroicSpellValue('))
        compile_run(headers+'\n'+fixture+bodies+CASES)

CASES=r'''
int main(){try{
 rules["Spells:FlatItemExtraSpellAmt"]=1;rules["Spells:ItemExtraSpellAmtCalcAsPercent"]=1;
 rules["Spells:IgnoreSpellDmgLvlRestriction"]=1;rules["Spells:NightcapTHJBehaviors"]=1;
 Mob c,t;
 auto heal=[&](int id,int base,bool original=true,bool tick=false){return NightcapHeroicCast::Cast::Deliver(original,[&]{return c.GetActSpellHealing(id,base,&t,tick);});};
 for(int id:{200,17}){
  spells[id].cast_time=id==200?1500:2000;spells[id].good_effect=true;
  for(int ha:{0,1,93,100,250,487,750})for(int base:{10,20,35,65,100,150}){
   c.ha=ha;expect("original quick heal floor",heal(id,base),base+std::max(ha,base*ha/100));
   expect("proc/click/skill stays percentage",heal(id,base,false),base+base*ha/100);
   expect("tick stays percentage",heal(id,base,true,true),base+base*ha/100);
  }
  c.ha=100;spells[id].no_heal_damage_item_mod=true;
  expect("item opt out",heal(id,20),20);spells[id].no_heal_damage_item_mod=false;
  rules["Spells:IgnoreSpellDmgLvlRestriction"]=0;expect("level restriction",heal(id,20),20);
  rules["Spells:IgnoreSpellDmgLvlRestriction"]=1;
  c.kind=Mob::NPC;expect("NPC unchanged",heal(id,20),40);c.kind=Mob::Client;
  spells[id].buff_duration=5;expect("duration hybrid unchanged",heal(id,20),20);spells[id].buff_duration=0;
  rules["Spells:NightcapTHJBehaviors"]=0;expect("disabled unchanged",heal(id,20),40);
  rules["Spells:NightcapTHJBehaviors"]=1;
  c.aabonuses.CriticalHealChance=100;expect("crit once",heal(id,20),240);
  rules["Spells:NightcapHeroicSpellScaling"]=1;c.hwis=100;expect("heroic once after crit",heal(id,20),264);
  c.hwis=0;c.aabonuses.CriticalHealChance=0;rules["Spells:NightcapHeroicSpellScaling"]=0;
 }
 for(int ha:{0,93,250,487,750})for(int id:{12,15,9,13502,13503,13504,16139,16140,16141,44380,60000}){
  c.ha=ha;expect("other and custom spells unchanged",heal(id,350),350+350*ha/100);
  expect("small custom heal unchanged",heal(id,20),20+20*ha/100);
 }
 std::cout<<checks<<" checks passed\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
'''
if __name__=='__main__':unittest.main()



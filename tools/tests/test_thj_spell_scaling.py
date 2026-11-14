"""Compile actual Mob spell methods; deterministic boundary fakes, not encounters."""
from pathlib import Path
import unittest
from test_pet_equipment import compile_run,ROOT
from test_gameplay_policies import function

class SpellParity(unittest.TestCase):
    def test_legacy_throw_stone_regressions_with_new_rules_disabled(self):
        import test_throw_stone as legacy
        source=(ROOT/'server-mods/code/zone/effects.cpp').read_text(encoding='utf-8')
        bodies='\n'.join(function(source,s) for s in ('int64 Mob::GetActSpellDamage(',
            'int64 Mob::GetExtraSpellAmt(', 'int64 Mob::GetActReflectedSpellDamage('))
        compile_run(legacy.PRELUDE+bodies+legacy.CASES)

    def test_reference_and_regression_contract(self):
        source=(ROOT/'server-mods/code/zone/effects.cpp').read_text(encoding='utf-8')
        signatures=['int64 Mob::GetActSpellDamage(', 'int64 Mob::GetActReflectedSpellDamage(',
            'int64 Mob::GetActDoTDamage(', 'int64 Mob::GetActSpellHealing(',
            'int64 Mob::GetExtraSpellAmt(', 'int32 Mob::GetNightcapRuneAmount(']
        for name in ('int64 Mob::GetNightcapSpellDamageBonus(', 'int64 Mob::GetNightcapHeroicSpellValue('):
            if name in source:signatures.append(name)
        prelude=(Path(__file__).with_name('thj_spell_fixture.h')).read_text()
        header=ROOT/'server-mods/code/common/nightcap_spell_scaling.h'
        if header.exists():prelude='#include "'+header.as_posix()+'"\n'+prelude
        heroic=ROOT/'server-mods/code/zone/nightcap_heroic_cast.h'
        compile_run('#include "'+heroic.as_posix()+'"\n'+prelude+'\n'.join(function(source,s) for s in signatures)+CASES)

CASES=r'''
int main(){try{
 rules["Spells:FlatItemExtraSpellAmt"]=1;rules["Spells:ItemExtraSpellAmtCalcAsPercent"]=1;
 rules["Spells:IgnoreSpellDmgLvlRestriction"]=1;rules["Spells:DOTsScaleWithSpellDmg"]=1;
 rules["Spells:HOTsScaleWithHealAmt"]=1;rules["Spells:DOTBonusDamageSplitOverDuration"]=1;
 rules["Spells:HOTBonusHealingSplitOverDuration"]=1;rules["Spells:BaseCritRatio"]=200;
 rules["Spells:NightcapTHJDamageScaling"]=1;rules["Spells:NightcapHeroicSpellScaling"]=1;
 Mob c,t;c.sd=191;c.ha=191;
 expect("post713 initial",c.GetActSpellDamage(1,-20,&t),-211);
 c.duration=8;expect("post713 Clinging",c.GetActDoTDamage(1,-8,&t,true),-103);
 c.duration=21;expect("post713 Infectious",c.GetActDoTDamage(1,-5,&t,true),-100);
 for(int sd:{0,191,250,750,780})for(int base:{1,20,75,350,1000}){
  c.sd=sd;expect("direct additive",c.GetActSpellDamage(1,-base,&t),-base-sd);
  for(int duration:{1,8,21,60}){c.duration=duration;
   expect("duration independent SD",c.GetActDoTDamage(1,-base,&t,true),-base-sd/2);}
 }
 c.sd=191;c.duration=8;c.aabonuses.CriticalSpellChance=100;
 expect("direct crit",c.GetActSpellDamage(1,-20,&t),-422);
 c.aabonuses.CriticalSpellChance=0;c.aabonuses.CriticalDoTChance=100;
 expect("calibrated DoT critical half before ratio",c.GetActDoTDamage(1,-8,&t,true),-206);
 c.aabonuses.CriticalDoTChance=0;c.focuses[focusFcDamageAmt]=80;
 expect("focus remains duration split",c.GetActDoTDamage(1,-8,&t,true),-113);
 c.focuses.clear();c.hint=100;c.hwis=100;
 auto direct_damage=[&](int base){return NightcapHeroicCast::Cast::Deliver(true,[&]{return c.GetActSpellDamage(1,base,&t);});};
 auto direct_heal=[&](int base){return NightcapHeroicCast::Cast::Deliver(true,[&]{return c.GetActSpellHealing(1,base,&t,false);});};
 expect("INT after item",direct_damage(-20),-232);
 expect("no INT on DoT",c.GetActDoTDamage(1,-8,&t,true),-103);
 expect("healing percentage and WIS",direct_heal(100),320);
 spells[1].buff_duration=8;
 expect("HoT unchanged no WIS",c.GetActSpellHealing(1,100,&t,true),123);
 expect("duration-bearing immediate heal gets WIS once",direct_heal(100),135);
 spells[1].buff_duration=0;c.hint=0;c.hwis=0;
 expect("healing unchanged",c.GetActSpellHealing(1,100,&t,false),291);
 c.ha=750;expect("rune calibration unchanged",c.GetNightcapRuneAmount(1,230),1955);
 spells[1].bard=true;expect("Bard rune fixed after instrument",c.GetNightcapRuneAmount(1,230),230);
 spells[1].bard=false;c.ha=191;
 expect("Throw Stone once",c.GetActSpellDamage(5225,-1,&t),-192);
 spells[1].no_heal_damage_item_mod=true;
 c.hint=100;c.hwis=100;
 expect("item opt out direct",direct_damage(-20),-20);
 expect("item opt out DoT",c.GetActDoTDamage(1,-8,&t,true),-8);
 expect("heroic healing opt out",direct_heal(100),100);
 spells[1].no_heal_damage_item_mod=false;
 expect("reflection keeps additive SD",c.GetActReflectedSpellDamage(1,-20,50),-201);
 rules["Spells:IgnoreSpellDmgLvlRestriction"]=0;
 expect("SD level gate retained; heroics independent",direct_damage(-20),-22);
 c.hint=0;c.hwis=0;
 expect("stone exemption retained",c.GetActSpellDamage(5225,-1,&t),-192);
 rules["Spells:IgnoreSpellDmgLvlRestriction"]=1;
 c.kind=Mob::NPC;c.pet=true;expect("permanent pet additive",c.GetActSpellDamage(1,-20,&t),-211);
 expect("pet effective SD half",c.GetActDoTDamage(1,-8,&t,true),-103);
 c.pet=false;expect("hostile NPC legacy",c.GetActSpellDamage(1,-20,&t),-58);
 c.kind=Mob::Client;rules["Spells:NightcapTHJDamageScaling"]=0;
 expect("disabled legacy direct",c.GetActSpellDamage(1,-20,&t),-58);
 expect("disabled legacy DoT",c.GetActDoTDamage(1,-8,&t,true),-9);
 c.hint=100;rules["Spells:NightcapHeroicSpellScaling"]=0;
 expect("heroics independently disabled",direct_damage(-20),-58);
 expect("heroic truncation",NightcapSpellScaling::HeroicValue(-999,1),-999);
 expect("heroic negative clamp",NightcapSpellScaling::HeroicValue(-1000,-5),-1000);
 expect("heroic upper saturation",NightcapSpellScaling::HeroicValue(INT64_MAX,INT32_MAX),INT64_MAX);
 expect("heroic lower saturation",NightcapSpellScaling::HeroicValue(INT64_MIN,INT32_MAX),INT64_MIN);
 std::cout<<checks<<" checks passed\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what();return 1;}}
'''
if __name__=='__main__':unittest.main()

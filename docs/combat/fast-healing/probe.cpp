#include "zone/nightcap_heroic_cast.h"
#include "zone/nightcap_sympathetic.h"
#include "zone/client.h"
#include "zone/zone.h"
#include "zone/entity.h"
#include "common/json/json.hpp"
#include "common/item_instance.h"
#include "common/ptimer.h"
#include <filesystem>
#include <fstream>
using json=nlohmann::json;
extern Zone *zone;
// Deterministic seeding only in the separately linked diagnostic executable.
extern "C" unsigned int __wrap__ZNSt13random_device9_M_getvalEv(void*){return 20261120u;}
static void check(bool ok,const std::string &why){if(!ok)throw std::runtime_error(why);}
bool NightcapBalancePreflight(int argc,char **argv){
 if(argc!=4||std::string(argv[1])!="tests:balance"||std::filesystem::current_path()!="/tmp/nightcap-fast-healing-20261120")return false;
 std::ifstream f("eqemu_config.json");json c;f>>c;auto&s=c["server"];
 return s["database"]["db"]=="nightcap_balance_20260912"&&s["database"]["username"]=="nightcap_balance"&&s["auto_database_updates"]=="false"&&!s.contains("content_database");
}
class Subject:public Client{
public:
 int forced_ha=-1;
 int32 GetHealAmt()const override{return forced_ha>=0?forced_ha:Client::GetHealAmt();}
 void init(){class_=3;level=50;race=base_race=1;auto&p=GetPP();p.class_=3;p.level=50;p.race=1;
 p.STR=p.STA=p.AGI=p.DEX=p.INT=p.WIS=p.CHA=100;p.hunger_level=p.thirst_level=6000;
 SetClientVersion(EQ::versions::ClientVersion::RoF2);GetInv().SetInventoryVersion(EQ::versions::ClientVersion::RoF2);
 for(int k=0;k<=EQ::skills::HIGHEST_SKILL;k++)p.skills[k]=200;
 CalcBonuses();SetPosition(0,0,0);SaveSpellLoc();
 }
 void equip(const json&row,bool exact){auto*i=database.GetItem(row[1]);check(i,"item");EQ::ItemInstance inst(i,1);
  int socket=0;for(int a:row[2]){if(a){auto*p=database.GetItem(a);check(p,"augment");const int selected=exact?socket:inst.AvailableAugmentSlot(p->AugType);check(selected>=0,"socket compatibility");inst.PutAugment(selected,EQ::ItemInstance(p,1));}++socket;}
  check(GetInv().PutItem(row[0],inst)==int(row[0]),"slot");
 }
 void stress(int ha){forced_ha=ha;}
 void critical(bool on){aabonuses.CriticalHealChance=on?100:0;}
 void tank(){SetHP(1000);}
 void receiver_hp(){auto* i=new EQ::ItemData(*database.GetItem(604342));i->HP=20000;GetInv().PutItem(17,EQ::ItemInstance(i,1));CalcBonuses();}
 void arm(int spell,int hits,int channel){casting_spell_id=spell;casting_spell_aa_id=0;delaytimer=false;attacked_count=hits;
  GetPTimers().Disable(pTimerSpellStart+spell);GetPP().mem_spells[0]=spell;GetPP().skills[EQ::skills::SkillChanneling]=channel;
  SaveSpellLoc();SetMana(GetMaxMana());
 }
 json stats(){return {{"heal",GetHealAmt()},{"damage",GetSpellDmg()},{"hwis",GetHeroicWIS()},{"hp",GetMaxHP()},{"mana",GetMaxMana()}};}
};
int NightcapBalanceMain(int argc,char **argv){
 EQEmuLogSys::Instance()->SilenceConsoleLogging();std::ifstream in(argv[2]);json data;in>>data;
 for(auto&r:data["rules"])check(RuleManager::Instance()->SetRule(r[0],r[1]),"rule");
 zone=new Zone(32,0,"soldungb");zone->LoadBaseData();zone->LoadAlternateAdvancement();
 auto target=new Subject();target->init();entity_list.AddClient(target);target->receiver_hp();target->tank();json out;
 auto seed=zone->random;
 for(auto&cohort:data["cases"]){
  auto c=new Subject();c->init();for(auto&r:cohort["slots"])c->equip(r,cohort.value("exact_sockets",false));c->CalcBonuses();entity_list.AddClient(c);
  if(cohort.contains("stress_ha"))c->stress(cohort["stress_ha"]);
  const std::string name=cohort["name"];out["cohorts"][name]["stats"]=c->stats();
  for(int spell:{200,17,12,15}){
   auto base=c->CalcSpellEffectValue(spell,0,50,10,c);
   int64 value=NightcapHeroicCast::Cast::Deliver(true,[&]{return c->GetActSpellHealing(spell,base,target);});
   auto&row=out["cohorts"][name]["spells"][std::to_string(spell)];
   row={{"base",base},{"direct",value},{"cast_ms",c->GetActSpellCasttime(spell,spells[spell].cast_time)},{"mana",spells[spell].mana}};
   // The real timed-cast completion/Channeling path receives controlled hit counts.
   // This isolates interruption outcomes; it is not a pathing/fizzle/raid simulation.
   for(bool symp:{false,true}){
    if(symp){check(c->SpellFinished(44380,c),"sympathetic buff");check(c->FindBuff(44380),"buff applied");}
    else c->BuffFadeBySpellID(44380);
    for(int channel:{175,200})for(int hits:{0,4,8}){
     zone->random=seed;int landed=0;int64 healing=0,mana=0;
     for(int n=0;n<200;n++){
      zone->random=seed;for(int draw=0;draw<n;draw++)zone->random.Real(0,100);
      target->tank();c->arm(spell,hits,channel);c->SetTarget(target);const auto before=c->GetMana();
      c->CastedSpellFinished(spell,target->GetID(),EQ::spells::CastingSlot::Gem1,spells[spell].mana);
      auto gained=target->GetHP()-1000;landed+=gained>0;healing+=gained;mana+=before-c->GetMana();
     }
     row["pressure"].push_back({{"sympathetic",symp},{"channeling",channel},{"hits",hits},{"attempts",200},{"landed",landed},{"healing",healing},{"mana",mana}});
    }
   }
   // Exact overheal and once-only sympathetic cap through the native application.
   NightcapSympathetic::Cast receipt;receipt.effect=NightcapSympathetic::Effect::Healing;receipt.recipient=target;receipt.recipient_id=target->GetID();receipt.Record(NightcapSympathetic::Line::Healing,value);
   target->tank();c->ApplySympatheticClick(receipt);row["sympathetic_full"]=target->GetHP()-1000;
   target->SetHP(target->GetMaxHP()-2);c->ApplySympatheticClick(receipt);row["sympathetic_overheal"]=target->GetHP()-(target->GetMaxHP()-2);
   receipt.worn_heal=true;target->tank();c->ApplySympatheticClick(receipt);row["worn_precedence"]=target->GetHP()-1000;
   c->tank();c->arm(spell,0,200);c->SetTarget(c);c->CastedSpellFinished(spell,c->GetID(),EQ::spells::CastingSlot::Gem1,spells[spell].mana);row["self_with_sympathetic"]=c->GetHP()-1000;
   c->CalcBonuses();
  }
  for(int spell:{13502,13503,13504,16139,16140,16141}){
   c->tank();const int64 base=c->CalcSpellEffectValue(spell,0,50,10,c);
   auto expected=c->GetActSpellHealing(spell,base,c);
   check(c->SpellFinished(spell,c,EQ::spells::CastingSlot::Item,0,0xFFFFFFFF,0,true),"paladin proc");
   out["cohorts"][name]["paladin_procs"][std::to_string(spell)]={{"resolved",expected},{"landed",c->GetHP()-1000}};
  }
 }
 std::ofstream f(argv[3]);f<<out.dump(1);return 0;
}

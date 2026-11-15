#include "zone/client.h"
#include "zone/npc.h"
#include "zone/zone.h"
#include "common/json/json.hpp"
#include <filesystem>
#include <fstream>
#include <stdexcept>
using json=nlohmann::json;
extern Zone *zone;
static void require(bool v,const char *label){if(!v)throw std::runtime_error(label);}
bool NightcapBalancePreflight(int argc,char **argv){
 if(argc!=4||std::string(argv[1])!="tests:balance"||std::filesystem::current_path()!="/tmp/nightcap-rest-test-20261114/qa")return false;
 std::ifstream f("eqemu_config.json");json cfg;f>>cfg;auto &s=cfg["server"];
 return s["database"]["db"]=="nightcap_balance_20260912"&&s["database"]["username"]=="nightcap_balance"&&s["auto_database_updates"]=="false"&&!s.contains("content_database");
}
class Fixture:public Client{
public:
 void init(){
  class_=4;level=50;race=base_race=1;auto &pp=GetPP();pp.class_=4;pp.level=50;pp.race=1;
  pp.hunger_level=pp.thirst_level=6000;pp.WIS=100;
  SetClientVersion(EQ::versions::ClientVersion::RoF2);
  CalcBonuses();max_hp=6000;itembonuses.Mana+=3000-CalcMaxMana();require(CalcMaxMana()==3000,"fixture mana pool");SetHP(1000);SetMana(500);playeraction=1;SetAppearance(eaSitting);
 }
 json tick(bool expected){
  CalcRestState();std::cerr<<"aggro="<<GetAggroCount()<<" sitting="<<IsSitting()<<" fast="<<CanFastRegen()<<" timer="<<GetRestTimer()<<" expected="<<expected<<std::endl;require(CanFastRegen()==expected,"rest eligibility");
  auto hp=GetHP(),mana=GetMana();DoHPRegen();DoManaRegen();
  auto dh=GetHP()-hp,dm=GetMana()-mana;
  std::cerr<<"hp gain="<<dh<<" mana gain="<<dm<<std::endl; if(expected)require(dh==218&&dm==106,"rested tick amounts");
  else require(dh<218&&dm<106,"premature fast recovery");
  return {{"fast",expected},{"aggro",GetAggroCount()},{"timer_seconds",GetRestTimer()},{"hp_gain",dh},{"mana_gain",dm}};
 }
};
class Target:public NPC{
public:
 using NPC::NPC;
 void engage(Client *c){hate_list.AddEntToHateList(c,100,1,false,true);}
 void leave(Client *c){require(hate_list.RemoveEntFromHateList(c),"hate loss");}
};
int NightcapBalanceMain(int argc,char **argv){
 EQEmuLogSys::Instance()->SilenceConsoleLogging();
 // The isolated balance database predates the test migration. Use the installed rule values passed by the caller.
 std::ifstream in(argv[2]);json data;in>>data;
 for(auto key:{"Character:RestRegenTimeToActivate","Character:RestRegenRaidTimeToActivate"}){
  require(data.at(key)=="0","installed rule");require(RuleManager::Instance()->SetRule(key,"0"),"set clone rule");
 }
 json report;
 for(auto spec:{std::make_tuple(66,"gukbottom",data.at("regular").get<int>(),false),std::make_tuple(73,"permafrost",73057,true)}){
  auto [z,shortname,id,raid]=spec;zone=new Zone(z,0,shortname);zone->LoadBaseData();
  zone->newzone_data.fast_regen_hp=zone->newzone_data.fast_regen_mana=180;
  auto def=content_db.LoadNPCTypesData(id);require(def!=nullptr,"NPC type");
  auto create=[&](){return new Target(def,nullptr,glm::vec4(0),GravityBehavior::Water);};
  auto n=create();require(n->IsRaidTarget()==raid,"NPC raid flag");
  auto c=new Fixture();c->init();n->engage(c);require(c->GetAggroCount()==1,"engage");
  auto &row=report[shortname];row["npc"]=n->GetName();row["id"]=id;row["raid"]=raid;row["engaged"]=c->tick(false);
  auto second=create();second->engage(c);n->leave(c);require(c->GetAggroCount()==1,"remaining enemy");row["remaining_enemy"]=c->tick(false);
  second->leave(c);require(!c->GetAggroCount()&&!c->GetRestTimer(),"final aggro loss");
  row["first_eligible_tick"]=c->tick(true);int spell=1;while(spell<10000 && !(IsValidSpell(spell) && IsDetrimentalSpell(spell) && !IsRestAllowedSpell(spell)))++spell;require(spell<10000,"rest-blocking spell");c->buffs[0].spellid=spell;c->buffs[0].ticsremaining=2;row["detrimental"]=c->tick(false);c->buffs[0].spellid=SPELL_UNKNOWN;c->playeraction=0;c->SetAppearance(eaStanding);row["standing"]=c->tick(false);
 }
 std::ofstream out(argv[3]);out<<report.dump(2);return 0;
}

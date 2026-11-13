#include "zone/client.h"
#include "zone/zone.h"
#include "common/json/json.hpp"
#include "common/item_instance.h"
#include <filesystem>
#include <fstream>
#include <cassert>
extern "C" unsigned int __wrap__ZNSt13random_device9_M_getvalEv(void *) { return 20261113U; }
using json=nlohmann::json;
extern Zone *zone;
bool NightcapBalancePreflight(int argc,char **argv) {
 if(argc!=4 || std::string(argv[1])!="tests:balance" || std::filesystem::current_path()!="/tmp/nightcap-balance-stock-worn-atk-20261113") return false;
 std::ifstream f("eqemu_config.json");json j;f>>j;auto &s=j["server"];
 return s["database"]["db"]=="nightcap_balance_20260912" && s["database"]["username"]=="nightcap_balance" && s["auto_database_updates"]=="false" && !s.contains("content_database");
}
class TestClient:public Client {
public:
 void init(int lv) {
  class_=4;level=lv;race=base_race=1;deity=396;
  auto &pp=GetPP();pp.class_=4;pp.level=lv;pp.race=1;pp.deity=deity;
  pp.STR=180;pp.STA=pp.AGI=pp.DEX=pp.INT=pp.WIS=pp.CHA=100;
  pp.hunger_level=pp.thirst_level=6000;
  std::fill(std::begin(pp.InnateSkills), std::end(pp.InnateSkills), InnateDisabled);
  SetClientVersion(EQ::versions::ClientVersion::RoF2);
  GetInv().SetInventoryVersion(EQ::versions::ClientVersion::RoF2);
  pp.skills[EQ::skills::SkillOffense]=110;pp.skills[EQ::skills::SkillHandtoHand]=140;
  CalcBonuses();
 }
 void equip(int slot,const EQ::ItemData *def){
  EQ::ItemInstance inst(def,1);
  assert((def->Slots&(1u<<slot)) && CanEquipItem(def)); assert(GetInv().PutItem(slot,inst)==slot); CalcBonuses();
 }
 json stats(){return {{"worn",GetItemBonuses().ATK},{"rating",GetTotalATK()},{"offense",offense(EQ::skills::SkillHandtoHand)},{"str",GetSTR()}};}
};
int NightcapBalanceMain(int argc,char **argv) {
 EQEmuLogSys::Instance()->SilenceConsoleLogging();
 zone=new Zone(32,0,"soldungb");zone->LoadBaseData();zone->LoadAlternateAdvancement();
 const EQ::ItemData *item=database.GetItem(626771);assert(item && item->ReqLevel==0 && item->RecLevel==60);
 json results=json::array();
 for(int lv:{50,60})for(int other:{0,199,200,250}){
  auto *c=new TestClient();c->init(lv);
  if(other){
   // Synthetic neck piece isolates a known worn total without adding STR or a buff.
   EQ::ItemData bg{};bg.ID=1;bg.Slots=1u<<5;bg.Classes=65535;bg.Races=65535;bg.Attack=other;bg.ItemType=EQ::item::ItemTypeArmor;
   c->equip(5,&bg);assert(c->GetItemBonuses().ATK==other);
  }
  auto empty=c->stats();EQ::ItemData reference=*item; reference.Attack=50;
  c->equip(7,&reference);auto reference_stats=c->stats();
  // Compare the DB reference at 50 ATK and the cache-loaded variant with the same mitigation rolls.
  auto random_state=zone->random;
  auto landed_hits=[&](){double sum=0;for(int n=0;n<20000;++n)sum+=c->RollD20(c->offense(EQ::skills::SkillHandtoHand),300);return sum/20000;};
  auto ref_damage=landed_hits();
  delete c->GetInv().PopItem(7);c->CalcBonuses();assert(c->stats()==empty);
  c->equip(7,item);auto equipped=c->stats();zone->random=random_state;auto measured_damage=landed_hits();
  auto *removed=c->GetInv().PopItem(7);assert(removed);delete removed;c->CalcBonuses();assert(c->stats()==empty);
  c->equip(7,item);assert(c->stats()==equipped);
  results.push_back({{"level",lv},{"other",other},{"empty",empty},{"equipped",equipped},{"raw",item->Attack},{"reference_atk_50",reference_stats},{"reference_mean_landed_multiplier",ref_damage},{"equipped_mean_landed_multiplier",measured_damage}});
 }
 std::ofstream out(argv[3]);out<<results.dump(2);out.close();return 0;
}

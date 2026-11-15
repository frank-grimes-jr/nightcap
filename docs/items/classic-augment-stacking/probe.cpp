#include "zone/nightcap_heroic_cast.h"
#include "common/raid_augment.h"
#include "zone/client.h"
#include "zone/zone.h"
#include "common/json/json.hpp"
#include "common/item_instance.h"
#include <filesystem>
#include <fstream>
#include <set>
using json=nlohmann::json;
extern Zone *zone;
static void check(bool ok,const std::string &label){if(!ok)throw std::runtime_error(label);}
bool NightcapBalancePreflight(int argc,char **argv){
 if(argc!=4||std::string(argv[1])!="tests:balance"||std::filesystem::current_path()!="/tmp/nightcap-classic-stack-20261114")return false;
 std::ifstream in("eqemu_config.json");json cfg;in>>cfg;auto &s=cfg["server"];
 return s["database"]["db"]=="nightcap_balance_20260912"&&s["database"]["username"]=="nightcap_balance"&&s["auto_database_updates"]=="false"&&!s.contains("content_database");
}
const EQ::ItemData *item(int id){auto p=database.GetItem(id);check(p,"cache item "+std::to_string(id));return p;}
class Subject:public Client{
public:
 void init(){
  class_=3;level=50;race=base_race=1;deity=396;auto &pp=GetPP();pp.class_=3;pp.level=50;pp.race=1;pp.deity=deity;
  pp.STR=pp.STA=pp.AGI=pp.DEX=pp.INT=pp.WIS=pp.CHA=100;pp.hunger_level=pp.thirst_level=6000;
  std::fill(std::begin(pp.InnateSkills),std::end(pp.InnateSkills),InnateDisabled);
  SetClientVersion(EQ::versions::ClientVersion::RoF2);GetInv().SetInventoryVersion(EQ::versions::ClientVersion::RoF2);
  for(auto skill:{EQ::skills::SkillDodge,EQ::skills::SkillParry,EQ::skills::SkillRiposte,EQ::skills::SkillBlock}) pp.skills[skill]=MaxSkill(skill);
  CalcBonuses();
 }
 bool allowed(EQ::ItemInstance &h,const EQ::ItemData *a,int slot){
  return (a->Slots&(1u<<slot)) && h.AvailableWearSlot(a->Slots) && h.AvailableAugmentSlot(a->AugType)>=0 &&
   !IsAugmentRestricted(h.GetItem()->ItemType,a->AugRestrict) && CanEquipItem(a) && a->ReqLevel<=50 && !h.ContainsAugmentByID(a->ID);
 }
 void equip(int slot,int id,const json &augs,json &equipment){
  auto h=item(id);check((h->Slots&(1u<<slot))&&CanEquipItem(h)&&h->ReqLevel<=50&&!h->Deity&&!CheckLoreConflict(h,false),"host eligibility "+std::to_string(id));
  EQ::ItemInstance inst(h,1);
  for(int aid:augs){auto a=item(aid);if(!allowed(inst,a,slot)||CheckLoreConflict(a,false))std::cerr<<"reject "<<aid<<" slots="<<a->Slots<<" socket="<<int(inst.AvailableAugmentSlot(a->AugType))<<" restriction="<<IsAugmentRestricted(h->ItemType,a->AugRestrict)<<" equip="<<CanEquipItem(a)<<" lore="<<CheckLoreConflict(a,false)<<" wear="<<inst.AvailableWearSlot(a->Slots)<<" host="<<int(h->AugSlotType[2])<<" vis="<<int(h->AugSlotVisible[2])<<std::endl;check(allowed(inst,a,slot)&&!CheckLoreConflict(a,false),"augment eligibility "+std::to_string(aid)+" on "+std::to_string(id));int socket=inst.AvailableAugmentSlot(a->AugType);if(NightcapRaidAug::IsReward(aid))check(NightcapRaidAug::CanInsert(inst,socket,false),"raid insertion");inst.PutAugment(socket,EQ::ItemInstance(a,1));check(inst.GetAugment(socket)->GetID()==aid,"native socket");}
  check(GetInv().PutItem(slot,inst)==slot,"equip");equipment.push_back({slot,id,h->Name,augs});
 }
 json stats(){const auto v=GetItemBonuses();return {{"hp",GetMaxHP()},{"mana",GetMaxMana()},{"heal",v.HealAmt},{"damage",v.SpellDmg},{"dodge",v.DodgeChance},{"shield",v.DamageShield}};}
 int dodges(Subject *attacker){
  attacker->SetPosition(0,5,0);SetPosition(0,0,0);
  if(attacker->BehindMob(this,attacker->GetX(),attacker->GetY()))attacker->SetPosition(0,-5,0);
  check(!attacker->BehindMob(this,attacker->GetX(),attacker->GetY()),"front");
  int count=0;
  for(int i=0;i<20000;i++){DamageHitInfo hit{};hit.hand=EQ::invslot::slotPrimary;hit.skill=EQ::skills::Skill1HBlunt;AvoidDamage(attacker,hit);if(hit.damage_done==DMG_DODGED)++count;}
  return count;
 }
 json direct(Subject *target){
  int64 h=CalcSpellEffectValue(15,0,50,10,this),d=CalcSpellEffectValue(117,0,50,10,this);
  check(h>0&&d<0,"spell bases");int64 hl=INT64_MAX,hh=0,dl=INT64_MAX,dh=0,hs=0,ds=0;
  for(int i=0;i<256;i++){
   auto heal=NightcapHeroicCast::Cast::Deliver(true,[&]{return GetActSpellHealing(15,h,target);});auto dmg=-NightcapHeroicCast::Cast::Deliver(true,[&]{return GetActSpellDamage(117,d,target);});
   hl=std::min(hl,heal);hh=std::max(hh,heal);dl=std::min(dl,dmg);dh=std::max(dh,dmg);hs+=heal;ds+=dmg;
  }
  return {{"base", {h,-d}},{"heal_range",{hl,hh}},{"damage_range",{dl,dh}},{"heal_sum",hs},{"damage_sum",ds}};
 }
};
int NightcapBalanceMain(int argc,char **argv){
 EQEmuLogSys::Instance()->SilenceConsoleLogging();
 std::ifstream in(argv[2]);json data;in>>data;
 for(auto &r:data["rules"]){check(RuleManager::Instance()->SetRule(r[0],r[1]),"rule");}
 zone=new Zone(32,0,"soldungb");zone->LoadBaseData();zone->LoadAlternateAdvancement();
 json result;auto target=new Subject();target->init();auto rng=zone->random;
 for(auto &test:data["cases"]){
  auto c=new Subject();c->init();json eq=json::array();
  for(auto &row:test["slots"]){c->equip(row[0],row[1],row[2],eq);}
  c->CalcBonuses();auto stats=c->stats();zone->random=rng;
  auto dodge_rolls=c->dodges(target);zone->random=rng;result["cases"][test["name"].get<std::string>()]={{"dodges_per_20000",dodge_rolls},{"stats",stats},{"direct",c->direct(target)},{"gear",eq}};
 }
 for(int id:{8401,5401,606500,620705,604342}){
  EQ::ItemInstance h(item(id),1);int slot=id==8401?11:id==620705?14:id==604342?17:13;
  result["socket_controls"][std::to_string(id)]=target->allowed(h,item(609602),slot);
 }
 std::ofstream out(argv[3]);out<<result.dump(1);return 0;
}

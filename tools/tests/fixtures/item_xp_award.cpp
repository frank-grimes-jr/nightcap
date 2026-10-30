// Boundary doubles for the extracted production award method. SQL arithmetic,
// metadata parsing, family checks and native row snapshots are production code.
#include "common/item_xp_eligibility.h"
#include "common/item_xp_metadata.h"
#include "common/item_xp_inventory.h"
#include "common/paladin_weapon_grip.h"
#include "common/advanced_loot_policy.h"
#include <array>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <map>
#include <stdexcept>
#include <vector>
using uint8=uint8_t;using uint32=uint32_t;using int16=int16_t;
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"line %d: %s\n",__LINE__,#x); std::exit(1); } } while(false)
bool enabled=true;
#define RuleB(category,rule) enabled
constexpr int INVALID_INDEX=-1,invWhereWorn=1,invWhereSharedBank=8,ItemPacketTrade=1;
namespace Chat {enum {Yellow,Green};}
namespace Strings {
std::vector<std::string> Split(const std::string& s,const std::string& delimiter) {
 std::vector<std::string> out;size_t start=0,end;
 while((end=s.find(delimiter,start))!=std::string::npos){out.push_back(s.substr(start,end-start));start=end+delimiter.size();}
 out.push_back(s.substr(start));return out;
}
}
namespace EQ {
namespace invslot {constexpr int16 slotPowerSource=21,EQUIPMENT_BEGIN=0,EQUIPMENT_END=22;}
namespace invaug {constexpr uint8 SOCKET_COUNT=6;}
struct ItemData {
 uint32 ID=1001,Slots=4,AugType=0,Color=7,AugRestrict=0;int LoreGroup=0;
 uint8 ItemClass=0,NoRent=255,ReqLevel=1,RecLevel=1,ItemType=0;
 bool Stackable=false;std::string Name="Cloth Cap";
 std::array<unsigned,6> AugSlotType{1,1,1,1,1,1};
};
struct ItemInstance {
 ItemData definition;uint32 color=7;int charges=-1;bool bound=true,evolving=false,scaling=false;
 std::map<std::string,std::string> m_custom_data;std::array<ItemInstance*,6> aug{};
 const ItemData* GetItem()const{return &definition;}uint32 GetID()const{return definition.ID;}
 bool IsEvolving()const{return evolving;}uint32 GetEvolveUniqueID()const{return 0;}
 bool IsScaling()const{return scaling;}bool IsStackable()const{return definition.Stackable;}
 ItemInstance* GetAugment(uint8 i)const{return aug[i];}
 uint32 GetAugmentItemID(uint8 i)const{return aug[i]?aug[i]->GetID():0;}
 uint32 GetColor()const{return color;}void SetColor(uint32 value){color=value;}
 uint32 GetSerialNumber()const{return 42;}int GetCharges()const{return charges;}
 bool IsAttuned()const{return bound;}uint32 GetOrnamentationIcon()const{return 72;}
 uint32 GetOrnamentationIDFile()const{return 73;}int GetOrnamentHeroModel()const{return -7;}
 std::string GetCustomDataString()const;
 void SetCustomDataString(const std::string&);
 void SetCustomData(const std::string&,const std::string&);
 void DeleteCustomData(const std::string&);
 void RefreshPaladinWeaponGrip(){} // separately covered by actual grip/Restore tests
};
}
struct InventoryRow {
 uint32 character_id=0,slot_id=0,item_id=0,charges=0,color=0;
 uint32 augment_one=0,augment_two=0,augment_three=0,augment_four=0,augment_five=0,augment_six=0,instnodrop=0;
 std::string custom_data;uint32 ornament_icon=0,ornament_idfile=0;int ornament_hero_model=0;uint32 guid=0;
};
struct Reply {
 bool ok=true;int affected=1;std::vector<std::string> row{"1"};std::vector<const char*> pointers;
 bool Success()const{return ok;}size_t RowCount()const{return 1;}int RowsAffected()const{return affected;}
 const char** begin(){pointers.clear();for(auto& field:row)pointers.push_back(field.c_str());return pointers.data();}
};
struct Database {
 std::map<uint32,EQ::ItemData> items;int failure=0,queries=0,updates=0;bool committed=false;
 EQ::ItemInstance *observed=nullptr;uint32 expected_id=0;std::string expected_data,sql;
 const EQ::ItemData* GetItem(uint32 id){auto it=items.find(id);return it==items.end()?nullptr:&it->second;}
 Reply QueryDatabase(const std::string& query,bool retry){
  CHECK(!retry);++queries;Reply r;
  if(query.find("UPDATE ")==0){
   CHECK(observed&&observed->GetID()==expected_id&&observed->GetCustomDataString()==expected_data);
   ++updates;sql=query;committed=true;
   if(failure==6){r.ok=false;return r;}
   if(failure==7){r.affected=0;committed=false;return r;}
   if(failure==8)throw std::runtime_error("lost acknowledgement");
   if(failure==9){r.affected=2;return r;}
   return r;
  }
  if(query.find("TABLES")!=std::string::npos){r.ok=failure!=1;if(failure==2)r.row={"0"};}
  if(query.find("TRIGGERS")!=std::string::npos)r.row={failure==3?"1":"0"};
  if(query.find("@@in_transaction")!=std::string::npos)r.row={failure==4?"1":"0",failure==5?"0":"1"};
  return r;
 }
} database;
struct Inventory {
 std::map<int16,EQ::ItemInstance> slots;bool fail_put=false,other_lore=false;int puts=0;
 EQ::ItemInstance* GetItem(int16 slot){auto it=slots.find(slot);return it==slots.end()?nullptr:&it->second;}
 int16 PutItem(int16 slot,const EQ::ItemInstance& item){CHECK(database.committed);++puts;if(fail_put)return -1;slots[slot]=item;return slot;}
 int HasItemByLoreGroup(int,uint8){return other_lore?23:INVALID_INDEX;}
};
struct Client {
 Inventory inventory;bool connected=true,loaded=true,dead=false,lore=false,pet_lore=false,bad_augment=false,packet_failure=false;
 uint8 level=10;int quarantines=0,packets=0,bonuses=0,messages=0;
 bool Connected(){return connected;}bool ClientDataLoaded(){return loaded;}bool IsDead(){return dead;}
 uint8 GetLevel(){return level;}uint32 CharacterID(){return 7;}Inventory& GetInv(){return inventory;}
 bool CheckLoreConflict(const EQ::ItemData*){return lore;}bool PetArmorLoreConflict(const EQ::ItemData*){return pet_lore;}
 bool IsAugmentRestricted(uint8,uint32){return bad_augment;}
 void QuarantineItemTransfer(const char*){++quarantines;connected=loaded=false;}
 void SendItemPacket(int16,const EQ::ItemInstance*,int){CHECK(database.committed);++packets;if(packet_failure)throw std::runtime_error("packet");}
 void CalcBonuses(){++bonuses;}
 template<class... T>void Message(T...){++messages;}
};

// NATIVE_METADATA
namespace NightcapLoot {
// NATIVE_AWARD
}

Client seed() {
 enabled=true;database=Database{};
 const char* names[]={"Cloth Cap","Cloth Cap (Polished)","Cloth Cap (Exalted)","Cloth Cap (Ascended)"};
 for(uint32 i=0;i<4;++i){EQ::ItemData d;d.ID=1001+i*200000;d.Name=names[i];d.Color=7+i;database.items[d.ID]=d;}
 Client c;c.inventory.slots[21]=EQ::ItemInstance{};return c;
}
void prepare(Client& c) {
 database.observed=c.inventory.GetItem(21);database.expected_id=database.observed->GetID();
 database.expected_data=database.observed->GetCustomDataString();database.committed=false;
}
void near_upgrade(Client& c){auto* item=c.inventory.GetItem(21);item->SetCustomData(NightcapItemXP::Key,"1:1001:79999999");}
int main() {
 using namespace NightcapLoot;
 using NightcapItemXP::ReadMetadata;
 {auto c=seed();for(unsigned n=0;n<60;++n){prepare(c);const auto result=AwardItemExperience(&c,136500);
  if(result!=TransferResult::Delivered)std::fprintf(stderr,"award=%u result=%d id=%u queries=%d updates=%d metadata=%s\n",n,int(result),c.inventory.GetItem(21)->GetID(),database.queries,database.updates,c.inventory.GetItem(21)->GetCustomDataString().c_str());
  CHECK(result==TransferResult::Delivered);}
  CHECK(c.inventory.GetItem(21)->GetID()==601001&&c.inventory.GetItem(21)->GetCustomDataString().empty());
  CHECK(c.packets==3&&c.bonuses==3&&database.updates==60);
  prepare(c);CHECK(AwardItemExperience(&c,136500)==TransferResult::Declined&&database.updates==60);}
 for(int failure=1;failure<=9;++failure){auto c=seed();prepare(c);database.failure=failure;
  const auto result=AwardItemExperience(&c,136500);
  CHECK(result==(failure<6?TransferResult::Declined:TransferResult::Uncertain));
  CHECK(c.inventory.GetItem(21)->GetCustomDataString().empty()&&!c.packets&&!c.inventory.puts);
  CHECK(c.quarantines==(failure<6?0:1));CHECK(database.updates==(failure<6?0:1));}
 {auto c=seed();prepare(c);c.inventory.fail_put=true;CHECK(AwardItemExperience(&c,136500)==TransferResult::Uncertain);
  CHECK(database.committed&&c.quarantines==1&&!c.loaded);}
 {auto c=seed();near_upgrade(c);prepare(c);c.packet_failure=true;CHECK(AwardItemExperience(&c,1)==TransferResult::Uncertain);
  CHECK(database.committed&&c.quarantines==1&&c.inventory.GetItem(21)->GetID()==201001);}
 for(bool dye:{false,true}){auto c=seed();near_upgrade(c);if(dye)c.inventory.GetItem(21)->color=999;prepare(c);
  CHECK(AwardItemExperience(&c,1)==TransferResult::Delivered);auto* item=c.inventory.GetItem(21);
  CHECK(item->GetColor()==(dye?999u:8u)&&item->GetCharges()==-1&&item->IsAttuned());
  CHECK(item->GetOrnamentationIcon()==72&&item->GetOrnamentHeroModel()==-7);}
 {auto c=seed();near_upgrade(c);c.lore=true;c.inventory.GetItem(21)->definition.LoreGroup=12;database.items[201001].LoreGroup=12;
  prepare(c);CHECK(AwardItemExperience(&c,1)==TransferResult::Delivered);}
 for(int conflict=0;conflict<3;++conflict){auto c=seed();near_upgrade(c);c.lore=true;
  c.inventory.GetItem(21)->definition.LoreGroup=12;database.items[201001].LoreGroup=12;
  if(conflict==0)c.inventory.other_lore=true;if(conflict==1)c.pet_lore=true;
  if(conflict==2){c.inventory.slots[0]=EQ::ItemInstance{};c.inventory.slots[0].definition.LoreGroup=12;}
  prepare(c);CHECK(AwardItemExperience(&c,1)==TransferResult::Declined&&!database.updates);}
 {auto c=seed();near_upgrade(c);EQ::ItemInstance aug;aug.definition.ID=77;c.inventory.GetItem(21)->aug[0]=&aug;
  prepare(c);CHECK(AwardItemExperience(&c,1)==TransferResult::Delivered&&c.inventory.GetItem(21)->GetAugmentItemID(0)==77);}
 {auto c=seed();near_upgrade(c);EQ::ItemInstance aug;c.inventory.GetItem(21)->aug[0]=&aug;database.items[201001].AugSlotType[0]=2;
  prepare(c);CHECK(AwardItemExperience(&c,1)==TransferResult::Declined&&!database.updates);}
 {auto c=seed();c.inventory.GetItem(21)->SetCustomData(NightcapItemXP::Key,"1:999:123");prepare(c);
  CHECK(AwardItemExperience(&c,1)==TransferResult::Declined&&!database.queries);}
 {auto c=seed();database.items.erase(601001);prepare(c);CHECK(AwardItemExperience(&c,1)==TransferResult::Declined);}
 {auto c=seed();enabled=false;prepare(c);CHECK(AwardItemExperience(&c,1)==TransferResult::Declined);}
 {auto c=seed();c.level=0;prepare(c);CHECK(AwardItemExperience(&c,1)==TransferResult::Declined);}
 {auto c=seed();c.loaded=false;prepare(c);CHECK(AwardItemExperience(&c,1)==TransferResult::Declined);}
 std::puts("actual award, failure, publication, metadata and lore cases passed");
}

#include "common/paladin_weapon_grip.h"
#include <cassert>
#include <cstdint>
#include <map>
#include <stdexcept>
#include <string>
#include <iostream>
using int16 = int16_t;
using int32 = int32_t;
using uint8 = uint8_t;
namespace EQ {
namespace item { enum { ItemType1HSlash, ItemType2HSlash }; }
namespace invslot { constexpr int slotPrimary=13, slotSecondary=14; }
namespace invaug { constexpr int SOCKET_COUNT=6; }
namespace textures { constexpr int weaponPrimary=7; }
}
namespace Chat { enum { Yellow, Green }; }
enum { ItemPacketTrade };
struct ItemData { int ItemType=1; unsigned AugRestrict=0; const char *Name="SoulFire"; };
struct Item {
 unsigned id=5504, guid=9, color=7, ornament=3;
 int charges=5; bool attuned=true, evolving=false, scaling=false;
 std::string metadata;
 ItemData data;
 Item *augment=nullptr;
 unsigned GetID() const {return id;}
 unsigned GetSerialNumber() const {return guid;}
 int GetCharges() const {return charges;}
 unsigned GetColor() const {return color;}
 bool IsAttuned() const {return attuned;}
 unsigned GetOrnamentationIcon() const {return ornament;}
 unsigned GetOrnamentationIDFile() const {return 4;}
 unsigned GetOrnamentHeroModel() const {return 5;}
 unsigned GetAugmentItemID(uint8 i) const {return i==0 && augment ? augment->id : 0;}
 Item *GetAugment(uint8 i) {return i==0 ? augment : nullptr;}
 const ItemData *GetItem() const {return &data;}
 std::string GetCustomDataString() const {return metadata;}
 bool IsEvolving() const {return evolving;}
 bool IsScaling() const {return scaling;}
 void SetCustomData(const std::string &key,const std::string &value) {metadata=key+"^"+value+"^";data.ItemType=0;}
 void DeleteCustomData(const std::string &) {metadata.clear();data.ItemType=1;}
};
struct Inventory {
 std::map<int,Item*> slots;
 Item *GetItem(int16 slot) {auto it=slots.find(slot);return it==slots.end()?nullptr:it->second;}
 bool SupportsClickCasting(int16 slot) {return slot==13 || slot==14 || slot==23 || slot==251;}
};
struct Trade {bool active=false;bool With(){return active;}};
struct Reply {bool ok=true;int rows=1;bool Success() const{return ok;} int RowsAffected() const{return rows;}};
struct Database {
 Reply reply; bool throws=false;int queries=0; std::string sql;
 Item *observed=nullptr; std::string expected;
 Reply QueryDatabase(const std::string &query,bool retry) {
  assert(!retry); assert(observed && observed->metadata==expected);
  ++queries;sql=query;if(throws)throw std::runtime_error("uncertain");return reply;
 }
} database;
struct Client {
 Inventory m_inv; bool client_data_loaded=true,m_pet_armor_transfer_valid=true;
 bool dead=false,engaged=false,auto_attack=false,casting=false,stunned=false,mezzed=false,feared=false,ai=false;
 bool station=false,trader=false,buyer=false,throw_packet=false;
 int aggro=0;int GetAggroCount(){return aggro;}
 Trade *trade=nullptr; int packets=0,bonuses=0,timers=0,wear=0,quarantines=0;
 bool IsDead(){return dead;} bool IsEngaged(){return engaged;} bool IsCasting(){return casting;}
 bool IsStunned(){return stunned;} bool IsMezzed(){return mezzed;} bool IsFeared(){return feared;}
 bool IsAIControlled(){return ai;} bool GetTradeskillObject(){return station;}
 bool IsTrader(){return trader;} bool IsBuyer(){return buyer;}
 bool IsAugmentRestricted(int type,unsigned restriction){return restriction && restriction!=unsigned(type+1);}
 unsigned CharacterID(){return 42;}
 template<class... A> void Message(int,const char*,A...){ }
 void QuarantineItemTransfer(const char*){++quarantines;m_pet_armor_transfer_valid=false;client_data_loaded=false;}
 void SendItemPacket(int16,Item*,int){assert(database.queries==1);++packets;if(throw_packet)throw std::runtime_error("publish");}
 void CalcBonuses(){++bonuses;} void SetAttackTimer(){++timers;} void SendWearChange(int){++wear;}
 bool TogglePaladinWeaponGrip(int32 slot_id);
};
// PRODUCTION_HANDLER
int main() {
 using namespace NightcapPaladinGrip;
 for(unsigned id : {5504u,205504u,405504u,605504u,11050u,211050u,411050u,611050u,10099u,810099u}) {
  Item sword; sword.id=id; Item aug; aug.id=123; sword.augment=&aug;
  for(int slot : {13,23,251}) {
   sword.metadata.clear();sword.data.ItemType=1;
   Client c; c.m_inv.slots[slot]=&sword;
   database={};database.observed=&sword;
   assert(c.TogglePaladinWeaponGrip(slot));
   assert(sword.data.ItemType==0 && sword.metadata==std::string(Key)+"^1^");
   assert(sword.id==id && sword.charges==5 && sword.color==7 && sword.attuned && sword.augment==&aug);
   assert(c.packets==1 && c.quarantines==0 && c.bonuses==(slot==13));
   database={};database.observed=&sword;database.expected=sword.metadata;
   assert(c.TogglePaladinWeaponGrip(slot));
   assert(sword.data.ItemType==1 && sword.metadata.empty() && c.packets==2);
  }
 }
 Item sword,offhand; Client c;c.m_inv.slots[13]=&sword;c.m_inv.slots[14]=&offhand;
 database={};database.observed=&sword;
 assert(c.TogglePaladinWeaponGrip(13)); // 2HS to 1HS can coexist with offhand
 database={};database.observed=&sword;database.expected=sword.metadata;
 assert(c.TogglePaladinWeaponGrip(13) && database.queries==0 && sword.data.ItemType==0);
 c.m_inv.slots.erase(14); Item aug;aug.data.AugRestrict=1;sword.augment=&aug;
 assert(c.TogglePaladinWeaponGrip(13) && database.queries==0); // 1HS-only augment
 sword.augment=nullptr;
 c.aggro=1;assert(c.TogglePaladinWeaponGrip(13) && database.queries==0);c.aggro=0;
 for(auto flag : {&Client::dead,&Client::engaged,&Client::auto_attack,&Client::casting,&Client::stunned,
                 &Client::mezzed,&Client::feared,&Client::ai,&Client::station,&Client::trader,&Client::buyer}) {
  c.*flag=true;assert(c.TogglePaladinWeaponGrip(13) && database.queries==0);c.*flag=false;
 }
 Trade trade;trade.active=true;c.trade=&trade;
 assert(c.TogglePaladinWeaponGrip(13) && database.queries==0);c.trade=nullptr;
 for(auto valid : {&Client::client_data_loaded,&Client::m_pet_armor_transfer_valid}) {
  c.*valid=false;assert(c.TogglePaladinWeaponGrip(13) && database.queries==0);c.*valid=true;
 }
 for(int slot : {30,2000,4000}) {c.m_inv.slots[slot]=&sword;assert(c.TogglePaladinWeaponGrip(slot) && database.queries==0);}
 for(int slot : {-1,65549,32768,2147483647}) assert(!c.TogglePaladinWeaponGrip(slot));
 assert(!c.TogglePaladinWeaponGrip(24));
 sword.id=5379;assert(!c.TogglePaladinWeaponGrip(13));sword.id=5504;
 sword.metadata="other^data^";assert(c.TogglePaladinWeaponGrip(13) && database.queries==0);
 assert(UpdateSQL(42,13,sword,true).empty());
 sword.metadata=std::string(Key)+"^1^";
 sword.evolving=true;assert(c.TogglePaladinWeaponGrip(13) && database.queries==0);sword.evolving=false;
 sword.scaling=true;assert(c.TogglePaladinWeaponGrip(13) && database.queries==0);sword.scaling=false;
 for(int failure : {0,1,2,3}) {
  Client failing;failing.m_inv.slots[13]=&sword;
  sword.metadata.clear();sword.data.ItemType=1;
  database={};database.observed=&sword;
  if(failure==0)database.reply.ok=false;
  if(failure==1)database.reply.rows=0;
  if(failure==2)database.throws=true;
  if(failure==3)failing.throw_packet=true;
  assert(failing.TogglePaladinWeaponGrip(13) && failing.quarantines==1);
  assert(database.queries==1 && !failing.client_data_loaded);
  assert(failing.packets==(failure==3?1:0));
  assert(sword.data.ItemType==(failure==3?0:1));
 }
 sword.metadata.clear();sword.data.ItemType=1;sword.charges=-1;
 std::cout << UpdateSQL(42,13,sword,true) << '\n';
 sword.metadata=std::string(Key)+"^1^";
 std::cout << UpdateSQL(42,13,sword,false) << '\n';
}

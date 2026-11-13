#include "zone/raid_augment.h"
#include "common/raid_augment_sources.h"
#include <array>
#include <cassert>
#include <cstdint>
using uint32 = uint32_t;
using int64 = int64_t;
enum { pTimerRaidAugment = 903 };
int database;
namespace EQ { namespace invslot { enum { slotChest = 17 }; } namespace invaug { enum { SOCKET_COUNT=6 }; } }
namespace Chat { enum { Spells }; }
struct Timer { static uint64_t now; static uint32_t GetCurrentTime() { return static_cast<uint32_t>(now); } };
uint64_t Timer::now = 999;
struct ItemData { uint32_t Slots=1u<<17; int AugSlotType[6]={22}; };
struct Item {
	ItemData data; unsigned ids[6]={};
	const ItemData *GetItem() const { return &data; }
	unsigned GetAugmentItemID(int i) const { return ids[i]; }
	bool IsClassCommon() const {return true;}
	int GetItemRequiredLevel(bool) const {return 50;}
};
struct Inventory { Item *chest; const Item *GetItem(int) const {return chest;} };
struct Clock {
	uint64_t deadline=0; bool storage=true;
	uint32_t GetRemainingTime(int) { return Timer::now < deadline ? static_cast<uint32_t>(deadline - Timer::now) : 0; }
	void Start(int,int duration) { deadline=(Timer::now/1000+duration)*1000; }
	Clock *Get(int) {return this;}
	bool Store(int*) { return storage; }
};
struct Buff { int spellid=0, melee_rune=0, magic_rune=0; };
bool IsValidSpell(int spell) {return spell>0;}
class Client;
class Mob {
public:
	virtual ~Mob()=default; virtual bool IsClient() const {return false;}
	bool IsNPC() const {return !IsClient();}
	bool HasOwner() const {return owner!=nullptr;}
	Mob *CastToNPC() {return this;} unsigned GetSwarmOwner() const {return 0;}
	Mob *owner=nullptr; Mob *GetUltimateOwner() {return owner ? owner : this;}
	Client *CastToClient();
};
class Client : public Mob {
public:
	NightcapRaidAug::State raid_augment;
	Item host; Inventory inv{&host}; Clock clock; Buff buffs[1]; int level=50; bool aggro=true;
	int64 hp=300,max_hp=1000,mana=0,endurance=0,max_mana=10000,max_endurance=1000;
	bool IsClient() const override {return true;}
	Inventory &GetInv() {return inv;} bool CanEquipItem(const ItemData*) const {return true;}
	int GetLevel() const {return level;} Clock &GetPTimers() {return clock;}
	int64 GetHP() const {return hp;} int64 GetMaxHP() const {return max_hp;}
	void SetHP(int64 v) {hp=v;} void SendHPUpdate() {}
	int GetMaxTotalSlots() const {return 1;} Buff *GetBuffs() {return buffs;}
	void Message(int,const char*,...) {} bool GetAggroCount() const {return aggro;}
	int64 GetMana() const {return mana;} int64 GetMaxMana() const {return max_mana;}
	int64 GetEndurance() const {return endurance;} int64 GetMaxEndurance() const {return max_endurance;}
	void SetMana(int64 v) {mana=v;} void SetEndurance(int64 v) {endurance=v;}
};
Client *Mob::CastToClient() {return static_cast<Client*>(this);}
#include "zone/raid_augment.inc"
int main() {
	using namespace NightcapRaidAug;
	Client c; Mob enemy; Item &host=c.host;
	assert(CanInsert(host,0,false)); assert(!CanInsert(host,6,false)); assert(!CanInsert(host,1,false));
	host.ids[0]=Heart; assert(!CanInsert(host,0,false)); assert(CanInsert(host,0,true));
	host.data.Slots|=1u<<7; assert(!CanInsert(host,0,true)); host.data.Slots=1u<<17;
	Refresh(c); assert(c.raid_augment.item==Heart);
	{ CastOrigin gem(&c,23,true);
	  { CastOrigin proc(&c,23,false); AfterHit(enemy,&c,100,23,false); assert(c.hp==300); }
	  AfterHit(enemy,&c,100,23,false); assert(c.hp==390);
	  AfterHit(enemy,&c,100,23,false); assert(c.hp==390); }
	host.ids[0]=Aegis; Refresh(c); AfterHit(c,&enemy,5,0,true); assert(!c.raid_augment.ward);
	Timer::now+=89999; c.hp=349; AfterHit(c,&enemy,1,0,true); assert(!c.raid_augment.ward);
	Timer::now+=1001; c.hp=349; c.buffs[0]={1,160,0}; AfterHit(c,&enemy,1,0,true);
	assert(!c.raid_augment.ward); c.buffs[0]={};
	enemy.owner=&c; AfterHit(c,&enemy,1,0,true); assert(!c.raid_augment.ward); enemy.owner=nullptr;
	{ CastOrigin proc(&enemy,23,false,true); AfterHit(c,&enemy,1,23,false); assert(!c.raid_augment.ward); }
	AfterHit(c,&enemy,1,0,true);
	assert(c.raid_augment.ward==120); int64_t damage=75; Incoming(c,&enemy,damage);
	assert(damage==0 && c.raid_augment.ward==45); damage=200; Incoming(c,&enemy,damage);
	assert(damage==155 && !c.raid_augment.ward);
	Timer::now+=91000; c.hp=350; AfterHit(c,&enemy,1,0,true); assert(!c.raid_augment.ward);
	c.hp=0; AfterHit(c,&enemy,1,0,true); assert(!c.raid_augment.ward);
	c.hp=1; AfterHit(c,&enemy,1,0,true); Timer::now+=12000; damage=20; Incoming(c,&enemy,damage); assert(damage==20);
	host.ids[0]=Prism; Refresh(c); Spend(c,1000,true); assert(!c.mana && !c.raid_augment.mana_spent);
	Timer::now+=91000; Spend(c,999,true); Spend(c,99,false); assert(!c.mana && !c.endurance);
	Spend(c,1,true); assert(c.mana==50 && !c.raid_augment.endurance_spent);
	Timer::now+=91000; Spend(c,90,false); c.raid_augment.ClearSpend(); Spend(c,10,false); assert(!c.endurance);
	host.ids[0]=Heart; Refresh(c); assert(!c.raid_augment.endurance_spent);
	c.hp=990; c.clock.storage=false; AfterHit(enemy,&c,2,65535,true); assert(c.hp==990);
	c.clock.storage=true; Timer::now+=91000; enemy.owner=&c; AfterHit(enemy,&c,2,65535,true); assert(c.hp==990);
	enemy.owner=nullptr; AfterHit(enemy,&c,2,65535,true); assert(c.hp==1000);
	c.level=49; Refresh(c); assert(!c.raid_augment.item);
	assert(FindDrop(71,71065)->item==Prism && FindDrop(186,76007)->item==Heart);
	assert(!FindDrop(48,72003) && !FindDrop(71,39138));
}

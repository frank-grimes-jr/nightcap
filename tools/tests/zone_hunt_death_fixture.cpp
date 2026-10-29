#include "common/zone_hunt_policy.h"
#include <cassert>
#include <map>
#include <set>
#include <vector>
using uint32=uint32_t;
namespace SpecialAbility {enum {AggroImmunity,BeingAggroImmunity,HarmFromClientImmunity};}
struct Item {uint32 id;};
struct LootdropEntriesRepository {struct Entry {int item_charges=0,equip_item=1;};static Entry NewNpcEntity(){return {};}};
struct Zone {
	struct RNG {std::vector<int> values;size_t calls=0;int Int(int a,int b){assert(a==0&&b==9999);return values.at(calls++);}} random;
	struct Time {bool night=true;bool IsNightTime(){return night;}} zone_time;
	uint32 zone_id=4,version=0,instance_id=0;uint32 GetZoneID(){return zone_id;}uint32 GetInstanceVersion(){return version;}
} instance,*zone=&instance;
struct ZoneDatabase {std::map<uint32,Item> items;const Item *GetItem(uint32 id){auto i=items.find(id);return i==items.end()?nullptr:&i->second;}} database;
struct WorldContentService {int era=0;static WorldContentService *Instance(){static WorldContentService service;return &service;}int GetCurrentExpansion(){return era;}};
struct NPC {
	bool owner=false,merc=false,swarm=false,restored=false;uint32 spawn=10,type=4001;int level=46;std::vector<uint32> drops;
	uint32 MerchantType=0;int npc_class=1,body=1;bool invul=false;std::set<int> abilities;
	int GetClass(){return npc_class;}int GetBodyType(){return body;}bool GetInvul(){return invul;}
	bool GetSpecialAbility(int a){return abilities.count(a)!=0;}
	uint32 GetSpawnPointID(){return spawn;}uint32 GetNPCTypeID(){return type;}bool HasOwner(){return owner;}bool IsMerc(){return merc;}
	bool GetSwarmInfo(){return swarm;}bool GetSwarmOwner(){return swarm;}bool IsQueuedForCorpse(){return restored;}int GetLevel(){return level;}
	void AddLootDrop(const Item *item,LootdropEntriesRepository::Entry entry,bool wear){assert(!wear&&entry.equip_item==0&&entry.item_charges==1);drops.push_back(item->id);}
};
namespace NightcapHunt {
struct Hunt {uint32 zone_id=4,augment=940024,gear=940028;int minimum=46;bool enabled=true,night_only=false;std::set<std::pair<uint32,uint32>> sources{{10,4001}};} hunt;
// ACTUAL_AWARD
}
int main() {
	using namespace NightcapHunt;
	for(uint32 id=940024;id<940032;++id)database.items.emplace(id,Item{id});
	NPC n;bool rolled=false;instance.random={{0,9999,0,6000},0};
	Award(n,false,rolled);assert((n.drops==std::vector<uint32>{940027,940029})&&rolled&&instance.random.calls==4);
	Award(n,false,rolled);assert(n.drops.size()==2&&instance.random.calls==4);
	for(int bad=0;bad<18;++bad) {
		n={};rolled=false;instance={};hunt={};WorldContentService::Instance()->era=0;
		hunt.sources.clear(); // Equipment must not mask augment rejection.
		switch(bad){case 0:n.spawn=0;break;case 1:n.merc=true;break;case 2:n.owner=true;break;case 3:n.swarm=true;break;
		case 4:n.restored=true;break;case 5:instance.version=1;break;case 6:WorldContentService::Instance()->era=1;break;
		case 7:n.MerchantType=1;break;case 8:n.npc_class=20;break;case 9:n.npc_class=0;break;
		case 10:n.body=11;break;case 11:n.body=60;break;case 12:n.body=66;break;case 13:n.body=67;break;
		case 14:n.invul=true;break;case 15:n.abilities.insert(SpecialAbility::AggroImmunity);break;
		case 16:n.abilities.insert(SpecialAbility::BeingAggroImmunity);break;case 17:n.abilities.insert(SpecialAbility::HarmFromClientImmunity);break;}
		Award(n,false,rolled);assert(!rolled&&n.drops.empty()&&instance.random.calls==0);
	}
	// Ordinary, named and private dungeon spawns need neither the old whitelist,
	// the old minimum level, nor the old Kithicor night gate for augments.
	for(uint32 instance_id : {0u,101u,102u}) {
		for(uint32 zone_id : {63u,73u,65u,66u,32u,76u,186u,20u}) {
			n={};n.level=1;n.type=999001;n.spawn=999001;rolled=false;instance={};hunt={};
			WorldContentService::Instance()->era=0;instance.instance_id=instance_id;
			instance.zone_id=zone_id;hunt.zone_id=zone_id;hunt.sources.clear();
			hunt.night_only=true;instance.zone_time.night=false;
			instance.random={{49,6000},0};Award(n,false,rolled);
			assert(rolled&&(n.drops==std::vector<uint32>{940025})&&instance.random.calls==2);
			Award(n,false,rolled);assert(instance.random.calls==2);
		}
	}
	// Exhaust the actual Award RNG domain: exactly 50 of 10,000 eligible deaths.
	int total=0;
	for(int roll=0;roll<10000;++roll) {
		n={};n.level=1;rolled=false;instance={};hunt={};hunt.sources.clear();
		instance.random={{roll,0},0};Award(n,false,rolled);
		total+=static_cast<int>(n.drops.size());assert(rolled);
		assert(instance.random.calls==(roll<50 ? 2u : 1u));
	}
	assert(total==50);
	// Each exclusion still suppresses both families when relevant; the legacy
	// equipment minimum and night restriction cannot suppress an augment roll.
	for(int gate=0;gate<3;++gate) {
		n={};rolled=false;instance={};hunt={};
		if(gate==0)n.level=45;
		if(gate==1){hunt.night_only=true;instance.zone_time.night=false;}
		if(gate==2)n.type=4002;
		instance.random={{0,0},0};Award(n,false,rolled);
		assert((n.drops==std::vector<uint32>{940024})&&instance.random.calls==2);
	}
	for(int gate=0;gate<3;++gate) {
		n={};rolled=false;instance={};hunt={};
		if(gate==0)hunt.enabled=false;
		if(gate==1)instance.zone_id=5;
		if(gate==2)rolled=true;
		Award(n,false,rolled);assert(n.drops.empty()&&instance.random.calls==0);
	}
	instance={};hunt={};n={};WorldContentService::Instance()->era=0;rolled=false;
	Award(n,true,rolled);assert(!rolled&&instance.random.calls==0); // charm faded during accepted death
	instance.random={{50,49,9800},0};Award(n,false,rolled);
	assert((n.drops==std::vector<uint32>{940031})&&instance.random.calls==3); // boundary and no quality draw for failed family
}

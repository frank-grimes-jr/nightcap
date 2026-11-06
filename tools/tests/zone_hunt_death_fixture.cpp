#include "common/zone_hunt_policy.h"
#include <cassert>
#include <map>
#include <set>
#include <vector>
using uint32=uint32_t;
struct Item {uint32 id;};
struct LootdropEntriesRepository {struct Entry {int item_charges=0,equip_item=1;};static Entry NewNpcEntity(){return {};}};
struct Zone {
	struct RNG {std::vector<int> values;size_t calls=0;int Int(int a,int b){assert(a==0&&b==9999);return values.at(calls++);}} random;
	struct Time {bool night=true;bool IsNightTime(){return night;}} zone_time;
	uint32 zone_id=4,version=0;uint32 GetZoneID(){return zone_id;}uint32 GetInstanceVersion(){return version;}
} instance,*zone=&instance;
struct ZoneDatabase {std::map<uint32,Item> items;const Item *GetItem(uint32 id){auto i=items.find(id);return i==items.end()?nullptr:&i->second;}} database;
struct WorldContentService {int era=0;static WorldContentService *Instance(){static WorldContentService service;return &service;}int GetCurrentExpansion(){return era;}};
struct NPC {
	bool owner=false,merc=false,swarm=false,restored=false;uint32 spawn=10,type=4001;int level=46;std::vector<uint32> drops;
	bool invulnerable=false,protected_npc=false;int body=1;
	int GetBodyType(){return body;}bool GetInvul(){return invulnerable;}bool GetSpecialAbility(int){return protected_npc;}
	uint32 GetSpawnPointID(){return spawn;}uint32 GetNPCTypeID(){return type;}bool HasOwner(){return owner;}bool IsMerc(){return merc;}
	bool GetSwarmInfo(){return swarm;}bool GetSwarmOwner(){return swarm;}bool IsQueuedForCorpse(){return restored;}int GetLevel(){return level;}
	void AddLootDrop(const Item *item,LootdropEntriesRepository::Entry entry,bool wear){assert(!wear&&entry.equip_item==0&&entry.item_charges==1);drops.push_back(item->id);}
};
namespace SpecialAbility {constexpr int AggroImmunity=1,BeingAggroImmunity=2,HarmFromClientImmunity=3;}
namespace NightcapDungeon {bool managed=false;bool Managed(){return managed;}}
namespace NightcapHunt {
struct Hunt {uint32 zone_id=4,augment=940024,gear=940028;int minimum=46,augment_chance=50,gear_chance=50;bool enabled=true,night_only=false;std::set<std::pair<uint32,uint32>> sources{{10,4001}};} hunt;
// ACTUAL_ELIGIBILITY
// ACTUAL_AWARD
}
int main() {
	using namespace NightcapHunt;
	for(uint32 id=940024;id<940032;++id)database.items.emplace(id,Item{id});
	NPC n;bool rolled=false;instance.random={{0,9999,0,6000},0};
	Award(n,false,rolled);assert((n.drops==std::vector<uint32>{940027,940029})&&rolled&&instance.random.calls==4);
	Award(n,false,rolled);assert(n.drops.size()==2&&instance.random.calls==4);
	for(int bad=0;bad<10;++bad) {
		n={};rolled=false;instance={};hunt={};WorldContentService::Instance()->era=0;
		switch(bad){case 0:n.invulnerable=true;break;case 1:n.protected_npc=true;break;case 2:n.owner=true;break;case 3:n.swarm=true;break;
		case 4:n.restored=true;break;case 5:instance.version=1;break;case 6:WorldContentService::Instance()->era=1;break;case 7:n.body=11;break;case 8:n.body=66;break;case 9:n.merc=true;break;}
		Award(n,false,rolled);assert(!rolled&&n.drops.empty()&&instance.random.calls==0);
	}
	instance={};hunt={};n={};WorldContentService::Instance()->era=0;rolled=false;
	Award(n,true,rolled);assert(!rolled&&instance.random.calls==0); // charm faded during accepted death
	instance.random={{50,49,9800},0};Award(n,false,rolled);
	assert((n.drops==std::vector<uint32>{940031})&&instance.random.calls==3); // boundary and no quality draw for failed family
	n={};rolled=false;hunt.augment_chance=150;hunt.gear_chance=0;instance.random={{149,0,0},0};Award(n,false,rolled);
	assert((n.drops==std::vector<uint32>{940024})&&instance.random.calls==3); // per-family zone chance; 0 never drops
	n={};rolled=false;instance.random={{150,9999},0};Award(n,false,rolled);
	assert(n.drops.empty()&&instance.random.calls==2); // 150 is exclusive
	// Every killable, unowned NPC qualifies: guards/named, low level, daytime,
	// merchants/service classes, and scripted actors without a spawn2 identity.
	for(int variant=0;variant<4;++variant) {
		n={};rolled=false;hunt={};instance={};n.type=999999;n.level=1;
		if(variant==1)n.spawn=0;
		if(variant==2){hunt.night_only=true;instance.zone_time.night=false;}
		if(variant==3)hunt.sources.clear();
		instance.random={{0,9800},0};Award(n,false,rolled);
		assert(rolled&&(n.drops==std::vector<uint32>{940027})&&instance.random.calls==2);
		Award(n,false,rolled);assert(instance.random.calls==2);
	}
	// Exactly 150 successes out of the full RNG domain, independent of sources.
	int successes=0;hunt={};hunt.augment_chance=150;hunt.sources.clear();
	for(int roll=0;roll<10000;++roll){n={};rolled=false;instance.random={{roll,0},0};Award(n,false,rolled);successes+=!n.drops.empty();}
	assert(successes==150);
	instance={};hunt={};n={};assert(CanDropAugment(n,false));
	hunt.enabled=false;assert(!CanDropAugment(n,false));
	NightcapDungeon::managed=true;instance.zone_id=760;assert(CanDropAugment(n,false));
	n.owner=true;assert(!CanDropAugment(n,false));n.owner=false;
	instance.zone_id=113;assert(CanDropAugment(n,false));
	NightcapDungeon::managed=false;assert(!CanDropAugment(n,false));
}

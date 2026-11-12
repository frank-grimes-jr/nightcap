#include "common/raid_augment_sources.h"
#include <cassert>
#include <set>
#include <string>
#include <vector>
#include <stdexcept>
#include <cstdint>
struct Mob {};
struct Client { unsigned CharacterID() const {return 7;} };
struct NPC {
	bool restored=false, staged=false, owner=false;
	unsigned id=32040, spawn=6461;
	std::vector<unsigned> loot;
	bool IsQueuedForCorpse() const {return restored;}
	bool HasOwner() const {return owner;}
	bool GetSwarmInfo() const {return false;}
	unsigned GetSwarmOwner() const {return 0;}
	bool IsMerc() const {return false;}
	std::string GetEntityVariable(const char*) {return staged?"1":"";}
	void SetEntityVariable(const char*,const char*) {staged=true;}
	unsigned GetNPCTypeID() const {return id;}
	unsigned GetSpawnPointID() const {return spawn;}
	const std::vector<unsigned>& GetLootItems() const {return loot;}
	void AddItem(unsigned item,int,bool){loot.push_back(item);}
};
struct Zone {
	unsigned version=0,id=32,instance=0;
	struct { unsigned value=0; unsigned Int(int,int){return value;} } random;
	unsigned GetZoneID()const{return id;} unsigned GetInstanceID()const{return instance;}
	unsigned GetInstanceVersion()const{return version;}
} location,*zone=&location;
struct {bool installed=true;bool GetItem(unsigned) const{return installed;}} database;
enum class Mode {Raid,Grind};
struct {Mode mode=Mode::Raid;unsigned seed=91;std::string id="test";} current;
bool managed=false,campaign=false,member_present=true,credited=true;
unsigned chosen_roll=0;
bool Managed(){return managed;} bool Campaign(){return campaign;}
struct Boss { unsigned objective=1; } fake_boss;
const Boss *Objective(unsigned spawn,unsigned npc){return spawn==6461 && npc==32040 ? &fake_boss : nullptr;}
std::set<unsigned> deaths,objectives;
std::vector<Client*> Credit(NPC*,Mob*) {static Client c;return credited?std::vector<Client*>{&c}:std::vector<Client*>{};}
struct Result {size_t RowCount()const{return member_present?1:0;}};
Result Query(const std::string&){return {};}
std::string Q(const std::string&s){return s;}
namespace fmt {template<class... T> std::string format(const char*,T...){return {};}}
unsigned Roll(unsigned,unsigned,unsigned,unsigned){return chosen_roll;}
template<class... T> void LogError(const char*, T...) {}
// ACTUAL_DROP
int main() {
	Mob killer; NPC n;
	for (const auto &d:NightcapRaidAug::Sources) {
		unsigned count=0;location.id=d.zone;
		for(unsigned i=0;i<100;++i){
			NPC trial;trial.id=d.npc;location.random.value=i;
			assert(PrepareRaidAugment(&trial,&killer,false));assert(trial.staged);
			count+=static_cast<unsigned>(trial.loot.size());
			auto original=trial.loot;assert(PrepareRaidAugment(&trial,&killer,false));assert(original==trial.loot);
			if(!original.empty()){assert(original[0]==d.item);}
		}
		assert(count==d.percent);
	}
	location.id=32;location.random.value=0;location.instance=1;
	assert(PrepareRaidAugment(&n,&killer,false) && n.loot.empty());
	managed=true;current.mode=Mode::Grind;assert(PrepareRaidAugment(&n,&killer,false) && n.loot.empty());
	current.mode=Mode::Raid;n.spawn=3;assert(PrepareRaidAugment(&n,&killer,false) && n.loot.empty());
	n.spawn=6461;member_present=false;assert(PrepareRaidAugment(&n,&killer,false) && n.loot.empty());
	member_present=true;credited=false;assert(PrepareRaidAugment(&n,&killer,false) && n.loot.empty());
	credited=true;deaths.insert(n.spawn);assert(PrepareRaidAugment(&n,&killer,false) && n.loot.empty());
	deaths.clear();objectives.insert(1);assert(PrepareRaidAugment(&n,&killer,false) && n.loot.empty());
	objectives.clear();n.restored=true;assert(PrepareRaidAugment(&n,&killer,false) && n.loot.empty());
	n.restored=false;assert(PrepareRaidAugment(&n,&killer,true) && n.loot.empty());
	assert(PrepareRaidAugment(&n,nullptr,false) && n.loot.empty());
	assert(PrepareRaidAugment(&n,&killer,false) && n.loot.size()==1 && n.staged);
}

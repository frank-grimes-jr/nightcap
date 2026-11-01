#include "common/zone_hunt_policy.h"
#include "common/zone_hunt_catalog.h"
#include <array>
#include <cassert>
#include <map>
#include <memory>
using uint8=uint8_t;using int16=int16_t;using int32=int32_t;
namespace EQ { namespace invaug { constexpr uint8 SOCKET_COUNT=6; } }
struct Data { std::array<uint8,6> AugSlotType{};int HeroicInt=0,HeroicWis=0;bool allowed=true; };
struct Item {
	Data data;int req=1,rec=1;uint32_t id=940024;std::array<std::shared_ptr<Item>,6> augs;
	bool IsClassCommon()const{return true;} const Data *GetItem()const{return &data;}
	uint32_t GetID()const{return id;}int GetItemRequiredLevel(bool)const{return req;}uint8 GetItemRecommendedLevel(bool)const{return static_cast<uint8>(rec);}
	const Item *GetAugment(uint8 n)const{return augs[n].get();}
};
struct Inventory {std::map<int16,Item> items;const Item *GetItem(int16 s)const{auto i=items.find(s);return i==items.end()?nullptr:&i->second;}};
class Client;
struct Bonuses {int HPRegen=0,ManaRegen=0,EnduranceRegen=0,ATK=0,SpellDmg=0,HealAmt=0;};
class Mob {
public:
	Bonuses itembonuses,spellbonuses;bool client=true;
	void ProcessItemCaps();int CalcRecommendedLevelBonus(uint8,uint8,int);
	int CalcHPRegenCap(){return 10000;}int CalcManaRegenCap(){return 10000;}int CalcEnduranceRegenCap(){return 10000;}int CalcItemATKCap(){return 10000;}
	bool IsOfClientBotMerc(){return true;}bool IsClient(){return client;}Client *CastToClient();bool FindBuff(int){return false;}
};
class Client:public Mob {
public:
	Inventory inv;uint8 level=50;
	uint8 GetLevel()const{return level;}const Inventory &GetInv()const{return inv;}
	bool CanEquipItem(const Data *d)const{return d->allowed;}
};
Client *Mob::CastToClient(){return static_cast<Client*>(this);}
constexpr int ItemSpellDmgCap=250,ItemHealAmtCap=250,SPELL_AVATAR_ST_PROC=0;
#define RuleI(category,rule) rule
bool IsValidSpell(int){return false;}
// ACTUAL_SCALING
namespace NightcapHunt {
// ACTUAL_HEADROOM
}
// ACTUAL_CAPS

int main() {
	using namespace NightcapHunt;
	std::array<int,4> counts{};for(int i=0;i<10000;++i)++counts[Quality(i)];
	assert((counts==std::array<int,4>{6000,3000,800,200}));
	DeathEligibility e{true,true,true,true,false,false,true,46,46};bool rolled=false;
	assert(BeginDeathRoll(rolled,e)&&rolled&&!BeginDeathRoll(rolled,e));
	for(int bad=0;bad<8;++bad) {
		auto copy=e;switch(bad){case 0:copy.enabled=false;break;case 1:copy.classic=false;break;case 2:copy.version_zero=false;break;
		case 3:copy.native_source=false;break;case 4:copy.owned=true;break;case 5:copy.restored=true;break;case 6:copy.night_allowed=false;break;case 7:copy.level=45;break;}
		rolled=false;assert(!BeginDeathRoll(rolled,copy)&&!rolled);
	}
	Client c;
	for(int16 s:std::array<int16,6>{2,7,12,17,18,19}) {auto &p=c.inv.items[s];p.data.AugSlotType[0]=22;p.augs[0]=std::make_shared<Item>();p.augs[0]->data.HeroicInt=10;p.augs[0]->data.HeroicWis=5;}
	assert(OutputHeadroom(c,false)==30&&OutputHeadroom(c,true)==15);
	c.itembonuses.SpellDmg=600;c.itembonuses.HealAmt=600;c.ProcessItemCaps();
	assert(c.itembonuses.SpellDmg==280&&c.itembonuses.HealAmt==265);
	c.level=49;assert(OutputHeadroom(c,false)==0);c.level=50;
	c.client=false;c.itembonuses.SpellDmg=600;c.ProcessItemCaps();assert(c.itembonuses.SpellDmg==250);c.client=true;
	for(auto &[s,p]:c.inv.items){p.augs[0]->data.HeroicInt=1;}
	assert(OutputHeadroom(c,false)==3); // aggregate before rounding
	c.inv.items[19].augs[0]->data.HeroicInt=0;assert(OutputHeadroom(c,false)==2);
	for(auto &[s,p]:c.inv.items){p.augs[0]->data.HeroicInt=10;p.rec=100;}
	assert(OutputHeadroom(c,false)==15); // actual recommended-level scaling
	for(auto &[s,p]:c.inv.items){p.rec=1;p.req=51;}assert(OutputHeadroom(c,false)==0);
	for(auto &[s,p]:c.inv.items){p.req=1;p.augs[0]->req=51;}assert(OutputHeadroom(c,false)==0);
	for(auto &[s,p]:c.inv.items){p.augs[0]->req=1;p.data.allowed=false;}assert(OutputHeadroom(c,false)==0);
	for(auto &[s,p]:c.inv.items){p.data.allowed=true;p.augs[0]->data.allowed=false;}assert(OutputHeadroom(c,false)==0);
	for(auto &[s,p]:c.inv.items){p.augs[0]->data.allowed=true;p.augs[0]->id=1001;}assert(OutputHeadroom(c,false)==0);
	for(auto &[s,p]:c.inv.items){p.augs[0]->id=940024;p.data.AugSlotType[0]=7;}assert(OutputHeadroom(c,false)==0);
	c.inv.items[15]=c.inv.items[2];c.inv.items[15].data.AugSlotType[0]=22;assert(OutputHeadroom(c,false)==0); // ring excluded
	c.inv.items[2].data.AugSlotType[0]=22;c.inv.items[2].data.AugSlotType[1]=22;c.inv.items[2].augs[1]=std::make_shared<Item>(*c.inv.items[2].augs[0]);
	assert(OutputHeadroom(c,false)==5); // malformed extra socket cannot exceed one credit per armor slot
	c.itembonuses.SpellDmg=2;c.ProcessItemCaps();assert(c.itembonuses.SpellDmg==2); // headroom never grants stats
}

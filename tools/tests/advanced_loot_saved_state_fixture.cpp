// Production serializer/restorer; explicit fake NPC/corpse/database dependencies.
#include <Windows.h>
#include <bcrypt.h>
#include <algorithm>
#include <cctype>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <vector>
#include "common/json/json.hpp"
#include "common/loot.h"
#include "zone/advanced_loot_saved_state.h"
void check(bool ok,const char *message){if(!ok)throw std::runtime_error(message);}
namespace fmt {
inline std::string format(std::string text){return text;}
template<class T,class... Rest> std::string format(std::string text,const T &value,const Rest &...rest){
	const auto at=text.find("{}");check(at!=std::string::npos,"fixture format");std::ostringstream out;out<<value;
	text.replace(at,2,out.str());return format(text,rest...);
}
}
namespace Strings { std::string ToLower(std::string text){for(char &c:text)c=static_cast<char>(std::tolower(static_cast<unsigned char>(c)));return text;} }
// Use the real MD5 algorithm through BCrypt, not a constant digest stub.
struct MD5 {
	static void Generate(const uint8 *bytes,size_t size,uint8 digest[16]){
		BCRYPT_ALG_HANDLE algorithm=nullptr;
		check(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_MD5_ALGORITHM,nullptr,0)>=0,"MD5 open");
		const auto result=BCryptHash(algorithm,nullptr,0,const_cast<PUCHAR>(bytes),static_cast<ULONG>(size),digest,16);
		BCryptCloseAlgorithmProvider(algorithm,0);check(result>=0,"MD5 hash");
	}
};
namespace EQ::Util {
struct UUID {
	std::string value;
	static UUID FromByteArray(const char *bytes){
		std::string text;const char *hex="0123456789abcdef";
		for(int i=0;i<16;++i){if(i==4||i==6||i==8||i==10)text+='-';const auto b=static_cast<unsigned char>(bytes[i]);text+=hex[b>>4];text+=hex[b&15];}
		return {text};
	}
	std::string ToString()const{return value;}
};
}
namespace NightcapLoot {
bool ValidDropID(const std::string &id){
	if(id.size()!=36)return false;
	for(size_t i=0;i<id.size();++i){if(i==8||i==13||i==18||i==23){if(id[i]!='-')return false;}else if(!std::isxdigit(static_cast<unsigned char>(id[i])))return false;}
	return true;
}
std::string NewDropID(){static uint32 next=1;char id[37]{};snprintf(id,sizeof(id),"11111111-1111-1111-1111-%012u",next++);return id;}
}
constexpr size_t MAX_LOOTERS=72;
#define LogError(...) ((void)0)
struct Database {bool missing=false;const void *GetItem(uint32 id){return !missing&&id?this:nullptr;} } database;
class NPC {
public:
	LootItems items;std::map<std::string,std::string> variables;std::array<uint32,4> coins{};bool fail_add=false;
	NPC()=default;NPC(const NPC&)=delete;virtual ~NPC(){ClearLootItems();}
	std::string GetEntityVariable(const char *key)const{const auto i=variables.find(key);return i==variables.end()?"":i->second;}
	void SetEntityVariable(const char *key,const std::string &value){variables[key]=value;}
	LootItems& GetLootItems(){return items;}void ClearLootItems(){for(auto i:items)delete i;items.clear();}
	void RemoveLootCash(){coins={};}void AddLootCash(uint32 c,uint32 s,uint32 g,uint32 p){coins={c,s,g,p};}
	void AddItem(uint32 id,uint16 charges,bool,uint32,uint32,uint32,uint32,uint32,uint32){if(!fail_add){auto i=new LootItem{};i->item_id=id;i->charges=charges;items.push_back(i);}}
	uint32 GetNPCTypeID(){return 22003;}
};
class Corpse : public NPC {
public:
	bool locked=false;std::vector<uint32> rights{77,88};uint32 delay=12345;
	bool IsNPCCorpse(){return true;}bool IsLocked(){return locked;}void Lock(){locked=true;}
	std::vector<uint32> AdvancedLootRights(){return rights;}uint32 AdvancedLootRightsDelay(){return delay;}
	void RestoreAdvancedLootRights(const std::vector<uint32>&r,uint32 d){rights=r;delay=d;}
};
namespace NightcapLoot { void SaveDistribution(Corpse*){} }
// ACTUAL_TRANSLATION_UNIT

static LootItem Example(){
	LootItem i{};i.item_id=13073;i.equip_slot=23;i.charges=5;i.aug_1=11;i.aug_2=12;i.aug_3=13;i.aug_4=14;i.aug_5=15;i.aug_6=16;
	i.attuned=true;i.custom_data="quote'\n^\\metadata";i.ornamenticon=201;i.ornamentidfile=202;i.ornament_hero_model=203;
	i.trivial_min_level=1;i.trivial_max_level=50;i.npc_min_level=2;i.npc_max_level=55;i.lootdrop_id=9;
	i.advanced_loot_id=NightcapLoot::NewDropID();return i;
}
static std::string Legacy(){return R"({"copper":7,"silver":3,"gold":2,"platinum":5,"entries":[{"item_id":13073,"charges":5,"lootdrop_id":0}]})";}
int main(){try{
	using namespace NightcapLoot;using Json=nlohmann::json;
	Corpse original;const auto item=Example();original.items.push_back(new LootItem(item));
	original.SetEntityVariable("nightcap:advloot-distribution","{\"retained\":true}");original.locked=true;
	const auto saved=SaveCorpseState(&original,Legacy());
	Corpse restored;check(RestoreCorpseItems(&restored,saved)==RestoreState::Restored,"corpse envelope not restored");
	StampRestoredDropIDs(&restored,saved,123,456);RestoreCorpseState(&restored,saved);
	check(restored.items.size()==1&&SamePhysicalLoot(item,*restored.items.front()),"corpse metadata changed");
	check(restored.coins==std::array<uint32,4>{7,3,2,5}&&restored.rights==original.rights&&restored.delay==12345&&restored.locked,"corpse rights/money/lock lost");
	check(restored.GetEntityVariable("nightcap:advloot-distribution")==original.GetEntityVariable("nightcap:advloot-distribution"),"distribution lost");
	check(restored.GetEntityVariable("nightcap:advloot-coin-id")==original.GetEntityVariable("nightcap:advloot-coin-id"),"purse identity changed");
	NPC living;living.items.push_back(new LootItem(item));const auto npc_saved=SaveNPCDropIDs(&living,Legacy());
	NPC resumed;check(RestoreCorpseItems(&resumed,npc_saved)==RestoreState::Restored,"living NPC envelope not restored");
	StampRestoredDropIDs(&resumed,npc_saved,123,456);
	check(SamePhysicalLoot(item,*resumed.items.front())&&resumed.GetEntityVariable("nightcap:advloot-coin-id")==living.GetEntityVariable("nightcap:advloot-coin-id"),"living NPC identity changed");
	// The same legacy checkpoint generates the same receipt keys on every replay.
	NPC first,second,different;for(auto n:{&first,&second,&different}){auto i=Example();i.advanced_loot_id.clear();n->items.push_back(new LootItem(i));}
	check(RestoreCorpseItems(&first,Legacy())==RestoreState::Legacy,"legacy classification failed");
	StampRestoredDropIDs(&first,Legacy(),123,456);StampRestoredDropIDs(&second,Legacy(),123,456);StampRestoredDropIDs(&different,Legacy(),124,456);
	check(first.items.front()->advanced_loot_id==second.items.front()->advanced_loot_id&&first.items.front()->advanced_loot_id!=different.items.front()->advanced_loot_id,"legacy item replay IDs unstable");
	check(first.GetEntityVariable("nightcap:advloot-coin-id")==second.GetEntityVariable("nightcap:advloot-coin-id"),"legacy purse replay IDs unstable");
	for(unsigned kind=0;kind<10;++kind){
		auto bad=Json::parse(saved);auto &row=bad["nightcap_advanced_loot_v1"]["items"][0];
		switch(kind){case 0:row["id"]="bad";break;case 1:row["item"]=0;break;case 2:row["charges"]=-1;break;
		case 3:row["charges"]=65536;break;case 4:row["slot"]=32768;break;case 5:row["attuned"]=17;break;
		case 6:row["custom"]=std::string(65536,'x');break;case 7:bad["nightcap_advanced_loot_v1"]["items"].push_back(row);break;
		case 8:bad["copper"]=-1;break;case 9:database.missing=true;break;}
		Corpse attempt;const auto raw=bad.dump();check(RestoreCorpseItems(&attempt,raw)==RestoreState::Invalid,"bad loot accepted");
		RestoreCorpseState(&attempt,raw);check(attempt.items.empty()&&attempt.coins==std::array<uint32,4>{}&&attempt.locked,"invalid loot not quarantined");
		check(SaveCorpseState(&attempt,Legacy())==raw,"quarantined evidence overwritten");database.missing=false;
	}
	for(unsigned kind=0;kind<4;++kind){
		auto bad=Json::parse(saved);auto &state=bad["nightcap_advanced_loot_v1"];
		switch(kind){case 0:state["rights"]={0};break;case 1:state["rights_delay"]=-1;break;case 2:state["coin_id"]="bad";break;case 3:state["locked"]=17;break;}
		Corpse attempt;const auto raw=bad.dump();check(RestoreCorpseItems(&attempt,raw)==RestoreState::Restored,"fixture item restore");
		RestoreCorpseState(&attempt,raw);check(attempt.locked&&SaveCorpseState(&attempt,Legacy())==raw,"bad rights were unlocked or evidence lost");
	}
	NPC failed;failed.fail_add=true;check(RestoreCorpseItems(&failed,saved)==RestoreState::Invalid&&failed.items.empty(),"incomplete item restore accepted");
	NPC mismatch;StampRestoredDropIDs(&mismatch,Legacy(),123,456);check(!mismatch.GetEntityVariable("nightcap:advloot-invalid-state").empty(),"legacy count mismatch ignored");
	NPC empty;check(RestoreCorpseItems(&empty,"")==RestoreState::Invalid&&!empty.GetEntityVariable("nightcap:advloot-invalid-state").empty(),"empty invalid checkpoint unlocked");
	std::cout<<"PASS: production saved-state complete metadata/rights/coin/distribution roundtrip, living NPCs, stable legacy replay IDs, malformed state and partial-restore quarantine\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}

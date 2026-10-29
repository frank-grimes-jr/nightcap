#include "common/zone_hunt_catalog.h"
#include "common/zone_hunt_policy.h"
#include <cassert>
#include <map>
#include <set>
#include <string>
#include <vector>
using uint32=uint32_t;
namespace fmt {
template<class... Args>std::string format(const char *text,Args... args) {
	std::string result=text;
	for(auto value : {static_cast<uint64_t>(args)...})result.replace(result.find("{}"),2,std::to_string(value));
	return result;
}
}
#define LogInfo(...) (void)0
struct Zone {uint32 id=186,version=0;uint32 GetZoneID(){return id;}uint32 GetInstanceVersion(){return version;}};
struct WorldContentService {int era=0;static WorldContentService *Instance(){static WorldContentService s;return &s;}int GetCurrentExpansion(){return era;}};
struct Result {
	std::vector<std::vector<const char*>> rows;bool success=true;
	struct Iterator {std::vector<std::vector<const char*>>::iterator i;const char* operator[](size_t n){return (*i)[n];}
		Iterator &operator++(){++i;return *this;}bool operator!=(const Iterator &other)const{return i!=other.i;}
		std::vector<const char*> operator*(){return *i;}};
	bool Success(){return success;}size_t RowCount(){return rows.size();}
	Iterator begin(){return {rows.begin()};}Iterator end(){return {rows.end()};}
};
struct DB {
	Result config{{{"940592","940596","46","0"}},true},sources{{},true};
	std::set<uint32> items;std::vector<std::string> queries;
	Result QueryDatabase(std::string q,bool){queries.push_back(q);return queries.size()==1 ? config : sources;}
	bool GetItem(uint32 id){return items.count(id)!=0;}
} database;
namespace NightcapHunt {
struct Hunt {uint32 zone_id=0,augment=0,gear=0;int minimum=0;bool enabled=false,night_only=false;std::set<std::pair<uint32,uint32>> sources;} hunt;
// ACTUAL_LOAD
}
int main() {
	using namespace NightcapHunt;
	Zone z;
	auto reset=[&](){database={};z={};WorldContentService::Instance()->era=0;
		for(uint32 id=940592;id<940600;++id)database.items.insert(id);};
	reset();Load(z);
	assert(hunt.enabled&&hunt.zone_id==186&&hunt.augment==940592&&hunt.sources.empty());
	assert(database.queries[0].find("z.zone_id=186 AND z.enabled=1")!=std::string::npos);
	assert(database.queries[0].find("s.enabled=1 AND s.revision=2026100901")!=std::string::npos);
	for(int bad=0;bad<8;++bad) {
		reset();
		switch(bad){case 0:z.version=1;break;case 1:WorldContentService::Instance()->era=1;break;
		case 2:database.config.success=false;break;case 3:database.config.rows.clear();break;
		case 4:database.config.rows.push_back(database.config.rows[0]);break;
		case 5:database.items.erase(940595);break;case 6:database.sources.success=false;break;
		case 7:database.config.rows[0][0]="1";break;}
		Load(z);assert(!hunt.enabled);
	}
	reset();database.sources.rows={{"10","4001"}};Load(z);
	assert(hunt.enabled&&hunt.sources.count({10,4001})==1);
}

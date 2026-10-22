#include <cstdint>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#define LogTasks(...)
#define LogTasksDetail(...)
#define RuleB(...) true
namespace glm { struct vec4 { float x=0,y=0,z=0,w=0; }; }
enum class TaskActivityType { Deliver, Loot, Explore };
constexpr int METHODQUEST=2, ActivityActive=1;
namespace Tasks {
bool IsInMatchList(const std::string &a,const std::string &b) { return ("|"+a+"|").find("|"+b+"|")!=std::string::npos; }
bool IsInMatchListPartial(const std::string &a,const std::string &b) { return b.find(a)!=std::string::npos; }
}
struct Item { uint32_t ID; std::string Name; };
struct Database {
	std::map<int,Item> items;
	const Item *GetItem(int id) { auto i=items.find(id); return i==items.end()?nullptr:&i->second; }
} database;
struct Client { glm::vec4 pos; const glm::vec4 &GetPosition() const { return pos; } };
struct Mob { std::string GetName(){return "Shakrn_Meadowgreen";} std::string GetCleanName(){return GetName();} int GetNPCTypeID(){return 14075;} };
struct Zone { int id=14,version=0; int GetZoneID(){return id;} int GetInstanceVersion(){return version;} } z;
Zone *zone=&z;
struct ActivityInformation {
	int goal_method=0,dz_switch_id=0;
	TaskActivityType activity_type=TaskActivityType::Deliver;
	bool has_area=false;
	float min_x=-10,max_x=10,min_y=-10,max_y=10,min_z=-10,max_z=10;
	std::string item_id_list="13737",npc_match_list="14075";
	bool CheckZone(int id,int version) const { return id==14 && version==0; }
};
struct ClientActivityInformation { int activity_state=ActivityActive,activity_id=0; };
struct TaskUpdateFilter {
	int method=0,dz_switch_id=0,item_id=0;
	TaskActivityType type=TaskActivityType::Deliver;
	bool ignore_area=false,use_pos=false;
	glm::vec4 pos; Mob *mob=nullptr;
};
struct ClientTaskState {
	bool CanUpdate(Client*,const TaskUpdateFilter&,int,const ActivityInformation&,const ClientActivityInformation&) const;
};
// CAN_UPDATE_METHOD
void require(bool ok,const char *why) { if(!ok) throw std::runtime_error(why); }
int main() { try {
	for(auto [id,name]:std::map<int,std::string>{{13737,"Aviak Charm"},{213737,"Aviak Charm (Polished)"},
		{413737,"Aviak Charm (Exalted)"},{613737,"Aviak Charm (Ascended)"},{813737,"Aviak Charm (Ascended)"},
		{213738,"Aviak Charm (Polished)"},{13738,"Wrong Charm"}}) database.items.emplace(id,Item{uint32_t(id),name});
	Client c; Mob npc; ClientTaskState t; TaskUpdateFilter f; f.mob=&npc;
	ActivityInformation a; ClientActivityInformation s;
	auto ok=[&](){return t.CanUpdate(&c,f,1,a,s);};
	for(int id:{13737,213737,413737,613737}) { f.item_id=id; require(ok(),"delivery tier rejected"); }
	for(int id:{813737,213738,940001,960001}) { f.item_id=id; require(!ok(),"unrelated delivery accepted"); }
	f.item_id=213737; a.item_id_list="10032|13737"; require(ok(),"alternate ID list failed");
	a.item_id_list="213737"; require(ok(),"exact quality failed");
	f.item_id=413737; require(!ok(),"explicit quality weakened");
	a.item_id_list="13737"; a.activity_type=f.type=TaskActivityType::Loot;
	require(!ok(),"non-delivery objective changed");
	a.activity_type=f.type=TaskActivityType::Deliver;
	z.id=22; require(!ok(),"wrong zone credited"); z.id=14;
	s.activity_state=0; require(!ok(),"inactive objective credited"); s.activity_state=ActivityActive;
	f.mob=nullptr; require(!ok(),"wrong NPC credited"); f.mob=&npc;
	a.has_area=true; c.pos.x=20; require(!ok(),"out-of-range credited"); c.pos.x=0;
	a.goal_method=METHODQUEST; require(!ok(),"script-only objective credited");
	std::cout<<"Task delivery regressions passed\n";
} catch(const std::exception &e) { std::cerr<<e.what()<<'\n'; return 1; } }

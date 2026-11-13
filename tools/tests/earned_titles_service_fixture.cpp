#include "common/earned_title_policy.h"
#include <cassert>
#include <cmath>
#include <cstdarg>
#include <cstdio>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fmt {
inline void Fill(std::ostringstream &o,const std::string &s) { o<<s; }
template<class T,class... Rest> void Fill(std::ostringstream &o,const std::string &s,T v,Rest... rest) {
 const auto at=s.find("{}"); assert(at!=std::string::npos);
 o<<s.substr(0,at)<<v; Fill(o,s.substr(at+2),rest...);
}
template<class... Args> std::string format(const std::string &s,Args... args) { std::ostringstream o; Fill(o,s,args...); return o.str(); }
}
namespace Strings { inline unsigned ToUnsignedInt(const char *s) { return static_cast<unsigned>(std::stoul(s)); } }
namespace Chat { constexpr int White=0,Yellow=1; }
namespace ConsiderColor { constexpr unsigned Gray=0; }
namespace EQ { namespace skills { enum SkillType { First=0 }; } }
namespace TitlesRepository {
struct Titles { unsigned id=0; std::string prefix,suffix; };
inline Titles NewEntity() { return {}; }
}
struct Manager { std::vector<TitlesRepository::Titles> titles; const auto &GetTitles() { return titles; } } title_manager;
struct Result {
 bool ok=true; unsigned affected=0;
 std::vector<std::vector<std::string>> rows;
 bool Success() const { return ok; }
 unsigned RowsAffected() const { return affected; }
 unsigned RowCount() const { return static_cast<unsigned>(rows.size()); }
 struct Row { const std::vector<std::string> *r; const char *operator[](size_t i) const { return r->at(i).c_str(); } };
 struct It {
  const std::vector<std::vector<std::string>> *r; size_t i;
  const char *operator[](size_t n) const { return r->at(i).at(n).c_str(); }
  Row operator*() const { return {&r->at(i)}; }
  It &operator++() { ++i; return *this; }
  bool operator!=(const It &o) const { return i!=o.i; }
 };
 It begin() const { return {&rows,0}; } It end() const { return {&rows,rows.size()}; }
};
struct DB {
 bool enabled=true,fail=false,uncertain=false;
 std::map<unsigned,uint64_t> counters;
 std::map<unsigned,unsigned> skills;
 std::set<unsigned> awards;
 std::vector<std::vector<std::string>> clears,bosses,tasks;
 unsigned writes=0;
 Result QueryDatabase(const std::string &s,bool) {
  if (fail) { Result r; r.ok=false; return r; }
  Result r;
  if (s.find("SELECT enabled")==0) { r.rows={{enabled?"1":"0"}}; }
  else if (s.find("SELECT title_id")==0) { for (auto id:awards) { r.rows.push_back({std::to_string(id)}); } }
  else if (s.find("SELECT skill_id")==0) { for (auto kv:skills) { r.rows.push_back({std::to_string(kv.first),std::to_string(kv.second)}); } }
  else if (s.find("SELECT counter_id")==0) { for (auto kv:counters) { r.rows.push_back({std::to_string(kv.first),std::to_string(kv.second)}); } }
  else if (s.find("SELECT DISTINCT r.zone_id,r.mode")==0) { r.rows=clears; }
  else if (s.find("SELECT DISTINCT r.zone_id,k.boss_id")==0) { r.rows=bosses; }
  else if (s.find("SELECT DISTINCT taskid")==0) { r.rows=tasks; }
  else if (s.find("INSERT IGNORE INTO nightcap_title_awards")==0) {
   std::smatch match; assert(std::regex_search(s,match,std::regex("VALUES \\([0-9]+,([0-9]+),")));
   r.affected=awards.insert(static_cast<unsigned>(std::stoul(match[1]))).second; ++writes;
   if (uncertain) { r.ok=false; uncertain=false; }
  } else if (s.find("INSERT INTO nightcap_title_counters")==0) {
   std::regex re("\\([0-9]+,([0-9]+),1\\)");
   for (auto i=std::sregex_iterator(s.begin(),s.end(),re);i!=std::sregex_iterator();++i) {
    auto &n=counters[static_cast<unsigned>(std::stoul((*i)[1]))]; n=std::min(uint64_t(10000),n+1);
   }
   ++writes;
  } else { assert(false && "unexpected SQL"); }
  return r;
 }
} database;
unsigned errors=0;
template<class... Args> void LogError(const char *,Args...) { ++errors; }
struct Client {
 unsigned id=42,level=1,admin=0,con=1;
 bool gm=false,connected=true,loaded=true,dead=false;
 float pos=0; int hp=100;
 std::map<unsigned,unsigned> raw,caps;
 std::vector<Client*> party;
 std::vector<std::string> messages;
 unsigned CharacterID() const { return id; } unsigned GetLevel() const { return level; }
 unsigned Admin() const { return admin; } bool GetGM() const { return gm; }
 bool Connected() const { return connected; } bool ClientDataLoaded() const { return loaded; }
 unsigned GetRawSkill(EQ::skills::SkillType n) const { auto i=raw.find(n); return i==raw.end()?0:i->second; }
 unsigned MaxSkill(EQ::skills::SkillType n,unsigned,unsigned) const { auto i=caps.find(n); return i==caps.end()?0:i->second; }
 std::vector<unsigned> GetMulticlassList() const { return {1,2}; }
 bool IsDead() const { return dead; } int GetHP() const { return hp; }
 unsigned GetLevelCon(unsigned) const { return con; }
 float GetPosition() const { return pos; }
 std::vector<Client*> GetPartyMembers() { return party.empty()?std::vector<Client*>{this}:party; }
 void Message(int,const char *format,...) {
  char out[2048]; va_list args; va_start(args,format); vsnprintf(out,sizeof(out),format,args); va_end(args); messages.push_back(out);
 }
};
struct NPC {
 unsigned spawn=1,body=3,npc=1; float pos=0; bool transient=false;
 std::map<std::string,std::string> vars;
 unsigned GetSpawnPointID() const { return spawn; } unsigned GetBodyType() const { return body; }
 unsigned GetNPCTypeID() const { return npc; } unsigned GetLevel() const { return 10; }
 float GetPosition() const { return pos; }
 std::string GetEntityVariable(const char *s) { return vars[s]; }
 void SetEntityVariable(const char *key,const char *value) { vars[key]=value; }
};
struct Zone { unsigned id=63; unsigned GetZoneID() const { return id; } } zone_instance;
Zone *zone=&zone_instance;
namespace NightcapDungeon {
bool campaign=false;
bool Campaign() { return campaign; }
bool HighkeepTransient(NPC *n) { return n->transient; }
}
inline float DistanceSquared(float a,float b) { return (a-b)*(a-b); }

// ACTUAL_SERVICE

int main() {
 using namespace NightcapTitles;
 Client c; std::vector<TitlesRepository::Titles> out;
 database.enabled=false;
 AppendEligible(&c,{},out); assert(out.empty() && database.writes==0);
 NPC n; RecordKill(&n,&c,false); assert(database.counters.empty());
 database.enabled=true; database.counters[1]=99;
 NPC first; RecordKill(&first,&c,false);
 assert(database.counters[1]==100 && database.counters[2]==1 && database.awards.count(1900000001));
 const auto messages=c.messages.size(); RecordKill(&first,&c,false);
 assert(database.counters[1]==100 && c.messages.size()==messages);
 NPC excluded; RecordKill(&excluded,&c,true); assert(database.counters[1]==100);
 NPC gray; c.con=0; RecordKill(&gray,&c,false); assert(database.counters[1]==100); c.con=1;
 NPC far; c.pos=201; RecordKill(&far,&c,false); assert(database.counters[1]==100); c.pos=0;
 c.admin=50; NPC gm; RecordKill(&gm,&c,false); assert(database.counters[1]==100); c.admin=0;
 NPC story; NightcapDungeon::campaign=true; RecordKill(&story,&c,false); assert(database.counters[1]==100); NightcapDungeon::campaign=false;
 AppendEligible(&c,{},out); assert(out.size()==1 && out[0].prefix=="Hunter");
 out.clear(); c.raw[1]=200; c.caps[1]=200; database.skills[1]=199; c.level=50;
 AppendEligible(&c,{},out); assert(!database.awards.count(1900000101)); // persisted skill still short
 database.skills[1]=200; CheckSkill(&c,1); assert(database.awards.count(1900000101));
 c.raw[1]=0; database.skills[1]=0; c.caps[1]=0;
 out.clear(); AppendEligible(&c,{},out);
 assert(std::any_of(out.begin(),out.end(),[](const auto &t){return t.id==1900000101;})); // permanent after class release
 database.clears={{"76","1"},{"186","1"},{"71","0"}};
 auto s=Read(&c); assert(s.raid_zones.size()==1 && s.raid_zones.count(186) && !s.raid_zones.count(71));
 database.bosses={{"32","13"},{"73","8"}}; s=Read(&c);
 assert(s.counters[100]==1 && s.counters[101]==1 && s.counters[1]==100);
 database.tasks={{"9515"}}; out.clear(); AppendEligible(&c,{},out);
 assert(std::any_of(out.begin(),out.end(),[](const auto &t){return t.suffix=="the Last Lantern";}));
 assert(Name(1900000151,true)=="the Last Lantern" && Name(1900000151,false).empty());
 title_manager.titles.push_back({1900000001,"foreign",""}); out.clear(); AppendEligible(&c,{},out);
 assert(out.empty()); title_manager.titles.clear();
 const auto saved=database.awards.size(); database.fail=true; out.clear(); AppendEligible(&c,{},out);
 assert(out.empty() && database.awards.size()==saved); database.fail=false;
 database.uncertain=true; const auto d=Find(1900000002); assert(d);
 try { Grant(&c,*d); assert(false); } catch (const std::runtime_error &) {}
 assert(database.awards.count(d->id)); // commit happened; acknowledgment lost
 out.clear(); AppendEligible(&c,{},out);
 assert(std::any_of(out.begin(),out.end(),[d](const auto &t){return t.id==d->id;}));
 assert(errors>=2);
}

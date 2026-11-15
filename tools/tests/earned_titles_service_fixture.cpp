#include "common/earned_title_policy.h"
#include <cassert>
#include <cmath>
#include <chrono>
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
 bool enabled=true,fail=false,uncertain=false,in_transaction=false;
 unsigned saved_level=50;
 std::map<unsigned,uint64_t> counters;
 std::map<unsigned,std::map<unsigned,uint64_t>> other_counters;
 std::map<unsigned,unsigned> skills;
 std::set<unsigned> awards;
 std::map<unsigned,std::set<unsigned>> other_awards;
 std::vector<std::vector<std::string>> clears,bosses,tasks;
 unsigned writes=0,queries=0;
 auto &Counters(unsigned character) { return character==42 ? counters : other_counters[character]; }
 auto &Awards(unsigned character) { return character==42 ? awards : other_awards[character]; }
 Result QueryDatabase(const std::string &s,bool) {
  ++queries;
  if (fail) { Result r; r.ok=false; return r; }
  Result r;
  if (s.find("SELECT enabled")==0) { r.rows={{enabled?"1":"0",in_transaction?"1":"0"}}; }
  else if (s.find("SELECT level FROM character_data")==0) { r.rows={{std::to_string(saved_level)}}; }
  else if (s.find("SELECT character_id,counter_id,value")==0) {
   const auto begin=s.find(" IN (")+5;
   std::stringstream input(s.substr(begin,s.size()-begin-1));std::string id;
   while (std::getline(input,id,',')) {
    const auto character=static_cast<unsigned>(std::stoul(id));
    for (auto kv:Counters(character)) { r.rows.push_back({id,std::to_string(kv.first),std::to_string(kv.second)}); }
   }
  }
  else if (s.find("SELECT character_id,title_id")==0) {
   const auto begin=s.find(" IN (")+5;
   std::stringstream input(s.substr(begin,s.size()-begin-1));std::string id;
   while (std::getline(input,id,',')) {
    for (auto title:Awards(static_cast<unsigned>(std::stoul(id)))) { r.rows.push_back({id,std::to_string(title)}); }
   }
  }
  else if (s.find("SELECT title_id")==0) { for (auto id:awards) { r.rows.push_back({std::to_string(id)}); } }
  else if (s.find("SELECT skill_id")==0) { for (auto kv:skills) { r.rows.push_back({std::to_string(kv.first),std::to_string(kv.second)}); } }
  else if (s.find("SELECT counter_id")==0) { for (auto kv:counters) { r.rows.push_back({std::to_string(kv.first),std::to_string(kv.second)}); } }
  else if (s.find("SELECT DISTINCT r.zone_id,r.mode")==0) { r.rows=clears; }
  else if (s.find("SELECT DISTINCT r.zone_id,k.boss_id")==0) { r.rows=bosses; }
  else if (s.find("SELECT DISTINCT taskid")==0) { r.rows=tasks; }
  else if (s.find("INSERT IGNORE INTO nightcap_title_awards")==0) {
   std::smatch match; assert(std::regex_search(s,match,std::regex("VALUES \\(([0-9]+),([0-9]+),")));
   r.affected=Awards(static_cast<unsigned>(std::stoul(match[1]))).insert(static_cast<unsigned>(std::stoul(match[2]))).second; ++writes;
   if (uncertain) { r.ok=false; uncertain=false; }
  } else if (s.find("INSERT INTO nightcap_title_counters")==0) {
   std::regex re("\\(([0-9]+),([0-9]+),1\\)");
   for (auto i=std::sregex_iterator(s.begin(),s.end(),re);i!=std::sregex_iterator();++i) {
    auto &n=Counters(static_cast<unsigned>(std::stoul((*i)[1])))[static_cast<unsigned>(std::stoul((*i)[2]))]; n=std::min(uint64_t(10000),n+1);
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
 std::map<std::string,std::string> vars;
 unsigned title_notifications=0;
 std::string GetEntityVariable(const std::string &key) const { auto i=vars.find(key);return i==vars.end()?"":i->second; }
 void SetEntityVariable(const std::string &key,const std::string &value) { vars[key]=value; }
 void NotifyNewTitlesAvailable() { ++title_notifications; }
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
 AppendEligible(&c,{},out); assert(out.size()==1 && out[0].prefix=="Hunter" && out[0].suffix=="the Hunter");
 assert(Name(1900000012,false)=="Flamebreaker" && Name(1900000012,true)=="the Flamebreaker");
 for (const auto &d:Catalog) { assert(Name(d.id,true).size()<32 && (d.suffix || !Name(d.id,false).empty())); }
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
 database=DB{}; Client second; second.id=43; c=Client{};
 c.party={&c,&second}; NPC party_kill;
 const auto query_start=database.queries;
 RecordKill(&party_kill,&c,false);
 assert(database.queries-query_start==4); // settings + one write + two reads, independent of party size
 assert(database.counters[1]==1 && database.other_counters[43][1]==1);
 database=DB{}; database.counters[1]=99;
 NPC threshold; RecordKill(&threshold,&c,false);
 assert(database.counters[1]==100 && database.other_counters[43][1]==1);
 assert(database.awards.count(1900000001) && database.other_awards[43].empty());
 database=DB{}; std::vector<Client> raid(72);
 for (unsigned i=0;i<raid.size();++i) { raid[i].id=42+i; raid[0].party.push_back(&raid[i]); }
 NPC raid_kill; RecordKill(&raid_kill,&raid[0],false);
 assert(database.queries==4 && database.counters[1]==1 && database.other_counters[113][1]==1);
 raid[0].party.push_back(&raid[0]); // duplicate member is still counted once
 raid[1].dead=true; raid[2].pos=201; NPC mixed_kill;
 RecordKill(&mixed_kill,&raid[0],false);
 assert(database.counters[1]==2 && database.other_counters[43][1]==1 && database.other_counters[44][1]==1);
 database=DB{}; c=Client{}; c.level=50;
 database.counters[100]=1; database.clears={{"36","1"}}; database.tasks={{"9515"}};
 RequestCheck(&c); assert(database.awards.empty());
 Pulse(&c); // login/committed completion requests work without title picker or #titles
 assert(database.awards.count(1900000012) && database.awards.count(1900000016));
 assert(database.awards.count(1900000150) && database.awards.count(1900000151));
 assert(c.title_notifications==database.awards.size());
 const auto announced=c.title_notifications, quiet_queries=database.queries;
 Pulse(&c); assert(database.queries==quiet_queries); // clean client: no SQL per frame
 RequestCheck(&c); Pulse(&c); assert(c.title_notifications==announced); // no repeat notices
 database=DB{}; c=Client{}; c.level=50; database.saved_level=49;
 c.raw[1]=200;c.caps[1]=200;database.skills[1]=200;
 RequestCheck(&c);Pulse(&c);
 assert(!database.awards.count(1900000150) && !database.awards.count(1900000101));
 database.saved_level=50;c.SetEntityVariable("nightcap:title-check-at","0");Pulse(&c);
 assert(database.awards.count(1900000150) && database.awards.count(1900000101));
 database=DB{};c=Client{};database.counters[100]=1;database.in_transaction=true;
 RequestCheck(&c);Pulse(&c);assert(database.awards.empty() && c.title_notifications==0);
 database.in_transaction=false;c.SetEntityVariable("nightcap:title-check-at","0");Pulse(&c);
 assert(database.awards.count(1900000012) && c.title_notifications==1);
 database=DB{};c=Client{};database.counters[100]=1;database.fail=true;
 RequestCheck(&c);Pulse(&c);const auto failed_queries=database.queries;
 Pulse(&c);assert(database.queries==failed_queries && c.title_notifications==0);
 database.fail=false;c.SetEntityVariable("nightcap:title-check-at","0");Pulse(&c);
 assert(database.awards.count(1900000012) && c.title_notifications==1);
 database=DB{};c=Client{};database.counters[100]=1;c.loaded=false;
 RequestCheck(&c);Pulse(&c);assert(database.queries==0);
 c.loaded=true;Pulse(&c);assert(database.awards.count(1900000012));
 database=DB{};c=Client{};database.counters[1]=99;database.in_transaction=true;
 NPC committed;RecordKill(&committed,&c,false);
 assert(database.counters[1]==100 && database.awards.empty());
 database.in_transaction=false;Pulse(&c);
 assert(database.counters[1]==100 && database.awards.count(1900000001) && c.title_notifications==1);
 database=DB{};c=Client{};database.counters[1]=99;database.in_transaction=true;
 NPC rolled_back;RecordKill(&rolled_back,&c,false);
 database.counters[1]=99;database.in_transaction=false;Pulse(&c);
 assert(database.counters[1]==99 && database.awards.empty() && c.title_notifications==0);
}

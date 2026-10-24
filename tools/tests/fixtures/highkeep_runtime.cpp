// Executes the actual native coordinator with explicit engine/storage doubles.
#include "common/highkeep_policy.h"
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <cstring>
namespace glm { struct vec4 {float x=0,y=0,z=0,w=0;}; }
float DistanceSquared(const glm::vec4&a,const glm::vec4&b) {return (a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y)+(a.z-b.z)*(a.z-b.z);}
namespace Chat {constexpr int White=0,Yellow=15,Shout=3;}
namespace SpecialAbility {constexpr int CharmImmunity=14,FleeingImmunity=21,AllowBeneficial=38,NPCDamageImmunity=48,DisableMelee=39,AggroImmunity=24;}
constexpr int FACTION_ALLY=1,FACTION_INDIFFERENTLY=5,FACTION_SCOWLS=9;
namespace GravityBehavior {constexpr int Water=0;}
namespace Strings {std::string ToLower(std::string s){for(auto &c:s)c=static_cast<char>(tolower(c));return s;}}
namespace Saylink {std::string Silent(const char*,const char*label){return label;}}
namespace fmt {
template<class T> std::string Value(T v){std::ostringstream s;s<<v;return s.str();}
template<class...T> std::string format(std::string s,T...args){
 std::vector<std::string> a{Value(args)...};for(const auto &v:a){auto p=s.find("{}");assert(p!=s.npos);s.replace(p,2,v);}return s;
}}
void strn0cpy(char*to,const char*from,size_t size){auto n=std::min(size-1,strlen(from));memcpy(to,from,n);to[n]=0;}
template<class...T>void LogError(const char*,T...){}
struct NPCType {
 char name[64]{},special_abilities[512]{};unsigned npc_id=0,loottable_id=0,npc_spells_id=0,npc_spells_effects_id=0,emoteid=0,merchanttype=0;
 int exp_mod=100,npc_faction_id=0;int64_t current_hp=1500,max_hp=1500,hp_regen=1,hp_regen_per_second=0;
};
struct NPC;
struct Mob {
 virtual ~Mob()=default;
 unsigned id=0,type=0;bool client=false,npc=false,engaged=false,dead=false,connected=true,loaded=true,ai=false,casting=false,los=true;
 Mob *owner=nullptr,*target=nullptr;glm::vec4 position;int64_t hp=100;
 std::map<std::string,std::string> vars;
 bool IsClient(){return client;}bool IsNPC(){return npc;}bool HasOwner(){return owner!=nullptr;}bool IsPet(){return owner!=nullptr;}bool IsMerc(){return false;}
 Mob*GetUltimateOwner(){return owner?owner:this;}NPC*CastToNPC();
 unsigned GetID(){return id;}unsigned GetNPCTypeID(){return type;}bool IsEngaged(){return engaged;}Mob*GetTarget(){return target;}
 glm::vec4 GetPosition(){return position;}int64_t GetHP(){return hp;}
 void SetEntityVariable(const std::string&k,const std::string&v){vars[k]=v;}std::string GetEntityVariable(const std::string&k){return vars[k];}
};
struct Client:Mob {
 unsigned character=0;Client(){client=true;}
 bool Connected(){return connected;}bool ClientDataLoaded(){return loaded;}bool IsDead(){return dead;}bool IsAIControlled(){return ai;}bool IsCasting(){return casting;}
 unsigned CharacterID(){return character;}
 template<class...T>void Message(int,const char*,T...){}
};
struct NPC:Mob {
 NPCType*data=nullptr;unsigned follow=0,follow_distance=0,swarm=0;int64_t ooc=10;bool depop=false;std::map<int,int> abilities;
 NPC(const NPCType*d,void*,const glm::vec4&p,int){npc=true;type=d->npc_id;hp=d->current_hp;position=p;}
 void GiveNPCTypeData(NPCType*d){data=d;}unsigned GetSwarmOwner(){return swarm;}void SetOOCRegen(int64_t value){ooc=value;}
 void SetSpecialAbility(int a,int v){abilities[a]=v;}void Depop(){depop=true;}
 void AddToHateList(Mob*m,int){target=m;engaged=true;}
 void SetFollowID(unsigned i){follow=i;}void SetFollowDistance(unsigned d){follow_distance=d;}void SetFollowCanRun(bool){}void StopNavigation(){} void SaveGuardSpot(){guard=position;} void IdleTick(){if(!follow)position=guard;} glm::vec4 guard;
 bool CheckLosFN(Mob*){return los;}
};
NPC*Mob::CastToNPC(){return static_cast<NPC*>(this);}
struct Entities {
 unsigned next=100;std::map<unsigned,NPC*> npcs;std::map<unsigned,Client*> clients;
 NPC*GetNPCByID(unsigned id){auto i=npcs.find(id);return i==npcs.end()||i->second->depop?nullptr:i->second;}
 Mob*GetMob(unsigned id){for(auto &e:clients)if(e.second->id==id)return e.second;return GetNPCByID(id);}
 Client*GetClientByCharID(unsigned id){auto i=clients.find(id);return i==clients.end()?nullptr:i->second;}
 auto&GetClientList(){return clients;}auto&GetNPCList(){return npcs;}
 void AddNPC(NPC*n,bool,bool){n->id=++next;npcs[n->id]=n;}
 void RemoveFromHateLists(Mob*m){for(auto&e:npcs)if(e.second->target==m){e.second->engaged=false;e.second->target=nullptr;}}
 void RemoveFromTargets(Mob*m){RemoveFromHateLists(m);}
 template<class...T>void Message(int,int,const char*,T...){}
} entity_list;
struct Content {NPCType type;const NPCType*LoadNPCTypesData(unsigned id){type.npc_id=id;return &type;}} content_db;
namespace Spawn2Repository {struct Spawn2 {unsigned id=0;float x=0,y=0,z=0,heading=0;int pathgrid=0;};}
namespace NightcapLoot {std::string NewDropID(){static unsigned n=0;return "token"+std::to_string(++n);}}
namespace NightcapDungeon {
enum class Mode{Grind=0,Raid=1};struct Dungeon{unsigned zone=6;};Dungeon dungeon;
struct Run{std::string id="run-a";uint64_t expiry=10000;Mode mode=Mode::Raid;Dungeon*dungeon=&NightcapDungeon::dungeon;} current;
struct Boss{unsigned objective;};
bool healthy=true;std::set<unsigned> objectives;uint64_t now=100;
uint64_t Now(){return now;}std::string Q(const std::string&s){return "'"+s+"'";}
std::set<unsigned> members,earned;std::map<unsigned,unsigned> kills;
bool enabled=true,stored_run=true,stored_alarm=false,stored_rescued=false,fail_query=false,fail_commit=false,commit_ack_lost=false;
unsigned journal_count=0,claims=0;std::vector<std::string> queries;
struct Rows {std::vector<std::string> row;unsigned affected=0;size_t RowCount(){return row.empty()?0:1;}struct It {Rows*r;const char*operator[](unsigned i){return r->row[i].c_str();}};It begin(){return {this};}unsigned RowsAffected(){return affected;}};
Rows Query(const std::string&s){
 queries.push_back(s);if(fail_query)throw std::runtime_error("injected storage failure");
 if(s.find("SELECT enabled")!=s.npos)return {{enabled?"1":"0"}};
 if(s.find("information_schema.tables")!=s.npos)return {{"2"}};
 if(s.find("information_schema.triggers")!=s.npos)return {{"0"}};
 if(s.find("information_schema.columns")!=s.npos){
  if(s.find("COUNT(*)")!=s.npos)return {{"1"}};
  return {{s.find("nightcap_highkeep_state")!=s.npos?"id:tinyint:NO,revision:bigint:NO,enabled:tinyint:NO":"run_id:char:NO,alarm:tinyint:NO,rescued_at:bigint:NO"}};
 }
 if(s.find("information_schema.statistics")!=s.npos)return {{s.find("nightcap_highkeep_state")!=s.npos?"PRIMARY:id":"PRIMARY:run_id"}};
 if(s.find("SELECT alarm,rescued_at")!=s.npos)return stored_run?Rows{{stored_alarm?"1":"0",stored_rescued?"100":"0"}}:Rows{};
 if(s.find("SET alarm=1")!=s.npos){stored_alarm=true;return {};}
 if(s.find("SET rescued_at=")!=s.npos){stored_rescued=true;return {};}
 if(s.find("UPDATE nightcap_dungeon_members")!=s.npos){
  auto p=s.find("character_id=");assert(p!=s.npos);unsigned id=static_cast<unsigned>(std::stoul(s.substr(p+13)));
  if(members.count(id)&&kills[id]==4&&!earned.count(id)){earned.insert(id);return {{},1};}return {};
 }
 if(s.find("INSERT INTO nightcap_highkeep_runs")!=s.npos){stored_run=true;return {};}
 assert(false);return {};
}
struct Transaction {
 bool alarm=stored_alarm,rescued=stored_rescued,done=false;std::set<unsigned> before=earned;
 void Commit(){if(fail_commit)throw std::runtime_error("injected commit failure");done=true;if(commit_ack_lost)throw std::runtime_error("committed but acknowledgement lost");}
 ~Transaction(){if(!done){stored_alarm=alarm;stored_rescued=rescued;earned=before;}}
};
Run ReadRun(const std::string&,bool){if(fail_query)throw std::runtime_error("injected read failure");return current;}
void Journal(Client*){++journal_count;}void Claim(Client*,bool){++claims;}
namespace Vigil {bool Member(const Run&,Client*c){return members.count(c->CharacterID())!=0;}}
#include "zone/highkeep_rescue.inc"
void Reset(){
 Highkeep::state={};entity_list.npcs.clear();entity_list.clients.clear();current={};dungeon.zone=6;healthy=true;objectives={};now=100;
 members={1,2};kills={{1,4},{2,4}};earned.clear();queries.clear();enabled=true;stored_run=true;stored_alarm=false;stored_rescued=false;
 fail_query=false;fail_commit=false;commit_ack_lost=false;journal_count=0;claims=0;Highkeep::Boot();
}
void Tick(){for(auto i=entity_list.npcs.begin();i!=entity_list.npcs.end();){if(i->second->depop)i=entity_list.npcs.erase(i);else ++i;}++now;Highkeep::Tick();}
void Add(Client&c,unsigned id){c.character=id;c.id=id;entity_list.clients[id]=&c;}
void KillWave(){auto ids=Highkeep::state.enemies;for(auto id:ids){auto n=entity_list.GetNPCByID(id);assert(n);assert(n->data->exp_mod==0&&n->data->loottable_id==0&&n->type==0);Highkeep::Death(n);n->Depop();}}
}
using namespace NightcapDungeon;
int main(){
 Reset();Client c;Add(c,1);c.position=Highkeep::Position(NightcapHighkeep::Gate);Tick();
 auto gate=entity_list.GetNPCByID(Highkeep::state.gate);assert(gate);
 assert(HighkeepFaction(&c,gate)==FACTION_INDIFFERENTLY);
 HighkeepSay(&c,gate,"see osargen");assert(!stored_alarm);
 HighkeepSay(&c,gate,"hail");now+=46;HighkeepSay(&c,gate,"relief detail");
 assert(Highkeep::state.dialogue[c.character].step==1); // expired reply offers a usable restart
 HighkeepSay(&c,gate,"hail");HighkeepSay(&c,gate,"relief detail");HighkeepSay(&c,gate,"see osargen");
 assert(stored_alarm&&Highkeep::state.alarm&&gate->target==&c&&HighkeepFaction(&c,gate)==FACTION_SCOWLS);
 Highkeep::Boot();assert(Highkeep::state.alarm); // reconnect/reboot reads durable alarm
 Reset();stored_run=false;Highkeep::Boot();assert(!Highkeep::Active());assert(HighkeepFaction(&c,gate)==-1);
 Reset();current.mode=Mode::Grind;Highkeep::Boot();assert(!Highkeep::Active());
 Reset();current.dungeon->zone=36;Highkeep::Boot();assert(!Highkeep::Active());
 Reset();Add(c,1);c.position=Highkeep::Position(NightcapHighkeep::Gate);Tick();gate=entity_list.GetNPCByID(Highkeep::state.gate);
 HighkeepSay(&c,gate,"hail");HighkeepSay(&c,gate,"relief detail");fail_commit=true;HighkeepSay(&c,gate,"see osargen");
 assert(!healthy&&!Highkeep::state.alarm&&!stored_alarm); // failure suspends before publishing an alarm
 Reset();stored_alarm=true;Highkeep::Boot();objectives={1,2,3,4};Add(c,1);Tick();
 auto prisoner=entity_list.GetNPCByID(Highkeep::state.prisoner);c.position=prisoner->position;
 assert(prisoner->hp==6000&&prisoner->ooc==0&&HighkeepProtected(&c,prisoner)&&HighkeepHealTarget(prisoner));
 auto guard=Highkeep::Actor(6005,NightcapHighkeep::Gate,"guard","");
 assert(HighkeepFaction(prisoner,guard)==FACTION_INDIFFERENTLY);
 NPCType pet_type;NPC pet(&pet_type,nullptr,c.position,0);pet.owner=&c;assert(HighkeepProtected(&pet,prisoner));
 pet.owner=nullptr;pet.swarm=c.id;assert(HighkeepProtected(&pet,prisoner));
 assert(HighkeepTransient(prisoner));assert(!HighkeepTransient(&pet));
 assert(!HighkeepProtected(gate,prisoner)); // NPCs may damage the escort
 HighkeepSay(&c,prisoner,"lead the way");assert(prisoner->follow==c.id&&prisoner->follow_distance==100);
 assert(HighkeepFaction(prisoner,guard)==FACTION_SCOWLS);guard->Depop();
 assert(prisoner->abilities[SpecialAbility::NPCDamageImmunity]==0);
 Tick();assert(Highkeep::state.wave==1&&Highkeep::state.enemies.size()==2&&prisoner->follow==0);
 for(auto id:Highkeep::state.enemies)assert(entity_list.GetNPCByID(id)->target==prisoner);
 KillWave();assert(Highkeep::state.cleared==1);
 c.connected=false;Tick();assert(prisoner->follow==0&&Highkeep::state.absent);
 auto paused=prisoner->position;prisoner->IdleTick();assert(DistanceSquared(paused,prisoner->position)==0);
 Client second;Add(second,2);second.position=prisoner->position;HighkeepSay(&second,prisoner,"lead the way");assert(Highkeep::state.leader==2);
 for(unsigned wave=1;wave<3;++wave){
  prisoner->position=Highkeep::Position(NightcapHighkeep::Checkpoints[wave]);second.position=prisoner->position;Tick();
  assert(Highkeep::state.wave==wave+1&&Highkeep::state.enemies.size()==2);KillWave();
 }
 assert(!stored_rescued&&earned.empty());
 prisoner->position=Highkeep::Position(NightcapHighkeep::Entrance);second.position=prisoner->position;
 c.connected=true;c.position=prisoner->position;kills[1]=3;Tick();
 assert(stored_rescued&&Highkeep::state.rescued&&earned==std::set<unsigned>{2}&&claims==1);
 Tick();assert(claims==1);Highkeep::Boot();Tick();assert(!Highkeep::state.prisoner&&claims==1);
 // Death clears only this attempt, preserves boss progress and permits retry.
 Reset();stored_alarm=true;Highkeep::Boot();objectives={1,2,3,4};Add(c,1);Tick();prisoner=entity_list.GetNPCByID(Highkeep::state.prisoner);c.position=prisoner->position;
 HighkeepSay(&c,prisoner,"lead the way");Tick();auto ids=Highkeep::state.enemies;
 Highkeep::Death(prisoner);prisoner->Depop();assert(!Highkeep::state.prisoner&&Highkeep::state.enemies.empty()&&objectives.size()==4&&earned.empty());
 assert(HighkeepTransient(prisoner)); // death/attempt cleanup cannot reopen XP awards
 for(auto id:ids)assert(!entity_list.GetNPCByID(id));Tick();assert(!Highkeep::state.prisoner);now+=21;Tick();assert(Highkeep::state.prisoner);
 // Missing/reused attacker identities fail the attempt, not count as kills.
 prisoner=entity_list.GetNPCByID(Highkeep::state.prisoner);c.position=prisoner->position;HighkeepSay(&c,prisoner,"lead the way");Tick();
 auto enemy=entity_list.GetNPCByID(*Highkeep::state.enemies.begin());enemy->SetEntityVariable("highkeep-attempt","foreign");Tick();
 assert(!Highkeep::state.leader&&!Highkeep::state.prisoner&&!enemy->depop&&earned.empty());
 // Non-death removal before escort is recoverable, preserving boss progress.
 Reset();stored_alarm=true;Highkeep::Boot();objectives={1,2,3,4};Tick();prisoner=entity_list.GetNPCByID(Highkeep::state.prisoner);prisoner->Depop();Tick();
 assert(!Highkeep::state.prisoner&&Highkeep::state.retry>now);now+=21;Tick();assert(Highkeep::state.prisoner&&objectives.size()==4);
 // No member can use a remote or reused gate entity as a dialogue endpoint.
 Reset();Add(c,1);Tick();gate=entity_list.GetNPCByID(Highkeep::state.gate);gate->SetEntityVariable("highkeep-run","foreign");assert(!HighkeepSay(&c,gate,"hail"));
 // The server can lose acknowledgement after COMMIT. Do not rerun completion.
 Reset();stored_alarm=true;Highkeep::Boot();objectives={1,2,3,4};Add(c,1);Tick();
 prisoner=entity_list.GetNPCByID(Highkeep::state.prisoner);c.position=prisoner->position;
 HighkeepSay(&c,prisoner,"lead the way");Highkeep::state.cleared=3;
 prisoner->position=c.position=Highkeep::Position(NightcapHighkeep::Entrance);commit_ack_lost=true;Tick();
 assert(!healthy&&stored_rescued&&earned==std::set<unsigned>{1}&&claims==0);
 healthy=true;commit_ack_lost=false;Highkeep::Boot();Tick();assert(Highkeep::state.rescued&&!Highkeep::state.prisoner&&claims==0);
}

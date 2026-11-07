"""Run actual native scene methods with deterministic transport/entity adapters."""
from pathlib import Path
import unittest
import re
import test_free_trade as native
from test_gameplay_policies import function

ROOT=Path(__file__).resolve().parents[2]


class LanternRuntimeTests(unittest.TestCase):
    def test_native_scene_lifetime_credit_and_membership(self):
        source=(ROOT/'server-mods/code/zone/last_lantern.inc').read_text()
        names=('glm::vec4 Position(', 'bool Live(', 'uint16_t Completed(', 'bool Actor(',
               'bool Friendly(', 'void Clear(', 'void Return(', 'bool Eligible(', 'bool Present(',
               'bool Credit(', 'void CreditNearby(', 'unsigned ResumeWave(', 'void CreditWave(', 'void Tick(', 'bool Death(', 'void Connected(')
        functions='\n'.join(function(source,n) for n in names)
        fixture=r'''
#include "common/last_lantern_catalog.h"
#include <cassert>
#include <map>
#include <set>
#include <string>
#include <vector>
#include <cmath>
#include <sstream>
#include <iostream>
template<class... A> void LogError(const A&...){}
namespace P=NightcapLantern;
namespace glm { struct vec4 { float x=0,y=0,z=0,w=0; vec4()=default; vec4(float a,float b,float c,float d):x(a),y(b),z(c),w(d){} }; }
float DistanceSquared(const glm::vec4&a,const glm::vec4&b){return (a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y)+(a.z-b.z)*(a.z-b.z);}
namespace Chat { constexpr int White=1,Yellow=2; }
namespace EQ { namespace spells { enum class CastingSlot { Item }; } }
namespace Saylink { std::string Silent(const std::string&,const std::string&label){return label;} }
namespace fmt {
inline std::string format(std::string s){return s;}
template<class T,class... A> std::string format(std::string s,const T&t,const A&...a){auto n=s.find("{}");std::ostringstream v;v<<t;if(n!=s.npos)s.replace(n,2,v.str());return format(s,a...);}
}
struct NPC;struct Client;
struct Mob {
 unsigned id=0,swarm=0;bool client=false,npc=false;Mob*owner=nullptr;glm::vec4 pos{};std::map<std::string,std::string> variables;
 bool IsNPC(){return npc;} bool IsClient(){return client;} NPC*CastToNPC();Client*CastToClient();
 Mob*GetUltimateOwner(){return owner ? owner : this;} unsigned GetSwarmOwner(){return swarm;} unsigned GetID(){return id;}
 std::string GetEntityVariable(const std::string&k){return variables[k];} void SetEntityVariable(const std::string&k,const std::string&v){variables[k]=v;}
 glm::vec4 GetPosition(){return pos;}
};
struct NPC:Mob {
 bool dead=false,stunned=false,mezzed=false;int casts=0;unsigned follow=0;
 NPC(){npc=true;} void Depop(){dead=true;} int GetHP(){return dead ? 0 : 100;}
 void SetFollowID(unsigned value){follow=value;} void SaveGuardSpot(){} void StopNavigation(){}
 void SetFollowDistance(unsigned){}void SetFollowCanRun(bool){}
 bool IsStunned(){return stunned;}bool IsMezzed(){return mezzed;}
 void CastSpell(int,unsigned,EQ::spells::CastingSlot,int,int){++casts;}
};
struct Client:Mob {
 bool connected=true,loaded=true,dead=false,ai=false,save=true,zoning=false;unsigned character=7,instance=16,level=25;uint16_t completed=1;int credits=0,returns=0,progress=0;
 std::set<unsigned> active{9501};std::set<std::pair<unsigned,unsigned>> activities{{9501,2}};
 std::vector<Client*> party; std::vector<Client*>GetPartyMembers(){return party.empty()?std::vector<Client*>{this}:party;}
 Client(){client=true;id=501;}
 bool Connected(){return connected;}bool ClientDataLoaded(){return loaded;}bool IsDead(){return dead;}bool IsAIControlled(){return ai;}bool IsZoning(){return zoning;}
 bool IsTaskCompleted(unsigned t){return completed&(1u<<(t-9500));} unsigned GetLevel(){return level;}bool IsTaskActive(unsigned t){return active.count(t);}
 bool IsTaskActivityActive(unsigned t,unsigned a){return activities.count({t,a});}
 void UpdateTaskActivity(unsigned t,unsigned a,unsigned,bool){++credits;++progress;activities.erase({t,a});}
 Client*GetTaskState(){return this;}int GetTaskActivityDoneCountFromTaskID(unsigned,unsigned){return progress;}
 bool SaveTaskState(){return save;}void Disconnect(){connected=false;}
 unsigned GetInstanceID(){return instance;}unsigned CharacterID(){return character;}
 template<class...A> void Message(A...){} void MovePC(uint32_t,uint16_t,float,float,float,float){++returns;}
};
NPC*Mob::CastToNPC(){return static_cast<NPC*>(this);}Client*Mob::CastToClient(){return static_cast<Client*>(this);}
struct Entities {
 unsigned serial=1000;std::map<unsigned,NPC*> npcs;std::map<unsigned,Client*> clients;std::map<unsigned,Mob*> mobs;
 NPC*GetNPCByID(unsigned id){auto i=npcs.find(id);return i!=npcs.end()&&!i->second->dead?i->second:nullptr;}
 Client*GetClientByCharID(unsigned id){auto i=clients.find(id);return i==clients.end()?nullptr:i->second;}
 Mob*GetMobID(unsigned id){auto i=mobs.find(id);return i==mobs.end()?nullptr:i->second;}
} entity_list;
struct Run{std::string id="run";unsigned instance=16,scene=0;uint64_t expires=1000;}run;
struct Attempt{std::string token;int segment=-1;unsigned wave=0,guardian=0,leader=0;uint64_t expires=0,next=0,brand_at=0;glm::vec4 brand{};std::set<unsigned>actors,enemies;}attempt;
bool owned=true,operational=true,enabled=true,stored_member=true;uint64_t tick=0,now=100;unsigned return_guide=0;
std::set<unsigned> members{7};uint64_t Now(){return now;}bool Enabled(){return enabled;}
namespace Strings { unsigned ToUnsignedInt(const char*s){return unsigned(std::stoul(s));} }
struct Row{std::string value;const char*operator[](unsigned)const{return value.c_str();}};
struct Result{std::vector<Row>rows;unsigned RowCount(){return unsigned(rows.size());}auto begin(){return rows.begin();}auto end(){return rows.end();}};
uint16_t db_completed=1;
std::string Q(const std::string&s){return "\'"+s+"\'";}
std::string last_query;Result Query(const std::string&s){last_query=s;Result r;if(s.find("SELECT taskid FROM completed_tasks")==0){for(unsigned i=0;i<16;++i)if(db_completed&(1u<<i))r.rows.push_back({std::to_string(9500+i)});}else if(stored_member){r.rows.push_back({"7"});}return r;}
void Say(const char*,const char*){}
NPC*Spawn(unsigned,const P::Point&p,const char*,const char*role){auto n=new NPC;n->id=++entity_list.serial;n->pos={p.x,p.y,p.z,p.h};n->variables={{"lantern-run",run.id},{"lantern-token",attempt.token},{"lantern-role",role}};entity_list.npcs[n->id]=n;attempt.actors.insert(n->id);return n;}
void Clear(unsigned dying=0);
void Begin(int phase,Client*c){Clear();attempt.segment=phase;attempt.token="attempt";attempt.expires=Now()+600;attempt.leader=c->CharacterID();}
unsigned replacements=0;void SpawnEnemy(unsigned,Client*,bool=false){++replacements;}
FUNCTIONS
int main(){
 Client c;c.pos=Position(P::Scenes[0].arrival);entity_list.clients[7]=&c;entity_list.mobs[501]=&c;
 // Exact-run membership is refreshed after a helper is enrolled into a booted instance.
 members.clear();Connected(&c);assert(members.count(7)&&!c.returns);assert(last_query.find("i.start_time=r.instance_start")!=last_query.npos);
 stored_member=false;Connected(&c);assert(!members.count(7)&&c.returns==1);stored_member=true;Connected(&c);
 // The return companion outlives encounter completion and attempt cleanup.
 Tick();assert(return_guide&&entity_list.GetNPCByID(return_guide));const auto guide=return_guide;
 c.activities.clear();++now;Tick();assert(entity_list.GetNPCByID(guide)&&attempt.actors.empty());
 // Actual native credit gates: corpse, disconnect, wrong instance, range, history.
 c.activities.insert({9501,2});auto where=c.pos;
 auto check=[&](){const int before=c.credits;assert(!Credit(&c,2,where)&&c.credits==before);};
 enabled=false;check();enabled=true;run.expires=now;check();run.expires=1000;c.zoning=true;check();c.zoning=false;c.dead=true;check();c.dead=false;c.connected=false;check();c.connected=true;c.instance=17;check();c.instance=16;
 where.x+=201;check();where=c.pos;db_completed=0;check();db_completed=1;
 assert(Credit(&c,2,where));assert(c.credits==1);
 // Swarm final blows resolve the native swarm owner before the ordinary owner chain.
 c.activities.insert({9501,2});attempt.segment=0;attempt.token="swarm";attempt.wave=3;
 NPC enemy;enemy.id=777;enemy.pos=c.pos;enemy.variables={{"lantern-run",run.id},{"lantern-token",attempt.token},{"lantern-role","enemy"}};
 attempt.enemies.insert(enemy.id);attempt.actors.insert(enemy.id);entity_list.npcs[777]=&enemy;
 NPC swarm;swarm.swarm=501;const int previous=c.credits;assert(Death(&enemy,&swarm));assert(c.credits==previous+1);
 // Per-wave checkpoints resume from native counts; late helpers cannot skip the first two checkpoints.
 run.scene=1;db_completed=15;c.level=38;c.active={9508};c.activities={{9508,1}};c.progress=2;
 const auto &segment=P::Programs[1].segments[1];assert(ResumeWave(segment)==2);
 Client late;late.character=8;late.id=502;late.level=38;late.pos=c.pos;late.active={9508};late.activities={{9508,1}};
 entity_list.clients[8]=&late;members.insert(8);assert(ResumeWave(segment)==0);
 attempt.wave=3;int before=c.credits;CreditWave(segment,c.pos,&c);assert(c.credits==before+1&&late.credits==0);
 assert(ResumeWave(segment)==0);attempt.wave=1;CreditWave(segment,c.pos,&c);assert(late.credits==0&&late.progress==0);
 c.party={&c,&late};CreditWave(segment,c.pos,&c);assert(late.credits==1&&late.progress==1);
 // An ordinary pet shares only its owner's native current party, even with other eligible expedition members nearby.
 run.scene=2;db_completed=0x10f;c.level=late.level=40;c.active=late.active={9509};
 c.party={&c};c.activities={{9509,0}};late.activities={{9509,0}};attempt.segment=0;attempt.token="pet";
 enemy.variables["lantern-token"]=attempt.token;attempt.enemies.insert(enemy.id);attempt.actors.insert(enemy.id);
 NPC pet;pet.owner=&c;before=c.credits;int outsider=late.credits;Death(&enemy,&pet);assert(c.credits==before+1&&late.credits==outsider);
 members.erase(8);run.scene=0;
 // Disabling the feature returns present members instead of loading public spawns.
 enabled=false;++now;Tick();assert(c.returns==2);assert(entity_list.GetNPCByID(guide));
 std::cout<<"Native campaign lifetime, exit, exact membership, swarm and negative-credit controls passed\n";
}
'''.replace('FUNCTIONS',functions.replace('void Clear(unsigned dying=0)','void Clear(unsigned dying)'))
        native.FreeTradeTests.compile_run(self,fixture)

    def test_actual_npc_death_dispatch_includes_campaign(self):
        source=(ROOT/'server-mods/code/zone/attack.cpp').read_text()
        expression=re.search(r'const bool prepared_dungeon_death = ([^;]+);',source).group(1)
        self.assertIn('!NightcapDungeon::BeforeDeath(this, killer, hunt_owned, corpse)',source)
        native.FreeTradeTests.compile_run(self,r'''
#include <cassert>
namespace NightcapDungeon{bool managed=false,campaign=false;bool Managed(){return managed;}bool Campaign(){return campaign;}}
bool queued=false;bool IsQueuedForCorpse(){return queued;}
int main(){for(unsigned bits=0;bits<8;++bits){NightcapDungeon::managed=bits&1;NightcapDungeon::campaign=bits&2;queued=bits&4;
 const bool prepared=('''+expression+''');assert(prepared==((bits&3)!=0&&!queued));}}
''')


    def test_native_death_storage_error_is_contained(self):
        source=(ROOT/'server-mods/code/zone/dungeon_service.cpp').read_text()
        death=function(source,'bool BeforeDeath(NPC *npc, Mob *killer, bool owned, Corpse *corpse)')
        branch=function(death,'if (Lantern::owned)')
        native.FreeTradeTests.compile_run(self,r"""
#include <cassert>
#include <stdexcept>
struct NPC{unsigned GetID(){return 7;}};struct Mob{};
template<class...A>void LogError(const A&...){}
namespace Lantern{bool owned=true,operational=true,fail=true;unsigned cleared=0;bool Death(NPC*,Mob*){if(fail)throw std::runtime_error("storage unavailable");return true;}void Clear(unsigned id){cleared=id;}}
bool Dispatch(NPC*npc,Mob*killer){BRANCH return true;}
int main(){NPC n;Mob killer;assert(!Dispatch(&n,&killer));assert(!Lantern::operational&&Lantern::cleared==7);
 Lantern::operational=true;Lantern::fail=false;assert(Dispatch(&n,&killer)&&Lantern::operational);
 Lantern::owned=false;Lantern::fail=true;assert(Dispatch(&n,&killer));}
""".replace('BRANCH',branch))


if __name__=='__main__':unittest.main()

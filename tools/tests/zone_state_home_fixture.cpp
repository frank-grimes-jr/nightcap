#include <cassert>
#include <cstdint>
#include <iostream>
#include <map>
#include <string>
#include <unordered_map>
#include <vector>
#include <cmath>
#ifdef _MSC_VER
// The real helper's zone parameter shadows the real global zone pointer.
#pragma warning(disable:4459)
#endif
using uint32 = uint32_t;
using EmuAppearance = int;
namespace glm {
struct vec4 {
 float x, y, z, w;
 vec4(float a=0, float b=0, float c=0, float d=0):x(a),y(b),z(c),w(d) {}
 bool operator==(const vec4& b) const {return x==b.x && y==b.y && z==b.z && w==b.w;}
 bool operator!=(const vec4& b) const {return !(*this==b);}
};
struct vec3 {
 float x,y,z;
 vec3(float a,float b,float c):x(a),y(b),z(c){}
 explicit vec3(const vec4& p):x(p.x),y(p.y),z(p.z){}
};
}
namespace GravityBehavior { constexpr int Water=0,Flying=1; }
bool FixPathingZOnSendTo=true,CheckForWaterOnSendTo=true;
float FixPathingZMaxDeltaSendTo=20;
#define RuleB(category,name) name
#define RuleR(category,name) name
#define LogAIDetail(...) ((void)0)
namespace ZoneStateSpawnsRepository {
struct ZoneStateSpawns {
 uint32 spawn2_id=7, spawngroup_id=8, npc_id=9, id=10;
 float x=400,y=500,z=60,heading=128;
 int respawn_time=600,variance=0,grid=0,condition_id=0,condition_min_value=0,anim=0;
 bool path_when_zone_idle=false,enabled=true,is_corpse=false,is_zone=false;
 int hp=37,mana=19,endurance=11,current_waypoint=3,decay_in_seconds=90,created_at=0;
 std::string entity_variables,loot_data,buffs;
};
}
namespace Spawn2Repository {
// Deterministic missing-row boundary. The generated production row has plain
// scalars; its loader must value-initialize the lookup result separately. This
// fake exercises the intended fallback but cannot detect uninitialized reads.
struct Spawn2 {uint32 id=0; float x=1,y=2,z=3,heading=64;};
}
struct Disabled {uint32 spawn2_id; bool disabled;};
struct Spawn2;
struct Zone;
struct NPC {
 glm::vec4 position,guard;
 // The native NPC constructor initializes m_SpawnPoint directly from its input.
 glm::vec4 m_SpawnPoint;
 glm::vec4 &m_Position=position,&m_GuardPoint=guard;
 Spawn2* respawn2;
 int flymode=GravityBehavior::Water;
 int hp=100,mana=100,endurance=100,grid=0,waypoint=0;
 bool resumed=false,queued=false,depopped=false;
 // Native AI_Start ends in SendTo then SaveGuardSpot, including map Z correction.
 NPC(const void*,Spawn2*,glm::vec4,int);
 void SendTo(float,float,float);
 bool IsNPC()const{return true;}NPC* CastToNPC(){return this;}
 float GetX()const{return position.x;}float GetY()const{return position.y;}float GetZ()const{return position.z;}
 void SetHP(int v){hp=v;} int GetHP()const{return hp;} int GetMaxHP()const{return 100;}
 void SetMana(int v){mana=v;} int GetMana()const{return mana;}
 void SetEndurance(int v){endurance=v;} void SetMaxHP(){hp=100;} void RestoreMana(){mana=100;}
 void AssignWaypoints(int g,int w){grid=g;waypoint=w;}
 void SetResumedFromZoneSuspend(bool v){resumed=v;}
 void SetPosition(float x,float y,float z){position.x=x;position.y=y;position.z=z;}
 void SetHeading(float h){position.w=h;} void SaveGuardSpot(const glm::vec4&);
 glm::vec4 GetPosition()const{return position;}
 uint32 GetID()const{return 9;} void SetQueuedToCorpse(){queued=true;} void Depop(){depopped=true;}
 void SetEntityVariable(const std::string&,const std::string&){} void AddLootTable(){}
 bool DropsGlobalLoot()const{return false;} void CheckGlobalLootTables(){}
 void SetSpawnGroupId(uint32){} void SaveGuardPointAnim(int){} void SetAppearance(int){}
};
struct Entities {
 std::vector<NPC*> published,corpses;
 std::vector<glm::vec4> published_positions;
 int movement_transitions=0;
 void AddNPC(NPC* n,bool=true,bool=true){published.push_back(n);published_positions.push_back(n->position);}
 void LimitAddNPC(NPC*){} void RestoreCorpse(NPC* n,int){corpses.push_back(n);}
 NPC* GetCorpseByID(uint32){return corpses.empty()?nullptr:corpses.back();}
 // Native ProcessMove compares old/new area membership. Equal XYZ cannot emit
 // an area transition; record mismatches without faking the quest dispatcher.
 void ProcessMove(NPC* n,float x,float y,float z){
  if(n->GetX()!=x||n->GetY()!=y||n->GetZ()!=z)++movement_transitions;
 }
} entity_list;
struct Map {float ground=8;float FindBestZ(glm::vec3,void*)const{return ground;}} map_value;
struct WaterMap {bool water=true;bool InWater(glm::vec3)const{return water;}} water_value;
struct Zone {
 bool has_map=true,has_water=true;Map* zonemap=&map_value;WaterMap* watermap=&water_value;
 int GetZoneID()const{return 66;}bool HasMap()const{return has_map;}bool HasWaterMap()const{return has_water;}
} zone_object;
Zone* zone=&zone_object;
// ACTUAL_POSITION_METHODS
NPC::NPC(const void*,Spawn2* s,glm::vec4 p,int gravity):position(p),guard(p),m_SpawnPoint(p),respawn2(s),flymode(gravity){
 SendTo(GetX(),GetY(),GetZ());
 SaveGuardSpot(GetPosition());
}
struct Content {
 int GetRandomWaypointFromGrid(glm::vec4& p,int,int){p=glm::vec4(20,30,40,50);return 2;}
 const void* LoadNPCTypesData(uint32){return this;}
} content_db;
namespace NightcapDungeon {
bool managed=false;
bool RequiredSpawn(uint32){return false;} bool Managed(){return managed;} bool RaidNPC(NPC*){return managed;}
}
namespace NightcapLoot {
void StampRestoredDropIDs(NPC*,const std::string&,uint32,int){}
void RestoreCorpseState(NPC*,const std::string&){}
}
void LoadLootStateData(Zone*,NPC*,const std::string&){}
void LoadNPCBuffs(NPC*,const std::string&){}
void LoadNPCStatePreSpawn(Zone*,NPC*,ZoneStateSpawnsRepository::ZoneStateSpawns&){}
std::map<std::string,std::string> GetVariablesDeserialized(const std::string&){return {};}
#define LogInfo(...) ((void)0)
#define LogZoneState(...) ((void)0)
#define Log(...) ((void)0)
struct Group {bool wp_spawns=false;int roamdist=0;} group;
struct Spawn2 {
 uint32 spawn2_id,spawngroup_id_,timeleft,grid_;
 float x,y,z,heading;
 int anim;
 bool enabled,m_resumed_from_zone_suspend=false;
 glm::vec4 m_stored_location{0,0,-1000,0};
 NPC* npcthis=nullptr;
 std::map<std::string,std::string> m_entity_variables;
 Spawn2(uint32 id,uint32 group_id,float a,float b,float c,float d,int,int,uint32 t,int g,bool,int,int,bool e,int animation)
 :spawn2_id(id),spawngroup_id_(group_id),timeleft(t),grid_(g),x(a),y(b),z(c),heading(d),anim(animation),enabled(e){}
 void SetStoredLocation(glm::vec4 p){m_stored_location=p;}
 void SetResumedNPCID(uint32){} void SetResumedFromZoneSuspend(bool r){m_resumed_from_zone_suspend=r;}
 void SetEntityVariables(std::map<std::string,std::string> v){m_entity_variables=v;}
 NPC* GetNPC(){return npcthis;}
 float GetX()const{return x;} float GetY()const{return y;} float GetZ()const{return z;} float GetHeading()const{return heading;}
 glm::vec4 GetPosition()const{return {x,y,z,heading};}
 void Process(){
  if(timeleft || !enabled) return;
  Group* spawn_group=&group;
  const void* tmp=this;
  // ACTUAL_SPAWN_LOCATION
  (void)starting_wp;
 }
};
struct Spawns {std::vector<Spawn2*> values; void Insert(Spawn2* s){values.push_back(s);}} spawn2_list;
// ACTUAL_STATE_APPLICATION
void Restore(std::vector<ZoneStateSpawnsRepository::ZoneStateSpawns> spawn_states,
 std::vector<Spawn2Repository::Spawn2> spawn2s,
 std::unordered_map<uint32,uint32> spawn_times={}) {
 std::vector<Disabled> disabled_spawns;
 // ACTUAL_SPAWN_RESTORE
 // ACTUAL_DYNAMIC_RESTORE
}
void Reset(){
 for(auto n:entity_list.published) delete n;
 for(auto s:spawn2_list.values) delete s;
 entity_list={};spawn2_list={};group={};
}
int main(){
 using State=ZoneStateSpawnsRepository::ZoneStateSpawns;
 State saved;
 const glm::vec4 pulled(saved.x,saved.y,saved.z,saved.heading),home(1,2,3,64);
 Spawn2Repository::Spawn2 canonical;canonical.id=saved.spawn2_id;

 // Script-created actors without a canonical spawn retain their saved pose/home.
 saved.spawngroup_id=0;saved.spawn2_id=0;
 Restore({saved},{});
 assert(entity_list.published.size()==1);
 assert(entity_list.published[0]->position==pulled && entity_list.published[0]->guard==pulled);
 Reset();

 // Corpses retain the actual death location, decay handling and no live spawn.
 saved.is_corpse=true;
 Restore({saved},{});
 assert(spawn2_list.values.empty() && entity_list.corpses.size()==1);
 assert(entity_list.corpses[0]->position==pulled && entity_list.corpses[0]->queued);
 Reset();

 // An NPC absent until its persisted respawn timer expires must not appear early.
 saved=State{};
 Restore({saved},{canonical},{{saved.spawn2_id,120}});
 assert(spawn2_list.values.size()==1 && entity_list.published.empty());
 Reset();

 // Restored roamers keep their current location and persisted waypoint.
 saved.grid=5;group.wp_spawns=true;
 Restore({saved},{canonical});
 auto roaming=entity_list.published.at(0);
 assert(roaming->position==pulled && roaming->grid==5 && roaming->waypoint==3);
 Reset();

 // Missing canonical spawn definitions fall back to the saved location.
 saved=State{};
 Restore({saved},{});
 auto fallback=entity_list.published.at(0);
 assert(fallback->position==pulled && fallback->guard==pulled);
 Reset();

 // A stationary NPC pulled from home must return to its canonical spawn after
 // state restore, while still restoring its position, HP and other state.
 Restore({saved},{canonical});
 auto stationary=entity_list.published.at(0);
 assert(stationary->position==pulled);
 assert(stationary->hp==37 && stationary->mana==19 && stationary->endurance==11);
 assert(stationary->resumed);
 if(stationary->guard!=home){
  std::cerr << "Saved pull position replaced stationary return-home guard: got "
   << stationary->guard.x << ',' << stationary->guard.y << ',' << stationary->guard.z
   << "; expected 1,2,3\n";
  Reset();return 1;
 }
 Reset();

 int failures=0;
 // Exercise the shared saved-spawn loop with both public and managed-mode
 // flags. Checkpoint selection/SQL is deliberately outside this native fixture.
 for(bool managed:{false,true}){
  NightcapDungeon::managed=managed;
  for(int terrain_case=0;terrain_case<3;++terrain_case){
   zone_object.has_map=terrain_case!=1;
   water_value.water=terrain_case==2;
   canonical.heading=0; // SaveGuardSpot normalizes zero heading to 0.0001.
   const glm::vec4 canonical_pose(canonical.x,canonical.y,canonical.z,canonical.heading);
   NPC fresh(nullptr,nullptr,canonical_pose,GravityBehavior::Water);
   NPC saved_fresh(nullptr,nullptr,pulled,GravityBehavior::Water);
   Restore({saved},{canonical});
   auto restored=entity_list.published.at(0);
   assert(restored->position==pulled);
   assert(restored->m_SpawnPoint==pulled);
   assert(entity_list.movement_transitions==0);
   // Quest/event publication must still see the original constructor's saved
   // position normalization, before LoadNPCState reapplies the saved raw pose.
   assert(entity_list.published_positions.at(0)==saved_fresh.position);
   if(restored->guard!=fresh.guard){
    std::cerr<<"Restored stationary home differs from fresh canonical NPC: managed="<<managed
     <<" terrain_case="<<terrain_case<<" guard_z="<<restored->guard.z
     <<" fresh_z="<<fresh.guard.z<<'\n';++failures;
   }
   Reset();

   // Absent canonical row uses the same normalized saved-location fallback as
   // a fresh NPC at that location, without changing its restored current pose.
   NPC fallback_fresh(nullptr,nullptr,pulled,GravityBehavior::Water);
   Restore({saved},{});
   auto absent=entity_list.published.at(0);
   assert(absent->position==pulled);
   if(absent->guard!=fallback_fresh.guard){
    std::cerr<<"Missing-row fallback lost native position normalization\n";++failures;
   }
   Reset();
  }
  zone_object.has_map=true;water_value.water=true;
  group.roamdist=50;
  Restore({saved},{canonical});
  auto roaming_box=entity_list.published.at(0);
  if(roaming_box->guard!=pulled){
   std::cerr<<"Roambox NPC had its previously retained saved guard replaced\n";++failures;
  }
  Reset();
 }
 return failures?1:0;
}

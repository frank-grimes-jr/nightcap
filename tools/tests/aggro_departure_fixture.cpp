#include <cassert>
#include <cstdint>
#include <iostream>
#include <map>
#include <set>
#include <algorithm>
#include <vector>
using uint32=uint32_t;
#define RuleB(category,name) false
#define RuleI(category,name) 4
constexpr int AIfeignremember_delay=1000;
struct Timer {bool enabled=false;void Start(int){enabled=true;}void Disable(){enabled=false;}bool Check(){return enabled;}};
struct Mob;
struct Dirty {void SetDirtyAutoHaters(){} void UpdateRaidXTargets(){}};
struct XTargetAutoHaters {
 struct HatersCount {uint32 spawn_id;int count;};
 std::vector<HatersCount> m_haters;
 Dirty *m_client=nullptr,*m_group=nullptr,*m_raid=nullptr;
 void decrement_count(Mob*);
 int Count(uint32 id)const{for(const auto& h:m_haters)if(h.spawn_id==id)return h.count;return 0;}
};
enum {CurrentTargetNPC,Auto};
struct XTarget {int Type=Auto;uint32 ID=0;bool dirty=false;};
#define LogXTargets(...) ((void)0)
struct Hate {
 std::set<Mob*> values;
 bool RemoveEntFromHateList(Mob* m){return values.erase(m)!=0;}
 bool IsHateListEmpty()const{return values.empty();}
 Mob* GetMobWithMostHateOnList(Mob*){return values.empty()?nullptr:*values.begin();}
};
struct Mob {
 uint32 id; bool client=false,corpse=false,feigned=false;
 Hate hate_list;std::set<uint32> feign_memory_list;std::set<Mob*> rampage,xtargets;
 Timer timer;Timer* AI_feign_remember_timer=&timer;
 int minLastFightingDelayMoving=0,maxLastFightingDelayMoving=0,disengages=0;
 Mob* target=nullptr;
 XTargetAutoHaters* m_activeautohatermgr=nullptr;XTarget XTargets[1];
 explicit Mob(uint32 v,bool c=false):id(v),client(c){}
 bool IsClient()const{return client;} bool IsNPC()const{return !client&&!corpse;}
 bool IsCorpse()const{return corpse;} bool GetFeigned()const{return feigned;}
 uint32 GetID()const{return id;} Mob* CastToClient(){return this;}
 bool CheckAggro(Mob* m){return hate_list.values.count(m)!=0;}
 void RemoveXTarget(Mob*,bool);
 bool XTargettingAvailable()const{return true;}int GetMaxXTargets()const{return 1;}
 Dirty* GetRaid(){return nullptr;}void ClearFeignMemoryOnDeparture();
 void RemoveFromRampageList(Mob* m){rampage.erase(m);}
 void SetRunAnimSpeed(int){} bool IsEngaged()const{return !hate_list.IsHateListEmpty();}
 void AI_Event_NoLongerEngaged(){++disengages;} void ResetAssistCap(){}
 Mob* GetTarget(){return target;}void SetTarget(Mob* m){target=m;}
 void AddToHateList(Mob* m,int){hate_list.values.insert(m);}
 bool RemoveFromHateList(Mob*);
 void AddFeignMemory(Mob*);void RemoveFromFeignMemory(Mob*);bool IsOnFeignMemory(Mob*)const;
 void Replay();void DeathCleanup();void DepartureCleanup();
};
struct EntityList {
 std::map<uint32,Mob*> mob_list,npc_list;
 void RemoveFromTargets(Mob*,bool=true);void ClearZoneFeignAggro(Mob*);
 const std::map<uint32,Mob*>& GetNPCList()const{return npc_list;}
 Mob* GetMob(uint32 id){auto it=mob_list.find(id);return it==mob_list.end()?nullptr:it->second;}
} entity_list;
struct Zone {void DelAggroMob(){}bool CanDoCombat()const{return true;}} zone_value;
Zone* zone=&zone_value;
// ACTUAL_METHODS
// ACTUAL_REPLAY
void Mob::DeathCleanup(){
 // ACTUAL_DEATH_CLEANUP
}
void Mob::DepartureCleanup(){
 // ACTUAL_DEPARTURE_CLEANUP
}
int main(){
 int failed=0;
 for(bool death:{false,true}){
  Mob departing(100,true),other(101,true),replacement(100,true),npc(200),memory_only(201),other_only(202);
  XTargetAutoHaters shared;shared.m_haters={{200,2},{201,1},{202,1}};
  departing.m_activeautohatermgr=&shared;other.m_activeautohatermgr=&shared;
  entity_list.mob_list={{100,&departing},{101,&other},{200,&npc},{201,&memory_only},{202,&other_only}};
  entity_list.npc_list={{200,&npc},{201,&memory_only},{202,&other_only}};
  other_only.AddToHateList(&other,10);
  other_only.minLastFightingDelayMoving=31;
  other_only.maxLastFightingDelayMoving=47;
  npc.AddToHateList(&departing,10);npc.AddToHateList(&other,20);
  npc.AddFeignMemory(&departing);npc.AddFeignMemory(&other);
  memory_only.AddFeignMemory(&departing);
  npc.rampage={&departing,&other};departing.xtargets={&npc,&memory_only};
  if(death) departing.DeathCleanup();else departing.DepartureCleanup();
  assert(!npc.CheckAggro(&departing) && npc.CheckAggro(&other));
  assert(!npc.rampage.count(&departing) && npc.rampage.count(&other));
  assert(npc.IsOnFeignMemory(&other));
  if(other_only.minLastFightingDelayMoving!=31||other_only.maxLastFightingDelayMoving!=47){
   std::cerr<<(death?"death":"departure")<<" reset an unrelated NPC's return delay\n";++failed;
  }
  // Death already removes this player's contributions through RemoveFromTargets.
  // Destructor fixture excludes group detachment: the new helper must leave
  // ALL counts untouched, including memory-only entries for existing bookkeeping.
  if(shared.Count(200)!=(death?1:2)||shared.Count(201)!=(death?0:1)||shared.Count(202)!=1){
   std::cerr<<(death?"death":"departure")<<" removed another player's shared XTarget contribution\n";++failed;
  }
  bool forgotten=!npc.IsOnFeignMemory(&departing)&&!memory_only.IsOnFeignMemory(&departing);
  if(forgotten){assert(!memory_only.timer.enabled);assert(npc.timer.enabled);}
  if(!forgotten){std::cerr<<(death?"death":"departure")<<" retained departed entity ID in feign memory\n";++failed;}
  // A different client reuses the removed ID before the AI's next memory tick.
  entity_list.mob_list[100]=&replacement;
  memory_only.Replay();
  if(memory_only.CheckAggro(&replacement)){
   std::cerr<<(death?"death":"departure")<<" replayed stale feign hate onto replacement client\n";++failed;
  }
 }
 // Ordinary removal from hate is used by feign, blur and encounter behavior;
 // the lifecycle repair must not globally erase another system's feign state.
 Mob feigner(300,true),npc(400);
 npc.AddToHateList(&feigner,1);npc.AddFeignMemory(&feigner);
 npc.RemoveFromHateList(&feigner);
 assert(!npc.CheckAggro(&feigner)&&npc.IsOnFeignMemory(&feigner));
 // Generic fade removal still retains feign memory; only terminal lifecycle
 // cleanup erases it. This guards against broadening RemoveFromTargets.
 entity_list.mob_list={{300,&feigner},{400,&npc}};
 entity_list.RemoveFromTargets(&feigner,true);
 assert(npc.IsOnFeignMemory(&feigner));
 return failed?1:0;
}

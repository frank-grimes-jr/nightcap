"""Execute native cooldown duration and identity boundaries with controlled focus.

Compiles the actual item-recast/cooldown APIs, discipline APIs, linked-recast and
Mend methods. Other skill
handlers execute their actual authorization/cooldown prologs, stopping before
the gameplay effects. Spell finish paths are exact extracted blocks, including
the preceding focus adjustment and custom AA/disc timers with their guard.
Engine inventory, damage, database and packet delivery are controlled fixtures.
Persistent timers use a deterministic clock; the saved-item timestamp API uses
its native wall clock with a one-second comparison tolerance.
No live server, client or player data is used.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from test_gameplay_policies import ROOT, function


SOURCE = ROOT / "server-mods/code"

FIXTURE = r'''
#include <algorithm>
#include <cstdint>
#include <ctime>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
using uint8=uint8_t;using uint16=uint16_t;using uint32=uint32_t;using uint64=uint64_t;
using int8=int8_t;using int16=int16_t;using int32=int32_t;using int64=int64_t;
/* NATIVE_TIMER_TYPE */
/* NATIVE_TIMER_ENUM */
enum {focusReduceRecastTime=1,RECAST_TYPE_UNLINKED_ITEM=-1,MendReuseTime=360,
 DisarmTrapsReuseTime=9,FeignDeathReuseTime=9,HideReuseTime=8,SenseTrapsReuseTime=9,
 MEND_CRITICAL,MEND_SUCCESS,MEND_WORSEN,MEND_FAIL,OP_LinkedReuse,
 SPELL_LAY_ON_HANDS=100,aaFervrentBlessing,aaTouchoftheWicked,
 MAX_PP_DISCIPLINES=4,MELEE_SILENCE,DISC_LEVEL_USE_ERROR,SNEAK_RESTRICT,ST_Self,ItemPacketCharmUpdate};
namespace EQ {namespace invaug {enum {SOCKET_BEGIN=0,SOCKET_END=5};}
 namespace skills {enum {SkillMend=32,SkillDisarmTraps=17,SkillFeignDeath=25,SkillHide=29,SkillSenseTraps=42};}
 namespace spells {enum class CastingSlot {Gem0=0,MaxGems=12,Item=13,AltAbility=14,Discipline=15};}
}
namespace Class {enum {Monk=7,Bard=8};}
namespace AA {struct Ability {int id=0;};struct Rank {Ability* base_ability=nullptr;uint32 spell_type=1;};}
using EQ::spells::CastingSlot;
namespace Chat {enum {Red,LightBlue,SpellFailure,White};}
namespace fmt {template<class... T> std::string format(const char* message,T...) {return message;}}
namespace Strings {std::string SecondsToTime(uint32) {return "fixture";}}
#define LogSpells(...) ((void)0)
#define LogDebug(...) ((void)0)
#define RuleI(category,name) 100
bool IsHarmTouchSpell(int) {return false;}
bool IsValidSpell(uint32 spell) {return spell>0 && spell<65536;}
bool IsCastNotStandingSpell(uint32) {return false;}
struct Timer {inline static uint32 now=1000;static uint32 GetCurrentTime() {return now*1000;}};
struct ItemData;
struct Database {
 std::vector<uint32> updated;
 std::map<uint32,const ItemData*> items;
 std::map<uint32,uint32> timestamps;
 void UpdateItemRecast(uint32,int32 key,uint32 timestamp) {updated.push_back(key);timestamps[key]=timestamp;}
 void DeleteItemRecast(uint32,uint32 key) {timestamps.erase(key);}
 const ItemData* GetItem(uint32 id) const {auto i=items.find(id);return i==items.end()?nullptr:i->second;}
 std::map<uint32,uint32> GetItemRecastTimestamps(uint32) const {return timestamps;}
} database;
struct PersistentTimer {
 uint32 start_time=0,timer_time=0,_char_id=0;pTimerType _type=0;bool enabled=false;
 PersistentTimer(uint32,pTimerType,uint32);
 uint32 get_current_time() const {return Timer::now;}
 bool Clear(Database*) {return true;}
 bool Expired(Database*,bool);
 void Start(uint32);
 uint32 GetRemainingTime();
 uint32 GetReadyTimestamp() const {return start_time+timer_time;}
};
struct PTimerList {
 uint32 _char_id=1;std::map<pTimerType,PersistentTimer*> _list;
 ~PTimerList() {for(auto& entry:_list)delete entry.second;}
 void Start(pTimerType,uint32);
 PersistentTimer* Get(pTimerType);
 uint32 GetRemainingTime(pTimerType);
 bool Expired(Database*,pTimerType,bool);
 void Clear(Database*,pTimerType);
 bool Enabled(pTimerType type) const {auto it=_list.find(type);return it!=_list.end() && it->second->enabled;}
 auto begin() {return _list.begin();}auto end() {return _list.end();}
};
struct ItemData {
 uint32 ID=1234,RecastDelay=20;int32 RecastType=4;
 struct {int32 Effect=1;} Click;
};
struct ItemInstance {
 ItemData data;ItemInstance* augment=nullptr;uint32 recast_timestamp=0;
 const ItemData* GetItem() const {return &data;}
 const ItemInstance* GetAugment(int slot) const {return slot==0?augment:nullptr;}
 uint32 GetID() const {return data.ID;}
 void SetRecastTimestamp(uint32 stamp) {recast_timestamp=stamp;}
};
namespace EQ {using ItemData=::ItemData;using ItemInstance=::ItemInstance;}
struct Inventory {
 ItemInstance item;bool missing=false;
 const ItemInstance* GetItem(uint32) const {return missing?nullptr:&item;}
 ItemInstance* GetItem(uint32) {return missing?nullptr:&item;}
};
struct LinkedSpellReuseTimer_Struct {uint32 timer_id=0,end_time=0,start_time=0;};
struct EQApplicationPacket {
 void* pBuffer=nullptr;uint32 size=0;
 EQApplicationPacket(int opcode=0,int bytes=sizeof(LinkedSpellReuseTimer_Struct)):size(bytes) {pBuffer=::operator new(bytes);}
 ~EQApplicationPacket() {::operator delete(pBuffer);}
 uint32 ReadUInt32(int) const {return 0;}
};
struct SPDat_Spell_Struct {uint32 recast_time=20000,endurance_cost=10,cast_time=0;
 // Native common/spdat.h field167 is signed int8 TIMER_INDEX, including -1.
 int8 timer_id=4;
 bool is_discipline=false,sneak=false;int buff_duration_formula=0,target_type=0,resist_difficulty=0;} spells[65536];
struct Mob {};
struct EntityList {Mob target;Mob* GetMob(uint32) {return &target;}} entity_list;
struct Zone {struct Random {int Int(int,int) const {return 0;}} random;
 AA::Rank* GetAlternateAdvancementRank(int) const {return nullptr;}} zone_value;
auto* zone=&zone_value;
struct Client {
 Inventory inventory;PTimerList p_timers;
 int focus=0,skill_reduction=0,hp=100,hp_updates=0,skill_checks=0,skill_actions=0,raw_skill=200;
 bool has_skill=true,client=true,triggered=false;
 bool stunned=false,feared=false,mezzed=false,amnesiad=false,pet=false,aura=false;
 bool hidden=true,disc_buff=false,casting=false,cast_ok=true,caster_checks=true;
 uint8 required_level=1,level=50;int endurance=100,casts=0;uint32 tmHidden=0;
 struct Profile {struct {uint32 values[MAX_PP_DISCIPLINES]={1,0,0,0};} disciplines;} m_pp;
 std::vector<uint32> discipline_packets;
 std::vector<uint32> discipline_packet_ids;
 uint8 class_id=Class::Monk;uint32 casting_spell_id=1,casting_spell_aa_id=0;
 uint32 casting_spell_timer=pTimerDisciplineReuseStart+1,casting_spell_timer_duration=30;
 struct Bonuses {int CriticalMend=0;} spellbonuses,itembonuses,aabonuses;
 std::vector<uint32> item_packets;
 std::vector<LinkedSpellReuseTimer_Struct> linked_packets;
 /* NATIVE_RECAST_ADJUST_MEMBER */
 Client():casting_spell_recast_adjust(0) {Timer::now=1000;}
 Client* CastToClient() {return this;}
 bool IsClient() const {return client;}uint8 GetClass() const {return class_id;}
 bool IsFromTriggeredSpell(CastingSlot,uint32) const {return triggered;}
 void ExpendAlternateAdvancementCharge(int) {} void SendAlternateAdvancementTimer(uint32,int,int) {}
 const Inventory& GetInv() const {return inventory;}
 Inventory& GetInv() {return inventory;}
 std::vector<int16> GetInventorySlots() const {return {0};}
 void SendItemPacket(int16,ItemInstance*,int) {}
 PTimerList& GetPTimers() {return p_timers;}
 uint32 CharacterID() const {return 1;}
 /* NATIVE_FOCUS_RETURN */ GetFocusEffect(int,int) const {return focus;}
 int16 GetSkillReuseTime(uint16) const {return int16(skill_reduction);}
 void SendItemRecastTimer(int32,uint32 delay,bool=false) {item_packets.push_back(delay);}
 void FastQueuePacket(EQApplicationPacket** p) {
  linked_packets.push_back(*static_cast<LinkedSpellReuseTimer_Struct*>((*p)->pBuffer));
  delete *p;*p=nullptr;
 }
 bool HasSkill(int) const {return has_skill;}
 int GetSkill(int) const {return raw_skill;}
 int GetHP() const {return hp;}int GetMaxHP() const {return 1000;}
 void SetHP(int value) {hp=value;}void SendHPUpdate() {++hp_updates;}
 int GetAA(int) const {return 0;}
 bool IsStunned() const {return stunned;}bool IsFeared() const {return feared;}
 bool IsMezzed() const {return mezzed;}bool IsAmnesiad() const {return amnesiad;}
 bool IsPet() const {return pet;}bool DivineAura() const {return aura;}
 uint8 GetSpellMinLevel(uint32) const {return required_level;}uint8 GetLevel() const {return level;}
 int GetEndurance() const {return endurance;}bool HasDiscBuff() const {return disc_buff;}
 bool IsCasting() const {return casting;}bool DoCastingChecksOnCaster(uint32,CastingSlot) const {return caster_checks;}
 void SendDisciplineTimer(uint32 id,uint32 duration) {discipline_packet_ids.push_back(id);discipline_packets.push_back(duration);}
 bool CastSpell(uint32 spell,uint32,CastingSlot slot,int=-1,int=-1,int=0,int=-1,uint32 timer=0xFFFFFFFF,uint32 duration=0) {
  ++casts;if(!cast_ok)return false;
  casting_spell_id=spell;casting_spell_timer=timer;casting_spell_timer_duration=duration;
  FinishCustom(spell,false,slot,0,timer,duration);return true;
 }
 bool SpellFinished(uint32 spell,Mob*,CastingSlot slot,int,int,int,bool,int,uint32 timer,uint32 duration,bool) {
  ++casts;if(!cast_ok)return false;
  casting_spell_timer=timer;casting_spell_timer_duration=duration;
  FinishCustom(spell,false,slot,0,timer,duration);return true;
 }
 template<class... T> void Message(T...) {} template<class... T> void MessageString(T...) {}
 template<class... T> void CheckIncreaseSkill(T...) {++skill_checks;}
 void SetItemRecastTimer(int32,uint32);
 void DeleteItemRecastTimer(uint32);
 bool HasItemRecastTimer(int32,uint32);
 void SetItemCooldown(uint32,bool,uint32);
 uint32 GetItemCooldown(uint32);
 void SetLinkedSpellReuseTimer(uint32,uint32);
 bool IsLinkedSpellReuseTimerReady(uint32);
 void Handle_OP_Mend(const EQApplicationPacket*);
 bool UseDiscipline(uint32,uint32);
 uint32 GetDisciplineTimer(uint32);
 void ResetDisciplineTimer(uint32);
 void ResetAllDisciplineTimers();
 void Handle_OP_DisarmTraps(const EQApplicationPacket*);
 void Handle_OP_FeignDeath(const EQApplicationPacket*);
 void Handle_OP_Hide(const EQApplicationPacket*);
 void Handle_OP_SenseTraps(const EQApplicationPacket*);
 void PrepareSpellRecast(int spell_id);
 void FinishCustom(int spell_id,bool isproc,CastingSlot slot,uint32 inventory_slot,uint32 timer,uint32 timer_duration);
 void FinishBard(int spell_id,CastingSlot slot);
 void FinishOrdinary(int spell_id,CastingSlot slot);
};
void check(bool ok,const std::string& why) {if(!ok)throw std::runtime_error(why);}
'''

CONTROLS = r'''
void item_case(int reduction,uint32 expected,bool augment,bool unlinked) {
 Client c;c.focus=reduction;
 ItemInstance aug;
 if(augment) {
  c.inventory.item.data.RecastDelay=0;c.inventory.item.augment=&aug;
  aug.data.ID=2345;aug.data.RecastType=unlinked?RECAST_TYPE_UNLINKED_ITEM:4;
 } else c.inventory.item.data.RecastType=unlinked?RECAST_TYPE_UNLINKED_ITEM:4;
 c.SetItemRecastTimer(1,0);
 for(const auto& entry:c.p_timers._list) {
  check(entry.second->timer_time==expected,"item reduction "+std::to_string(reduction)+
   " produced "+std::to_string(entry.second->timer_time)+" seconds; expected "+std::to_string(expected));
 }
 if(expected==0) {
  check(c.p_timers._list.empty() || c.p_timers._list.begin()->second->timer_time==0,
   "fully reduced item must be ready");
 } else check(c.p_timers._list.size()==1,"normal item cooldown missing");
 if(!augment && expected>0)
  check(c.item_packets==std::vector<uint32>{expected},"item wire cooldown disagrees with persistent timer");
 if(augment)check(c.item_packets.empty(),"augment must retain native packet suppression");
}
void item_normal() {
 for(bool augment:{false,true})for(bool unlinked:{false,true}) {
  item_case(0,20,augment,unlinked);item_case(3,17,augment,unlinked);
  item_case(-5,25,augment,unlinked);
 }
}
void item_equal() {
 for(bool augment:{false,true})for(bool unlinked:{false,true})item_case(20,0,augment,unlinked);
}
void item_excess() {
 for(int reduction:{21,80,2000})for(bool augment:{false,true})for(bool unlinked:{false,true})
  item_case(reduction,0,augment,unlinked);
}
void finish(Client& c,bool bard) {
 if(bard)c.FinishBard(1,CastingSlot::Gem0);else c.FinishOrdinary(1,CastingSlot::Gem0);
}
void check_linked(Client& c,uint32 expected,const std::string& why) {
 uint32 actual=c.p_timers.GetRemainingTime(pTimerLinkedSpellReuseStart+4);
 if(expected==0)
  check(c.p_timers.Expired(&database,pTimerLinkedSpellReuseStart+4,false),why+": zero cooldown must be ready");
 else check(actual==expected,why+": got "+std::to_string(actual)+" seconds; expected "+std::to_string(expected));
 if(!c.linked_packets.empty()) {
  const auto& packet=c.linked_packets.back();
  check(packet.timer_id==4 && packet.end_time-packet.start_time==expected,
   "linked cooldown wire duration disagrees with persistent timer");
 }
}
void linked_normal() {
 for(bool bard:{false,true})for(int reduction:{0,3,20,21,2000}) {
  Client c;c.focus=reduction;c.PrepareSpellRecast(1);finish(c,bard);
  check_linked(c,reduction>=20?0:20-reduction,"normal focus preparation/completion");
 }
}
void linked_negative_focus(bool bard) {
 for(int reduction:{-1,-5,-60}) {
  Client c;c.focus=reduction;c.PrepareSpellRecast(1);
  check(c.p_timers.GetRemainingTime(pTimerSpellStart+1)==uint32(20-reduction),
   "ordinary spell timer must retain negative focus extension");
  finish(c,bard);check_linked(c,20-reduction,"negative focus preparation/completion");
 }
}
void linked_excess_adjustment(bool bard) {
 for(int adjustment:{20000,21000,60000}) {
  Client c;c.casting_spell_recast_adjust=adjustment;finish(c,bard);
  check_linked(c,0,"equal/excess completed-cast adjustment");
 }
}
void linked_non_gem() {
 for(bool bard:{false,true}) {
  Client c;c.focus=3;c.PrepareSpellRecast(1);
  if(bard)c.FinishBard(1,CastingSlot::Item);else c.FinishOrdinary(1,CastingSlot::Item);
  check(c.p_timers.GetRemainingTime(pTimerLinkedSpellReuseStart+4)==0 && c.linked_packets.empty(),
   "item casts unexpectedly start linked gem cooldowns");
 }
}
void mend_case(int reduction,uint32 expected) {
 Client c;c.skill_reduction=reduction;c.Handle_OP_Mend(nullptr);
 uint32 actual=c.p_timers.GetRemainingTime(pTimerMend);
 if(expected==0)
  check(c.p_timers.Expired(&database,pTimerMend,false),"fully reduced Mend must be ready");
 else check(actual==expected,"Mend reduction "+std::to_string(reduction)+" produced "+
  std::to_string(actual)+" seconds; expected "+std::to_string(expected));
 check(c.hp_updates==1 && c.skill_checks==1,"valid Mend must retain heal and skill progression");
 c.Handle_OP_Mend(nullptr);
 check(c.hp_updates==(expected>0?1:2),"Mend readiness disagrees with reduced cooldown");
}
void mend_normal() {
 mend_case(0,360);mend_case(30,330);mend_case(-30,390);mend_case(360,0);
 Client unavailable;unavailable.has_skill=false;unavailable.Handle_OP_Mend(nullptr);
 check(unavailable.p_timers._list.empty() && unavailable.hp_updates==0,"unavailable Mend changed state");
}
void mend_excess() {mend_case(361,0);mend_case(2000,0);}
void retained_mend(int reduction) {
 Client c;c.Handle_OP_Mend(nullptr);
 check(c.p_timers.GetRemainingTime(pTimerMend)==360,"original Mend cooldown missing");
 Timer::now+=360;
 check(c.p_timers.Expired(&database,pTimerMend,false),"original Mend timer must have expired");
 check(c.p_timers._list.count(pTimerMend)==1,"native expiry must retain timer object for this regression");
 c.skill_reduction=reduction;c.Handle_OP_Mend(nullptr);
 check(c.p_timers.Expired(&database,pTimerMend,false),"zero reduced Mend restarted the retained 360-second duration");
 c.Handle_OP_Mend(nullptr);check(c.hp_updates==3,"retained expired timer still blocks fully reduced Mend");
}
void retained_linked(int reduction,bool bard) {
 Client c;c.PrepareSpellRecast(1);finish(c,bard);
 check_linked(c,20,"original linked timer");
 Timer::now+=20;
 check(c.p_timers.Expired(&database,pTimerLinkedSpellReuseStart+4,false),"original linked timer must expire");
 check(c.p_timers._list.count(pTimerLinkedSpellReuseStart+4)==1,"native expiry must retain timer object for this regression");
 c.focus=reduction;c.PrepareSpellRecast(1);finish(c,bard);
 check_linked(c,0,"zero reduced spell restarted retained linked duration");
}
struct SkillBoundary {
 const char* name;pTimerType timer;int base;
 void (Client::*handler)(const EQApplicationPacket*);
};
const std::vector<SkillBoundary> skill_boundaries={
 {"disarm",pTimerDisarmTraps,DisarmTrapsReuseTime,&Client::Handle_OP_DisarmTraps},
 {"feign",pTimerFeignDeath,FeignDeathReuseTime,&Client::Handle_OP_FeignDeath},
 {"hide",pTimerHide,HideReuseTime,&Client::Handle_OP_Hide},
 {"sense",pTimerSenseTraps,SenseTrapsReuseTime,&Client::Handle_OP_SenseTraps}};
void skill_normal() {
 EQApplicationPacket app;
 for(const auto& row:skill_boundaries) {
  for(int reduction:{0,2,-3}) {
   Client c;c.skill_reduction=reduction;(c.*row.handler)(&app);
   int expected=row.base-1-reduction;
   check(c.p_timers.GetRemainingTime(row.timer)==uint32(expected),std::string(row.name)+" ordinary reuse changed");
   check(c.skill_actions==1,"successful cooldown prolog did not reach gameplay boundary");
   (c.*row.handler)(&app);check(c.skill_actions==1,"active timer failed to guard gameplay boundary");
   Timer::now+=expected;(c.*row.handler)(&app);
   check(c.skill_actions==2,"expired normal skill remains blocked");
  }
  Client unavailable;unavailable.has_skill=false;unavailable.raw_skill=0;(unavailable.*row.handler)(&app);
  check(unavailable.skill_actions==0 && unavailable.p_timers._list.empty(),"unavailable skill started cooldown");
 }
 Client cancel;EQApplicationPacket cancel_packet(0,4);cancel.Handle_OP_Hide(&cancel_packet);
 check(cancel.skill_actions==0 && cancel.p_timers._list.empty(),"cancel-hide packet started cooldown");
}
void skill_zero(const std::string& skill) {
 EQApplicationPacket app;
 for(const auto& row:skill_boundaries) {
  if(skill!=row.name)continue;
  for(int reduction:{row.base-1,row.base,row.base+20}) {
   Client c;(c.*row.handler)(&app);Timer::now+=row.base-1;
   check(c.p_timers.Expired(&database,row.timer,false),"prior skill timer should expire");
   check(c.p_timers._list.count(row.timer)==1,"prior skill timer object must remain");
   c.skill_reduction=reduction;(c.*row.handler)(&app);
   check(c.p_timers.Expired(&database,row.timer,false),skill+" zero duration restarted retained timer");
   (c.*row.handler)(&app);check(c.skill_actions==3,skill+" retained timer blocks fully reduced reuse");
  }
  return;
 }
 throw std::runtime_error("unknown skill scenario");
}
void custom_cast(Client& c,bool bard,uint32 duration,bool proc=false) {
 c.class_id=bard?Class::Bard:Class::Monk;c.casting_spell_id=bard?2:1;
 c.casting_spell_timer_duration=duration;
 c.FinishCustom(1,proc,CastingSlot::AltAbility,0,c.casting_spell_timer,duration);
}
void custom_zero(bool bard) {
 Client c;custom_cast(c,bard,30);Timer::now+=30;
 check(c.p_timers.Expired(&database,c.casting_spell_timer,false),"prior custom timer should expire");
 check(c.p_timers._list.count(c.casting_spell_timer)==1,"custom timer must retain object after expiry");
 custom_cast(c,bard,0);
 check(c.p_timers.Expired(&database,c.casting_spell_timer,false),"zero custom AA/disc duration restarted retained 30-second timer");
}
void custom_controls() {
 for(bool bard:{false,true}) {
  Client c;custom_cast(c,bard,30);
  check(c.p_timers.GetRemainingTime(c.casting_spell_timer)==30,"normal custom timer duration changed");
  Timer::now+=30;custom_cast(c,bard,17);
  check(c.p_timers.GetRemainingTime(c.casting_spell_timer)==17,"new positive custom timer did not replace expired duration");
  for(int guard:{0,1,2}) {
   Client blocked;blocked.p_timers.Start(blocked.casting_spell_timer,30);Timer::now+=30;
   blocked.triggered=guard==1;blocked.client=guard!=2;custom_cast(blocked,bard,17,guard==0);
   check(blocked.p_timers.Expired(&database,blocked.casting_spell_timer,false),"proc/trigger/nonclient bypassed custom reuse guard");
   check(blocked.p_timers._list.size()==1,"guarded custom completion started unrelated timer");
  }
 }
}
void discipline_focus(int reduction,uint32 expected) {
 for(bool bard:{false,true})for(bool retained:{false,true}) {
  Client c;spells[1].is_discipline=true;c.focus=reduction;c.class_id=bard?Class::Bard:Class::Monk;c.casting=bard;
  pTimerType timer=pTimerDisciplineReuseStart+spells[1].timer_id;
  if(retained){c.p_timers.Start(timer,30);Timer::now+=30;}
  check(c.UseDiscipline(1,44),"valid discipline rejected");
  check(c.casts==1,"discipline should cast exactly once");
  if(expected==0)check(c.p_timers.Expired(&database,timer,false),"fully reduced discipline must remain ready");
  else {
   uint32 actual=c.p_timers.GetRemainingTime(timer);
   check(actual==expected,"discipline focus "+std::to_string(reduction)+" produced "+std::to_string(actual)+" seconds; expected "+std::to_string(expected));
   check(c.discipline_packets==std::vector<uint32>{expected},"discipline client timer disagrees with native duration");
  }
 }
}
void discipline_normal() {discipline_focus(0,20);discipline_focus(3,17);discipline_focus(20,0);discipline_focus(21,0);}
void discipline_negative() {for(int reduction:{-1,-5,-10,-30,-5000})discipline_focus(reduction,20-reduction);}
void discipline_guards() {
 for(int guard=0;guard<12;++guard) {
  Client c;spells[1].is_discipline=true;spells[1].sneak=false;spells[1].buff_duration_formula=0;
  if(guard==0)c.stunned=true;if(guard==1)c.feared=true;if(guard==2)c.mezzed=true;
  if(guard==3)c.amnesiad=true;if(guard==4)c.pet=true;if(guard==5)c.aura=true;
  if(guard==6)c.m_pp.disciplines.values[0]=0;if(guard==7)c.required_level=255;
  if(guard==8)c.required_level=60;if(guard==9)c.endurance=0;
  if(guard==10){spells[1].sneak=true;c.hidden=false;}
  if(guard==11){spells[1].buff_duration_formula=1;spells[1].target_type=ST_Self;c.disc_buff=true;}
  check(!c.UseDiscipline(1,44),"discipline authorization guard accepted");
  check(c.p_timers._list.empty() && c.casts==0 && c.discipline_packets.empty(),"rejected discipline consumed cooldown");
 }
 spells[1].sneak=false;spells[1].buff_duration_formula=0;
 Client active;pTimerType timer=pTimerDisciplineReuseStart+spells[1].timer_id;active.p_timers.Start(timer,30);
 check(!active.UseDiscipline(1,44) && active.casts==0,"active discipline cooldown allowed a recast");
 for(bool retained:{false,true}) {
  Client failed;failed.cast_ok=false;failed.focus=-5;
  if(retained){failed.p_timers.Start(timer,30);Timer::now+=30;}
  check(!failed.UseDiscipline(1,44),"failed normal cast must reject discipline");
  check(failed.p_timers.Expired(&database,timer,false) && failed.discipline_packets.empty(),"failed discipline cast consumed or advertised cooldown");
 }
}
void select_unlinked_item(Client& c,uint32 id,uint32 delay=20,bool augment=false) {
 c.inventory.item.data.ID=id;c.inventory.item.data.RecastType=RECAST_TYPE_UNLINKED_ITEM;
 c.inventory.item.data.RecastDelay=delay;
 database.items[id]=&c.inventory.item.data;
 if(augment) {
  check(c.inventory.item.augment!=nullptr,"augment fixture missing");
  c.inventory.item.augment->data=c.inventory.item.data;
  c.inventory.item.data.RecastDelay=0;
  database.items[id]=&c.inventory.item.augment->data;
 }
}
void item_legacy_aa_collision() {
 for(bool augment:{false,true}) {
  Client c;ItemInstance aug;c.inventory.item.augment=augment?&aug:nullptr;
  select_unlinked_item(c,64350,20,augment);c.SetItemRecastTimer(1,0);
  check(c.HasItemRecastTimer(1,0),"unlinked item must see its own cooldown");
  check(c.p_timers.Expired(&database,1186,false),"item 64350 overwrote legacy AA key 1186");
  check(c.p_timers.Expired(&database,pTimerAAStart+186,false),"item cooldown blocked an AA family");
 }
}
void item_modulo_pair() {
 for(bool augment:{false,true}) {
  Client c;ItemInstance aug;c.inventory.item.augment=augment?&aug:nullptr;
  select_unlinked_item(c,64350,20,augment);c.SetItemRecastTimer(1,0);
  select_unlinked_item(c,129886,45,augment);
  check(!c.HasItemRecastTimer(1,0),"items differing by 65536 share a cooldown");
  c.SetItemRecastTimer(1,0);
  select_unlinked_item(c,64350,20,augment);Timer::now+=20;
  check(!c.HasItemRecastTimer(1,0),"second item overwrote the first item's deadline");
  c.DeleteItemRecastTimer(64350);
  select_unlinked_item(c,129886,45,augment);
  check(c.HasItemRecastTimer(1,0),"resetting first item also reset its modulo partner");
  c.DeleteItemRecastTimer(129886);
  check(!c.HasItemRecastTimer(1,0),"item reset did not clear the active item cooldown");
 }
}
void item_cooldown_api() {
 Client c;select_unlinked_item(c,64350);Timer::now=static_cast<uint32>(std::time(nullptr));
 c.p_timers.Start(pTimerAAStart+186,77);c.SetItemCooldown(64350,false,30);
 check(c.HasItemRecastTimer(1,0),"SetItemCooldown and item click lookup disagree");
 check(c.GetItemCooldown(64350)>=29 && c.GetItemCooldown(64350)<=30,"saved item deadline disagrees with native timer");
 check(c.p_timers.GetRemainingTime(pTimerAAStart+186)==77,"SetItemCooldown changed an AA timer");
 c.DeleteItemRecastTimer(64350);
 check(!c.HasItemRecastTimer(1,0) && c.GetItemCooldown(64350)==0,"item reset did not clear both timer stores");
 check(c.p_timers.GetRemainingTime(pTimerAAStart+186)==77,"item reset cleared an AA timer");
}
void item_saved_timer_preserves_longer_native_deadline() {
 Client c;select_unlinked_item(c,64350);Timer::now=static_cast<uint32>(std::time(nullptr));
 c.SetItemCooldown(64350,false,300);
 check(c.p_timers._list.size()==1,"native item timer fixture missing");
 const auto* native=c.p_timers._list.begin()->second;
 const uint32 original_start=native->start_time,original_duration=native->timer_time;
 const uint32 saved_timestamp=Timer::now+30;
 database.timestamps[64350]=saved_timestamp;database.updated.clear();c.item_packets.clear();
 const uint32 remaining=c.GetItemCooldown(64350);
 check(remaining>=299 && remaining<=300,"item cooldown read hid the longer native deadline");
 c.SetItemCooldown(64350,true,0);
 // This fixture records helper arguments. Real SendItemRecastTimer suppresses
 // OP_ItemRecastDelay for unlinked items; their inventory timestamp is the UI boundary.
 check(c.item_packets.size()==1 && c.item_packets.back()>=299 && c.item_packets.back()<=300,
  "saved item refresh did not pass the longer cooldown to the recast helper");
 const uint32 published=c.inventory.item.recast_timestamp-static_cast<uint32>(std::time(nullptr));
 check(published>=299 && published<=300,"inventory item timestamp disagrees with the published native deadline");
 check(native->start_time==original_start && native->timer_time==original_duration,
  "saved item refresh changed the authoritative persistent timer");
 check(database.timestamps.at(64350)==saved_timestamp && database.updated.empty(),
  "saved item refresh rewrote the original saved timestamp");
}
void item_namespace_bounds() {
 for(bool augment:{false,true}) {
  Client c;ItemInstance aug;c.inventory.item.augment=augment?&aug:nullptr;
  select_unlinked_item(c,0xfffff,20,augment);c.SetItemRecastTimer(1,0);
  check(c.HasItemRecastTimer(1,0),"maximum legal item ID must retain cooldown");
  c.DeleteItemRecastTimer(0xfffff);
  check(!c.HasItemRecastTimer(1,0),"maximum legal item ID did not reset");
  for(uint32 invalid:{0x100000u,0xffffffffu}) {
   select_unlinked_item(c,invalid,20,augment);c.SetItemRecastTimer(1,0);
   check(c.p_timers._list.empty(),"out-of-range item ID wrote into another timer namespace");
   check(c.HasItemRecastTimer(1,0),"out-of-range item ID must fail closed at click admission");
   // A rejected deletion must preserve all existing namespaces and DB rows.
   c.p_timers.Start(pTimerDisciplineReuseStart,77);database.timestamps[invalid]=1077;
   c.DeleteItemRecastTimer(invalid);
   check(c.p_timers.GetRemainingTime(pTimerDisciplineReuseStart)==77 && database.timestamps.count(invalid),
    "out-of-range item reset changed existing cooldowns");
   c.p_timers.Clear(&database,pTimerDisciplineReuseStart);
  }
 }
 Client c;select_unlinked_item(c,0xfffff);Timer::now=static_cast<uint32>(std::time(nullptr));
 c.SetItemCooldown(0xfffff,false,20);
 check(c.HasItemRecastTimer(1,0),"SetItemCooldown rejected maximum legal item ID");
 c.DeleteItemRecastTimer(0xfffff);
 for(uint32 invalid:{0x100000u,0xffffffffu}) {
  select_unlinked_item(c,invalid);c.SetItemCooldown(invalid,false,20);
  check(c.p_timers._list.empty(),"SetItemCooldown accepted out-of-range item ID");
 }
}
void discipline_isolation(uint32 group) {
 for(bool prior_other:{false,true}) {
  Client c;spells[1].is_discipline=true;spells[1].timer_id=group;
  if(prior_other) {
   if(group==11)c.p_timers.Start(pTimerCombatAbility,41);
   else c.SetLinkedSpellReuseTimer(0,41);
  }
  check(c.UseDiscipline(1,44),"unrelated combat/linked timer blocked discipline group "+std::to_string(group));
  check(c.GetDisciplineTimer(group)==20,"discipline did not retain its own timer");
  if(group==11)check(c.p_timers.GetRemainingTime(pTimerCombatAbility)==(prior_other?41:0),"discipline group 11 changed basic combat timer");
  else check(c.IsLinkedSpellReuseTimerReady(0)==!prior_other,"discipline group 14 changed linked spell timer 0");
  c.ResetDisciplineTimer(group);
  check(c.GetDisciplineTimer(group)==0,"individual discipline reset failed");
  if(prior_other)check(c.p_timers.GetRemainingTime(group==11?pTimerCombatAbility:pTimerLinkedSpellReuseStart)==41,
   "discipline reset cleared an unrelated timer");
 }
}
void discipline_reset_all_twenty() {
 Client c;spells[1].is_discipline=true;
 for(uint32 group=0;group<20;++group) {
  spells[1].timer_id=group;check(c.UseDiscipline(1,44),"valid discipline group rejected");
  check(c.GetDisciplineTimer(group)==20,"valid discipline group was not stored");
 }
 const pTimerType unrelated[]={pTimerAAStart+186,pTimerMend,pTimerCombatAbility,pTimerLinkedSpellReuseStart,pTimerItemStart+4};
 for(auto key:unrelated)c.p_timers.Start(key,77);
 select_unlinked_item(c,64350,55);c.SetItemRecastTimer(1,0);
 c.discipline_packets.clear();c.discipline_packet_ids.clear();c.ResetAllDisciplineTimers();
 for(uint32 group=0;group<20;++group)check(c.GetDisciplineTimer(group)==0,"reset all left discipline group "+std::to_string(group)+" active");
 for(auto key:unrelated)check(c.p_timers.GetRemainingTime(key)==77,"reset all disciplines cleared an unrelated timer");
 check(c.HasItemRecastTimer(1,0),"reset all disciplines cleared an unlinked item timer");
 check(c.discipline_packet_ids.size()==20,"reset all must send exactly 20 client group resets");
 for(uint32 group=0;group<20;++group)check(c.discipline_packet_ids[group]==group && c.discipline_packets[group]==0,
  "reset all sent an incorrect group/duration");
}
void discipline_invalid_twenty() {
 for(int group:{20,21,-2}) {
  Client c;spells[1].is_discipline=true;spells[1].timer_id=group;
  check(!c.UseDiscipline(1,44),"out-of-range discipline group accepted");
  check(c.casts==0 && c.p_timers._list.empty() && c.discipline_packets.empty(),"invalid discipline consumed cooldown");
  c.p_timers.Start(pTimerDisciplineReuseStart+group,77);
  check(c.GetDisciplineTimer(group)==0,"invalid discipline read leaked a persistent timer");
  c.ResetDisciplineTimer(group);
  check(c.p_timers.GetRemainingTime(pTimerDisciplineReuseStart+group)==77 && c.discipline_packets.empty(),
   "invalid discipline reset touched another namespace or sent a packet");
 }
 Client c;c.p_timers.Start(pTimerDisciplineReuseStart-1,77);
 check(c.GetDisciplineTimer(0xffffffffu)==0,"invalid public group lookup reached an unrelated timer");
 c.ResetDisciplineTimer(0xffffffffu);
 check(c.p_timers.GetRemainingTime(pTimerDisciplineReuseStart-1)==77 && c.discipline_packets.empty(),
  "invalid public group reset reached an unrelated timer");
}
void unlinked_discipline_isolation() {
 // Actual catalog timer=-1 families: Thief's Eyes8001 / Thief's Vision40294.
 for(bool prior_disarm:{false,true}) {
  Client c;c.m_pp.disciplines.values[0]=8001;c.m_pp.disciplines.values[1]=40294;
  for(uint32 id:{8001u,40294u}){spells[id].is_discipline=true;spells[id].timer_id=-1;}
  if(prior_disarm)c.p_timers.Start(pTimerDisarmTraps,77);
  check(c.UseDiscipline(8001,44),"legitimate timer -1 discipline rejected");
  const pTimerType first=c.casting_spell_timer;
  check(c.p_timers.GetRemainingTime(pTimerDisarmTraps)==(prior_disarm?77:0),"timer -1 discipline changed Disarm Traps timer13");
  check(c.UseDiscipline(40294,44),"second timer -1 discipline shares first family's cooldown");
  const pTimerType second=c.casting_spell_timer;
  check(first!=second,"unlinked discipline families use the same persistent key");
  check(!c.UseDiscipline(8001,44) && !c.UseDiscipline(40294,44),"active unlinked discipline accepted a recast");
  check(c.discipline_packets.empty(),"unlinked discipline sent an invalid native timer group");
  c.ResetAllDisciplineTimers();
  check(c.p_timers.Expired(&database,first,false) && c.p_timers.Expired(&database,second,false),
   "reset all failed to clear unlinked discipline timers");
  check(c.p_timers.GetRemainingTime(pTimerDisarmTraps)==(prior_disarm?77:0),"unlinked discipline reset cleared Disarm Traps");
  check(c.UseDiscipline(8001,44) && c.UseDiscipline(40294,44),"reset unlinked disciplines remain blocked");
 }
}
int main(int argc,char** argv) {
 try {
  check(argc==2,"scenario required");std::string scenario=argv[1];
  if(scenario=="item-normal")item_normal();
  else if(scenario=="item-equal")item_equal();
  else if(scenario=="item-excess")item_excess();
  else if(scenario=="linked-normal")linked_normal();
  else if(scenario=="linked-negative-bard")linked_negative_focus(true);
  else if(scenario=="linked-negative-ordinary")linked_negative_focus(false);
  else if(scenario=="linked-excess-bard")linked_excess_adjustment(true);
  else if(scenario=="linked-excess-ordinary")linked_excess_adjustment(false);
  else if(scenario=="linked-non-gem")linked_non_gem();
  else if(scenario=="mend-normal")mend_normal();
  else if(scenario=="mend-excess")mend_excess();
  else if(scenario=="retained-mend-equal")retained_mend(360);
  else if(scenario=="retained-mend-excess")retained_mend(361);
  else if(scenario=="retained-linked-equal-bard")retained_linked(20,true);
  else if(scenario=="retained-linked-equal-ordinary")retained_linked(20,false);
  else if(scenario=="retained-linked-excess-bard")retained_linked(21,true);
  else if(scenario=="retained-linked-excess-ordinary")retained_linked(21,false);
  else if(scenario=="skill-normal")skill_normal();
  else if(scenario.find("skill-zero-")==0)skill_zero(scenario.substr(11));
  else if(scenario=="custom-zero-bard")custom_zero(true);
  else if(scenario=="custom-zero-ordinary")custom_zero(false);
  else if(scenario=="custom-controls")custom_controls();
  else if(scenario=="discipline-normal")discipline_normal();
  else if(scenario=="discipline-negative")discipline_negative();
  else if(scenario=="discipline-guards")discipline_guards();
  else if(scenario=="item-legacy-aa")item_legacy_aa_collision();
  else if(scenario=="item-modulo-pair")item_modulo_pair();
  else if(scenario=="item-cooldown-api")item_cooldown_api();
  else if(scenario=="item-saved-native-deadline")item_saved_timer_preserves_longer_native_deadline();
  else if(scenario=="item-namespace-bounds")item_namespace_bounds();
  else if(scenario=="discipline-combat-isolation")discipline_isolation(11);
  else if(scenario=="discipline-linked-isolation")discipline_isolation(14);
  else if(scenario=="discipline-reset-all-twenty")discipline_reset_all_twenty();
  else if(scenario=="discipline-invalid-twenty")discipline_invalid_twenty();
  else if(scenario=="unlinked-discipline-isolation")unlinked_discipline_isolation();
  else throw std::runtime_error("unknown scenario");
  std::cout<<"PASS: "<<scenario<<'\n';
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
'''


class CooldownDurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spells = (SOURCE / "zone/spells.cpp").read_text(encoding="utf-8")
        packets = (SOURCE / "zone/client_packet.cpp").read_text(encoding="utf-8")
        effects = (SOURCE / "zone/effects.cpp").read_text(encoding="utf-8")
        client = (SOURCE / "zone/client.cpp").read_text(encoding="utf-8")
        mob = (SOURCE / "zone/mob.h").read_text(encoding="utf-8")
        timers = (SOURCE / "common/ptimer.h").read_text(encoding="utf-8")
        member = re.search(r"\b(?:u?int\d+)\s+casting_spell_recast_adjust\s*;", mob)
        if not member:
            raise AssertionError("native recast-adjust field declaration not found")
        fixture = FIXTURE.replace("/* NATIVE_TIMER_ENUM */", function(timers, "enum : int") + ";")
        timer_type = re.search(r"typedef\s+\w+\s+pTimerType\s*;", timers)
        if not timer_type:
            raise AssertionError("native persistent timer type declaration not found")
        fixture = fixture.replace("/* NATIVE_TIMER_TYPE */", timer_type.group())
        fixture = fixture.replace("/* NATIVE_RECAST_ADJUST_MEMBER */", member.group())
        focus_return = re.search(r"virtual\s+(\w+)\s+GetFocusEffect\(", mob)
        if not focus_return:
            raise AssertionError("native GetFocusEffect return type not found")
        fixture = fixture.replace("/* NATIVE_FOCUS_RETURN */", focus_return.group(1))
        timer_source = SOURCE / "common/ptimer.cpp"
        if not timer_source.is_file():
            timer_source = Path(__file__).with_name("fixtures") / "cooldown_persistent_timer.cpp"
        native_timers = timer_source.read_text(encoding="utf-8")
        methods = "\n".join(function(native_timers, signature) for signature in (
            "PersistentTimer::PersistentTimer(uint32 char_id, pTimerType type, uint32 in_timer_time)",
            "bool PersistentTimer::Expired(", "void PersistentTimer::Start(",
            "uint32 PersistentTimer::GetRemainingTime(", "void PTimerList::Start(",
            "void PTimerList::Clear(Database *db, pTimerType type)", "bool PTimerList::Expired(",
            "uint32 PTimerList::GetRemainingTime(", "PersistentTimer *PTimerList::Get("))
        methods += "\n".join(function(spells, signature) for signature in (
            "void Client::SetItemRecastTimer(", "void Client::SetLinkedSpellReuseTimer(",
            "void Client::DeleteItemRecastTimer(", "bool Client::HasItemRecastTimer(",
            "bool Client::IsLinkedSpellReuseTimerReady("))
        methods += "\n".join(function(client, signature) for signature in (
            "void Client::SetItemCooldown(", "uint32 Client::GetItemCooldown("))
        methods += function(packets, "void Client::Handle_OP_Mend(")
        methods += "\n".join(function(effects, signature) for signature in (
            "bool Client::UseDiscipline(", "uint32 Client::GetDisciplineTimer(",
            "void Client::ResetDisciplineTimer(", "void Client::ResetAllDisciplineTimers("))
        # Keep actual admission/reuse logic; stop exactly at the first gameplay
        # effect statement and record that it was reached. This does not test
        # trap detection, feign outcomes, visibility or their downstream effects.
        for name, boundary in (
            ("DisarmTraps", "uint8 success = SKILLUP_FAILURE;"),
            ("FeignDeath", "uint16 primfeign ="),
            ("Hide", "float hidechance ="),
            ("SenseTraps", "float trap_curdist ="),
        ):
            handler = function(packets, f"void Client::Handle_OP_{name}(")
            methods += handler[:handler.index(boundary)] + "\n++skill_actions;\n}\n"
        prepare = function(spells, "if (spells[spell_id].recast_time > 1000 && !spells[spell_id].is_discipline)")
        methods += "\nvoid Client::PrepareSpellRecast(int spell_id) {\n" + prepare + "\n}\n"
        spell_finished = function(spells, "bool Mob::SpellFinished(")
        custom = function(spell_finished, "if(IsClient() && !isproc && !IsFromTriggeredSpell(slot, inventory_slot))")
        methods += "\nvoid Client::FinishCustom(int spell_id,bool isproc,CastingSlot slot,uint32 inventory_slot,uint32 timer,uint32 timer_duration) {uint32 aa_id=0;\n" + custom + "\n}\n"
        complete = function(spells, "void Mob::CastedSpellFinished(")
        marker = "if (spells[spell_id].timer_id > 0 && slot < CastingSlot::MaxGems)"
        for name in ("FinishBard", "FinishOrdinary"):
            block = function(complete, marker)
            complete = complete[complete.index(block) + len(block):]
            methods += f"\nvoid Client::{name}(int spell_id,CastingSlot slot) {{auto* c=this;\n{block}\n}}\n"
        cls.temp = tempfile.TemporaryDirectory(prefix="cooldown-duration-")
        cls.addClassCleanup(cls.temp.cleanup)
        path = Path(cls.temp.name)
        (path / "test.cpp").write_text(fixture + methods + CONTROLS, encoding="utf-8")
        cls.binary = path / "test.exe"
        if os.name == "nt":
            (path / "build.cmd").write_text(
                '@echo off\ncall "C:\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat" >nul\n'
                f'cl /nologo /EHsc /W4 /std:c++17 /I"{SOURCE}" test.cpp /Fe:test.exe\n')
            command = ["cmd", "/d", "/c", str(path / "build.cmd")]
        else:
            command = ["g++", "-std=c++17", "-Wall", "-Wextra", "-I", str(SOURCE), "test.cpp", "-o", "test.exe"]
        result = subprocess.run(command, cwd=path, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def run_scenario(self, scenario):
        result = subprocess.run([self.binary, scenario], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout.strip())

    def test_item_normal_and_negative_focus_preserve_duration(self):
        self.run_scenario("item-normal")

    def test_item_equal_reduction_is_ready(self):
        self.run_scenario("item-equal")

    def test_item_excess_reduction_is_ready(self):
        self.run_scenario("item-excess")

    def test_linked_bard_and_ordinary_normal_focus(self):
        self.run_scenario("linked-normal")

    def test_linked_negative_focus_extends_duration_without_wrapping(self):
        for path in ("bard", "ordinary"):
            with self.subTest(path=path):
                self.run_scenario("linked-negative-" + path)

    def test_linked_equal_and_excess_adjustment_is_ready(self):
        for path in ("bard", "ordinary"):
            with self.subTest(path=path):
                self.run_scenario("linked-excess-" + path)

    def test_linked_completion_ignores_non_gem_casts(self):
        self.run_scenario("linked-non-gem")

    def test_mend_normal_equal_negative_and_unavailable_controls(self):
        self.run_scenario("mend-normal")

    def test_mend_excess_reduction_is_ready(self):
        self.run_scenario("mend-excess")

    def test_expired_retained_mend_does_not_restart_on_zero_duration(self):
        for reduction in ("equal", "excess"):
            with self.subTest(reduction=reduction):
                self.run_scenario("retained-mend-" + reduction)

    def test_expired_retained_linked_timer_does_not_restart_on_zero_duration(self):
        for path in ("bard", "ordinary"):
            for reduction in ("equal", "excess"):
                with self.subTest(path=path, reduction=reduction):
                    self.run_scenario("retained-linked-" + reduction + "-" + path)

    def test_other_skill_prologs_preserve_normal_duration_and_guards(self):
        self.run_scenario("skill-normal")

    def test_other_skill_prologs_do_not_revive_expired_timers(self):
        for skill in ("disarm", "feign", "hide", "sense"):
            with self.subTest(skill=skill):
                self.run_scenario("skill-zero-" + skill)

    def test_custom_aa_disc_timers_preserve_positive_duration_and_guards(self):
        self.run_scenario("custom-controls")

    def test_custom_aa_disc_zero_duration_does_not_revive_expired_timers(self):
        for path in ("bard", "ordinary"):
            with self.subTest(path=path):
                self.run_scenario("custom-zero-" + path)

    def test_discipline_normal_equal_and_excess_focus(self):
        self.run_scenario("discipline-normal")

    def test_discipline_negative_focus_extends_reuse(self):
        self.run_scenario("discipline-negative")

    def test_discipline_authorization_active_reuse_and_failed_cast_controls(self):
        self.run_scenario("discipline-guards")

    def test_unlinked_item_64350_does_not_collide_with_legacy_aa_key_1186(self):
        self.run_scenario("item-legacy-aa")

    def test_unlinked_item_ids_separated_by_65536_retain_independent_deadlines_and_resets(self):
        self.run_scenario("item-modulo-pair")

    def test_set_get_and_delete_item_cooldown_use_same_isolated_timer(self):
        self.run_scenario("item-cooldown-api")

    def test_saved_item_refresh_publishes_longer_native_deadline_without_rewriting_sources(self):
        self.run_scenario("item-saved-native-deadline")

    def test_discipline_groups_11_and_14_do_not_block_combat_or_linked_spells(self):
        for path in ("combat", "linked"):
            with self.subTest(path=path):
                self.run_scenario("discipline-" + path + "-isolation")

    def test_reset_all_twenty_discipline_groups_preserves_other_namespaces(self):
        self.run_scenario("discipline-reset-all-twenty")

    def test_invalid_discipline_groups_cannot_cast_read_or_reset_timers(self):
        self.run_scenario("discipline-invalid-twenty")

    def test_item_id_namespace_bounds_reject_writes_resets_and_clicks_above_client_limit(self):
        self.run_scenario("item-namespace-bounds")

    def test_unlinked_discipline_minus_one_is_independent_from_disarm_and_other_disciplines(self):
        self.run_scenario("unlinked-discipline-isolation")


if __name__ == "__main__":
    unittest.main(verbosity=2)

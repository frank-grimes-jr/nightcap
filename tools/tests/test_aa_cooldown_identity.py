"""Compile native AA activation, catalog, resets and resend against a clock fixture.

Content comes from the retained AA catalog and current compiled policy. Set
NIGHTCAP_AA_COOLDOWN_CATALOG to a SELECT-only cooldown-content.json capture to
overlay current spell/group/duration/class fields. Ownership, cast completion,
packet transport and timer persistence are explicit deterministic boundaries;
this is not a complete zone build or native RoF2 consumer test.
"""
import gzip
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from test_gameplay_policies import ROOT, function

sys.path.insert(0, str(ROOT / "tools"))
from aa_tbs_policy import compile_policy

SOURCE = ROOT / "server-mods/code"

FIXTURE = r'''
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
#include "common/nightcap_aa_policy.h"
using uint8=uint8_t;using uint16=uint16_t;using uint32=uint32_t;using int64=int64_t;
/* TIMER_DECLARATIONS */
uint32 clock_now=100000;
#define time(unused) clock_now
#define safe_delete(p) delete p
namespace EQ {namespace spells {enum class CastingSlot {AltAbility};}}
namespace Chat {enum {Red,White,SpellFailure};}
namespace Class {enum {Warrior=1,Cleric=2,Monk=7,Bard=8};}
enum {SNEAK_RESTRICT,ST_Pet,ST_SummonedPet,eaSitting,eaStanding,STAND_TO_CAST,
 OP_AAAction,OP_SendAATable};
struct UseAA_Struct {uint32 ability=0,begin=0,end=0;};
struct AARankInfo_Struct {
 int id,upper_hotkey_sid,lower_hotkey_sid,title_sid,desc_sid,cost,seq,type,spell,
 spell_type,spell_refresh,classes,level_req,current_level,max_level,prev_id,next_id,
 total_cost,expansion,category,charges,grant_only,total_effects,total_prereqs;
};
struct AARankEffect_Struct {int effect_id=0,base_value=0,limit_value=0,slot=0;};
struct AARankPrereq_Struct {int ability,points;};
struct EQApplicationPacket {
 int opcode;unsigned char* pBuffer;
 EQApplicationPacket(int op,int size):opcode(op),pBuffer(new unsigned char[size]{}) {}
 ~EQApplicationPacket() {delete[] pBuffer;}
 void SetWritePosition(int) {} void WriteSInt32(int) {}
};
struct Database {} database;
struct PersistentTimer {
 pTimerType type=0;uint32 start=0,duration=0;
 pTimerType GetType() const {return type;} uint32 GetStartTime() const {return start;}
 uint32 GetTimerTime() const {return duration;}
};
struct PTimerList {
 std::map<pTimerType,PersistentTimer> values;
 std::map<pTimerType,PersistentTimer*> pointers;
 using iterator=std::map<pTimerType,PersistentTimer*>::iterator;
 iterator begin() {return pointers.begin();} iterator end() {return pointers.end();}
 void Start(pTimerType key,uint32 duration) {
  values[key]={key,clock_now,duration};pointers[key]=&values.at(key);
 }
 bool Expired(Database*,pTimerType key,bool) const {
  const auto it=values.find(key);return it==values.end() || clock_now-it->second.start>=it->second.duration;
 }
 uint32 GetRemainingTime(pTimerType key) const {
  const auto it=values.find(key);return Expired(nullptr,key,false)?0:it->second.duration-(clock_now-it->second.start);
 }
 void Clear(Database*,pTimerType key) {pointers.erase(key);values.erase(key);}
 PersistentTimer* Get(pTimerType key) {
  const auto it=pointers.find(key);return it==pointers.end()?nullptr:it->second;
 }
 void Restore(const PTimerList& saved) {
  values=saved.values;pointers.clear();for(auto& row:values)pointers[row.first]=&row.second;
 }
};
struct Client;
namespace AA {
struct Ability {
 int id=0,charges=0,type=0,category=0,grant_only=0,reset_on_death=0;
 uint32 classes=0;int GetMaxLevel(Client*) const {return 100;}
};
struct Rank {
 int id=0,spell=0,spell_type=0,recast_time=0,current_value=1,expansion=0;
 int upper_hotkey_sid=0,lower_hotkey_sid=0,title_sid=0,desc_sid=0,cost=0,
 prev_id=-1,next_id=-1,total_cost=0;
 Ability* base_ability=nullptr;Rank* next=nullptr;
 std::vector<AARankEffect_Struct> effects;std::map<int,int> prereqs;
};
}
struct Zone {
 std::map<int,AA::Ability> aa_abilities_values;
 std::map<int,AA::Rank> aa_ranks_values;
 struct RankPointer {AA::Rank* value;AA::Rank* get() const {return value;}};
 std::map<int,RankPointer> aa_ranks;
 AA::Rank* GetAlternateAdvancementRank(int id) {
  auto it=aa_ranks_values.find(id);return it==aa_ranks_values.end()?nullptr:&it->second;
 }
 std::pair<AA::Ability*,AA::Rank*> GetAlternateAdvancementAbilityAndRank(int aid,int ordinal) {
  for(auto& row:aa_ranks_values)if(row.second.base_ability->id==aid && row.second.current_value==ordinal)
   return {row.second.base_ability,&row.second};
  return {nullptr,nullptr};
 }
 int GetZoneID() const {return 1;} int GetInstanceID() const {return 0;}
} zone_value;
auto* zone=&zone_value;
struct Spell {int sneak=0,target_type=0,cast_time=1,mana=0,resist_difficulty=0;} spells[65536];
bool IsValidSpell(int id) {return id>0 && id<65536;}
bool IsCastWhileInvisibleSpell(int) {return false;}
bool IsCastNotStandingSpell(int) {return false;}
bool UseTogglePassiveHotkey(const AA::Rank&) {return false;}
struct Timer {static uint32 GetCurrentTime() {return clock_now;}};
struct Mob {};
struct Entities {Mob* GetMob(int) {return nullptr;}} entity_list;
struct Client {
 // Keep the primary Warrior in the authoritative mask. Pair scenarios add
 // at most one class for each ability, respecting Nightcap's three-class cap.
 PTimerList p_timers;uint32 held=1u<<Class::Warrior;std::map<int,uint32> earned;
 std::map<int,std::pair<int,int>> aa_ranks;
 std::vector<int> casts;std::vector<UseAA_Struct> actions;std::vector<AARankInfo_Struct> catalog;
 bool valid=true,cast_ok=true,hidden=false,casting=false,m_nightcap_ui_enabled=false;
 int primary=Class::Warrior,appearance=eaStanding,reduction=0,rejected=0,casting_spell_aa_id=0;
 uint32 tmHidden=0,m_nightcap_ui_generation=1;
 uint32 CharacterID() const {return 1;} int GetID() const {return 1;}
 uint32 GetClassMask() const {return held;}
 bool HasValidEarnedAAState() const {return valid;}
 bool CanUseAlternateAdvancementRank(AA::Rank* rank) const {
  return rank && rank->base_ability && (held&rank->base_ability->classes) &&
   NightcapAA::RequiredLevel(rank->id,rank->base_ability->id,rank->current_value,rank->expansion)>0;
 }
 uint32 GetAA(int id,uint32* charges=nullptr) const {
  if(charges)*charges=1;const auto it=earned.find(id);return it==earned.end()?0:it->second;
 }
 int GetAlternateAdvancementCooldownReduction(AA::Rank*) const {return reduction;}
 template<class... T> void Message(T...) {++rejected;}
 template<class... T> void MessageString(T...) {++rejected;}
 void CommonBreakInvisible() {} int GetPetID() const {return 5;}
 int GetAppearance() const {return appearance;} void SetAppearance(int value,bool) {appearance=value;}
 int GetClass() const {return primary;} bool IsCasting() const {return casting;}
 bool DoCastingChecksOnCaster(int,EQ::spells::CastingSlot) const {return cast_ok;}
 void TogglePassiveAlternativeAdvancement(AA::Rank&,int) {}
 void QueuePacket(EQApplicationPacket* packet) {
  if(packet->opcode==OP_AAAction)actions.push_back(*reinterpret_cast<UseAA_Struct*>(packet->pBuffer));
  else if(packet->opcode==OP_SendAATable)catalog.push_back(*reinterpret_cast<AARankInfo_Struct*>(packet->pBuffer));
 }
 // Controlled cast-completion boundary: consumes exactly the timer/duration
 // handed to native casting. Targeting, damage and transport are not modeled.
 bool CompleteCast(int rank_id,pTimerType timer,int duration) {
  if(!cast_ok)return false;casts.push_back(rank_id);casting_spell_aa_id=rank_id;
  PublishAACompletion(rank_id);
  if(duration>0)p_timers.Start(timer,duration);else p_timers.Clear(&database,timer);
  return true;
 }
 bool CastSpell(int,int,EQ::spells::CastingSlot,int,int,int,int,pTimerType timer,
  int duration,void*,int rank_id) {return CompleteCast(rank_id,timer,duration);}
 bool SpellFinished(int,Mob*,EQ::spells::CastingSlot,int,int,int,bool,int,pTimerType timer,
  int duration,bool,int rank_id) {return CompleteCast(rank_id,timer,duration);}
 void ActivateAlternateAdvancementAbility(int,int);
 void SendAlternateAdvancementRank(int,int);
 void SendAlternateAdvancementTimer(int,int,int);
 void SendAlternateAdvancementTimers();
 void ResetAlternateAdvancementTimer(int);
 void ResetAlternateAdvancementTimers();
 void ResetOnDeathAlternateAdvancement();
 int GetAlternateAdvancementTimerSlot(int);
 Client* CastToClient() {return this;}
 void ExpendAlternateAdvancementCharge(int) {}
 void PublishAACompletion(int);
};
void check(bool ok,const std::string& why) {if(!ok)throw std::runtime_error(why);}
std::vector<int> family_representatives;
void add_rank(int aid,int rid,int ordinal,int spell,int group,int seconds,int expansion,uint32 raw_classes) {
 auto& ability=zone->aa_abilities_values[aid];ability.id=aid;ability.classes=raw_classes<<1;
 auto& rank=zone->aa_ranks_values[rid];rank.id=rid;rank.current_value=ordinal;
 rank.spell=spell;rank.spell_type=group;rank.recast_time=seconds;rank.expansion=expansion;rank.base_ability=&ability;
 zone->aa_ranks[rid]={&rank};
}
uint32 first_class(uint32 classes) {return classes&(~classes+1);}
void own(Client& c,int rank_id) {
 auto* rank=zone->GetAlternateAdvancementRank(rank_id);check(rank!=nullptr,"fixture missing rank");
 c.earned[rank_id]=rank->current_value;c.held|=first_class(rank->base_ability->classes);
 c.aa_ranks[rank->base_ability->id]={rank->current_value,0};
}
int wire_group(Client& c,int rank_id) {
 auto* rank=zone->GetAlternateAdvancementRank(rank_id);c.catalog.clear();
 c.SendAlternateAdvancementRank(rank->base_ability->id,rank->current_value);
 check(c.catalog.size()==1,"owned legal AA absent from table");return c.catalog.back().spell_type;
}
// Native client subtracts HastenedAASkill from the catalog base duration.
// Signed arithmetic here intentionally permits a projected future begin time.
int64 native_remaining(const Client& c,int rank_id,const UseAA_Struct& action) {
 const auto* rank=zone->GetAlternateAdvancementRank(rank_id);
 const int duration=rank->recast_time-c.reduction;
 if(duration==0)return 0; // Native IsAbilityReady returns before reading its clock.
 return std::max<int64>(0,int64(duration)-(int64(action.end)-action.begin));
}
std::map<int,int64> active_wire_timers(Client& c,const std::vector<int>& ranks) {
 std::map<int,int> slots;for(int rank:ranks)slots[wire_group(c,rank)]=rank;
 std::map<int,int64> result;
 for(const auto& action:c.actions) {
  auto found=slots.find(action.ability);if(found==slots.end())continue;
  const auto remaining=native_remaining(c,found->second,action);
  if(remaining>0)result[found->second]=remaining;else result.erase(found->second);
 }
 return result;
}
'''

SCENARIOS = r'''
void pair_case(int first,int second) {
 Client c;own(c,first);own(c,second);c.ActivateAlternateAdvancementAbility(first,1);
 check(c.casts.size()==1,"first earned ability failed");c.ActivateAlternateAdvancementAbility(second,1);
 check(c.casts.size()==2,"rank "+std::to_string(first)+" blocks unrelated rank "+std::to_string(second));
 check(c.actions.size()==2 && c.actions[0].ability==wire_group(c,first) &&
  c.actions[1].ability==wire_group(c,second),"successful AA pulses address wrong catalog slots");
}
void all_pairs(bool table) {
 int failures=0,cases=0;
 for(int first:family_representatives)for(int second:family_representatives) {
  if(first==second)continue;Client c;own(c,first);own(c,second);++cases;
  bool passed=false;
  if(table)passed=wire_group(c,first)!=wire_group(c,second);
  else {
   c.ActivateAlternateAdvancementAbility(first,1);check(c.casts.size()==1,"first pair ability not usable");
   c.ActivateAlternateAdvancementAbility(second,1);passed=c.casts.size()==2;
  }
  if(!passed) {if(failures<8)std::cerr<<first<<" aliases "<<second<<'\n';++failures;}
 }
 std::cout<<cases<<" ordered cases across "<<family_representatives.size()<<" families\n";
 check(failures==0,std::to_string(failures)+" cross-family aliases");
}
void same_family() {
 int cases=0;
 for(const auto& first:zone->aa_ranks_values)for(const auto& second:zone->aa_ranks_values) {
  if(first.second.base_ability!=second.second.base_ability)continue;
  Client c;own(c,first.first);own(c,second.first);
  check(wire_group(c,first.first)==wire_group(c,second.first),"same-family catalog groups diverge");
  c.ActivateAlternateAdvancementAbility(first.first,1);
  check(c.casts.size()==1,"first same-family cast failed");
  c.ActivateAlternateAdvancementAbility(second.first,1);
  check(c.casts.size()==1,"same family bypasses cooldown by changing rank");
  clock_now+=first.second.recast_time-1;c.ActivateAlternateAdvancementAbility(second.first,1);
  check(c.casts.size()==1,"same-family cooldown ended early");
  ++clock_now;c.ActivateAlternateAdvancementAbility(second.first,1);
  check(c.casts.size()==2,"same-family cooldown did not expire exactly");++cases;
 }
 std::cout<<cases<<" ordered same-family rank cases\n";
}
void guards() {
 for(int guard=0;guard<7;++guard) {
  Client c;own(c,258);
  if(guard==0)c.valid=false;if(guard==1)c.earned.clear();if(guard==2)c.held=0;
  if(guard==3)c.cast_ok=false;if(guard==4)c.appearance=99;
  if(guard==5)zone->aa_ranks_values[258].effects.push_back({});
  if(guard==6){c.hidden=false;spells[5233].sneak=1;}
  c.ActivateAlternateAdvancementAbility(258,1);
  check(c.casts.empty() && c.p_timers.values.empty(),"rejected/unearned AA started cooldown");
  zone->aa_ranks_values[258].effects.clear();spells[5233].sneak=0;
 }
}
void reset_one(bool stale_argument) {
 Client c;own(c,258);own(c,233);c.ActivateAlternateAdvancementAbility(258,1);
 c.casting_spell_aa_id=stale_argument?258:233;
 c.ResetAlternateAdvancementTimer(233);
 auto before=c.casts.size();c.ActivateAlternateAdvancementAbility(258,1);
 check(c.casts.size()==before,"reset Purify Body cleared active Rampage cooldown");
 c.ActivateAlternateAdvancementAbility(233,1);
 check(c.casts.size()==before+1,"reset Purify Body failed to make only Purify Body ready");
}
void reset_all() {
 Client c;own(c,258);own(c,233);c.ActivateAlternateAdvancementAbility(258,1);
 c.ActivateAlternateAdvancementAbility(233,1);c.p_timers.Start(pTimerMend,360);
 c.ResetAlternateAdvancementTimers();
 check(!c.p_timers.Expired(&database,pTimerMend,false),"AA reset-all cleared unrelated skill reuse");
 auto before=c.casts.size();c.ActivateAlternateAdvancementAbility(258,1);c.ActivateAlternateAdvancementAbility(233,1);
 check(c.casts.size()==before+2,"AA reset-all did not restore both distinct abilities");
}
void relog(bool inspect_packets) {
 Client previous;own(previous,258);own(previous,233);
 previous.ActivateAlternateAdvancementAbility(258,1);previous.ActivateAlternateAdvancementAbility(233,1);
 check(previous.casts.size()==2,"both independent abilities must activate before saving their deadlines");
 Client restored;own(restored,258);own(restored,233);restored.p_timers.Restore(previous.p_timers);
 if(inspect_packets) {
  restored.SendAlternateAdvancementTimers();
  const int a=wire_group(restored,258),b=wire_group(restored,233);
  check(a!=b,"relog catalog still aliases Rampage and Purify Body");
  const auto active=active_wire_timers(restored,{258,233});
  check(active==std::map<int,int64>{{258,600},{233,1800}},
   "relog resend does not match both catalog timer identities and remaining durations");
 } else {
  clock_now+=600;restored.ActivateAlternateAdvancementAbility(258,1);
  check(restored.casts.size()==1,"Rampage did not recover at600s after relog");
  restored.ActivateAlternateAdvancementAbility(233,1);
  check(restored.casts.size()==1,"Purify Body lost its1800s deadline after relog");
  clock_now+=1200;restored.ActivateAlternateAdvancementAbility(233,1);
  check(restored.casts.size()==2,"Purify Body still locked at own1800s deadline");
 }
}
void death_reset() {
 Client c;own(c,258);own(c,233);c.ActivateAlternateAdvancementAbility(258,1);
 // Synthetic reset flag exercises the native reset policy without changing
 // the retained catalog's real reset_on_death definitions.
 zone->aa_abilities_values[98].reset_on_death=1;c.ResetOnDeathAlternateAdvancement();
 c.ActivateAlternateAdvancementAbility(258,1);
 check(c.casts.size()==1,"death-reset family Purify Body cleared non-reset Rampage");
}
void purchase_stability() {
 Client c;c.held=(1u<<Class::Warrior)|(1u<<Class::Monk);
 const int rampage=wire_group(c,258),purify=wire_group(c,233);
 own(c,233);check(wire_group(c,258)==rampage,"buying earlier family moved Rampage's slot");
 own(c,258);check(wire_group(c,233)==purify,"buying another family moved Purify Body's slot");
 c.earned.erase(233);c.aa_ranks.erase(98);
 check(wire_group(c,258)==rampage && wire_group(c,233)==purify,
  "ownership removal changed slots despite unchanged held classes");
 check(rampage>=0 && rampage<100 && purify>=0 && purify<100 && rampage!=purify,
  "native wire slots invalid or aliased");
}
void class_remap() {
 Client c;own(c,258);own(c,233);
 const int old_slot=wire_group(c,258);
 c.ActivateAlternateAdvancementAbility(258,1);c.ActivateAlternateAdvancementAbility(233,1);
 check(c.casts.size()==2,"both initial class abilities must activate");
 clock_now+=100;
 c.held=1u<<Class::Warrior;
 const int new_slot=wire_group(c,258);
 check(new_slot!=old_slot,"fixture must exercise an actual class-slot reassignment");
 c.actions.clear();c.SendAlternateAdvancementTimers();
 check(c.actions.size()>=101,"class remap did not clear all100 native slots before projection");
 for(uint32 slot=0;slot<100;++slot)
  check(c.actions[slot].ability==slot && c.actions[slot].begin==0 && c.actions[slot].end==clock_now,
   "native slot clear sweep missing or out of order");
 check(active_wire_timers(c,{258})==std::map<int,int64>{{258,500}},
  "remaining Rampage deadline moved or vanished with class slots");
 const auto before=c.casts.size();c.ActivateAlternateAdvancementAbility(233,1);
 check(c.casts.size()==before,"released Monk retained Purify Body access");
 c.held|=1u<<Class::Monk;c.actions.clear();c.SendAlternateAdvancementTimers();
 check(active_wire_timers(c,{258,233})==std::map<int,int64>{{258,500},{233,1700}},
  "restored class lost or borrowed another family's persistent deadline");
}
void focused_resend() {
 Client c;own(c,258);c.reduction=120;c.ActivateAlternateAdvancementAbility(258,1);
 check(c.casts.size()==1,"focused Rampage did not activate");clock_now+=180;
 for(int focus:{120,0,500,1000,-60}) {
  c.reduction=focus;c.actions.clear();c.SendAlternateAdvancementTimers();
  check(active_wire_timers(c,{258})==std::map<int,int64>{{258,300}},
   "resend changes stored300s remaining under current focus "+std::to_string(focus));
 }
 // Native readiness cannot express a retained wait once its current effective
 // reuse is exactly zero. It returns before inspecting the projected clock.
 c.reduction=600;c.actions.clear();c.SendAlternateAdvancementTimers();
 check(active_wire_timers(c,{258}).empty(),"native zero-focus readiness oracle disagrees");
 const auto before=c.casts.size();c.ActivateAlternateAdvancementAbility(258,1);
 check(c.casts.size()==before,"native zero focus bypassed retained server cooldown");
 clock_now+=300;c.actions.clear();c.SendAlternateAdvancementTimers();
 check(active_wire_timers(c,{258}).empty(),"expired AA recreated an active client countdown");
}
void completion_pulses() {
 for(const auto& row:zone->aa_ranks_values) {
  Client c;own(c,row.first);const int slot=wire_group(c,row.first);
  c.ActivateAlternateAdvancementAbility(row.first,1);
  check(c.actions.size()==1 && c.actions.back().ability==slot &&
   c.actions.back().begin==0 && c.actions.back().end==0,
   "successful rank "+std::to_string(row.first)+" did not start its catalog slot");
  c.actions.clear();c.PublishAACompletion(0);
  check(c.actions.size()==1 && c.actions.back().ability==slot,
   "native completion fallback lost casting AA family");
 }
 Client c;own(c,258);c.PublishAACompletion(-1);
 check(c.actions.empty(),"invalid completion rank emitted unrelated cooldown pulse");
}
int main(int argc,char** argv) {
 try {
  check(argc==2,"scenario required");content();std::string s=argv[1];
  if(s=="rampage-purify")pair_case(258,233);
  else if(s=="purify-rampage")pair_case(233,258);
  else if(s=="all-pairs")all_pairs(false);
  else if(s=="all-catalog")all_pairs(true);
  else if(s=="same-family")same_family();
  else if(s=="guards")guards();
  else if(s=="reset-one")reset_one(false);
  else if(s=="reset-argument")reset_one(true);
  else if(s=="reset-all")reset_all();
  else if(s=="relog")relog(false);
  else if(s=="resend")relog(true);
  else if(s=="death-reset")death_reset();
  else if(s=="purchase-stability")purchase_stability();
  else if(s=="class-remap")class_remap();
  else if(s=="focused-resend")focused_resend();
  else if(s=="completion-pulses")completion_pulses();
  else throw std::runtime_error("unknown scenario");
  std::cout<<s<<": PASS\n";return 0;
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
'''


def native_content():
    config = json.loads((ROOT / "config/aa-policy.json").read_text())
    with gzip.open(ROOT / config["catalog"], "rt", encoding="utf-8") as stream:
        data = json.load(stream)
    snapshot = os.environ.get("NIGHTCAP_AA_COOLDOWN_CATALOG")
    if snapshot:
        current = json.loads(Path(snapshot).read_text(encoding="utf-8-sig"))
        for table, capture in (("aa_ability", "abilities"), ("aa_ranks", "ranks")):
            overrides = {int(row["id"]): row for row in current[capture]}
            for row in data[table]:
                for key, value in overrides.get(row["id"], {}).items():
                    if key in row and isinstance(row[key], int):
                        row[key] = int(value)
        print("Catalog overlay:", current.get("captured_at", snapshot))
    policy = compile_policy(data, config)
    ranks = {row["id"]: row for row in data["aa_ranks"]}
    effects = {row["rank_id"] for row in data["aa_rank_effects"]}
    active = [row for row in policy if row["rank_id"] not in effects
              and 0 < ranks[row["rank_id"]]["spell"] < 65536
              and ranks[row["rank_id"]]["recast_time"] > 0]
    representatives = {}
    lines = ["void content() {"]
    for row in active:
        rank = ranks[row["rank_id"]]
        values = [row["ability_id"], row["rank_id"], row["ordinal"], rank["spell"],
                  rank["spell_type"], rank["recast_time"], row["expansion"], row["classes"]]
        lines.append(" add_rank(" + ",".join(map(str, values)) + ");")
        representatives.setdefault(row["ability_id"], row["rank_id"])
    lines.append(" family_representatives={" + ",".join(map(str, representatives.values())) + "};")
    lines.append("}\n")
    return "\n".join(lines)


class AACooldownIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        timers = (SOURCE / "common/ptimer.h").read_text(encoding="utf-8")
        declarations = function(timers, "enum : int") + ";\n"
        declarations += re.search(r"typedef\s+\w+\s+pTimerType\s*;", timers).group(0)
        aa = (SOURCE / "zone/aa.cpp").read_text(encoding="utf-8")
        methods = "\n".join(function(aa, signature) for signature in (
            "int Client::GetAlternateAdvancementTimerSlot(",
            "void Client::ActivateAlternateAdvancementAbility(",
            "void Client::SendAlternateAdvancementRank(",
            "void Client::SendAlternateAdvancementTimer(",
            "void Client::SendAlternateAdvancementTimers(",
            "void Client::ResetAlternateAdvancementTimer(",
            "void Client::ResetAlternateAdvancementTimers(",
            "void Client::ResetOnDeathAlternateAdvancement("))
        spells = (SOURCE / "zone/spells.cpp").read_text(encoding="utf-8")
        completion = spells[spells.index("Set Recast Timer on spells."):]
        completion = function(completion, "if (slot == CastingSlot::AltAbility)")
        methods += "\nvoid Client::PublishAACompletion(int aa_id) {\n"
        methods += "using CastingSlot=EQ::spells::CastingSlot;auto slot=CastingSlot::AltAbility;\n"
        methods += completion + "\n}\n"
        cls.temp = tempfile.TemporaryDirectory(prefix="aa-cooldown-identity-")
        cls.addClassCleanup(cls.temp.cleanup)
        path = Path(cls.temp.name)
        fixture = FIXTURE.replace("/* TIMER_DECLARATIONS */", declarations)
        (path / "test.cpp").write_text(fixture + methods + native_content() + SCENARIOS, encoding="utf-8")
        cls.binary = path / "test.exe"
        if os.name == "nt":
            (path / "build.cmd").write_text(
                '@echo off\ncall "C:\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat" >nul\n'
                f'cl /nologo /EHsc /W4 /std:c++17 /I"{SOURCE}" test.cpp /Fe:test.exe\n')
            command = ["cmd", "/d", "/c", str(path / "build.cmd")]
        else:
            command = ["g++", "-std=c++17", "-Wall", "-Wextra", "-I", str(SOURCE),
                       "test.cpp", "-o", "test.exe"]
        result = subprocess.run(command, cwd=path, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def scenario(self, name):
        result = subprocess.run([self.binary, name], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout.strip())

    def test_rampage_does_not_lock_purify_body(self): self.scenario("rampage-purify")
    def test_purify_body_does_not_lock_rampage(self): self.scenario("purify-rampage")
    def test_all_eligible_family_pairs_activate_independently(self): self.scenario("all-pairs")
    def test_all_eligible_family_pairs_publish_distinct_timer_identity(self): self.scenario("all-catalog")
    def test_all_same_family_ranks_share_cooldown_and_exact_expiry(self): self.scenario("same-family")
    def test_unearned_ineligible_or_failed_cast_starts_no_cooldown(self): self.scenario("guards")
    def test_reset_one_family_preserves_other_family(self): self.scenario("reset-one")
    def test_reset_uses_requested_rank_even_if_casting_member_is_stale(self): self.scenario("reset-argument")
    def test_reset_all_aa_restores_families_and_preserves_skill(self): self.scenario("reset-all")
    def test_relog_preserves_both_individual_deadlines(self): self.scenario("relog")
    def test_relog_timer_packets_match_catalog_family_identity(self): self.scenario("resend")
    def test_death_reset_is_scoped_to_flagged_family(self): self.scenario("death-reset")
    def test_wire_slots_do_not_move_on_purchase_or_refund(self): self.scenario("purchase-stability")
    def test_class_slot_remap_preserves_family_deadlines(self): self.scenario("class-remap")
    def test_resend_focus_changes_preserve_stored_remaining_time(self): self.scenario("focused-resend")
    def test_native_successful_completion_pulses_target_catalog_slots(self): self.scenario("completion-pulses")


if __name__ == "__main__":
    unittest.main(verbosity=2)

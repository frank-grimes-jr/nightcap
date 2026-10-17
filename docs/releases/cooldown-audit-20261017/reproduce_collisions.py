"""Native cooldown collision regressions with deterministic engine boundaries.

Compiles the production AA activation and item timer methods unchanged, along
with the actual persistent timer enum and key type. Database, spell completion,
ownership, inventory and time are controlled boundaries. The named content rows
were read SELECT-only from the production catalog on 2026-10-17; no player data
is used. This does not certify the complete zone or the client packet consumer.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools/tests"))
from test_gameplay_policies import ROOT, function


SOURCE = ROOT / "server-mods/code"

FIXTURE = r'''
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
using uint8=uint8_t; using uint16=uint16_t; using uint32=uint32_t;
using int32=int32_t; using int64=int64_t;
/* NATIVE_TIMER_DECLARATIONS */
namespace EQ {
namespace invaug {enum {SOCKET_BEGIN=0,SOCKET_END=5};}
namespace spells {enum class CastingSlot {AltAbility};}
}
namespace Chat {enum {Red,SpellFailure};}
namespace Class {enum {Cleric=2,Paladin=3,ShadowKnight=5,Bard=8};}
enum {RECAST_TYPE_UNLINKED_ITEM=-1,focusReduceRecastTime=1,
 SNEAK_RESTRICT,ST_Pet,ST_SummonedPet,eaSitting,eaStanding,STAND_TO_CAST};
struct ItemData {
 uint32 ID=0; int RecastType=-1; uint32 RecastDelay=0;
 struct {int Effect=0;} Click;
};
struct Item {
 ItemData data; std::map<int,Item*> augments;
 const ItemData* GetItem() const {return &data;}
 const Item* GetAugment(int slot) const {
  const auto it=augments.find(slot);return it==augments.end()?nullptr:it->second;
 }
};
struct Inventory {
 std::map<uint32,Item> slots;
 Item* GetItem(uint32 slot) {
  const auto it=slots.find(slot);return it==slots.end()?nullptr:&it->second;
 }
};
struct Database {
 std::map<uint32,ItemData> items;std::map<int,uint32> recasts;
 void UpdateItemRecast(uint32,int key,uint32 until) {recasts[key]=until;}
 void DeleteItemRecast(uint32,int key) {recasts.erase(key);}
 const ItemData* GetItem(uint32 id) const {
  auto it=items.find(id);return it==items.end()?nullptr:&it->second;
 }
} database;
struct PersistentTimer {
 uint32 deadline=0;
 uint32 GetReadyTimestamp() const {return deadline;}
};
struct PTimerList {
 uint32 now=100000;std::map<pTimerType,PersistentTimer> timers;
 bool Expired(Database*,pTimerType key,bool) const {
  const auto it=timers.find(key);return it==timers.end() || it->second.deadline<=now;
 }
 uint32 GetRemainingTime(pTimerType key) const {
  const auto it=timers.find(key);
  return it==timers.end() || it->second.deadline<=now?0:it->second.deadline-now;
 }
 void Start(pTimerType key,uint32 duration) {timers[key].deadline=now+duration;}
 PersistentTimer* Get(pTimerType key) {return &timers.at(key);}
 void Clear(Database*,pTimerType key) {timers.erase(key);}
};
namespace AA {
struct Ability {int id=0,charges=0;uint32 classes=0;};
struct Rank {
 int id=0,spell=0,spell_type=0,recast_time=0,current_value=1;
 Ability* base_ability=nullptr;std::vector<int> effects;
};
}
struct Zone {
 std::map<int,AA::Ability> abilities;std::map<int,AA::Rank> ranks;
 AA::Rank* GetAlternateAdvancementRank(int id) {
  auto it=ranks.find(id);return it==ranks.end()?nullptr:&it->second;
 }
} zone_value;
auto* zone=&zone_value;
struct Spell {int sneak=0,target_type=0,cast_time=1,mana=0,resist_difficulty=0;} spells[65536];
bool IsValidSpell(int id) {return id>0 && id<65536;}
bool IsCastWhileInvisibleSpell(int) {return false;}
bool IsCastNotStandingSpell(int) {return false;}
bool UseTogglePassiveHotkey(const AA::Rank&) {return false;}
struct Timer {static uint32 GetCurrentTime() {return 100000;}};
struct Mob {};
struct Entities {Mob* GetMob(int) {return nullptr;}} entity_list;
struct Client {
 Inventory inventory;PTimerList p_timers;uint32 held=(1u<<1)|(1u<<2)|(1u<<4);
 std::map<int,uint32> earned;std::vector<int> casts;bool valid=true,cast_ok=true;
 bool hidden=false,casting=false;uint32 tmHidden=0;int appearance=eaStanding;
 int primary=Class::Cleric,reduction=0,rejected=0,casting_spell_aa_id=0;
 Client* CastToClient() {return this;} Inventory& GetInv() {return inventory;}
 PTimerList& GetPTimers() {return p_timers;} uint32 CharacterID() const {return 1;}
 int GetFocusEffect(int,int) const {return 0;}
 void SendItemRecastTimer(int32,uint32,bool=false) {}
 bool HasValidEarnedAAState() const {return valid;}
 bool CanUseAlternateAdvancementRank(AA::Rank* rank) const {
  return rank && rank->base_ability && (rank->base_ability->classes&held)!=0;
 }
 uint32 GetAA(int id,uint32* charges) const {
  *charges=1;const auto it=earned.find(id);return it==earned.end()?0:it->second;
 }
 int GetAlternateAdvancementCooldownReduction(AA::Rank*) const {return reduction;}
 template<class... T> void Message(T...) {++rejected;}
 template<class... T> void MessageString(T...) {++rejected;}
 void CommonBreakInvisible() {} int GetPetID() const {return 5;}
 int GetAppearance() const {return appearance;}
 void SetAppearance(int value,bool) {appearance=value;}
 int GetClass() const {return primary;} bool IsCasting() const {return casting;}
 bool DoCastingChecksOnCaster(int,EQ::spells::CastingSlot) const {return cast_ok;}
 void TogglePassiveAlternativeAdvancement(AA::Rank&,int) {}
 bool CompleteCast(int rank_id,pTimerType timer,int duration) {
  if(!cast_ok)return false;
  casts.push_back(rank_id);p_timers.Start(timer,duration);return true;
 }
 bool CastSpell(int,int,EQ::spells::CastingSlot,int,int,int,int,pTimerType timer,
  int duration,void*,int rank_id) {return CompleteCast(rank_id,timer,duration);}
 bool SpellFinished(int,Mob*,EQ::spells::CastingSlot,int,int,int,bool,int,pTimerType timer,
  int duration,bool,int rank_id) {return CompleteCast(rank_id,timer,duration);}
 void ActivateAlternateAdvancementAbility(int,int);
 void SetItemRecastTimer(int32,uint32);
 bool HasItemRecastTimer(int32,uint32);
 void DeleteItemRecastTimer(uint32);
};
void check(bool ok,const std::string& why) {if(!ok)throw std::runtime_error(why);}
void content() {
 zone_value=Zone{};database=Database{};
 // Exact first-rank catalog identities, class masks, shared groups and reuse.
 for(const AA::Ability a: {AA::Ability{36,0,2},AA::Ability{73,0,4},
  AA::Ability{6000,0,16},AA::Ability{6001,0,4}})zone->abilities[a.id]=a;
 for(const AA::Rank r: {
  AA::Rank{129,2738,2,64800,1,&zone->abilities[36],{}},
  AA::Rank{188,2190,2,30,1,&zone->abilities[73],{}},
  AA::Rank{1277,5924,2,30,2,&zone->abilities[73],{}},
  AA::Rank{7800,13531,39,4320,1,&zone->abilities[6000],{}},
  AA::Rank{7850,13546,39,4320,1,&zone->abilities[6001],{}}})zone->ranks[r.id]=r;
}
void earn(Client& c) {for(const auto& row:zone->ranks)c.earned[row.first]=row.second.current_value;}
void item(Client& c,uint32 slot,uint32 id,uint32 delay,int group,int spell) {
 Item value;value.data.ID=id;value.data.RecastDelay=delay;
 value.data.RecastType=group;value.data.Click.Effect=spell;
 c.inventory.slots[slot]=value;database.items[id]=value.data;
}
'''

CONTROLS = r'''
void aa_pair(int first,int second) {
 Client c;earn(c);c.ActivateAlternateAdvancementAbility(first,1);
 check(c.casts.size()==1,"first earned AA did not activate");
 c.ActivateAlternateAdvancementAbility(second,1);
 check(c.casts.size()==2 && c.casts.back()==second,
  "AA rank "+std::to_string(first)+" incorrectly locks rank "+std::to_string(second)+
  " for "+std::to_string(zone->ranks[first].recast_time)+" seconds");
}
void aa_same() {
 Client c;earn(c);c.ActivateAlternateAdvancementAbility(188,1);
 c.ActivateAlternateAdvancementAbility(188,1);check(c.casts.size()==1,"same AA bypassed reuse");
 c.p_timers.now+=29;c.ActivateAlternateAdvancementAbility(188,1);
 check(c.casts.size()==1,"same AA expired early");
 ++c.p_timers.now;c.ActivateAlternateAdvancementAbility(188,1);
 check(c.casts.size()==2,"same AA not ready exactly at deadline");
}
void aa_rank_family() {
 Client c;earn(c);c.ActivateAlternateAdvancementAbility(188,1);
 c.ActivateAlternateAdvancementAbility(1277,1);
 check(c.casts.size()==1,"higher rank bypassed same AA family reuse");
}
void aa_guards() {
 for(int guard=0;guard<6;++guard) {
  Client c;earn(c);
  if(guard==0)c.valid=false;
  if(guard==1)c.earned.clear();
  if(guard==2)c.held=2;
  if(guard==3)c.cast_ok=false;
  if(guard==4)zone->ranks[188].effects.push_back(1);
  if(guard==5)c.appearance=99;
  c.ActivateAlternateAdvancementAbility(188,1);
  check(c.casts.empty() && c.p_timers.timers.empty(),"rejected AA consumed reuse");
  zone->ranks[188].effects.clear();
 }
}
void item_pair() {
 Client c;
 // Real production rows differ by 65536, which used to truncate to key3551.
 item(c,1,61985,10,-1,19797);item(c,2,127521,5,-1,37951);
 c.SetItemRecastTimer(19797,1);
 check(c.HasItemRecastTimer(19797,1),"clicked item lost own reuse");
 check(!c.HasItemRecastTimer(37951,2),"Rallos Zek Puppet blocks unrelated Plasmatic Priest Robe");
 c.SetItemRecastTimer(37951,2);c.p_timers.now+=5;
 check(!c.HasItemRecastTimer(37951,2),"second item not ready at own deadline");
 check(c.HasItemRecastTimer(19797,1),"short item overwrote long item's deadline");
}
void item_spell() {
 Client c;
 // Mark of Emperor Zhisza32278: -32278 wraps to33258,
 // also the old persistent timer for spell28258 (Unified Hand... Rk.II).
 item(c,1,32278,9,-1,11566);
 c.p_timers.Start(pTimerSpellStart+28258,3600);
 check(!c.HasItemRecastTimer(11566,1),"unrelated spell blocks unlinked item for3600s");
 c.SetItemRecastTimer(11566,1);
 check(c.p_timers.GetRemainingTime(pTimerSpellStart+28258)==3600,
  "unlinked item overwrites unrelated spell deadline");
}
void item_delete() {
 Client c;item(c,1,32278,9,-1,11566);
 c.p_timers.Start(pTimerSpellStart+28258,3600);
 c.DeleteItemRecastTimer(32278);
 check(c.p_timers.GetRemainingTime(pTimerSpellStart+28258)==3600,
  "deleting item reuse clears unrelated spell timer");
}
void item_linked() {
 Client c;item(c,1,4544,55,2,487);item(c,2,999999,55,2,487);
 c.SetItemRecastTimer(487,1);
 check(c.HasItemRecastTimer(487,2),"deliberately linked item group stopped sharing reuse");
 c.p_timers.now+=54;check(c.HasItemRecastTimer(487,2),"linked group expired early");
 ++c.p_timers.now;check(!c.HasItemRecastTimer(487,2),"linked group expiry changed");
}
void item_augment() {
 Client c;item(c,1,500000,0,-1,0);item(c,2,32278,9,-1,11566);
 c.inventory.slots[1].augments[0]=&c.inventory.slots[2];
 c.SetItemRecastTimer(11566,1);
 check(c.HasItemRecastTimer(11566,1),"augment failed to enforce its reuse");
 check(c.HasItemRecastTimer(11566,2),"same augment identity bypasses reuse outside host");
 c.p_timers.now+=9;check(!c.HasItemRecastTimer(11566,1),"augment expiry changed");
}
int main(int argc,char** argv) {
 try {
  check(argc==2,"scenario required");content();std::string scenario=argv[1];
  if(scenario=="rez-stun")aa_pair(129,188);
  else if(scenario=="harm-hands")aa_pair(7800,7850);
  else if(scenario=="hands-harm")aa_pair(7850,7800);
  else if(scenario=="aa-same")aa_same();
  else if(scenario=="aa-family")aa_rank_family();
  else if(scenario=="aa-guards")aa_guards();
  else if(scenario=="item-pair")item_pair();
  else if(scenario=="item-spell")item_spell();
  else if(scenario=="item-delete")item_delete();
  else if(scenario=="item-linked")item_linked();
  else if(scenario=="item-augment")item_augment();
  else throw std::runtime_error("unknown scenario");
  std::cout<<scenario<<": PASS\n";return 0;
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
'''


class CooldownCollisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        timers = (SOURCE / "common/ptimer.h").read_text(encoding="utf-8")
        declarations = function(timers, "enum : int") + ";\n"
        declarations += re.search(r"typedef\s+\w+\s+pTimerType\s*;", timers).group(0)
        aa = (SOURCE / "zone/aa.cpp").read_text(encoding="utf-8")
        spells = (SOURCE / "zone/spells.cpp").read_text(encoding="utf-8")
        methods = function(aa, "void Client::ActivateAlternateAdvancementAbility(")
        for signature in ("void Client::SetItemRecastTimer(",
                          "bool Client::HasItemRecastTimer(",
                          "void Client::DeleteItemRecastTimer("):
            methods += function(spells, signature)
        cls.temp = tempfile.TemporaryDirectory(prefix="cooldown-collisions-")
        cls.addClassCleanup(cls.temp.cleanup)
        path = Path(cls.temp.name)
        source = FIXTURE.replace("/* NATIVE_TIMER_DECLARATIONS */", declarations)
        (path / "test.cpp").write_text(source + methods + CONTROLS, encoding="utf-8")
        cls.binary = path / "test.exe"
        if os.name == "nt":
            (path / "build.cmd").write_text(
                '@echo off\ncall "C:\\BuildTools\\VC\\Auxiliary\\Build\\vcvars64.bat" >nul\n'
                f'cl /nologo /EHsc /W4 /std:c++17 /I"{SOURCE}" test.cpp /Fe:test.exe\n'
            )
            command = ["cmd", "/d", "/c", str(path / "build.cmd")]
        else:
            command = ["g++", "-std=c++17", "-Wall", "-Wextra", "-I", str(SOURCE),
                       "test.cpp", "-o", "test.exe"]
        result = subprocess.run(command, cwd=path, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def run_scenario(self, scenario):
        result = subprocess.run([self.binary, scenario], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout.strip())

    def test_divine_resurrection_does_not_lock_divine_stun_for_18_hours(self):
        self.run_scenario("rez-stun")

    def test_harm_touch_does_not_lock_lay_on_hands(self):
        self.run_scenario("harm-hands")

    def test_lay_on_hands_does_not_lock_harm_touch(self):
        self.run_scenario("hands-harm")

    def test_same_aa_still_obeys_its_native_deadline(self):
        self.run_scenario("aa-same")

    def test_ranks_of_one_aa_family_share_the_family_deadline(self):
        self.run_scenario("aa-family")

    def test_rejected_or_unearned_aa_does_not_consume_cooldown(self):
        self.run_scenario("aa-guards")

    def test_unlinked_item_ids_separated_by_65536_stay_independent(self):
        self.run_scenario("item-pair")

    def test_unlinked_item_does_not_read_or_overwrite_spell_timer(self):
        self.run_scenario("item-spell")

    def test_deleting_item_reuse_does_not_clear_spell_cooldown(self):
        self.run_scenario("item-delete")

    def test_deliberate_linked_item_group_preserves_shared_deadline(self):
        self.run_scenario("item-linked")

    def test_augment_uses_its_own_item_identity_and_expiry(self):
        self.run_scenario("item-augment")


if __name__ == "__main__":
    unittest.main(verbosity=2)

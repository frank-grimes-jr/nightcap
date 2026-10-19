"""Compile actual native eligibility/projection methods with narrow engine doubles.

Run in Linux: python3 verify_aa_tbs_native.py SOURCE_ROOT OUTPUT_DIR.
No database or game process is touched. This is not an in-game/client test.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def method(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


STUBS = r'''
#include <algorithm>
#include <cassert>
#include <cstring>
#include <cstdint>
#include <iostream>
#include <map>
#include <unordered_map>
#include <vector>
#include <string>
#include "common/nightcap_aa_policy.h"
using uint32 = uint32_t;
using uint64 = uint64_t;
#define LogError(...) ((void)0)
constexpr int MAX_PP_AA_ARRAY = 240;
namespace AACategory { constexpr int ShroudPassive=3, ShroudActive=4; }
namespace EQ { namespace versions { constexpr int maskTitaniumAndEarlier=1; enum class ClientVersion { RoF2, UF }; }
namespace expansions { uint32 ConvertClientVersionToExpansionsMask(versions::ClientVersion v) { return v==versions::ClientVersion::RoF2 ? 0x7ffff : 0x7fff; } } }
namespace RaceIndex { constexpr int Drakkin=16; }
namespace Race { constexpr int Human=1, Drakkin=522; }
bool client_expansion_settings=true, current_era_aa_only=false;
#define RuleI(group,key) (std::string(#key)=="ExpansionSettings" ? 2097151 : 4)
#define RuleB(group,key) (std::string(#key)=="UseClientBasedExpansionSettings" ? client_expansion_settings : std::string(#key)=="UseCurrentExpansionAAOnly" ? current_era_aa_only : false)
int GetPlayerRaceValue(int) { return 1; }
class Mob; class Client;
namespace AA {
struct Ability;
struct Rank {
 int id=0, current_value=0, expansion=0, level_req=1;
 Ability* base_ability=nullptr; Rank* next=nullptr;
 Rank* prev=nullptr; int cost=1, total_cost=100;
 std::map<int,int> prereqs;
};
struct Ability {
 int id=0, first_rank_id=0, classes=0, category=0, charges=0;
 int races=65535, deities=131071, status=0, drakkin_heritage=127;
 bool grant_only=false;
 Rank* first=nullptr;
 int GetMaxLevel(Mob*);
 Rank* GetRankByPointsSpent(int);
};
}
struct Profile {
 int expansions=2097151;
 uint32 aapoints=17,aapoints_spent=105;
 struct Entry { uint32 AA=0,value=0,charges=0; } aa_array[MAX_PP_AA_ARRAY];
};
struct Bot { int GetExpansionBitmask() { return 2097151; } } bot;
class Mob {
public:
 int level=1, class_id=1, mask=2;
 bool client=true;
 using UsableAAState=std::unordered_map<uint32,std::pair<uint32,uint32>>;
 UsableAAState aa_ranks;
 bool IsClient() { return client; }
 bool IsBot() { return false; }
 int GetLevel() { return level; }
 int GetClass() { return class_id; }
 int GetBaseRace() { return 1; }
 int GetDeityBit() { return 1; }
 int GetDrakkinHeritage() { return 0; }
 Bot* CastToBot() { return &bot; }
 Client* CastToClient();
 bool CanUseAlternateAdvancementRank(AA::Rank*);
 bool CanPurchaseAlternateAdvancementRank(AA::Rank*, bool, bool);
 uint32 GetAA(int, uint32* = nullptr);
};
class Client : public Mob {
public:
 Profile m_pp;
 std::map<uint32,std::pair<uint32,uint32>> m_earned_aa_ranks;
 bool valid=true;
 bool& m_earned_aa_valid=valid;
 struct { uint32 expended_aa=5; } m_epp;
 int character_id=1;
 int CharacterID() { return character_id; }
 int GetClassMask() { return mask; }
 int ClientVersionBit() { return 2; }
 EQ::versions::ClientVersion client_version=EQ::versions::ClientVersion::RoF2;
 EQ::versions::ClientVersion ClientVersion() const { return client_version; }
 int Admin() { return 0; }
 Profile& GetPP() { return m_pp; }
 bool HasValidEarnedAAState() { return valid; }
 void InvalidateEarnedAAState() { valid=false; }
 bool ReprojectEarnedAAs();
 std::vector<int> refresh;
 void SendAlternateAdvancementTable();
 void LoadMulticlassMask() { refresh.push_back(1); }
 void CalcBonuses() { refresh.push_back(2); }
 void SendClearPlayerAA() { refresh.push_back(3); }
 void SendLoadedAlternateAdvancementTable() { refresh.push_back(4); }
 void SendAlternateAdvancementPoints() { refresh.push_back(5); }
 void SendAlternateAdvancementStats() { refresh.push_back(6); }
 bool SaveAA();
 uint32 GetEarnedAACount(uint32) const;
 bool HasAlreadyPurchasedRank(AA::Rank*);
 int GetAAPoints() { return m_pp.aapoints; }
};
Client* Mob::CastToClient() { return static_cast<Client*>(this); }
struct Zone {
 std::map<int,AA::Ability> abilities;
 AA::Ability* GetAlternateAdvancementAbility(int id) { return abilities.count(id)?&abilities.at(id):nullptr; }
 AA::Ability* GetAlternateAdvancementAbilityByRank(int id) {
  for(auto& p:abilities) for(auto* r=p.second.first;r;r=r->next) if(r->id==id) return &p.second;
  return nullptr;
 }
 std::pair<AA::Ability*,AA::Rank*> GetAlternateAdvancementAbilityAndRank(int id, int count) {
  auto* a=GetAlternateAdvancementAbility(id); return {a,a?a->GetRankByPointsSpent(count):nullptr};
 }
} instance;
Zone* zone=&instance;
uint32 Mob::GetAA(int rank_id, uint32* charges) {
 auto* a=zone->GetAlternateAdvancementAbilityByRank(rank_id);
 auto it=a?aa_ranks.find(a->id):aa_ranks.end();
 if(it==aa_ranks.end())return 0;
 if(charges)*charges=it->second.second;
 return it->second.first;
}
int database=0;
struct CharacterAlternateAbilitiesRepository {
 struct CharacterAlternateAbilities { int id=0; uint32 aa_id=0,aa_value=0,charges=0; };
 static CharacterAlternateAbilities NewEntity() { return {}; }
 static std::vector<CharacterAlternateAbilities> saved;
 static bool ReplaceMany(int, const std::vector<CharacterAlternateAbilities>& rows) { saved=rows; return true; }
};
std::vector<CharacterAlternateAbilitiesRepository::CharacterAlternateAbilities> CharacterAlternateAbilitiesRepository::saved;
'''

TESTS = r'''
int main() {
 Client c;
 AA::Ability a;
 a.id=28; a.classes=0x1fffe;
 int checked=0;
 for(const auto& p:NightcapAA::Ranks) {
  a.id=p.ability_id;
  AA::Rank rank{p.rank_id,p.ordinal,p.expansion,255,&a,nullptr};
  for(int level: {1,10,20,30,40,50}) {
   c.level=level;
   assert(p.level==1);
   assert(c.CanUseAlternateAdvancementRank(&rank));
   ++checked;
  }
  c.level=50; a.classes=4;
  assert(!c.CanUseAlternateAdvancementRank(&rank));
  c.mask=6; assert(c.CanUseAlternateAdvancementRank(&rank));
  c.mask=2; a.classes=0x1fffe;
  ++rank.current_value; assert(!c.CanUseAlternateAdvancementRank(&rank));
 }
 a.id=515; AA::Rank forbidden{1,1,17,1,&a,nullptr};
 assert(!c.CanUseAlternateAdvancementRank(&forbidden));
 // Actual RoF2 mask, not the old fixture's all21-expansion entitlement.
 a.id=1205; AA::Rank companion{16475,4,21,1,&a,nullptr};
 c.m_pp.expansions=0x7ffff;assert(c.CanUseAlternateAdvancementRank(&companion));
 c.m_pp.expansions=0x3ffff;assert(!c.CanUseAlternateAdvancementRank(&companion));
 c.m_pp.expansions=0;assert(!c.CanUseAlternateAdvancementRank(&companion));
 c.m_pp.expansions=0x7ffff;client_expansion_settings=false;assert(!c.CanUseAlternateAdvancementRank(&companion));
 c.m_pp.expansions=2097151;assert(c.CanUseAlternateAdvancementRank(&companion));
 client_expansion_settings=true;c.m_pp.expansions=0x7ffff;current_era_aa_only=true;
 assert(!c.CanUseAlternateAdvancementRank(&companion));current_era_aa_only=false;
 companion.id=16476;companion.current_value=5;assert(!c.CanUseAlternateAdvancementRank(&companion));
 companion.id=16475;companion.current_value=4;c.client_version=EQ::versions::ClientVersion::UF;
 assert(!c.CanUseAlternateAdvancementRank(&companion));c.client_version=EQ::versions::ClientVersion::RoF2;
 c.m_pp.expansions=2097151;
 // Real policy ranks for Natural Durability: all at creation, higher release-excluded ranks dormant.
 std::map<int,AA::Rank> ranks;
 auto& durability=zone->abilities[28]; durability.id=28; durability.classes=0x1fffe;
 AA::Rank* tail=nullptr;
 for(const auto& p:NightcapAA::Ranks) if(p.ability_id==28) {
  auto& r=ranks[p.ordinal]; r={p.rank_id,p.ordinal,p.expansion,1,&durability,nullptr};
 }
 for(auto& p:ranks) { if(tail)tail->next=&p.second; else durability.first=&p.second; tail=&p.second; }
 AA::Rank deep{999999,4,14,1,&durability,nullptr}; tail->next=&deep;
 durability.first_rank_id=durability.first->id;
 auto first=durability.first_rank_id;
 c.m_earned_aa_ranks[first]={4,7};
 for(auto pair: {std::pair<int,int>{1,3},{20,3},{30,3},{10,3},{50,3}}) {
  c.level=pair.first;
  assert(c.ReprojectEarnedAAs());
  assert(c.aa_ranks.at(28).first==unsigned(pair.second));
  assert(c.m_earned_aa_ranks.at(first)==std::make_pair(4u,7u));
  assert(c.m_pp.aa_array[0].value==unsigned(pair.second));
  assert(c.SaveAA());
  assert(CharacterAlternateAbilitiesRepository::saved.at(0).aa_value==4);
  assert(CharacterAlternateAbilitiesRepository::saved.at(0).charges==7);
  assert(c.m_pp.aapoints_spent==105 && c.GetAAPoints()==17);
  assert(c.HasAlreadyPurchasedRank(durability.first));
  assert(!c.CanPurchaseAlternateAdvancementRank(durability.first,true,true));
 }
 // Retain consumed charges when suspending for a class restriction.
 c.aa_ranks.at(28).second=2; c.mask=0;
 assert(c.ReprojectEarnedAAs()); assert(c.aa_ranks.empty());
 assert(c.m_pp.aa_array[0].AA==0);
 assert(c.m_earned_aa_ranks.at(first)==std::make_pair(4u,2u));
 assert(c.SaveAA()); assert(CharacterAlternateAbilitiesRepository::saved.at(0).aa_value==4);
 assert(CharacterAlternateAbilitiesRepository::saved.at(0).charges==2);
 c.mask=2; assert(c.ReprojectEarnedAAs()); assert(c.aa_ranks.at(28).second==2);
 c.valid=false; auto before=c.aa_ranks;
 assert(!c.ReprojectEarnedAAs()); assert(c.aa_ranks==before);
 c.valid=true; c.m_earned_aa_ranks[first].first=5;
 assert(!c.ReprojectEarnedAAs()); assert(!c.valid); assert(c.aa_ranks==before);
 c.valid=true; c.m_earned_aa_ranks.clear(); c.aa_ranks.clear(); c.level=1;
 durability.first->level_req=255;
 durability.first->prereqs[99999]=1;
 assert(!c.CanPurchaseAlternateAdvancementRank(durability.first,false,true));
 durability.first->prereqs.clear();
 assert(c.CanPurchaseAlternateAdvancementRank(durability.first,true,true));
 c.m_pp.aapoints=0; assert(!c.CanPurchaseAlternateAdvancementRank(durability.first,true,true));
 auto* second=durability.first->next;
 second->prev=durability.first; second->level_req=255;
 assert(!c.CanPurchaseAlternateAdvancementRank(second,false,true));
 c.aa_ranks[28]={1,0}; c.m_pp.aapoints=17;
 assert(c.CanPurchaseAlternateAdvancementRank(second,true,true));
 assert(c.CanPurchaseAlternateAdvancementRank(second,false,false));
 c.client=false; assert(!c.CanPurchaseAlternateAdvancementRank(second,false,false)); c.client=true;
 c.aa_ranks.clear();
 c.SendAlternateAdvancementTable();
 // Current native refresh intentionally preserves the client's loaded AA table.
 // The removed ClearAA packet belongs to the older October 13 baseline.
 assert(c.refresh==std::vector<int>({1,2,4,5,6}));
 // Previously earned Slay 10 survives while the expanded legal prefix restores 9.
 // Use the actual generated identities and costs; the excluded next rank is retained.
 std::map<std::pair<int,int>,AA::Rank> expanded;
 for(int aid : {30,75}) {
  auto& ability=zone->abilities[aid];ability.id=aid;ability.classes=0x1fffe;
  for(const auto& p:NightcapAA::Ranks) if(p.ability_id==aid) {
   auto& r=expanded[{aid,p.ordinal}];r={p.rank_id,p.ordinal,p.expansion,255,&ability,nullptr};
   if(aid==75) { r.cost=p.ordinal==1?3:p.ordinal==2?6:p.ordinal==3?9:7;r.prereqs[30]=3; }
   else r.cost=p.ordinal*2;
  }
  AA::Rank* previous=nullptr;int total=0;
  for(auto& p:expanded) if(p.first.first==aid) {
   auto& r=p.second;r.prev=previous;total+=r.cost;r.total_cost=total;
   if(previous)previous->next=&r;else ability.first=&r;
   previous=&r;
  }
  ability.first_rank_id=ability.first->id;
 }
 auto& slay=zone->abilities.at(75);
 AA::Rank slay_later{15141,10,19,255,&slay,nullptr};slay_later.cost=9;slay_later.total_cost=69;
 expanded.at({75,9}).next=&slay_later;slay_later.prev=&expanded.at({75,9});
 c.m_earned_aa_ranks.clear();c.aa_ranks.clear();c.mask=8;
 c.m_earned_aa_ranks[slay.first_rank_id]={10,0};
 c.m_earned_aa_ranks[zone->abilities.at(30).first_rank_id]={3,0};
 c.m_pp.aapoints_spent=86; // Slay10=69, Combat Fury3=12, prior expended=5.
 for(int level : {1,50,1}) {
  c.level=level;assert(c.ReprojectEarnedAAs());assert(c.aa_ranks.at(75).first==9);
  assert(c.m_earned_aa_ranks.at(slay.first_rank_id).first==10);
  assert(c.SaveAA());
  auto saved=std::find_if(CharacterAlternateAbilitiesRepository::saved.begin(),CharacterAlternateAbilitiesRepository::saved.end(),
    [&](const auto& row){return row.aa_id==unsigned(slay.first_rank_id);});
  assert(saved!=CharacterAlternateAbilitiesRepository::saved.end() && saved->aa_value==10);
  assert(c.GetAAPoints()==17 && c.m_pp.aapoints_spent==86);
  assert(!c.CanPurchaseAlternateAdvancementRank(&expanded.at({75,9}),true,true));
 }
 c.m_earned_aa_ranks[slay.first_rank_id].first=8;c.aa_ranks[75].first=8;
 c.m_pp.aapoints=6;assert(!c.CanPurchaseAlternateAdvancementRank(&expanded.at({75,9}),true,true));
 c.m_pp.aapoints=7;assert(c.CanPurchaseAlternateAdvancementRank(&expanded.at({75,9}),true,true));
 c.aa_ranks.erase(30);assert(!c.CanPurchaseAlternateAdvancementRank(&expanded.at({75,9}),true,true));
 std::cout << "{\"native_eligibility_cases\":" << checked << ",\"client_expansion_checks\":8,\"projection_checks\":9,\"restored_earned_rank_cases\":3,\"passed\":true}\n";
}
'''


def main():
    root, output = map(Path, sys.argv[1:3])
    output.mkdir(parents=True, exist_ok=True)
    aa = (root / 'zone/aa.cpp').read_text()
    ability = (root / 'zone/aa_ability.cpp').read_text()
    client = (root / 'zone/client.cpp').read_text()
    functions = [method(aa, 'bool Mob::CanUseAlternateAdvancementRank('),
                 method(aa, 'bool Client::ReprojectEarnedAAs('),
                 method(aa, 'void Client::SendAlternateAdvancementTable('),
                 method(aa, 'bool Mob::CanPurchaseAlternateAdvancementRank('),
                 method(aa, 'bool Client::HasAlreadyPurchasedRank('),
                 method(client, 'uint32 Client::GetEarnedAACount('),
                 method(client, 'bool Client::SaveAA('),
                 method(ability, 'int AA::Ability::GetMaxLevel('),
                 method(ability, 'AA::Rank *AA::Ability::GetRankByPointsSpent(')]
    source = output / 'native.cpp'
    source.write_text(STUBS + '\n'.join(functions) + TESTS)
    exe = output / 'native-test'
    subprocess.run(['clang++','-std=c++17','-Wall','-Wextra','-Werror','-Wno-class-memaccess','-Wno-unused-variable','-Wno-sign-compare','-Wno-missing-field-initializers',
                    '-Wno-unknown-warning-option','-I',str(root),str(source),'-o',str(exe)], check=True)
    result = json.loads(subprocess.check_output([str(exe)], text=True))
    result['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    (output / 'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()

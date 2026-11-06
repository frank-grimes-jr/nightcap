"""Compile actual expedition augment blocks and exercise native per-life guards."""
from pathlib import Path
import unittest
import test_free_trade as native

ROOT = Path(__file__).resolve().parents[2]


class ExpeditionAugments(unittest.TestCase):
    def test_actual_both_expedition_rolls(self):
        source = (ROOT / 'server-mods/code/zone/dungeon_service.cpp').read_text()
        blocks = '\n'.join(native.body(source, f'if (run.dungeon->zone=={zone} && augment_eligible &&') for zone in (760, 113))
        fixture = r'''
#include "common/zone_hunt_policy.h"
#include <cassert>
#include <cstdint>
#include <map>
#include <string>
#include <stdexcept>
#include <vector>
struct NPC {uint32_t spawn=1,type=555;std::vector<uint32_t> loot;std::map<std::string,std::string> vars;
 uint32_t GetSpawnPointID(){return spawn;}uint32_t GetNPCTypeID(){return type;}
 std::string GetEntityVariable(const char*k){return vars[k];}void SetEntityVariable(const char*k,std::string v){vars[k]=v;}
 std::vector<uint32_t>&GetLootItems(){return loot;}void AddItem(uint32_t id,int,bool){loot.push_back(id);}};
struct Zone {struct Random {std::vector<int> values;size_t calls=0;int Int(int,int){return values.at(calls++);}}random;} instance,*zone=&instance;
struct Dungeon {int zone=760;}dungeon;
struct Run {Dungeon*dungeon;std::string id="run";uint64_t seed=123;}current{&dungeon,"run",123};
std::map<uint32_t,uint64_t>death_times;uint64_t Mix(uint64_t seed){return seed;}
uint32_t chance=0,quality_roll=0;uint32_t Roll(uint64_t,uint32_t,uint32_t stream,uint32_t){return stream==303?quality_roll:chance;}
namespace NightcapVigil {constexpr uint32_t Augment=961000;bool Combat(uint32_t id){return id==777;}uint32_t MiniReward(uint32_t id){return id==777?961010:0;}}
namespace NightcapAshen {constexpr uint32_t Augment=961020;bool Combat(uint32_t id){return id==777;}uint32_t MiniReward(uint32_t id){return id==777?961030:0;}}
void Exercise(NPC*npc,bool augment_eligible){const auto&run=current;
// ACTUAL_BLOCKS
}
int main(){
 for(int z:{760,113}){dungeon.zone=z;uint32_t base=z==760?961000:961020;
  NPC n;chance=149;quality_roll=9800;Exercise(&n,true);assert((n.loot==std::vector<uint32_t>{base+3}));
  Exercise(&n,true);assert(n.loot.size()==1); // per-life guard
  n={};Exercise(&n,false);assert(n.loot.empty()&&n.vars.empty()); // owned/protected/restored
  n={};chance=150;Exercise(&n,true);assert(n.loot.empty());Exercise(&n,true);assert(n.loot.empty());
  n={};n.spawn=0;instance.random={{149,9800},0};Exercise(&n,true);assert((n.loot==std::vector<uint32_t>{base+3}));
  Exercise(&n,true);assert(instance.random.calls==2); // dynamic enemies draw once per life
  n={};n.type=777;chance=0;quality_roll=0;Exercise(&n,true);assert(n.loot.size()==2); // original static miniboss
  n={};n.type=777;n.spawn=0;instance.random={{9999},0};Exercise(&n,true);assert(n.loot.empty()); // no new dynamic mini farm
  int successes=0;for(uint32_t r=0;r<10000;++r){n={};chance=r;quality_roll=0;Exercise(&n,true);successes+=!n.loot.empty();}assert(successes==150);
 }
}
'''
        native.FreeTradeTests.compile_run(self, fixture.replace('// ACTUAL_BLOCKS', blocks))


if __name__ == '__main__':
    unittest.main()

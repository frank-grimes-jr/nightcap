"""Compile the actual death-loss decision against the proposed rule value."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / 'docs/ops/no-death-exp-loss-20261017'


class DeathExperienceTests(unittest.TestCase):
    def test_native_death_policy(self):
        source = (ROOT / 'server-mods/code/zone/attack.cpp').read_text()
        start = source.index('\t// figure out if they should lose exp')
        end = source.index('\n\tbool leave_corpse = false;', start)
        decision = source[start:end]
        start = source.index('\t\tif (exploss > 0) {', end)
        end = source.index('\n\t\tauto illusion_spell_id', start)
        apply = source[start:end]
        threshold = int(re.search(r"SET rule_value = '(\d+)'", (OPS / 'forward.sql').read_text())[1])
        harness = r'''
#include <cassert>
#include <cstdint>
#include <iostream>
using int32 = int32_t; using uint32 = uint32_t; using uint16 = uint16_t;
namespace EQ { bool ValueWithin(int v,int lo,int hi) { return v>=lo && v<=hi; } }
namespace ExpSource { enum Type { Death }; }
int DeathExpLossLevel=10, DeathExpLossMaxLevel=255, DeathExpLossMultiplier=3;
bool UseDeathExpLossMult=false, LevelBasedEXPMods=false, DeathKeepLevel=false;
#define RuleI(category,name) name
#define RuleB(category,name) name
struct Mob { bool IsOfClientBot(){return false;} Mob* GetOwner(){return nullptr;} };
struct Mod { float ExpMod=1.0f; };
struct Zone { Mod level_exp_mod[256]; } zone_value;
auto* zone=&zone_value;
struct Buff { uint32 spellid=0; bool client=false; } buffs[1];
uint8_t level=50; uint32 xp=100000000, aaxp=2326; int writes=0;
uint8_t GetLevel(){return level;} uint32 GetEXP(){return xp;}
uint32 GetAAXP(){return aaxp;} uint32 GetEXPForLevel(int){return xp-5;}
bool IsBecomeNPC(){return false;} bool IsValidSpell(int){return false;}
uint32 GetMaxTotalSlots(){return 0;}
void SetEXP(ExpSource::Type, uint32 value, uint32 aa){xp=value; aaxp=aa; ++writes;}
int death(){
 int exploss=0, killed_level=level, spell=0; Mob* killer_mob=nullptr;
 DECISION
 APPLY
 return exploss;
}
int main(){
 // Prove the pre-change penalty exists, including multiplier index zero.
 assert(death()>0 && writes==1);
 UseDeathExpLossMult=true; DeathExpLossMultiplier=0; xp=100000000; writes=0;
 assert(death()>0 && writes==1);
 DeathExpLossLevel=THRESHOLD;
 int cases=0;
 for(int l=0;l<=255;++l) for(int mult=0;mult<=1;++mult)
 for(int keep=0;keep<=1;++keep) for(int mods=0;mods<=1;++mods){
  level=static_cast<uint8_t>(l); UseDeathExpLossMult=mult;
  DeathKeepLevel=keep; LevelBasedEXPMods=mods;
  zone->level_exp_mod[l].ExpMod=1.5f; xp=100000000; aaxp=2326; writes=0;
  assert(death()==0); // Also the exploss passed to new Corpse(this, exploss, ...).
  assert(xp==100000000 && aaxp==2326 && writes==0);
  ++cases;
 }
 std::cout<<cases<<" native no-loss cases and 2 previous-policy controls passed\n";
}
'''.replace('DECISION', decision).replace('APPLY', apply).replace('THRESHOLD', str(threshold))
        compiler = shutil.which('g++')
        self.assertIsNotNone(compiler, 'g++ is required for native policy verification')
        with tempfile.TemporaryDirectory() as temp:
            cpp = Path(temp) / 'death.cpp'
            exe = Path(temp) / 'death.exe'
            cpp.write_text(harness)
            subprocess.run([compiler, '-std=c++11', '-Wall', '-Wextra', str(cpp), '-o', str(exe)], check=True)
            subprocess.run([str(exe)], check=True)

    def test_corpse_and_resurrection_use_recorded_loss(self):
        attack = (ROOT / 'server-mods/code/zone/attack.cpp').read_text()
        self.assertIn('new Corpse(this, exploss, killed_by)', attack)
        rez = (ROOT / 'server-mods/code/zone/client_process.cpp').read_text()
        begin = rez.index('void Client::OPRezzAnswer(')
        rez = rez[begin:rez.index('PendingRezzXP = -1;', begin)]
        self.assertIn('base_value[0] > 0 && PendingRezzXP > 0', rez)
        self.assertIn('base_value[0] == 100 && PendingRezzXP > 0', rez)


if __name__ == '__main__':
    unittest.main()

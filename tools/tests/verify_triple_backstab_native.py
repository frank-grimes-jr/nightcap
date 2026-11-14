"""Compile the actual TryBackstab method with controlled engine boundaries.

Linux: python3 verify_triple_backstab_native.py SOURCE_ROOT OUTPUT_DIR.
No database or running server is touched. Random outcomes are deterministic.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from verify_aa_tbs_native import method

STUBS = r'''
#include <cassert>
#include <iostream>
#include <vector>
namespace EQ {
namespace invslot { constexpr int slotPrimary=0, slotSecondary=1; }
namespace item { constexpr int ItemType1HPiercing=2; }
namespace skills { constexpr int SkillBackstab=8; }
struct ItemData { int ItemType=2; };
struct ItemInstance {
 ItemData item;
 const ItemData* GetItem() const { return &item; }
 bool IsEquipable(int) const { return true; }
 int GetItemRequiredLevel(bool) const { return 0; }
};
}
namespace Chat { constexpr int Red=1, White=2; }
constexpr int BACKSTAB_WEAPON=1;
enum class eSpecialAttacks { None, ChaoticStab };
#define RuleI(group,key) 55
struct Random {
 bool pass=true;
 std::vector<int> rolls;
 bool Roll(int chance) { rolls.push_back(chance); return pass; }
};
struct Zone { Random random; } zone_value;
Zone* zone=&zone_value;
struct Bonuses {
 int TripleBackstab=0,FrontalBackstabChance=0,Double_Backstab_Front=0;
 bool FrontalBackstabMinDmg=false;
};
struct Inventory {
 EQ::ItemInstance weapon, offhand;
 bool present=true, secondary=false;
 const EQ::ItemInstance* GetItem(int slot) {
  return slot == EQ::invslot::slotPrimary ? (present ? &weapon : nullptr) : (secondary ? &offhand : nullptr);
 }
};
class Mob {
public:
 int level=1,kind=0,hp=100,stabs=0,minimum_stabs=0,swings=0,kill_on_stab=0;
 bool behind=true,double_success=true,facestab=false;
 int double_checks=0;
 Inventory inventory;
 Bonuses aabonuses,itembonuses,spellbonuses;
 eSpecialAttacks m_specialattacks=eSpecialAttacks::None;
 bool IsClient() { return kind==0; }
 bool IsBot() { return kind==1; }
 bool IsNPC() { return kind==2; }
 bool IsOfClientBot() { return kind!=2; }
 Mob* CastToClient() { return this; }
 bool CanEquipItem(const EQ::ItemData*) { return true; }
 bool CanThisClassDualWield() { return true; }
 int GetLevel() const { return level; }
 Mob* CastToBot() { return this; }
 Inventory& GetInv() { return inventory; }
 const EQ::ItemInstance* GetBotItem(int i) { return inventory.GetItem(i); }
 bool GetCombatRoundForAlerts() { return false; }
 void SetCombatRoundForAlerts() {}
 void RaidGroupSay(const char*) {}
 void MessageString(int,int) {}
 void Message(int,const char*) {}
 bool BehindMob(Mob*,float,float) { return behind; }
 float GetX() { return 0; } float GetY() { return 0; }
 bool CanFacestab() { return facestab; }
 int GetHP() { return hp; }
 bool CheckDoubleAttack() { ++double_checks; return double_success; }
 void CheckIncreaseSkill(int,Mob*,int) {}
 void Attack(Mob*,int) { ++swings; }
 void RogueBackstab(Mob* other,bool minimum,int) {
  ++stabs; if(minimum)++minimum_stabs;
  if(kill_on_stab==stabs)other->hp=0;
 }
 void TryBackstab(Mob*,int);
};
using Client=Mob;
'''

TESTS = r'''
int main() {
 int cases=0;
 for(int level : {1,10,30,50}) for(int bonus : {5,45}) {
  Mob c,t; c.level=level;c.aabonuses.TripleBackstab=bonus;zone->random.rolls.clear();
  c.TryBackstab(&t,10);
  assert(c.stabs==3 && c.double_checks==1);
  assert(zone->random.rolls==std::vector<int>{bonus}); ++cases;
 }
 for(int kind : {0,1,2}) {
  Mob c,t;c.kind=kind;c.TryBackstab(&t,10);assert(c.stabs==1);++cases;
 }
 for(int source : {0,1}) {
  Mob c,t;(source ? c.itembonuses : c.spellbonuses).TripleBackstab=100;
  c.TryBackstab(&t,10);assert(c.stabs==1 && c.double_checks==0);++cases;
 }
 { Mob c,t;c.kind=1;c.aabonuses.TripleBackstab=45;c.TryBackstab(&t,10);assert(c.stabs==1);++cases; }
 { Mob c,t;c.level=55;c.TryBackstab(&t,10);assert(c.stabs==2);++cases; }
 { Mob c,t;c.level=55;c.itembonuses.TripleBackstab=45;c.TryBackstab(&t,10);assert(c.stabs==3);++cases; }
 { Mob c,t;c.aabonuses.TripleBackstab=45;c.double_success=false;c.TryBackstab(&t,10);assert(c.stabs==1);++cases; }
 { Mob c,t;c.aabonuses.TripleBackstab=45;zone->random.pass=false;c.TryBackstab(&t,10);assert(c.stabs==2);zone->random.pass=true;++cases; }
 for(int death : {1,2}) {
  Mob c,t;c.aabonuses.TripleBackstab=45;c.kill_on_stab=death;c.TryBackstab(&t,10);assert(c.stabs==death);++cases;
 }
 for(int invalid : {0,1}) {
  Mob c,t;c.aabonuses.TripleBackstab=45;
  if(invalid)c.inventory.weapon.item.ItemType=0;else c.inventory.present=false;
  c.TryBackstab(&t,10);assert(c.stabs==0 && c.swings==0);++cases;
 }
 { Mob c;c.aabonuses.TripleBackstab=45;c.TryBackstab(nullptr,10);assert(c.stabs==0);++cases; }
 { Mob c,t;c.aabonuses.TripleBackstab=45;c.behind=false;c.TryBackstab(&t,10);assert(c.stabs==0 && c.swings==1);++cases; }
 { Mob c,t;c.aabonuses.TripleBackstab=45;c.behind=false;c.aabonuses.FrontalBackstabMinDmg=true;c.TryBackstab(&t,10);assert(c.stabs==1 && c.minimum_stabs==1);++cases; }
 { Mob c,t;c.aabonuses.TripleBackstab=45;c.behind=false;c.aabonuses.FrontalBackstabChance=100;c.TryBackstab(&t,10);assert(c.stabs==3);++cases; }
 std::cout << "{\"native_backstab_cases\":" << cases << ",\"passed\":true}\n";
}
'''


def main():
    root, output = map(Path, sys.argv[1:3])
    output.mkdir(parents=True, exist_ok=True)
    source = root / 'zone/special_attacks.cpp'
    text = source.read_text()
    body = method(text, 'void Mob::TryBackstab(')
    if 'BackstabPiercer(' in body:
        body = method(text, 'const EQ::ItemInstance* BackstabPiercer(') + '\n' + body
    harness = output / 'native.cpp'
    harness.write_text(STUBS + body + TESTS)
    executable = output / 'native-test'
    subprocess.run(['clang++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                    str(harness), '-o', str(executable)], check=True)
    result = json.loads(subprocess.check_output([str(executable)], text=True))
    result['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    result['harness_sha256'] = hashlib.sha256(harness.read_bytes()).hexdigest()
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()

"""Compile the actual fist formulas; compare every held-class slot with native Monk.

The fixture substitutes identity/rules/skills, not the damage or delay formulas.
"""
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_gameplay_policies import ZONE, function

FIXTURE = r'''
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
using uint8 = uint8_t;
using int64 = int64_t;
namespace Class { enum { Wizard=12, Monk=7, Beastlord=15, MonkGM=27, BeastlordGM=35 }; }
namespace Race { enum { Human=1, Iksar=128 }; }
namespace EQ {
 namespace skills { enum { SkillHandtoHand=28, SkillDualWield=22 }; }
 namespace invslot { enum { slotHands=12, slotPrimary=13, slotSecondary=14 }; }
 namespace item { enum { ItemTypeArmor=10 }; }
 struct ItemData {
  bool two=false, Magic=false; int Damage=10, Slots=8192, ItemType=0, ElemDmgAmt=0;
  int BaneDmgBody=0, BaneDmgAmt=0, BaneDmgRace=0, BaneDmgRaceAmt=0;
  bool IsType2HWeapon() const { return two; }
  bool IsType1HWeapon() const { return !two; }
 };
 struct ItemInstance {
  ItemData item; bool weapon=true;
  bool IsWeapon() const { return weapon; }
  const ItemData* GetItem() const { return &item; }
  int GetItemRequiredLevel(bool) const { return 0; }
  int GetItemRecommendedLevel(bool) const { return 0; }
  int GetItemWeaponDamage(bool) const { return item.Damage; }
  bool IsClassEquipable(int) const { return true; }
  bool IsRaceEquipable(int) const { return true; }
  bool GetItemMagical(bool) const { return item.Magic; }
  bool GetItemElementalFlag(bool) const { return false; }
  int GetItemBaneDamageBody(bool) const { return 0; }
  int GetItemBaneDamageRace(bool) const { return 0; }
 };
}
struct Inventory {
 EQ::ItemInstance *primary=nullptr, *secondary=nullptr, *hands=nullptr;
 const EQ::ItemInstance* GetItem(int slot) const { return slot==12 ? hands : slot==13 ? primary : secondary; }
};
struct DamageTable { int max_extra,chance,minusfactor; };
namespace SpecialAbility { enum { MeleeImmunity=1, MeleeImmunityExceptMagical=2,
 MagicalAttack=3, MagicImmunity=4, MeleeImmunityExceptBane=5, BaneAttack=6 }; }
bool revamp = false;
#define RuleB(category, name) revamp
#define RuleI(category, name) 30
struct Mob {
 int level=2, base=Class::Wizard, second=0, third=0, skill=10, race=Race::Human, gloves=0;
 bool client=true, dual=true; Inventory inv;
 bool invul=false; int ability=0;
 struct { bool MagicWeapon=false; } spellbonuses,itembonuses;
 bool IsClient() const { return client; }
 bool IsNPC() const { return !client; }
 bool IsBot() const { return false; }
 bool GetInvul() const { return invul; }
 int GetSpecialAbility(int id) const { return id==ability; }
 int GetBodyType() const { return 1; }
 int GetBaseRace() const { return race; }
 Mob* GetOwner() const { return nullptr; }
 bool CanEquipItem(const EQ::ItemData*) const { return true; }
 int CalcRecommendedLevelBonus(int,int,int v) const { return v; }
 int ResistElementalWeaponDmg(const EQ::ItemInstance*) const { return 0; }
 int CheckBaneDamage(const EQ::ItemInstance*) const { return 0; }
 const Mob* CastToClient() const { return this; }
 Mob* CastToClient() { return this; }
 int GetClass() const { return base; }
 int GetLevel() const { return level; }
 int GetRace() { return race; }
 int GetSkill(int) const { return skill; }
 int GetItemIDAt(int) { return gloves; }
 bool IsMulticlassMember(int id) const { return id==base || id==second || id==third; }
 bool IsWarriorClass() const { return base==Class::Monk || base==Class::Beastlord; }
 bool HasSkill(int) const { return dual; }
 const Inventory& GetInv() const { return inv; }
 uint8 GetHandToHandClass() const;
 bool CanThisClassDualWield() const;
 const DamageTable& GetDamageTable(bool unarmed=false) const;
 int GetHandToHandDamage();
 int GetHandToHandDelay();
 int64 GetWeaponDamage(Mob*,const EQ::ItemData*);
 int64 GetWeaponDamage(Mob*,const EQ::ItemInstance*,int64*);
};
#define class_ base
void check(bool ok, const char* message) { if (!ok) throw std::runtime_error(message); }
'''

CONTROLS = r'''
int main() {
 try {
  Mob native, second, third, wizard;
  native.base=Class::Monk; second.second=Class::Monk; third.third=Class::Monk;
  check(native.GetHandToHandDamage()==4, "native level-2 baseline");
  check(second.GetHandToHandDamage()==4, "Wizard/Monk level-2 fist damage is not 4");
  check(third.GetHandToHandDamage()==4, "tertiary Monk level-2 fist damage is not 4");
  check(wizard.GetHandToHandDamage()==2, "ordinary caster fists changed");
  check(second.CanThisClassDualWield(), "secondary Monk cannot dual wield empty fists");
  check(third.CanThisClassDualWield(), "tertiary Monk cannot dual wield empty fists");
  check(!wizard.CanThisClassDualWield(), "ordinary caster gained empty offhand");
  second.dual=false;
  check(!second.CanThisClassDualWield(), "unlearned dual wield became available");
  second.dual=true;
  EQ::ItemInstance twohand, shield, onehand; twohand.item.two=true; shield.weapon=false;
  second.inv.primary=&twohand;
  check(!second.CanThisClassDualWield(), "two-handed weapon allows offhand");
  second.inv.primary=nullptr; second.inv.secondary=&shield;
  check(!second.CanThisClassDualWield(), "shield allows offhand");
  second.inv.secondary=&onehand;
  check(second.CanThisClassDualWield(), "one-handed weapon rejected");
  second.inv.secondary=nullptr;
  Mob target; target.ability=SpecialAbility::MeleeImmunityExceptMagical;
  EQ::ItemInstance magic_gloves, weapon; magic_gloves.item.Magic=true;
  for (int cls : {Class::Monk,Class::Beastlord}) for (int slot : {2,3}) for (int lvl : {2,29,30,50}) {
   Mob held; held.level=lvl; (slot==2 ? held.second : held.third)=cls;
   native.base=cls; native.level=lvl;
   check(held.GetWeaponDamage(&target,(const EQ::ItemData*)nullptr)==native.GetWeaponDamage(&target,(const EQ::ItemData*)nullptr), "data magical fists differ");
   for (bool magic : {false,true}) {
    held.inv.hands=native.inv.hands=magic ? &magic_gloves : nullptr;
    int64 held_hate=0,native_hate=0;
    check(held.GetWeaponDamage(&target,(const EQ::ItemInstance*)nullptr,&held_hate)==native.GetWeaponDamage(&target,(const EQ::ItemInstance*)nullptr,&native_hate), "inventory magical fists differ");
    check(held_hate==native_hate, "fist hate differs");
    weapon.item.Magic=magic;
    check(held.GetWeaponDamage(&target,&weapon,nullptr)==(magic ? 10 : 0), "equipped weapon immunity changed");
    check(held.GetWeaponDamage(&target,&weapon.item)==(magic ? 10 : 0), "data weapon immunity changed");
   }
  }
  check(wizard.GetWeaponDamage(&target,(const EQ::ItemInstance*)nullptr,nullptr)==0, "caster gained magical fists");
  target.invul=true;
  check(second.GetWeaponDamage(&target,(const EQ::ItemInstance*)nullptr,nullptr)==0, "invulnerability bypassed");
  for (bool rule : {false,true}) for (int cls : {Class::Monk,Class::Beastlord})
   for (int race : {Race::Human,Race::Iksar}) for (int level=1; level<=85; ++level)
    for (int gloves : {0,10652}) {
     revamp=rule; native.base=cls; second.second=cls; third.third=cls;
     for (auto m : {&native,&second,&third}) {
      m->level=level; m->race=race; m->skill=std::min(level*5,300); m->gloves=gloves;
     }
     check(second.GetHandToHandDamage()==native.GetHandToHandDamage(), "secondary damage differs");
     check(third.GetHandToHandDamage()==native.GetHandToHandDamage(), "tertiary damage differs");
     check(second.GetHandToHandDelay()==native.GetHandToHandDelay(), "secondary delay differs");
     check(third.GetHandToHandDelay()==native.GetHandToHandDelay(), "tertiary delay differs");
     const auto &expected=native.GetDamageTable(true), &held=second.GetDamageTable(true);
     check(expected.max_extra==held.max_extra && expected.chance==held.chance && expected.minusfactor==held.minusfactor,
      "unarmed damage table differs");
     const auto &weapon_expected = cls==Class::Monk ? native.GetDamageTable() : wizard.GetDamageTable();
     check(second.GetDamageTable().max_extra==weapon_expected.max_extra, "held Monk weapon table or Beastlord control differs");
    }
  revamp=false; second.client=false; second.level=2; second.gloves=0;
  check(second.GetHandToHandDamage()==2, "NPC gained player secondary class");
  second.client=true; second.second=0; second.third=0;
  check(second.GetHandToHandDamage()==2, "released Monk retained fists");
  std::cout << "fist slot/rule/level/race/epic controls passed\n";
 } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
'''

class MulticlassFists(unittest.TestCase):
    def test_native_fist_formulas(self):
        source = (ZONE / 'attack.cpp').read_text()
        signatures = ['int Mob::GetHandToHandDamage(', 'int Mob::GetHandToHandDelay(', 'const DamageTable &Mob::GetDamageTable(',
                      'int64 Mob::GetWeaponDamage(Mob *against, const EQ::ItemData *weapon_item)',
                      'int64 Mob::GetWeaponDamage(Mob *against, const EQ::ItemInstance *weapon_item, int64 *hate)']
        if 'uint8 Mob::GetHandToHandClass(' in source:
            signatures.insert(0, 'uint8 Mob::GetHandToHandClass(')
        bodies = '\n'.join(function(source, sig) for sig in signatures)
        bodies += function((ZONE/'mob.cpp').read_text(), 'bool Mob::CanThisClassDualWield(')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out/'test.cpp').write_text(FIXTURE+bodies+CONTROLS)
            (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
            build = subprocess.run(['cmd','/d','/c',str(out/'build.cmd')], cwd=out)
            self.assertEqual(build.returncode, 0, (out/'build.log').read_text())
            run = subprocess.run([str(out/'test.exe')], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout+run.stderr)

if __name__ == '__main__': unittest.main()

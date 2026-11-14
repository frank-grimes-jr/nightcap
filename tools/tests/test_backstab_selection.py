"""Verify the Backstab weapon comparison against the native elemental roll distribution."""
import unittest

from test_gameplay_policies import function
from test_pet_equipment import ROOT, compile_run
import verify_triple_backstab_native as triple


class BackstabSelection(unittest.TestCase):
    def test_zero_selected_base_does_not_reselect_without_the_target(self):
        source = (ROOT / "server-mods/code/zone/special_attacks.cpp").read_text()
        legacy = function(source, "void Mob::DoSpecialAttackDamage(")
        attack = (function(source, "void Mob::DoSpecialAttackDamageWithBase(")
                  if "void Mob::DoSpecialAttackDamageWithBase(" in source else legacy)
        # Exercise the native hit initialization up to the next independent damage/immunity guard.
        start = attack.index("DamageHitInfo my_hit;")
        end = attack.index("if (base_damage == DMG_INVULNERABLE)", start)
        compile_run(r'''
#include <cassert>
struct DamageHitInfo { int damage_done,base_damage,min_damage,skill; };
struct Mob {
 int selections=0;
 // The targetless fallback would allow a stronger, non-magical primary against a magic-only target.
 int GetBaseSkillDamage(int) { ++selections; return 240; }
 int Dispatch(int base_damage, bool resolved) {
  int skill=8, min_damage=0;
''' + attack[start:end] + r'''
  return my_hit.base_damage;
 }
};
int main() {
 Mob rogue;
 assert(rogue.Dispatch(0,true)==0 && rogue.selections==0);
 assert(rogue.Dispatch(0,false)==240 && rogue.selections==1);
 assert(rogue.Dispatch(37,true)==37 && rogue.selections==1);
}
''')
        self.assertIn("ReuseTime, IsClient())", function(source, "void Mob::RogueBackstab("))
        self.assertIn("ReuseTime, false)", legacy)

    def test_original_triple_backstab_class_level_front_and_target_death_controls(self):
        source = (ROOT / "server-mods/code/zone/special_attacks.cpp").read_text()
        compile_run(triple.STUBS + function(source, "const EQ::ItemInstance* BackstabPiercer(") +
                    function(source, "void Mob::TryBackstab(") + triple.TESTS)

    def test_expected_elemental_damage_consumes_no_rng_and_matches_all_possible_rolls(self):
        source = (ROOT / "server-mods/code/zone/mob.cpp").read_text()
        methods = "\n".join(function(source, signature) for signature in (
            "int WeaponElementRoll(", "template <typename Resolve>\nint64 ResolveWeaponElements(",
            "int Mob::ResistElementalWeaponDmg(", "int64 Mob::ExpectedElementalWeaponDamage("))
        compile_run(r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
using int64 = int64_t;
enum { RESIST_MAGIC, RESIST_FIRE, RESIST_COLD, RESIST_POISON, RESIST_DISEASE,
       RESIST_CORRUPTION, RESIST_CHROMATIC, RESIST_PRISMATIC, RESIST_PHYSICAL };
struct RNG { int draw = 0, calls = 0; int Int(int lo, int hi) {
  assert(lo == 0 && hi == 200); ++calls; return draw;
} };
struct Zone { RNG random; } zone_value, *zone = &zone_value;
namespace EQ {
struct ItemInstance {
  int amount, school;
  void GetItemElementalDamage(int& magic, int& fire, int& cold, int& poison, int& disease,
    int& chromatic, int& prismatic, int& physical, int& corruption, bool augments) const {
    assert(augments);
    int *by_type[] = {&magic,&fire,&cold,&poison,&disease,&corruption,&chromatic,&prismatic,&physical};
    *by_type[school] = amount;
  }
};
}
struct Mob {
 int resistance = 0, school = 0;
 int GetResist(int type) { assert(type == school && type != RESIST_PHYSICAL); return resistance; }
 int GetPhR() { assert(school == RESIST_PHYSICAL); return resistance; }
 int ResistElementalWeaponDmg(const EQ::ItemInstance*);
 int64 ExpectedElementalWeaponDamage(const EQ::ItemInstance*);
};
''' + methods + r'''
int main() {
  Mob target;
  for (int type = 0; type <= RESIST_PHYSICAL; ++type) {
    target.school = type;
    for (int resist : {-120, -1, 0, 75, 199, 200, 201, 300}) {
      target.resistance = resist;
      for (int amount : {1, 11, 100, 255}) {
        EQ::ItemInstance item{amount, type};
        zone->random.calls = 0;
        auto expected = target.ExpectedElementalWeaponDamage(&item);
        assert(zone->random.calls == 0);
        int sum = 0;
        for (int draw = 0; draw <= 200; ++draw) {
          zone->random.draw = draw;
          int native = target.ResistElementalWeaponDmg(&item);
          int retained = amount * std::max(0, std::min(100, draw - resist)) / 100;
          assert(native == retained);
          sum += native;
        }
        assert(expected == sum && zone->random.calls == (resist >= 201 ? 0 : 201));
      }
    }
  }
}
''')


if __name__ == "__main__":
    unittest.main()

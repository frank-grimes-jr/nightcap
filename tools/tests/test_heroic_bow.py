"""Exercise the native ordinary-arrow curve and its actual dispatch boundaries."""
import unittest

from test_gameplay_policies import function
from test_pet_equipment import ROOT, compile_run


class HeroicBow(unittest.TestCase):
    def test_published_points_rounding_and_saturation(self):
        header = (ROOT / "server-mods/code/common/nightcap_melee.h").as_posix()
        compile_run(f'#include "{header}"\n' + r'''
#include <cassert>
int main() {
	using NightcapMelee::ScaleNormalBowHit;
	assert(ScaleNormalBowHit(400, -1) == 400);
	assert(ScaleNormalBowHit(400, 0) == 400);
	assert(ScaleNormalBowHit(400, 1) == 401);
	assert(ScaleNormalBowHit(399, 1) == 399);
	assert(ScaleNormalBowHit(10000, 99) == 12475);
	assert(ScaleNormalBowHit(10000, 100) == 12500);
	assert(ScaleNormalBowHit(10000, 101) == 12509);
	assert(ScaleNormalBowHit(10000, 199) == 13391);
	assert(ScaleNormalBowHit(10000, 200) == 13400);
	assert(ScaleNormalBowHit(10000, 201) == 13406);
	assert(ScaleNormalBowHit(10000, 250) == 13700);
	assert(ScaleNormalBowHit(10000, 300) == 14000);
	assert(ScaleNormalBowHit(10000, 400) == 14600);
	assert(ScaleNormalBowHit(-5, 300) == -5);
	assert(ScaleNormalBowHit(0, 300) == 0);
	const auto maximum = std::numeric_limits<int64_t>::max();
	assert(ScaleNormalBowHit(maximum - 1, 0) == maximum - 1);
	assert(ScaleNormalBowHit(maximum, std::numeric_limits<int>::max()) == maximum);
	assert(ScaleNormalBowHit(10000, std::numeric_limits<int>::max()) == 12884914082LL);
}
''')

    def test_only_validated_shots_and_their_projectiles_supply_bow_origin(self):
        zone = ROOT / "server-mods/code/zone"
        special = (zone / "special_attacks.cpp").read_text()
        launch = function(special, "bool Client::RangedAttack(")
        for kind in ("ItemTypeBow", "ItemTypeArrow"):
            self.assertLess(launch.index(kind), launch.index("DoArcheryAttackDmg("))
        projectile = function(special, "bool Mob::TryProjectileAttack(")
        self.assertIn("ranged_id = RangeWeapon->GetItem()->ID", projectile)
        self.assertIn("ammo_id = Ammo->GetItem()->ID", projectile)
        impact = function(special, "void Mob::ProjectileAttack(")
        self.assertIn("ProjectileAtk[i].ranged_id,", impact)
        self.assertIn("ProjectileAtk[i].ammo_id, nullptr,", impact)
        spell = function((zone / "spell_effects.cpp").read_text(), "bool Mob::SpellEffect(")
        self.assertIn("DoArcheryAttackDmg(this, nullptr, nullptr,", spell)
        self.assertIn("focus, ReuseTime, 0, 0, nullptr, 0, 4.0f, true)", spell)


if __name__ == "__main__":
    unittest.main()

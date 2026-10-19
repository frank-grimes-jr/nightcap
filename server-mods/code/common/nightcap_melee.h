#pragma once
#include <algorithm>
#include <cstdint>
#include <limits>

namespace NightcapMelee {
constexpr int HolyShieldAbility = 30200;
constexpr int HolyShieldRank = 43210;
constexpr int MarrRenewalSpell = 42845;

inline uint64_t MarrHealing(uint64_t amount)
{
	const auto bonus = amount / 10;
	return amount > std::numeric_limits<uint64_t>::max() - bonus ?
		std::numeric_limits<uint64_t>::max() : amount + bonus;
}

// Autoattack weapon skills only. Ranged and activated specials retain native damage.
constexpr bool IsWeaponSkill(int skill)
{
	return skill == 0 || skill == 1 || skill == 2 || skill == 3 ||
		skill == 28 || skill == 36 || skill == 77;
}

inline double HeroicDamagePercent(int heroic_strength)
{
	const double strength = std::max(heroic_strength, 0);
	const double excess = std::max(strength - 100.0, 0.0);
	constexpr double floor = 1.0 / 3.0;
	constexpr double decay = 0.0055;
	const double declining = std::min(excess, (1.0 - floor) / decay);
	return std::min(strength, 100.0) + declining - decay * declining * declining / 2.0 +
		(excess - declining) * floor;
}

inline int64_t ScaleHeroicHit(int64_t damage, int heroic_strength)
{
	if (damage <= 0) {
		return damage;
	}
	const long double scaled = damage * (1.0L + HeroicDamagePercent(heroic_strength) / 100.0L);
	return scaled >= std::numeric_limits<int64_t>::max() ? std::numeric_limits<int64_t>::max() :
		static_cast<int64_t>(scaled);
}
}

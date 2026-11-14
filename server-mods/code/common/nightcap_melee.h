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

// Melee weapon skills eligible for the heroic STR multiplier.
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

inline int64_t ScaleNormalBowHit(int64_t damage, int heroic_dexterity)
{
	if (damage <= 0 || heroic_dexterity <= 0) {
		return damage;
	}

	// THJ guide anchors: +25% at 100, ~34% at 200, ~37% at 250, ~40% at 300.
	// Nightcap interpolates in basis points and keeps the last slope above 300.
	const int64_t multiplier = 10000 + 25 * std::min(heroic_dexterity, 100) +
		9 * std::clamp(heroic_dexterity - 100, 0, 100) + 6LL * std::max(heroic_dexterity - 200, 0);
	const int64_t whole = damage / 10000;
	const int64_t remainder = (damage % 10000) * multiplier / 10000;
	constexpr int64_t maximum = std::numeric_limits<int64_t>::max();
	if (whole > (maximum - remainder) / multiplier) {
		return maximum;
	}
	return whole * multiplier + remainder;
}
}

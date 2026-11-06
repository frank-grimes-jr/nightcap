#pragma once
#include <algorithm>
#include <cstdint>

namespace NightcapHunt {
constexpr uint64_t Revision = 2026100901;
constexpr uint32_t ArmorMask = 921732;
constexpr int ExpeditionAugmentChance = 150; // Same 1.5% default; retained per-life dungeon rolls.
// Family chances are per zone: nightcap_zone_hunt_zones.augment_chance/gear_chance, out of 10000.

inline int Quality(int roll)
{
	return roll < 6000 ? 0 : roll < 9000 ? 1 : roll < 9800 ? 2 : 3;
}

inline int Headroom(int level, int effective_heroic)
{
	return level < 50 ? 0 : std::min(30, std::max(0, effective_heroic) / 2);
}

struct DeathEligibility {
	bool enabled, classic, version_zero, native_source, owned, restored, night_allowed;
	int level, minimum_level;
};

// No name, level, class, faction, spawn2 or time-of-day gate: guards,
// named/quest enemies and unowned scripted combat NPCs use the same roll.
inline bool AugmentDeathEligible(const DeathEligibility &e, int body, bool protected_npc)
{
	return e.enabled && e.classic && e.version_zero && !e.owned && !e.restored &&
		!protected_npc && body != 11 && body != 60 && body != 66 && body != 67;
}

// Keep at most the strongest Hunt shield-block contribution, even with six
// identical augments. Shielding (damage mitigation) is a separate item stat.
inline int AugmentShieldBlock(uint32_t id)
{
	for (uint32_t base : {940040u, 940280u, 940528u}) {
		if (id >= base && id <= base + 3) { return id == base ? 0 : id == base + 3 ? 2 : 1; }
	}
	return 0;
}

inline bool BeginDeathRoll(bool &rolled, const DeathEligibility &e)
{
	if (rolled || !e.enabled || !e.classic || !e.version_zero || !e.native_source ||
		e.owned || e.restored || !e.night_allowed || e.level < e.minimum_level) { return false; }
	rolled = true;
	return true;
}
}

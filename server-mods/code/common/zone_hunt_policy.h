#pragma once
#include <algorithm>
#include <cstdint>

namespace NightcapHunt {
constexpr uint64_t Revision = 2026100901;
constexpr uint32_t ArmorMask = 921732;
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

inline bool BeginDeathRoll(bool &rolled, const DeathEligibility &e)
{
	if (rolled || !e.enabled || !e.classic || !e.version_zero || !e.native_source ||
		e.owned || e.restored || !e.night_allowed || e.level < e.minimum_level) { return false; }
	rolled = true;
	return true;
}
}

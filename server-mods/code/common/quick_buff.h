#pragma once
#include <algorithm>
#include <cstdint>

namespace NightcapQuickBuff {
constexpr int Family = 48;
inline bool IsRank(int rank) { return rank >= 147 && rank <= 149; }
inline int32_t ManaCost(int64_t maximum) {
	return maximum <= 0 ? 0 : static_cast<int32_t>(std::max<int64_t>(1,
		std::min<int64_t>(maximum, INT32_MAX) / 2));
}
template <typename Ability, typename Rank>
void Configure(int family, Ability &ability, Rank &rank) {
	if (family != Family || !IsRank(rank.id)) { return; }
	ability.type = 3;
	// Existing RoF2 instant self spell: presentation marker ONLY. Activation
	// dispatches the memorized spells; it must never cast Cleanse itself.
	rank.spell = 8;
	rank.recast_time = 0;
	rank.upper_hotkey_sid = rank.lower_hotkey_sid = 147;
	rank.effects.clear();
}
}

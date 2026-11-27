#pragma once

namespace NightcapImitateDeath {
constexpr int Family = 420;
constexpr int RankId = 1255;
// RoF2 requires positive reuse for Make Hotkey. Every family 420 timer packet
// resets readiness; this display marker never becomes a server deadline.
inline int ClientPresentationReuse(int family, int reuse) { return family == Family ? 1 : reuse; }

template <typename Rank>
void Configure(int family, Rank &rank) {
	if (family == Family) { rank.recast_time = 0; }
}
}

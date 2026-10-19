#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <limits>

// Released May7 constants plus explicitly documented candidate calibrations.
namespace NightcapTHJ {
constexpr uint16_t DimensionalShielding = 43220;
inline int ResourcePercent(uint16_t spell) {
	switch (spell) {
	case 2775: return 50;
	case 8450: return 10;
	case 8451: return 20;
	case 8452: return 30;
	case 11068: return 40;
	default: return 0;
	}
}
inline bool ManaBurn(uint16_t spell) { return spell != 2775 && ResourcePercent(spell) != 0; }
inline int32_t PercentMana(int64_t maximum, int percent) {
	if (maximum <= 0 || percent <= 0 || percent > 100) { return 0; }
	maximum = std::min<int64_t>(maximum, std::numeric_limits<int32_t>::max());
	return static_cast<int32_t>(std::max<int64_t>(1, maximum * percent / 100));
}
inline bool Harvest(uint16_t spell) {
	return spell == 3338 || spell == 13198 || spell == 13692 || spell == 16707 || spell == 27431;
}
inline bool RetiredAA(uint32_t ability) {
	return ability == 25 || ability == 252 || ability == 8300 || ability == 3521 || ability == 3522 || ability == 758;
}
inline bool SilentCasting(uint16_t spell) { return (spell >= 8054 && spell <= 8058) || spell == 27432; }
inline bool FixedDuration(uint16_t spell) {
	return SilentCasting(spell) || spell == 23528 || spell == 5939 || spell == 11033 || spell == 12802;
}
inline int BoundDuration(uint16_t spell, int duration) {
	if (!FixedDuration(spell) || duration == 0) { return duration; }
	return duration < 0 ? 1 : std::min(duration, SilentCasting(spell) ? 600 : 2);
}
inline int StrongestEndpoint(int base, int limit) {
	if (!limit) { return base; }
	return std::abs(int64_t(limit)) > std::abs(int64_t(base)) ? limit : base;
}
inline int ScaleFocus(int value, bool damage, bool bard, bool dot, bool absolute) {
	const int factor = damage && !absolute && !(bard && dot) ? 10 : 1;
	return static_cast<int>(std::clamp<int64_t>(int64_t(value) * factor,
		std::numeric_limits<int>::min(), std::numeric_limits<int>::max()));
}
inline bool AreaTarget(int type) { return type == 2 || type == 4 || type == 8 || type == 17 || type == 18; }
inline bool BroadenDamageTarget(int limit, int target, bool damage) {
	return damage && AreaTarget(target) && (limit == 5 || (limit < 0 && AreaTarget(-limit)));
}
}

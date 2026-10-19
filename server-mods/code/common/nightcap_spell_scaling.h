#pragma once
#include <algorithm>
#include <cstdint>
#include <limits>

namespace NightcapSpellScaling {
// 0.1% per point, truncating only the final bonus. Preserve signed damage and
// saturate exceptional values without overflowing intermediate multiplication.
inline int64_t HeroicValue(int64_t value, int heroic)
{
	const uint64_t points = std::max(heroic, 0);
	if (!value || !points) { return value; }
	const bool negative = value < 0;
	const uint64_t magnitude = negative ? uint64_t(-(value + 1)) + 1 : uint64_t(value);
	const uint64_t limit = uint64_t(std::numeric_limits<int64_t>::max()) + (negative ? 1 : 0);
	const uint64_t headroom = limit - magnitude;
	const uint64_t remainder = (magnitude % 1000) * points / 1000;
	if (remainder > headroom || magnitude / 1000 > (headroom - remainder) / points) {
		return negative ? std::numeric_limits<int64_t>::min() : std::numeric_limits<int64_t>::max();
	}
	const uint64_t result = magnitude + (magnitude / 1000) * points + remainder;
	if (negative && result == limit) { return std::numeric_limits<int64_t>::min(); }
	return negative ? -int64_t(result) : int64_t(result);
}
}

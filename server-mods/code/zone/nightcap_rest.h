#pragma once
#include <cstdint>

namespace NightcapRest {
// Preserve the zone's native floor and round its ten-percent bonus to the nearest point.
inline constexpr int64_t RecoveryFloor(int64_t pool, int seconds)
{
	const int64_t native = 6 * (pool / (seconds > 0 ? seconds : 180));
	return native + (native + 5) / 10;
}
}

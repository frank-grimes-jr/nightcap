#pragma once
#include <cstdint>

namespace Cairnwright {
inline constexpr uint8_t ClassId = 17;
inline constexpr uint16_t StrikeCairn = 44381;
inline constexpr uint16_t SoundTheSeam = 44382;

inline constexpr bool IsLearnedSpell(uint32_t spell_id)
{
	return spell_id == StrikeCairn || spell_id == SoundTheSeam;
}
}

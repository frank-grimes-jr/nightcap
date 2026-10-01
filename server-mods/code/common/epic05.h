#pragma once

#include <cstdint>

namespace Epic05 {
constexpr uint32_t Contract = 1;
constexpr uint16_t InvokeSpell = 42800;
constexpr uint16_t FirstEffect = 42801;
constexpr uint16_t LastEffect = 42805;
constexpr int32_t MaximumTicks = 3;

inline bool IsEffect(uint16_t spell_id)
{
	return spell_id >= FirstEffect && spell_id <= LastEffect;
}

inline int32_t BoundDuration(int32_t duration)
{
	// Preserve instantaneous effects; reject permanent/extended buff overrides.
	return duration == 0 ? 0 : (duration > 0 && duration < MaximumTicks ? duration : MaximumTicks);
}
}

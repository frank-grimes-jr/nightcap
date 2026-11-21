#pragma once
#include <cstdint>
#include <optional>

namespace Cairnwright {
inline constexpr uint8_t ClassId = 17;
inline constexpr uint16_t StrikeCairn = 44381;
inline constexpr uint16_t SoundTheSeam = 44382;
inline constexpr uint16_t SeamFracture = 44383;

inline constexpr bool IsLearnedSpell(uint32_t spell_id)
{
	return spell_id == StrikeCairn || spell_id == SoundTheSeam;
}

// Spell effects used by NPC service classes historically use the base class
// modulo 17. Keep that mapping for valid slots in the stock spell record.
inline constexpr std::optional<uint8_t> EffectLevel(
	uint32_t spell_id, uint8_t class_id, const uint8_t (&stock_levels)[16])
{
	// A secondary or tertiary Cairnwright casts the same level-one effects.
	if (IsLearnedSpell(spell_id) || spell_id == SeamFracture) { return uint8_t{1}; }
	if (class_id == ClassId) { return std::nullopt; }
	const auto stock_class = class_id % 17;
	if (!stock_class) { return std::nullopt; }
	return stock_levels[stock_class - 1];
}
}

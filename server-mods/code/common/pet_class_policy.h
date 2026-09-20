#pragma once
#include "pet_spell_catalog.h"
#include <algorithm>
#include <iterator>

namespace NightcapPetClasses {
inline bool Eligible(uint32_t spell_id, uint8_t level, uint8_t class_id, uint8_t primary)
{
	if (class_id < 1 || class_id > 16) { return false; }
	const auto spell = std::lower_bound(std::begin(Catalog), std::end(Catalog), spell_id,
		[](const Spell& row, uint32_t id) { return row.id < id; });
	if (spell == std::end(Catalog) || spell->id != spell_id) { return false; }
	bool class_spell = false;
	for (const auto minimum : spell->levels) {
		if (minimum > 0 && minimum < 255) { class_spell = true; break; }
	}
	const auto minimum = spell->levels[class_id - 1];
	return class_spell ? (minimum > 0 && minimum < 255 && minimum <= level) : class_id == primary;
}

// Return one held class for this summon. Shared spells use held-slot order among
// eligible ORIGINAL levels. Widened live spell columns must never select a slot.
inline uint8_t Resolve(uint32_t spell_id, uint8_t level, const std::array<uint8_t, 3>& classes)
{
	const auto spell = std::lower_bound(std::begin(Catalog), std::end(Catalog), spell_id,
		[](const Spell& row, uint32_t id) { return row.id < id; });
	if (spell == std::end(Catalog) || spell->id != spell_id) { return 0; }
	bool class_spell = false;
	for (const auto minimum : spell->levels) {
		if (minimum > 0 && minimum < 255) { class_spell = true; break; }
	}
	// Original item/AA-only summons have no spell-list class. Preserve their
	// primary-class slot; they cannot create a fourth pet or another of that class.
	if (!class_spell) { return classes[0] >= 1 && classes[0] <= 16 ? classes[0] : 0; }
	for (const auto class_id : classes) {
		if (class_id < 1 || class_id > 16) { continue; }
		const auto minimum = spell->levels[class_id - 1];
		if (minimum > 0 && minimum < 255 && minimum <= level) { return class_id; }
	}
	return 0;
}
}

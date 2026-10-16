#pragma once

#include <cstdint>

namespace NightcapDivineSummons {

// Paladin/Cleric item-summoning hammer families, including existing quality tiers.
// Pet spells (Unswerving/Celestial Hammer) and other classes' summons are separate.
constexpr bool IsWeapon(uint32_t id)
{
	if (id >= 800000) { return false; }
	switch (id % 200000) {
		case 6307:  // Wrath
		case 6309:  // Striking
		case 6313:  // Requital
		case 5800:  // Judgment
		case 15996: // Divinity
		case 5798:  // Souls
		case 29365: // Damnation
		case 77517: // Reproach
		case 90491: // Reverence
		case 90492: // Reverence II
		case 90493: // Reverence III
			return true;
		default:
			return false;
	}
}

template <typename Item>
void ApplyMerchantPolicy(Item &item)
{
	if (IsWeapon(item.ID)) {
		// Apply after FreeTrade: its former-NO-DROP payout must not turn an
		// unlimited summon into platinum. Preserve the original SQL flags.
		item.Price = 0;
		item.FixedSellPrice = 0;
	}
}

} // namespace NightcapDivineSummons

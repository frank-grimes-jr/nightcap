#pragma once
#include <cstdint>
#include <string>

namespace NightcapPaladinGrip {
inline constexpr const char *Key = "nightcap_paladin_grip";
// Existing client spell token makes the item clickable. Both packet paths are
// intercepted server-side; this spell is never cast by the weapon.
inline constexpr int ClickSpell = 288; // Minor Shielding: existing self-target client spell

inline bool Supported(uint32_t id)
{
	if (id == 10099 || id == 810099) { return true; } // Fiery Defender / Forgemaster Ascended
	if (id >= 800000) { return false; }
	const auto base = id % 200000;
	return base == 5504 || base == 11050;
}

inline bool PlainMetadata(const std::string &data)
{
	// Native multi-key custom data does not reliably round-trip. Never add a
	// second key to another system's metadata or silently normalize its data.
	return data.empty() || data == std::string(Key) + "^1^";
}

template <typename Item>
std::string UpdateSQL(uint32_t character, int16_t slot, const Item &item, bool one_handed)
{
	const auto before = item.GetCustomDataString();
	if (!Supported(item.GetID()) || !PlainMetadata(before)) { return {}; }
	const auto after = one_handed ? std::string(Key) + "^1^" : std::string{};
	if (before == after) { return {}; }
	// Only fixed, validated metadata strings and decimal integers enter SQL.
	// One InnoDB UPDATE is atomic; no delete/summon or read-then-write window.
	std::string sql = "UPDATE inventory SET custom_data='" + after + "' WHERE character_id=" + std::to_string(character) +
		" AND slot_id=" + std::to_string(slot) + " AND item_id=" + std::to_string(item.GetID()) +
		" AND guid=" + std::to_string(uint32_t(item.GetSerialNumber())) +
		" AND charges=" + std::to_string(item.GetCharges() < 0 ? 32767 : item.GetCharges()) +
		" AND color=" + std::to_string(item.GetColor()) +
		" AND instnodrop=" + std::to_string(item.IsAttuned() ? 1 : 0) +
		" AND BINARY COALESCE(custom_data,'')=BINARY '" + before + "'" +
		" AND ornament_icon=" + std::to_string(item.GetOrnamentationIcon()) +
		" AND ornament_idfile=" + std::to_string(item.GetOrnamentationIDFile()) +
		" AND ornament_hero_model=" + std::to_string(item.GetOrnamentHeroModel());
	const char *augments[] = {"augment_one", "augment_two", "augment_three", "augment_four", "augment_five", "augment_six"};
	for (uint8_t i = 0; i < 6; ++i) {
		sql += " AND " + std::string(augments[i]) + "=" + std::to_string(item.GetAugmentItemID(i));
	}
	return sql;
}
}

#pragma once
#include <cstdint>
#include <string>

namespace NightcapPaladinGrip {
inline constexpr const char *Key = "nightcap_paladin_grip";
// Existing client spell token makes the item clickable. Both packet paths are
// intercepted server-side; this spell is never cast by the weapon.
inline constexpr int ClickSpell = 288; // Minor Shielding: existing self-target client spell

struct Profile {
	uint32_t id;
	uint32_t two_hand_damage;
	uint8_t two_hand_delay;
	uint32_t one_hand_damage;
	uint8_t one_hand_delay;
	int8_t accuracy;
	uint8_t shield_block;
};

// October 28 assessed progression. Absolute owned-instance values; SQL preimages
// remain separately pinned by release preflight. Shield AAs can favor 1HS damage.
inline constexpr Profile Profiles[] = {
	{5504,   23, 45, 13, 30,  4, 0},
	{205504, 31, 45, 18, 30,  6, 0},
	{405504, 38, 45, 22, 30,  8, 0},
	{605504, 46, 45, 26, 30, 10, 0},
	{11050,  33, 44, 15, 30,  5, 0},
	{211050, 44, 44, 20, 30,  8, 0},
	{411050, 55, 44, 25, 30, 12, 1},
	{611050, 66, 44, 30, 30, 15, 1},
	{10099,  64, 40, 32, 30, 20, 2},
	{810099, 72, 40, 36, 30, 25, 3},
};

inline const Profile *FindProfile(uint32_t id)
{
	for (const auto &profile : Profiles) {
		if (profile.id == id) { return &profile; }
	}
	return nullptr;
}

inline bool Supported(uint32_t id) { return FindProfile(id) != nullptr; }

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

template <typename Item>
std::string AscendSQL(uint32_t character, int16_t slot, const Item &item)
{
	if (item.GetID() != 10099 || !PlainMetadata(item.GetCustomDataString())) { return {}; }
	// Reuse the exact instance preimage, but change only identity. Grip, charges,
	// augments, binding, ornaments and GUID stay in the same inventory row.
	const auto toggle = UpdateSQL(character, slot, item, item.GetCustomDataString().empty());
	const auto where = toggle.find(" WHERE ");
	if (where == std::string::npos) { return {}; }
	return "UPDATE inventory SET item_id=810099" + toggle.substr(where);
}
}

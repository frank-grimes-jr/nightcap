#ifndef NIGHTCAP_EQUIPMENT_RACE_POLICY_H
#define NIGHTCAP_EQUIPMENT_RACE_POLICY_H

namespace NightcapEquipment {

template <typename Item>
void ApplyRacePolicy(Item &item)
{
	// Project only effective loaded definitions. SQL retains the original masks.
	// No playable class/race is a non-player sentinel, not a racial exclusion.
	constexpr unsigned player_mask = 0xffffu;
	constexpr unsigned equipment_slots = 0x7fffffu; // charm through ammo, 0..22
	if (item.ItemClass == 0 && (item.Classes & player_mask) &&
		(item.Races & player_mask) &&
		((item.Slots & equipment_slots) || item.AugType)) {
		item.Races = player_mask;
	}
}

} // namespace NightcapEquipment

#endif

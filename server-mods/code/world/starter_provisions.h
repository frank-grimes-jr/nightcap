#pragma once

// Called only while creating a character, before StoreCharacter persists it.
// Fail closed if item caches were not regenerated with the matching content.
inline bool NightcapStartingItems(SharedDatabase &content, PlayerProfile_Struct &profile, EQ::InventoryProfile &inventory)
{
	if (profile.class_ < 1 || profile.class_ > 16) { return false; }
	// Preserve future race/deity-specific equipped rewards: only the audited
	// default weapons may be replaced, and the baseline chest slot is empty.
	if (inventory.GetItem(EQ::invslot::slotChest)) { return false; }
	const auto old_weapon = inventory.GetItem(EQ::invslot::slotPrimary);
	if (old_weapon && !old_weapon->GetItem()) { return false; }
	if (old_weapon && old_weapon->GetItem()->ID != 9997 && old_weapon->GetItem()->ID != 9998 &&
		old_weapon->GetItem()->ID != 9999 && old_weapon->GetItem()->ID != 55623) { return false; }
	const auto robe_id = 998599u + profile.class_;
	const auto weapon_id = 998619u + profile.class_;
	std::unique_ptr<EQ::ItemInstance> robe(content.CreateItem(robe_id, 1));
	std::unique_ptr<EQ::ItemInstance> weapon(content.CreateItem(weapon_id, 1));
	if (!robe || !weapon || !robe->GetItem() || !weapon->GetItem()) { return false; }
	const auto class_bit = 1u << (profile.class_ - 1);
	if (!(robe->GetItem()->Classes & class_bit) || !(weapon->GetItem()->Classes & class_bit) ||
		robe->GetItem()->AC != 10 || !weapon->GetItem()->Damage) { return false; }
	// Equip the robe and replace the rusty weapon only in this unsaved profile.
	return inventory.PutItem(EQ::invslot::slotChest, *robe) == EQ::invslot::slotChest &&
		inventory.PutItem(EQ::invslot::slotPrimary, *weapon) == EQ::invslot::slotPrimary;
}

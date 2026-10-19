#pragma once

#include "common/item_instance.h"
#include "common/repositories/inventory_repository.h"
#include <array>
#include <memory>
#include <map>

namespace NightcapPetArmor {
// Keep the first eight protocol indices and persisted native slot IDs stable.
// Capacity counts occupied locations, not the number of available locations.
inline constexpr std::array<int16, 22> Slots = {
	EQ::invslot::slotHead, EQ::invslot::slotChest, EQ::invslot::slotArms,
	EQ::invslot::slotWrist1, EQ::invslot::slotHands, EQ::invslot::slotLegs,
	EQ::invslot::slotFeet, EQ::invslot::slotWaist,
	EQ::invslot::slotPrimary, EQ::invslot::slotSecondary,
	EQ::invslot::slotEar1, EQ::invslot::slotEar2, EQ::invslot::slotNeck,
	EQ::invslot::slotFace, EQ::invslot::slotShoulders, EQ::invslot::slotBack,
	EQ::invslot::slotWrist2, EQ::invslot::slotFinger1, EQ::invslot::slotFinger2,
	EQ::invslot::slotRange, EQ::invslot::slotCharm, EQ::invslot::slotPowerSource
};
inline constexpr std::array<const char *, Slots.size()> Names = {
	"Head", "Chest", "Arms", "Wrist 1", "Hands", "Legs", "Feet", "Waist",
	"Primary", "Secondary", "Ear 1", "Ear 2", "Neck", "Face", "Shoulders", "Back",
	"Wrist 2", "Finger 1", "Finger 2", "Range", "Charm", "Power source"
};
inline constexpr unsigned Capacity(uint8 pet_class) { return pet_class == 13 ? 15 : 8; }
struct Item {
	InventoryRepository::Inventory saved;
	std::shared_ptr<EQ::ItemInstance> instance;
};
using Equipment = std::array<Item, Slots.size()>;
using Collection = std::map<uint8, Equipment>;

// Inventory-compatible fields are moved with INSERT ... SELECT; item IDs alone
// are never used to refund equipment. Load creates the same instance fields as
// the ordinary character inventory loader.
bool Load(uint32 character_id, Collection &items);
bool Transfer(uint32 character_id, uint8 pet_class, uint8 index, bool equip,
	const EQ::ItemInstance *cursor, const Item &stored, Item &result);
bool Allowed(const EQ::ItemInstance *item, uint8 index);
bool CanEquip(const Equipment &items, uint8 pet_class, uint8 index, const EQ::ItemInstance *item);
}

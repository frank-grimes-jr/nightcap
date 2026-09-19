#pragma once

#include "common/item_instance.h"
#include "common/repositories/inventory_repository.h"
#include <array>
#include <memory>
#include <map>

namespace NightcapPetArmor {
// One wrist slot, no weapons/jewelry, and a hard eight-slot bound.
inline constexpr std::array<int16, 8> Slots = {
	EQ::invslot::slotHead, EQ::invslot::slotChest, EQ::invslot::slotArms,
	EQ::invslot::slotWrist1, EQ::invslot::slotHands, EQ::invslot::slotLegs,
	EQ::invslot::slotFeet, EQ::invslot::slotWaist
};
inline constexpr std::array<const char *, 8> Names = {
	"Head", "Chest", "Arms", "Wrist", "Hands", "Legs", "Feet", "Waist"
};
struct Item {
	InventoryRepository::Inventory saved;
	std::shared_ptr<EQ::ItemInstance> instance;
};
using Equipment = std::array<Item, 8>;
using Collection = std::map<uint8, Equipment>;

// Inventory-compatible fields are moved with INSERT ... SELECT; item IDs alone
// are never used to refund equipment. Load creates the same instance fields as
// the ordinary character inventory loader.
bool Load(uint32 character_id, Collection &items);
bool Transfer(uint32 character_id, uint8 pet_class, uint8 index, bool equip,
	const EQ::ItemInstance *cursor, const Item &stored, Item &result);
bool Allowed(const EQ::ItemInstance *item, uint8 index);
}

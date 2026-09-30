#pragma once

#include "common/types.h"

#include <list>
#include <string>
#include <tuple>

struct LootItem {
	uint32      item_id{};
	int16       equip_slot{};
	uint16      charges{};
	uint16      lootslot{};
	uint32      aug_1{};
	uint32      aug_2{};
	uint32      aug_3{};
	uint32      aug_4{};
	uint32      aug_5{};
	uint32      aug_6{};
	bool        attuned{};
	std::string custom_data;
	uint32      ornamenticon{};
	uint32      ornamentidfile{};
	uint32      ornament_hero_model{};
	uint16      trivial_min_level{};
	uint16      trivial_max_level{};
	uint16      npc_min_level{};
	uint16      npc_max_level{};
	uint32      lootdrop_id{}; // required for zone state referencing
	std::string advanced_loot_id; // physical drop receipt, retained in NPC corpse saved state
};

typedef std::list<LootItem*> LootItems;

inline bool SamePhysicalLoot(const LootItem &a, const LootItem &b)
{
	// A classic loot-window refresh can renumber lootslot. All physical item
	// fields, including the durable receipt ID, must still match the selection.
	return std::tie(a.item_id,a.equip_slot,a.charges,a.aug_1,a.aug_2,a.aug_3,a.aug_4,a.aug_5,a.aug_6,a.attuned,
		a.custom_data,a.ornamenticon,a.ornamentidfile,a.ornament_hero_model,a.trivial_min_level,a.trivial_max_level,
		a.npc_min_level,a.npc_max_level,a.lootdrop_id,a.advanced_loot_id) ==
		std::tie(b.item_id,b.equip_slot,b.charges,b.aug_1,b.aug_2,b.aug_3,b.aug_4,b.aug_5,b.aug_6,b.attuned,
		b.custom_data,b.ornamenticon,b.ornamentidfile,b.ornament_hero_model,b.trivial_min_level,b.trivial_max_level,
		b.npc_min_level,b.npc_max_level,b.lootdrop_id,b.advanced_loot_id);
}


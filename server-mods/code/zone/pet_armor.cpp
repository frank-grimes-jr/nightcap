#include "zone/pet_armor.h"
#include "zone/zonedb.h"
#include "common/strings.h"
#include <algorithm>
#include <limits>

extern ZoneDatabase database;

namespace NightcapPetArmor {
namespace {
using Row = InventoryRepository::Inventory;

Row ReadRow(MySQLRequestRow r)
{
	Row e{};
	auto number = [&](int i) { return r[i] ? strtoull(r[i], nullptr, 10) : 0; };
	e.character_id = number(0); e.slot_id = number(1); e.item_id = number(2);
	e.charges = number(3); e.color = number(4);
	e.augment_one = number(5); e.augment_two = number(6); e.augment_three = number(7);
	e.augment_four = number(8); e.augment_five = number(9); e.augment_six = number(10);
	e.instnodrop = number(11); e.custom_data = r[12] ? r[12] : "";
	e.ornament_icon = number(13); e.ornament_idfile = number(14);
	e.ornament_hero_model = r[15] ? atoi(r[15]) : 0; e.guid = number(16);
	return e;
}

Row FromInstance(uint32 character_id, int16 slot, const EQ::ItemInstance &inst)
{
	Row e{};
	e.character_id = character_id; e.slot_id = slot; e.item_id = inst.GetID();
	e.charges = inst.GetCharges() < 0 ? std::numeric_limits<int16>::max() : inst.GetCharges();
	e.color = inst.GetColor();
	e.augment_one = inst.GetAugmentItemID(0); e.augment_two = inst.GetAugmentItemID(1);
	e.augment_three = inst.GetAugmentItemID(2); e.augment_four = inst.GetAugmentItemID(3);
	e.augment_five = inst.GetAugmentItemID(4); e.augment_six = inst.GetAugmentItemID(5);
	e.instnodrop = inst.IsAttuned(); e.custom_data = inst.GetCustomDataString();
	e.ornament_icon = inst.GetOrnamentationIcon(); e.ornament_idfile = inst.GetOrnamentationIDFile();
	e.ornament_hero_model = inst.GetOrnamentHeroModel(); e.guid = inst.GetSerialNumber();
	return e;
}

std::string Predicate(const Row &e)
{
	// Hex literals preserve custom data without depending on SQL escape mode.
	std::string hex;
	for (unsigned char c : e.custom_data) {
		hex += "0123456789abcdef"[c >> 4]; hex += "0123456789abcdef"[c & 15];
	}
	const std::vector<std::string> values = {
		std::to_string(e.character_id), std::to_string(e.slot_id), std::to_string(e.item_id),
		std::to_string(e.charges), std::to_string(e.color), std::to_string(e.augment_one),
		std::to_string(e.augment_two), std::to_string(e.augment_three), std::to_string(e.augment_four),
		std::to_string(e.augment_five), std::to_string(e.augment_six), std::to_string(e.instnodrop),
		"X'" + hex + "'", std::to_string(e.ornament_icon), std::to_string(e.ornament_idfile),
		std::to_string(e.ornament_hero_model), std::to_string(e.guid)
	};
	const auto columns = InventoryRepository::Columns();
	std::vector<std::string> parts;
	for (size_t i = 0; i < columns.size(); ++i) {
		parts.push_back((i == 12 ? "BINARY COALESCE(`custom_data`,'')" : "`" + columns[i] + "`") + "=" + values[i]);
	}
	return Strings::Implode(" AND ", parts);
}

bool SchemaReady()
{
	for (const auto &table : {std::string("inventory"), std::string("character_pet_armor")}) {
		auto columns = database.QueryDatabase("SHOW COLUMNS FROM " + table, false);
		auto expected = InventoryRepository::Columns();
		if (table == "character_pet_armor") { expected.push_back("pet_class"); }
		if (!columns.Success() || columns.RowCount() != expected.size()) { return false; }
		size_t i = 0;
		for (auto row : columns) { if (!row[0] || expected[i++] != row[0]) { return false; } }
	}
	auto result = database.QueryDatabase(std::string(
		"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() "
		"AND TABLE_NAME IN ('inventory','character_pet_armor') AND ENGINE='InnoDB'"), false);
	if (!result.Success() || result.RowCount() != 1 || Strings::ToUnsignedInt(result.begin()[0]) != 2) { return false; }
	auto triggers = database.QueryDatabase(std::string(
		"SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() "
		"AND EVENT_OBJECT_TABLE IN ('inventory','character_pet_armor')"), false);
	return triggers.Success() && triggers.RowCount() == 1 && Strings::ToUnsignedInt(triggers.begin()[0]) == 0;
}
}

bool Allowed(const EQ::ItemInstance *inst, uint8 index)
{
	if (!inst || !inst->GetItem() || index >= Slots.size()) { return false; }
	const auto item = inst->GetItem();
	// Evolving/scaling objects have state in other tables. Refuse them instead of
	// degrading that state. Ordinary augment IDs and all inventory fields persist.
	if (!item->IsClassCommon() || inst->IsStackable() || inst->IsEvolving() || inst->IsScaling() ||
		!item->NoRent || item->NoPet || item->IsQuestItem() || !(item->Slots & (1u << Slots[index]))) { return false; }
	for (int i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) {
		const auto aug = inst->GetAugment(i);
		if (aug && (!aug->GetItem()->NoRent || aug->IsEvolving() || aug->IsScaling())) { return false; }
	}
	return true;
}

bool CanEquip(const Equipment &items, uint8 pet_class, uint8 index, const EQ::ItemInstance *inst)
{
	if (pet_class < 1 || pet_class > 16 || !Allowed(inst, index) || items[index].instance) { return false; }
	unsigned used = 0;
	for (size_t i = 0; i < items.size(); ++i) {
		const auto other = items[i].instance.get();
		if (!other) { continue; }
		++used;
		if ((Slots[index] == EQ::invslot::slotPrimary && inst->GetItem()->IsType2HWeapon() &&
			Slots[i] == EQ::invslot::slotSecondary) ||
			(Slots[index] == EQ::invslot::slotSecondary && Slots[i] == EQ::invslot::slotPrimary &&
			other->GetItem()->IsType2HWeapon())) { return false; }
	}
	return used < Capacity(pet_class);
}

bool Load(uint32 character_id, Collection &items)
{
	if (!character_id || !SchemaReady()) { return false; }
	auto rows = database.QueryDatabase(fmt::format("SELECT {},pet_class FROM character_pet_armor WHERE character_id={}",
		InventoryRepository::SelectColumnsRaw(), character_id), false);
	if (!rows.Success() || rows.RowCount() > 16 * Slots.size()) { return false; }
	Collection loaded;
	const auto timestamps = database.GetItemRecastTimestamps(character_id);
	for (auto r : rows) {
		const Row row = ReadRow(r);
		const uint32 pet_class = r[17] ? Strings::ToUnsignedInt(r[17]) : 0;
		auto slot = std::find(Slots.begin(), Slots.end(), row.slot_id);
		if (pet_class < 1 || pet_class > 16 || slot == Slots.end()) { return false; }
		const uint8 index = std::distance(Slots.begin(), slot);
		if (loaded[pet_class][index].instance) { return false; }
		// Saved GUID is a database preimage only. CreateItem allocates a fresh
		// session serial, as it does for ordinary inventory loading.
		std::shared_ptr<EQ::ItemInstance> inst(database.CreateItem(row.item_id,
			row.charges == std::numeric_limits<int16>::max() ? -1 : row.charges,
			row.augment_one, row.augment_two, row.augment_three, row.augment_four, row.augment_five, row.augment_six,
			row.instnodrop, row.custom_data, row.ornament_icon, row.ornament_idfile, row.ornament_hero_model));
		if (!CanEquip(loaded[pet_class], pet_class, index, inst.get())) { return false; }
		inst->SetCharges(row.charges == std::numeric_limits<int16>::max() ? -1 : row.charges);
		const std::array<uint32, 6> augments = {row.augment_one, row.augment_two, row.augment_three,
			row.augment_four, row.augment_five, row.augment_six};
		for (size_t i = 0; i < augments.size(); ++i) {
			if (inst->GetAugmentItemID(i) != augments[i]) { return false; }
		}
		inst->SetColor(row.color);
		const auto item = inst->GetItem();
		const auto recast = item->RecastType == RECAST_TYPE_UNLINKED_ITEM ? item->ID : item->RecastType;
		if (timestamps.count(recast)) { inst->SetRecastTimestamp(timestamps.at(recast)); }
		loaded[pet_class][index] = {row, std::move(inst)};
	}
	items.swap(loaded);
	return true;
}

bool Transfer(uint32 character_id, uint8 pet_class, uint8 index, bool equip,
	const EQ::ItemInstance *cursor, const Item &stored, Item &result)
{
	if (!character_id || pet_class < 1 || pet_class > 16 || index >= Slots.size() ||
		(equip ? (!Allowed(cursor, index) || stored.instance) : (!stored.instance || cursor))) { return false; }
	if (!SchemaReady()) { return false; }
	auto active = database.QueryDatabase(std::string("SELECT @@in_transaction"), false);
	if (!active.Success() || active.RowCount() != 1 || Strings::ToUnsignedInt(active.begin()[0])) { return false; }
	Row source = equip ? FromInstance(character_id, EQ::invslot::slotCursor, *cursor) : stored.saved;
	if (source.character_id != character_id || (!equip && source.slot_id != Slots[index])) { return false; }
	// Prepare memory before committing. No gameplay state changes before COMMIT.
	Item moved = equip ? Item{source, std::shared_ptr<EQ::ItemInstance>(cursor->Clone())} : stored;
	moved.saved.slot_id = equip ? Slots[index] : EQ::invslot::slotCursor;
	moved.saved.guid = moved.instance->GetSerialNumber();
	const std::string source_table = equip ? "inventory" : "character_pet_armor";
	const std::string target_table = equip ? "character_pet_armor" : "inventory";
	const std::string extra = " AND pet_class=" + std::to_string(pet_class);
	const std::string source_where = Predicate(source) + (equip ? "" : extra);
	const std::string cursor_where = fmt::format("character_id={} AND (slot_id={} OR slot_id BETWEEN {} AND {})",
		character_id, EQ::invslot::slotCursor, EQ::invbag::CURSOR_BAG_BEGIN, EQ::invbag::CURSOR_BAG_END);
	if (!database.QueryDatabase(std::string("START TRANSACTION"), false).Success()) { return false; }
	auto failed = [&]() { database.QueryDatabase(std::string("ROLLBACK"), false); return false; };
	// Lock the entire per-class equipment range as well as the cursor queue.
	// Capacity and hand exclusions must remain authoritative across concurrent
	// transfers; locking only the destination would allow two final-budget equips.
	auto cursor_rows = database.QueryDatabase("SELECT slot_id FROM inventory WHERE " + cursor_where + " FOR UPDATE", false);
	if (!cursor_rows.Success() || cursor_rows.RowCount() != (equip ? 1u : 0u)) { return failed(); }
	auto armor_rows = database.QueryDatabase(fmt::format(
		"SELECT slot_id,item_id FROM character_pet_armor WHERE character_id={} AND pet_class={} FOR UPDATE",
		character_id, pet_class), false);
	if (!armor_rows.Success() || (equip && armor_rows.RowCount() >= Capacity(pet_class))) { return failed(); }
	unsigned occupied = 0;
	for (auto row : armor_rows) {
		const int16 slot = row[0] ? atoi(row[0]) : -1;
		occupied += slot == Slots[index];
		if (!equip) { continue; } // Removal remains a recovery path.
		const auto other = database.GetItem(row[1] ? Strings::ToUnsignedInt(row[1]) : 0);
		if (!other || std::find(Slots.begin(), Slots.end(), slot) == Slots.end()) { return failed(); }
		if ((Slots[index] == EQ::invslot::slotPrimary && cursor->GetItem()->IsType2HWeapon() &&
			slot == EQ::invslot::slotSecondary) ||
			(Slots[index] == EQ::invslot::slotSecondary && slot == EQ::invslot::slotPrimary &&
			other->IsType2HWeapon())) { return failed(); }
	}
	if (occupied != (equip ? 0u : 1u)) { return failed(); }
	auto matched = database.QueryDatabase("SELECT slot_id FROM " + source_table + " WHERE " + source_where + " FOR UPDATE", false);
	if (!matched.Success() || matched.RowCount() != 1) { return failed(); }
	auto columns = InventoryRepository::Columns();
	auto select = columns;
	select[1] = std::to_string(moved.saved.slot_id);
	select[16] = std::to_string(moved.saved.guid);
	if (equip) { columns.push_back("pet_class"); select.push_back(std::to_string(pet_class)); }
	auto inserted = database.QueryDatabase("INSERT INTO " + target_table + " (" + Strings::Implode(",", columns) +
		") SELECT " + Strings::Implode(",", select) + " FROM " + source_table + " WHERE " + source_where, false);
	if (!inserted.Success() || inserted.RowsAffected() != 1) { return failed(); }
	auto removed = database.QueryDatabase("DELETE FROM " + source_table + " WHERE " + source_where, false);
	if (!removed.Success() || removed.RowsAffected() != 1) { return failed(); }
	if (!database.QueryDatabase(std::string("COMMIT"), false).Success()) { return failed(); }
	result = std::move(moved);
	return true;
}
}

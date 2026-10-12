#include "zone/advanced_loot_inventory.h"
#include "zone/client.h"
#include "zone/zonedb.h"
#include "common/evolving_items.h"
#include "common/repositories/inventory_repository.h"
#include "common/util/uuid.h"
#include "common/zone_hunt_catalog.h"
#include "common/zone_hunt_policy.h"
#include "common/item_upgrade_policy.h"
#include <algorithm>
#include <limits>
#include <memory>
#include <set>

extern ZoneDatabase database;

namespace NightcapLoot {
namespace {
using InventoryRow = InventoryRepository::Inventory;
using Plan = std::map<int16, std::unique_ptr<EQ::ItemInstance>>;

class RollbackGuard {
	bool active_ = true;
public:
	~RollbackGuard() { if (active_) { try { database.QueryDatabase(std::string("ROLLBACK"), false); } catch (...) {} } }
	void Release() { active_ = false; }
};

InventoryRow FromItem(uint32 character, int16 slot, const EQ::ItemInstance &item)
{
	InventoryRow r{};
	r.character_id = character; r.slot_id = slot; r.item_id = item.GetID();
	r.charges = item.GetCharges() < 0 ? std::numeric_limits<int16>::max() : item.GetCharges();
	r.color = item.GetColor(); r.instnodrop = item.IsAttuned();
	r.augment_one = item.GetAugmentItemID(0); r.augment_two = item.GetAugmentItemID(1);
	r.augment_three = item.GetAugmentItemID(2); r.augment_four = item.GetAugmentItemID(3);
	r.augment_five = item.GetAugmentItemID(4); r.augment_six = item.GetAugmentItemID(5);
	r.custom_data = item.GetCustomDataString(); r.ornament_icon = item.GetOrnamentationIcon();
	r.ornament_idfile = item.GetOrnamentationIDFile(); r.ornament_hero_model = item.GetOrnamentHeroModel();
	r.guid = item.GetSerialNumber();
	return r;
}

InventoryRow ReadRow(MySQLRequestRow row)
{
	InventoryRow r{};
	auto number = [&](int i) { return row[i] ? strtoull(row[i], nullptr, 10) : 0; };
	r.character_id = number(0); r.slot_id = number(1); r.item_id = number(2); r.charges = number(3); r.color = number(4);
	r.augment_one = number(5); r.augment_two = number(6); r.augment_three = number(7);
	r.augment_four = number(8); r.augment_five = number(9); r.augment_six = number(10); r.instnodrop = number(11);
	r.custom_data = row[12] ? row[12] : ""; r.ornament_icon = number(13); r.ornament_idfile = number(14);
	r.ornament_hero_model = row[15] ? atoi(row[15]) : 0; r.guid = number(16);
	return r;
}

std::vector<std::string> Values(const InventoryRow &r)
{
	return {std::to_string(r.character_id), std::to_string(r.slot_id), std::to_string(r.item_id),
		std::to_string(r.charges), std::to_string(r.color), std::to_string(r.augment_one), std::to_string(r.augment_two),
		std::to_string(r.augment_three), std::to_string(r.augment_four), std::to_string(r.augment_five), std::to_string(r.augment_six),
		std::to_string(r.instnodrop), "X'" + Hex(r.custom_data) + "'", std::to_string(r.ornament_icon),
		std::to_string(r.ornament_idfile), std::to_string(r.ornament_hero_model), std::to_string(r.guid)};
}

bool SameItem(InventoryRow a, InventoryRow b, bool compare_charges = true)
{
	// Runtime serials are regenerated at login. The locked database row provides
	// the saved GUID preimage; compare every other inventory field to memory.
	a.guid = b.guid = 0;
	if (!compare_charges) { a.charges = b.charges = 0; }
	return Values(a) == Values(b);
}

bool BuildPlan(Client *c, const EQ::ItemInstance &source, Plan &plan)
{
	auto &inventory = c->GetInv();
	std::vector<int16> slots;
	for (int16 slot = EQ::invslot::GENERAL_BEGIN; slot <= EQ::invslot::GENERAL_END; ++slot) {
		if (!(inventory.GetLookup()->PossessionsBitmask & (uint64{1} << slot))) { continue; }
		slots.push_back(slot);
		const auto bag = inventory.GetItem(slot);
		if (!bag || !bag->IsClassBag()) { continue; }
		for (uint8 index = 0; index < bag->GetItem()->BagSlots && index < EQ::invbag::SLOT_COUNT; ++index) {
			slots.push_back(EQ::InventoryProfile::CalcSlotId(slot, index));
		}
	}
	const bool stackable = source.IsStackable();
	int remaining = stackable ? source.GetCharges() : 1;
	if (remaining <= 0 || (stackable && source.GetItem()->StackSize <= 0)) { return false; }
	if (stackable) {
		for (int16 slot : slots) {
			const auto owned = inventory.GetItem(slot);
			if (!owned || !owned->IsStackable() || owned->GetCharges() <= 0 || owned->GetCharges() >= owned->GetItem()->StackSize ||
				!SameItem(FromItem(c->CharacterID(), slot, *owned), FromItem(c->CharacterID(), slot, source), false)) { continue; }
			const int amount = std::min(remaining, owned->GetItem()->StackSize - owned->GetCharges());
			auto next = std::unique_ptr<EQ::ItemInstance>(owned->Clone());
			next->SetCharges(owned->GetCharges() + amount); plan.emplace(slot, std::move(next));
			remaining -= amount;
			if (!remaining) { return true; }
		}
	}
	for (int16 slot : slots) {
		if (inventory.GetItem(slot) || plan.count(slot)) { continue; }
		if (slot > EQ::invslot::GENERAL_END) {
			const auto bag = inventory.GetItem(EQ::InventoryProfile::CalcSlotId(slot));
			if (!bag || !EQ::InventoryProfile::CanItemFitInContainer(source.GetItem(), bag->GetItem())) { continue; }
		}
		auto next = std::unique_ptr<EQ::ItemInstance>(source.Clone());
		const int amount = stackable ? std::min<int>(remaining, source.GetItem()->StackSize) : 1;
		if (stackable) {
			next->SetCharges(amount);
			const EQ::ItemInstance serial_source(source.GetItem(), amount);
			next->SetSerialNumber(serial_source.GetSerialNumber());
		}
		plan.emplace(slot, std::move(next));
		if (source.IsClassBag()) {
			for (uint8 i = 0; i < EQ::invbag::SLOT_COUNT; ++i) {
				const auto child = source.GetItem(i);
				if (!child) { continue; }
				if (i >= source.GetItem()->BagSlots || child->IsClassBag()) { return false; }
				plan.emplace(EQ::InventoryProfile::CalcSlotId(slot, i), std::unique_ptr<EQ::ItemInstance>(child->Clone()));
			}
		}
		remaining -= amount;
		if (!remaining) { return true; }
	}
	return false;
}

bool BuildCursorPlan(Client *c, const EQ::ItemInstance &source, Plan &plan)
{
	// Classic manual clicks retain cursor pickup. Never overwrite or extend an
	// occupied cursor queue; automatic advanced loot remains inventory-only.
	plan.clear();
	if (!c->GetInv().CursorEmpty() || !(c->GetInv().GetLookup()->PossessionsBitmask & (uint64{1} << EQ::invslot::slotCursor))) { return false; }
	plan.emplace(EQ::invslot::slotCursor, std::unique_ptr<EQ::ItemInstance>(source.Clone()));
	if (source.IsClassBag()) {
		for (uint8 i = 0; i < EQ::invbag::SLOT_COUNT; ++i) {
			const auto child = source.GetItem(i);
			if (!child) { continue; }
			if (i >= source.GetItem()->BagSlots || child->IsClassBag()) { return false; }
			plan.emplace(EQ::InventoryProfile::CalcSlotId(EQ::invslot::slotCursor, i), std::unique_ptr<EQ::ItemInstance>(child->Clone()));
		}
	}
	return true;
}

bool TransactionTablesReady()
{
	const auto expected = InventoryRepository::Columns();
	auto columns = database.QueryDatabase(std::string("SHOW COLUMNS FROM inventory"), false);
	if (!columns.Success() || columns.RowCount() != expected.size()) { return false; }
	size_t index = 0;
	for (auto row : columns) { if (!row[0] || expected[index++] != row[0]) { return false; } }
	auto tables = database.QueryDatabase(std::string(
		"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND ENGINE='InnoDB' "
		"AND TABLE_NAME IN ('inventory','character_advloot_claims','character_evolving_items')"), false);
	if (!tables.Success() || tables.RowCount() != 1 || !tables.begin()[0] || atoi(tables.begin()[0]) != 3) { return false; }
	auto triggers = database.QueryDatabase(std::string(
		"SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() "
		"AND EVENT_OBJECT_TABLE IN ('inventory','character_advloot_claims','character_evolving_items')"), false);
	return triggers.Success() && triggers.RowCount() == 1 && triggers.begin()[0] && atoi(triggers.begin()[0]) == 0;
}

bool PersistEvolution(uint32 character, int16 slot, EQ::ItemInstance &item)
{
	const bool equipped = slot >= EQ::invslot::EQUIPMENT_BEGIN && slot <= EQ::invslot::EQUIPMENT_END;
	item.SetEvolveEquipped(equipped);
	if (!item.IsEvolving()) { return true; }
	// NPC corpse serialization cannot provide an existing character-owned evolve
	// record. Refuse such a cross-owner instance instead of resetting its progress.
	if (item.GetEvolveUniqueID()) { return false; }
	const auto final_item = EvolvingItemsManager::Instance()->GetFinalItemID(item);
	auto inserted = database.QueryDatabase(fmt::format(
		"INSERT INTO character_evolving_items (character_id,item_id,activated,equipped,current_amount,progression,final_item_id) "
		"VALUES ({},{},0,{},{},0,{})", character, item.GetID(), equipped ? 1 : 0, item.GetEvolveCurrentAmount(), final_item), false);
	if (!inserted.Success() || inserted.RowsAffected() != 1) { return false; }
	auto id = database.QueryDatabase(std::string("SELECT LAST_INSERT_ID()"), false);
	if (!id.Success() || id.RowCount() != 1 || !id.begin()[0]) { return false; }
	const auto unique_id = strtoull(id.begin()[0], nullptr, 10);
	if (!unique_id) { return false; }
	item.SetEvolveUniqueID(unique_id); item.SetEvolveCharID(character); item.SetEvolveItemID(item.GetID());
	item.SetEvolveFinalItemID(final_item); item.CalculateEvolveProgression();
	return true;
}
}

bool ValidDropID(const std::string &id)
{
	if (id.size() != 36) { return false; }
	for (size_t i = 0; i < id.size(); ++i) {
		if (i == 8 || i == 13 || i == 18 || i == 23) { if (id[i] != '-') { return false; } }
		else if (!((id[i] >= '0' && id[i] <= '9') || (id[i] >= 'a' && id[i] <= 'f'))) { return false; }
	}
	return true;
}

std::string NewDropID() { return Strings::ToLower(EQ::Util::UUID::Generate().ToString()); }

ClaimStatus ReadClaim(const std::string &id)
{
	if (!ValidDropID(id)) { return ClaimStatus::Unavailable; }
	auto result = database.QueryDatabase(fmt::format("SELECT drop_id FROM character_advloot_claims WHERE drop_id='{}'", id), false);
	if (!result.Success() || result.RowCount() > 1) { return ClaimStatus::Unavailable; }
	return result.RowCount() ? ClaimStatus::Claimed : ClaimStatus::Available;
}

static TransferResult ReceiveItemImpl(Client *c, const EQ::ItemInstance &item, const std::vector<std::string> &drop_ids, bool quiet, Destination destination)
{
	if (!c || !c->Connected() || !c->ClientDataLoaded() || !item.GetItem() || drop_ids.empty() ||
		drop_ids.size() > 11 || std::set<std::string>(drop_ids.begin(), drop_ids.end()).size() != drop_ids.size() ||
		!std::all_of(drop_ids.begin(), drop_ids.end(), ValidDropID)) { return TransferResult::Declined; }
	Plan plan;
	const int16 equip = destination == Destination::InventoryOrCursor ? c->FindLootEquipSlot(item) : EQ::invslot::SLOT_INVALID;
	bool placed = equip != EQ::invslot::SLOT_INVALID;
	if (placed) { plan.emplace(equip, std::unique_ptr<EQ::ItemInstance>(item.Clone())); }
	else if (destination != Destination::Cursor) { placed = BuildPlan(c, item, plan); }
	if (!placed && destination != Destination::Inventory) { placed = BuildCursorPlan(c, item, plan); }
	if (!placed) { if (!quiet) { c->Message(Chat::Red, "There is not enough inventory space for this loot."); } return TransferResult::Declined; }
	if (!TransactionTablesReady()) { if (!quiet) { c->Message(Chat::Red, "Advanced loot storage is unavailable."); } return TransferResult::Declined; }
	auto active = database.QueryDatabase(std::string("SELECT @@in_transaction"), false);
	if (!active.Success() || active.RowCount() != 1 || !active.begin()[0] || atoi(active.begin()[0]) != 0 ||
		!database.QueryDatabase(std::string("START TRANSACTION"), false).Success()) { return TransferResult::Declined; }
	RollbackGuard transaction;
	auto rollback = [&]() {
		// Never retry a failed write after a connection change. A rollback may
		// reconnect, but no further mutation follows it on this attempt.
		database.QueryDatabase(std::string("ROLLBACK"), false);
		transaction.Release();
		return TransferResult::Declined;
	};
	std::map<uint32, InventoryRow> saved;
	auto rows = database.QueryDatabase(fmt::format("SELECT {} FROM inventory WHERE character_id={} FOR UPDATE",
		InventoryRepository::ColumnsRaw(), c->CharacterID()), false);
	if (!rows.Success()) { return rollback(); }
	for (auto row : rows) { const auto r = ReadRow(row); if (!saved.emplace(r.slot_id, r).second) { return rollback(); } }
	if (equip != EQ::invslot::SLOT_INVALID) {
		// Equipment selection depends on other worn slots (notably both hands).
		// Lock and compare their persisted preimages before committing the choice.
		for (int16 slot = EQ::invslot::EQUIPMENT_BEGIN; slot <= EQ::invslot::EQUIPMENT_END; ++slot) {
			const auto current = c->GetInv().GetItem(slot);
			const auto old = saved.find(slot);
			if (current ? (old == saved.end() || !SameItem(old->second, FromItem(c->CharacterID(), slot, *current))) : old != saved.end()) { return rollback(); }
		}
	}
	if (plan.count(EQ::invslot::slotCursor)) {
		for (int16 slot = EQ::invbag::CURSOR_BAG_BEGIN; slot <= EQ::invbag::CURSOR_BAG_END; ++slot) {
			if (saved.count(slot)) { return rollback(); }
		}
	}
	for (const auto &[slot, next] : plan) {
		const auto current = c->GetInv().GetItem(slot);
		const auto old = saved.find(slot);
		if (current ? (old == saved.end() || !SameItem(old->second, FromItem(c->CharacterID(), slot, *current))) : old != saved.end()) { return rollback(); }
		if (slot > EQ::invslot::GENERAL_END && slot != EQ::invslot::slotCursor) {
			const int16 parent = EQ::InventoryProfile::CalcSlotId(slot);
			if (!plan.count(parent)) {
				const auto bag = c->GetInv().GetItem(parent);
				if (!bag || !saved.count(parent) || !SameItem(saved.at(parent), FromItem(c->CharacterID(), parent, *bag))) { return rollback(); }
			}
		}
		if (next->IsClassBag() && !current) {
			for (uint8 i = 0; i < EQ::invbag::SLOT_COUNT; ++i) {
				if (saved.count(EQ::InventoryProfile::CalcSlotId(slot, i))) { return rollback(); }
			}
		}
	}
	std::string audit;
	for (auto &[slot, next] : plan) {
		if (!PersistEvolution(c->CharacterID(), slot, *next)) { return rollback(); }
		auto r = FromItem(c->CharacterID(), slot, *next);
		const auto values = Values(r);
		std::string query;
		if (!saved.count(slot)) {
			query = "INSERT INTO inventory (" + InventoryRepository::ColumnsRaw() + ") VALUES (" + Strings::Implode(",", values) + ")";
		} else {
			std::vector<std::string> assignments;
			const auto columns = InventoryRepository::Columns();
			for (size_t i = 2; i < columns.size(); ++i) { assignments.push_back("`" + columns[i] + "`=" + values[i]); }
			query = fmt::format("UPDATE inventory SET {} WHERE character_id={} AND slot_id={} AND guid={}",
				Strings::Implode(",", assignments), c->CharacterID(), slot, saved.at(slot).guid);
		}
		auto write = database.QueryDatabase(query, false);
		if (!write.Success() || write.RowsAffected() != 1) { return rollback(); }
		audit += Strings::Implode("|", values) + "\n";
	}
	for (const auto &id : drop_ids) {
		auto claim = database.QueryDatabase(fmt::format(
			"INSERT INTO character_advloot_claims (drop_id,character_id,item_id,charges,inventory_after) VALUES ('{}',{},{},{},X'{}')",
			id, c->CharacterID(), item.GetID(), item.GetCharges(), Hex(audit)), false);
		if (!claim.Success() || claim.RowsAffected() != 1) { return rollback(); }
	}
	if (!database.QueryDatabase(std::string("COMMIT"), false).Success()) {
		database.QueryDatabase(std::string("ROLLBACK"), false);
		transaction.Release();
		c->QuarantineItemTransfer("The loot transfer could not be confirmed. Reconnect to reload your inventory.");
		return TransferResult::Uncertain;
	}
	transaction.Release();
	// No quest callbacks, inventory packets or in-memory mutations preceded the
	// acknowledged commit. Installing clones cannot cause another database write.
	for (const auto &[slot, next] : plan) {
		if (c->GetInv().PutItem(slot, *next) != slot) {
			c->QuarantineItemTransfer("Your loot was saved. Reconnect to reload your inventory.");
			return TransferResult::Uncertain;
		}
	}
	for (const auto &[slot, next] : plan) { c->SendItemPacket(slot, c->GetInv().GetItem(slot), ItemPacketTrade); }
	c->CalcBonuses();
	if (equip != EQ::invslot::SLOT_INVALID) { c->NotifyLootEquipped(*plan.at(equip), equip); }
	return TransferResult::Delivered;
}

TransferResult ReceiveItem(Client *c, const EQ::ItemInstance &item, const std::vector<std::string> &drop_ids, bool quiet, Destination destination)
{
	try { return ReceiveItemImpl(c, item, drop_ids, quiet, destination); }
	catch (...) {
		if (c) { c->QuarantineItemTransfer("The loot transfer was interrupted. Reconnect to reload your inventory."); }
		return TransferResult::Uncertain;
	}
}

std::vector<int16_t> ForgeSlots(Client *c)
{
	std::vector<int16_t> result;
	for (int16 slot = EQ::invslot::GENERAL_BEGIN; slot <= EQ::invslot::GENERAL_END; ++slot) {
		if (!(c->GetInv().GetLookup()->PossessionsBitmask & (uint64{1} << slot))) { continue; }
		result.push_back(slot);
		const auto bag = c->GetInv().GetItem(slot);
		if (!bag || !bag->IsClassBag()) { continue; }
		for (uint8 i = 0; i < bag->GetItem()->BagSlots && i < EQ::invbag::SLOT_COUNT; ++i) {
			result.push_back(EQ::InventoryProfile::CalcSlotId(slot, i));
		}
	}
	return result;
}

bool PlainForgeItem(const EQ::ItemInstance *item)
{
	if (!item || !item->IsClassCommon() || !NightcapHunt::NextTier(item->GetID()) ||
		item->IsStackable() || item->IsEvolving() || item->GetEvolveUniqueID() || item->IsScaling() || item->GetCharges() != 1 ||
		item->GetColor() || !item->GetCustomDataString().empty() || item->GetOrnamentationIcon() ||
		item->GetOrnamentationIDFile() || item->GetOrnamentHeroModel()) { return false; }
	for (uint8 i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) { if (item->GetAugmentItemID(i)) { return false; } }
	return true;
}

static uint32 UpgradeTarget(uint32 id)
{
	const auto next = NightcapUpgrade::LegacyTarget(id);
	const auto source = database.GetItem(id);
	const auto target = database.GetItem(next ? next : NightcapUpgrade::ZoneTarget(id));
	if (!source || !target) { return 0; }
	if (next && !NightcapUpgrade::NamesMatch(source->Name, target->Name, id > 400000)) { return 0; }
	return target->ID;
}

static bool PlainUpgradeItem(const EQ::ItemInstance *item)
{
	if (!item || !item->IsClassCommon() ||
		item->IsEvolving() || item->GetEvolveUniqueID() || item->IsScaling() || item->GetColor() ||
		!item->GetCustomDataString().empty() || item->GetOrnamentationIcon() ||
		item->GetOrnamentationIDFile() || item->GetOrnamentHeroModel()) { return false; }
	for (uint8 i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) { if (item->GetAugmentItemID(i)) { return false; } }
	for (uint8 i = 0; i < EQ::invbag::SLOT_COUNT; ++i) { if (item->GetItem(i)) { return false; } }
	return true;
}

static TransferResult ForgeItemsImpl(Client *c, const std::vector<ForgeInput> &inputs, const std::string &request_id, int16 container_slot)
{
	const bool upgrade = container_slot != EQ::invslot::SLOT_INVALID;
	if (!c || !c->Connected() || !c->ClientDataLoaded() || inputs.empty() || !ValidDropID(request_id)) { return TransferResult::Declined; }
	auto allowed = ForgeSlots(c);
	if (upgrade) {
		allowed.clear();
		for (uint8 i = 0; i < NightcapUpgrade::Copies; ++i) { allowed.push_back(EQ::InventoryProfile::CalcSlotId(container_slot, i)); }
	}
	std::set<int16> distinct;
	uint32 input_id = 0;
	unsigned quantity = 0;
	bool bound = false;
	for (const auto &[slot, serial] : inputs) {
		const auto item = c->GetInv().GetItem(slot);
		if (std::find(allowed.begin(), allowed.end(), slot) == allowed.end() || !distinct.insert(slot).second ||
			!(upgrade ? PlainUpgradeItem(item) : PlainForgeItem(item)) || uint32(item->GetSerialNumber()) != serial || (input_id && item->GetID() != input_id)) { return TransferResult::Declined; }
		input_id = item->GetID(); bound = bound || item->IsAttuned();
		if (upgrade && item->IsStackable() && item->GetCharges() <= 0) { return TransferResult::Declined; }
		quantity += upgrade && item->IsStackable() ? item->GetCharges() : 1;
	}
	if (quantity != (upgrade ? NightcapUpgrade::Copies : NightcapUpgrade::ZoneCopies(input_id))) { return TransferResult::Declined; }
	const uint32 target_id = upgrade ? UpgradeTarget(input_id) : NightcapHunt::NextTier(input_id);
	if (!target_id) { return TransferResult::Declined; }
	const auto definition = upgrade ? database.GetItem(target_id) : nullptr;
	std::unique_ptr<EQ::ItemInstance> output(database.CreateItem(target_id, definition && definition->MaxCharges ? definition->MaxCharges : 1));
	if (!output || c->CheckLoreConflict(output->GetItem())) { return TransferResult::Declined; }
	if (output->IsStackable()) { output->SetCharges(1); }
	output->SetAttuned(bound);
	int16 destination = inputs.front().first;

	if (destination > EQ::invslot::GENERAL_END) {
		const auto bag = c->GetInv().GetItem(EQ::InventoryProfile::CalcSlotId(destination));
		if (!bag || !EQ::InventoryProfile::CanItemFitInContainer(output->GetItem(), bag->GetItem())) { return TransferResult::Declined; }
	}
	if (!TransactionTablesReady()) { return TransferResult::Declined; }
	const std::string state_table = upgrade ? "nightcap_item_upgrade_state" : "nightcap_zone_hunt_state";
	const std::string receipts = upgrade ? "nightcap_item_upgrades" : "nightcap_zone_hunt_forges";
	auto tables = database.QueryDatabase("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() "
		"AND TABLE_NAME IN ('" + state_table + "','" + receipts + "') AND ENGINE='InnoDB'", false);
	auto triggers = database.QueryDatabase("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() "
		"AND EVENT_OBJECT_TABLE IN ('" + state_table + "','" + receipts + "')", false);
	if (!tables.Success() || tables.RowCount()!=1 || !tables.begin()[0] || atoi(tables.begin()[0])!=2 ||
		!triggers.Success() || triggers.RowCount()!=1 || !triggers.begin()[0] || atoi(triggers.begin()[0])!=0) { return TransferResult::Declined; }
	auto uncertain = [&]() {
		c->QuarantineItemTransfer("The forge result could not be confirmed. Reconnect to reload your inventory.");
		return TransferResult::Uncertain;
	};
	auto active = database.QueryDatabase(std::string("SELECT @@in_transaction"), false);
	if (!active.Success() || active.RowCount()!=1 || !active.begin()[0] || atoi(active.begin()[0]) ||
		!database.QueryDatabase(std::string("START TRANSACTION"), false).Success()) { return uncertain(); }
	RollbackGuard transaction;
	auto reject = [&]() {
		const bool confirmed = database.QueryDatabase(std::string("ROLLBACK"), false).Success();
		transaction.Release();
		return confirmed ? TransferResult::Declined : uncertain();
	};
	auto state = database.QueryDatabase(fmt::format("SELECT revision FROM {} WHERE id=1 AND enabled=1 AND revision={} FOR UPDATE", state_table, upgrade ? NightcapUpgrade::Revision : NightcapHunt::Revision), false);
	if (!state.Success() || state.RowCount()!=1) { return reject(); }
	if (upgrade && NightcapUpgrade::ZoneTarget(input_id)) {
		auto hunt = database.QueryDatabase(fmt::format("SELECT revision FROM nightcap_zone_hunt_state WHERE id=1 AND enabled=1 AND revision={} FOR UPDATE", NightcapHunt::Revision), false);
		if (!hunt.Success() || hunt.RowCount()!=1) { return reject(); }
	}
	auto receipt = database.QueryDatabase(fmt::format("SELECT request_id FROM {} WHERE request_id='{}' FOR UPDATE", receipts, request_id), false);
	if (!receipt.Success() || receipt.RowCount()) { return reject(); }
	std::map<int16, InventoryRow> saved;
	auto rows = database.QueryDatabase(fmt::format("SELECT {} FROM inventory WHERE character_id={} FOR UPDATE", InventoryRepository::ColumnsRaw(), c->CharacterID()), false);
	if (!rows.Success()) { return reject(); }
	for (auto row : rows) { auto r = ReadRow(row); if (!saved.emplace(r.slot_id,r).second) { return reject(); } }
	if (upgrade) {
		for (uint8 i = 0; i < EQ::invbag::SLOT_COUNT; ++i) {
			const int16 slot = EQ::InventoryProfile::CalcSlotId(container_slot,i);
			const auto item = c->GetInv().GetItem(slot);
			if (item ? (!saved.count(slot) || !SameItem(saved.at(slot),FromItem(c->CharacterID(),slot,*item))) : saved.count(slot)) { return reject(); }
		}
	}

	std::string before;
	for (const auto &[slot, serial] : inputs) {
		const auto item = c->GetInv().GetItem(slot);
		if (!saved.count(slot) || !SameItem(saved.at(slot), FromItem(c->CharacterID(), slot, *item))) { return reject(); }
		if (slot > EQ::invslot::GENERAL_END) {
			const int16 parent = EQ::InventoryProfile::CalcSlotId(slot);
			const auto bag = c->GetInv().GetItem(parent);
			if (!bag || !saved.count(parent) || !SameItem(saved.at(parent),FromItem(c->CharacterID(),parent,*bag))) { return reject(); }
		}
		before += Strings::Implode("|", Values(saved.at(slot))) + "\n";
	}
	// Every source was validated before the first write. Persisted GUIDs are
	// CAS preimages; runtime serials were checked only against the single-use quote.
	for (const auto &[slot, serial] : inputs) {
		const auto values = Values(saved.at(slot)); const auto columns = InventoryRepository::Columns();
		std::vector<std::string> predicates;
		for (size_t i=0; i<columns.size(); ++i) {
			predicates.push_back((i==12 ? "BINARY COALESCE(custom_data,'')" : "`"+columns[i]+"`")+"="+values[i]);
		}
		auto removed = database.QueryDatabase("DELETE FROM inventory WHERE "+Strings::Implode(" AND ",predicates), false);
		if (!removed.Success() || removed.RowsAffected()!=1) { return reject(); }
	}
	const auto next = Values(FromItem(c->CharacterID(),destination,*output));
	auto added = database.QueryDatabase("INSERT INTO inventory ("+InventoryRepository::ColumnsRaw()+") VALUES ("+Strings::Implode(",",next)+")", false);
	if (!added.Success() || added.RowsAffected()!=1) { return reject(); }
	auto audit = database.QueryDatabase(fmt::format("INSERT INTO {}(request_id,character_id,input_id,output_id,inventory_before,inventory_after) "
		"VALUES ('{}',{},{},{},X'{}',X'{}')", receipts,request_id,c->CharacterID(),input_id,output->GetID(),Hex(before),Hex(Strings::Implode("|",next))), false);
	if (!audit.Success() || audit.RowsAffected()!=1) { return reject(); }
	if (!database.QueryDatabase(std::string("COMMIT"), false).Success()) {
		database.QueryDatabase(std::string("ROLLBACK"), false); transaction.Release(); return uncertain();
	}
	transaction.Release();
	for (const auto &[slot, serial] : inputs) { c->DeleteItemInInventory(slot,0,true,false); }
	if (c->GetInv().PutItem(destination,*output)!=destination) { return uncertain(); }
	c->SendItemPacket(destination,c->GetInv().GetItem(destination),ItemPacketTrade);
	c->CalcBonuses();
	return TransferResult::Delivered;
}

TransferResult ForgeItems(Client *c, const std::vector<ForgeInput> &inputs, const std::string &request_id)
{
	try { return ForgeItemsImpl(c, inputs, request_id, EQ::invslot::SLOT_INVALID); }
	catch (...) {
		if (c) { c->QuarantineItemTransfer("The forge was interrupted. Reconnect to reload your inventory."); }
		return TransferResult::Uncertain;
	}
}

TransferResult CombineUpgrade(Client *c, int16_t container_slot, const std::string &request_id)
{
	try {
		if (!c || !c->Connected() || !c->ClientDataLoaded() || c->IsDead() || c->IsEngaged() ||
			c->AutoAttackEnabled() || c->IsCasting() || c->IsStunned() || c->IsMezzed() ||
			c->IsFeared() || c->IsAIControlled() || (c->trade && c->trade->With()) ||
			c->IsLooting() || c->GetMerchantSessionEntityID() || c->GetTradeskillObject() ||
			container_slot < EQ::invslot::GENERAL_BEGIN || container_slot > EQ::invslot::GENERAL_END ||
			!(c->GetInv().GetLookup()->PossessionsBitmask & (uint64{1} << container_slot))) { return TransferResult::Declined; }
		const auto box = c->GetInv().GetItem(container_slot);
		if (!box || !box->IsClassBag() || box->GetID() != NightcapUpgrade::ContainerID ||
			box->GetItem()->BagSlots != NightcapUpgrade::Copies || box->GetItem()->BagType != 13) { return TransferResult::Declined; }
		std::vector<ForgeInput> inputs;
		for (uint8 i = 0; i < EQ::invbag::SLOT_COUNT; ++i) {
			const int16 slot = EQ::InventoryProfile::CalcSlotId(container_slot, i);
			const auto item = c->GetInv().GetItem(slot);
			if (!item) { continue; }
			if (i >= NightcapUpgrade::Copies) { return TransferResult::Declined; }
			inputs.emplace_back(slot, item->GetSerialNumber());
		}
		return ForgeItemsImpl(c, inputs, request_id, container_slot);
	}
	catch (...) {
		if (c) { c->QuarantineItemTransfer("The combine was interrupted. Reconnect to reload your inventory."); }
		return TransferResult::Uncertain;
	}
}
}

#include "zone/queryserv.h"
#include "zone/corpse.h"
#include "zone/advanced_loot_inventory.h"
#include "zone/dynamic_zone.h"
#include "zone/entity.h"
#include "zone/groups.h"
#include "zone/quest_parser_collection.h"
#include "zone/raids.h"
#include "zone/string_ids.h"
#include "zone/worldserver.h"
#include "common/events/player_event_logs.h"
#include "common/rulesys.h"
#include "common/say_link.h"
#include <memory>
#include <set>

extern QueryServ *QServ;

extern EntityList entity_list;
extern Zone *zone;

namespace {
std::unique_ptr<EQ::ItemInstance> MakeDrop(const LootItem &i)
{
	return std::unique_ptr<EQ::ItemInstance>(database.CreateItem(i.item_id, i.charges, i.aug_1, i.aug_2,
		i.aug_3, i.aug_4, i.aug_5, i.aug_6, i.attuned, i.custom_data, i.ornamenticon, i.ornamentidfile, i.ornament_hero_model));
}
bool LoreConflict(Client *c, const EQ::ItemInstance &item, std::set<std::pair<bool, int64>> &incoming)
{
	const auto data = item.GetItem();
	if (!data || c->CheckLoreConflict(data)) { return true; }
	if (data->LoreFlag && data->LoreGroup && !incoming.emplace(data->LoreGroup == -1,
		data->LoreGroup == -1 ? static_cast<int64>(data->ID) : data->LoreGroup).second) { return true; }
	if (item.IsClassBag()) {
		for (uint8 i = 0; i < EQ::invbag::SLOT_COUNT; ++i) {
			if (const auto child = item.GetItem(i); child && LoreConflict(c, *child, incoming)) { return true; }
		}
	} else {
		for (int i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) {
			if (const auto augment = item.GetAugment(i); augment && LoreConflict(c, *augment, incoming)) { return true; }
		}
	}
	return false;
}
bool LoreConflict(Client *c, const EQ::ItemInstance &item)
{
	std::set<std::pair<bool, int64>> incoming;
	return LoreConflict(c, item, incoming);
}
bool ConsentNeeded(const EQ::ItemInstance &item)
{
	if (!item.GetItem()->NoDrop || item.GetItem()->NoTransfer || item.IsAttunedForTrade()) { return true; }
	for (int i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) {
		const auto augment = item.GetAugment(i);
		if (augment && (!augment->GetItem()->NoDrop || augment->GetItem()->NoTransfer || augment->IsAttunedForTrade())) { return true; }
	}
	for (uint8 i = 0; i < EQ::invbag::SLOT_COUNT; ++i) {
		if (const auto child = item.GetItem(i); child && ConsentNeeded(*child)) { return true; }
	}
	return false;
}
}

bool Corpse::ClassicLootOverride(Client *c)
{
	return c && c->GetGM() && c->Admin() >= AccountStatus::GMAdmin &&
		m_loot_request_type == LootRequestType::GMAllowed && IsBeingLootedBy(c);
}

bool Corpse::AdvancedLootAccessible(Client *c, bool own_transfer, bool classic)
{
	// The advanced list already contains earned drops throughout this zone.
	// Public corpses and classic corpse clicks still require native loot range.
	const auto rights = AdvancedLootRights();
	const bool earned = c && !classic && std::find(rights.begin(), rights.end(), c->CharacterID()) != rights.end();
	return c && zone && IsNPCCorpse() && !IsBecomeNPCCorpse() && !m_player_corpse_depop && GetDecayTime() != 0 &&
		GetEntityVariable("nightcap:advloot-invalid-state").empty() && (!m_is_locked || (classic && c->Admin() >= AccountStatus::GMAdmin)) &&
		(!m_advanced_loot_busy || own_transfer) && (!IsBeingLooted() || IsBeingLootedBy(c)) &&
		c->Connected() && c->ClientDataLoaded() && !c->IsDead() && c->GetHP() > 0 && !c->IsAIControlled() &&
		!c->IsStunned() && !c->IsMezzed() && !c->IsFeared() && !c->GetFeigned() && !c->IsTrader() && !c->IsBuyer() &&
		!(c->trade && c->trade->With()) && !c->GetTradeskillObject() &&
		(CanPlayerLoot(c->CharacterID()) || (classic && ClassicLootOverride(c))) &&
		(earned || DistanceSquaredNoZ(c->GetPosition(), GetPosition()) <= 625);
}

NightcapLoot::TransferResult Corpse::LootAdvancedItem(Client *c, LootItem *selected, bool consent, bool automatic, NightcapLoot::Destination destination)
{
	using namespace NightcapLoot;
	const bool classic = destination != Destination::Inventory;
	const bool classic_override = classic && ClassicLootOverride(c);
	if (!AdvancedLootAccessible(c, false, classic) || !selected || (automatic && IsBeingLooted()) ||
		std::find(m_item_list.begin(), m_item_list.end(), selected) == m_item_list.end() || !ValidDropID(selected->advanced_loot_id)) { return TransferResult::Declined; }
	if (RuleB(Character, CheckCursorEmptyWhenLooting) && !c->GetInv().CursorEmpty()) { return TransferResult::Declined; }
	const uint16 corpse_id = GetID();
	const auto generation = GetEntityVariable("nightcap:advloot-generation");
	const auto npc_id = GetNPCTypeID();
	const auto source_name = EntityList::RemoveNumbers(corpse_name);
	auto alive = [&]() { return entity_list.GetCorpseByID(corpse_id) == this && GetEntityVariable("nightcap:advloot-generation") == generation; };
	struct BusyGuard {
		Corpse *corpse; uint16 id; std::string generation;
		~BusyGuard() { if (entity_list.GetCorpseByID(id) == corpse && corpse->GetEntityVariable("nightcap:advloot-generation") == generation) { corpse->m_advanced_loot_busy = false; } }
	};
	m_advanced_loot_busy = true;
	BusyGuard busy{this, corpse_id, generation};
	std::vector<std::pair<LootItem *, LootItem>> sources{{selected, *selected}};
	auto inst = MakeDrop(*selected);
	if (!inst) { return TransferResult::Declined; }
	if (inst->IsClassBag() && EQ::InventoryProfile::SupportsContainers(selected->equip_slot)) {
		const int16 first = EQ::InventoryProfile::CalcSlotId(selected->equip_slot, 0);
		for (auto child : m_item_list) {
			if (child == selected || child->equip_slot < first || child->equip_slot >= first + EQ::invbag::SLOT_COUNT) { continue; }
			if (!ValidDropID(child->advanced_loot_id)) { return TransferResult::Declined; }
			auto content = MakeDrop(*child);
			if (!content || child->equip_slot - first >= inst->GetItem()->BagSlots) { return TransferResult::Declined; }
			inst->PutItem(child->equip_slot - first, *content);
			sources.emplace_back(child, *child);
		}
	}
	std::vector<std::string> ids;
	for (const auto &[source, before] : sources) {
		auto item = MakeDrop(before);
		if (!item || LoreConflict(c, *item) || (!consent && ConsentNeeded(*item)) || ReadClaim(before.advanced_loot_id) != ClaimStatus::Available) { return TransferResult::Declined; }
		ids.push_back(before.advanced_loot_id);
	}
	if (LoreConflict(c, *inst)) { return TransferResult::Declined; }
	const auto export_string = fmt::format("{} {} {} {}", inst->GetID(), inst->GetCharges(), EntityList::RemoveNumbers(corpse_name), corpse_id);
	std::vector<std::any> args{inst.get(), this};
	// The same NPC, player, zone and item EVENT_LOOT vetoes used by classic
	// corpse looting run before the checked transfer. Scripts may change state,
	// so the physical source, permissions and inventory are checked again below.
	if (RuleB(Zone, UseZoneController)) {
		const auto controller = entity_list.GetNPCByNPCTypeID(ZONE_CONTROLLER_NPC_ID);
		if (controller && parse->HasQuestSub(ZONE_CONTROLLER_NPC_ID, EVENT_LOOT_ZONE) &&
			parse->EventNPC(EVENT_LOOT_ZONE, controller, c, export_string, 0, &args) != 0) { return TransferResult::Declined; }
		if (!alive()) { return TransferResult::Declined; }
	}
	if (parse->PlayerHasQuestSub(EVENT_LOOT) && parse->EventPlayer(EVENT_LOOT, c, export_string, 0, &args) != 0) { return TransferResult::Declined; }
	if (!alive()) { return TransferResult::Declined; }
	if (parse->ZoneHasQuestSub(EVENT_LOOT_ZONE)) {
		std::vector<std::any> zone_args{inst.get(), this, c};
		if (parse->EventZone(EVENT_LOOT_ZONE, zone, export_string, 0, &zone_args) != 0) { return TransferResult::Declined; }
		if (!alive()) { return TransferResult::Declined; }
	}
	if (const auto dz = zone->GetDynamicZone(); dz && !dz->CanClientLootCorpse(c, GetNPCTypeID(), corpse_id)) { return TransferResult::Declined; }
	if (parse->ItemHasQuestSub(inst.get(), EVENT_LOOT) && parse->EventItem(EVENT_LOOT, c, inst.get(), this, export_string, 0, &args) != 0) { return TransferResult::Declined; }
	if (!alive() || !AdvancedLootAccessible(c, true, classic) || (classic_override && !ClassicLootOverride(c)) ||
		LoreConflict(c, *inst) || (!consent && ConsentNeeded(*inst))) { return TransferResult::Declined; }
	for (const auto &[source, before] : sources) {
		if (std::find(m_item_list.begin(), m_item_list.end(), source) == m_item_list.end() || !SamePhysicalLoot(*source, before)) { return TransferResult::Declined; }
	}
	const auto timestamps = database.GetItemRecastTimestamps(c->CharacterID());
	const auto item = inst->GetItem();
	if (item->RecastDelay) {
		const auto recast = item->RecastType == RECAST_TYPE_UNLINKED_ITEM ? item->ID : item->RecastType;
		inst->SetRecastTimestamp(timestamps.count(recast) ? timestamps.at(recast) : 0);
	}
	const auto result = ReceiveItem(c, *inst, ids, automatic, destination);
	if (result != TransferResult::Delivered) { return result; }
	if (!alive()) { return result; }
	for (const auto &[source, before] : sources) {
		if (std::find(m_item_list.begin(), m_item_list.end(), source) != m_item_list.end() && SamePhysicalLoot(*source, before)) { RemoveItem(source); }
	}
	c->CommonBreakInvisible();
	c->CheckItemDiscoverability(inst->GetID());
	const int count = inst->IsStackable() ? inst->GetCharges() : 1;
	if (zone->adv_data) {
		const auto adventure = reinterpret_cast<ServerZoneAdventureDataReply_Struct *>(zone->adv_data);
		if (adventure->type == Adventure_Collect && adventure->data_id == item->ID) { zone->DoAdventureCountIncrease(); }
	}
	if (PlayerEventLogs::Instance()->IsEventEnabled(PlayerEvent::LOOT_ITEM)) {
		auto event = PlayerEvent::LootItemEvent{.item_id = item->ID, .item_name = item->Name, .charges = inst->GetCharges(),
			.augment_1_id = inst->GetAugmentItemID(0), .augment_2_id = inst->GetAugmentItemID(1), .augment_3_id = inst->GetAugmentItemID(2),
			.augment_4_id = inst->GetAugmentItemID(3), .augment_5_id = inst->GetAugmentItemID(4), .augment_6_id = inst->GetAugmentItemID(5),
			.npc_id = npc_id, .corpse_name = source_name};
		RecordPlayerEventLogWithClient(c, PlayerEvent::LOOT_ITEM, event);
	}
	EQ::SayLinkEngine link;
	link.SetLinkType(EQ::saylink::SayLinkItemInst); link.SetItemInst(inst.get()); link.GenerateLink();
	c->MessageString(Chat::Loot, LOOTED_MESSAGE, link.Link().c_str());
	if (auto group = c->GetGroup()) { group->GroupMessageString(c, Chat::Loot, OTHER_LOOTED_MESSAGE, c->GetName(), link.Link().c_str()); }
	else if (auto raid = c->GetRaid()) { raid->RaidMessageString(c, Chat::Loot, OTHER_LOOTED_MESSAGE, c->GetName(), link.Link().c_str()); }
	c->SendItemLink(inst.get(), true);
	if (alive() && RuleB(TaskSystem, EnableTaskSystem)) { c->UpdateTasksOnLoot(this, item->ID, count); }
	if (alive() && IsEmpty() && !IsBeingLooted()) { ResetDecayTimer(); }
	return result;
}

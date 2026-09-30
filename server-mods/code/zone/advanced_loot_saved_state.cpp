#include "zone/advanced_loot_saved_state.h"
#include "zone/advanced_loot.h"
#include "zone/advanced_loot_inventory.h"
#include "zone/corpse.h"
#include "zone/npc.h"
#include "common/json/json.hpp"
#include "common/md5.h"
#include "common/util/uuid.h"
#include <set>
#include <stdexcept>

namespace NightcapLoot {
namespace {
using Json = nlohmann::json;
constexpr const char *Key = "nightcap_advanced_loot_v1";
constexpr const char *InvalidKey = "nightcap:advloot-invalid-state";
constexpr const char *DistributionKey = "nightcap:advloot-distribution";
constexpr const char *CoinKey = "nightcap:advloot-coin-id";
constexpr const char *IDsKey = "nightcap_loot_ids_v1";
constexpr const char *NPCKey = "nightcap_npc_loot_v1";

uint32 NumberAt(const Json &j, const char *key, uint64 maximum = UINT32_MAX)
{
	const auto &value = j.at(key);
	if (!value.is_number_integer() || value.get<int64_t>() < 0 || value.get<uint64_t>() > maximum) { throw std::invalid_argument(key); }
	return value.get<uint32>();
}
std::string TextAt(const Json &j, const char *key, size_t maximum)
{
	const auto result = j.at(key).get<std::string>();
	if (result.size() > maximum) { throw std::invalid_argument(key); }
	return result;
}
Json SaveItem(const LootItem &i)
{
	return {{"id", i.advanced_loot_id}, {"item", i.item_id}, {"slot", i.equip_slot}, {"charges", i.charges},
		{"aug1", i.aug_1}, {"aug2", i.aug_2}, {"aug3", i.aug_3}, {"aug4", i.aug_4}, {"aug5", i.aug_5}, {"aug6", i.aug_6},
		{"attuned", i.attuned}, {"custom", i.custom_data}, {"icon", i.ornamenticon}, {"idfile", i.ornamentidfile},
		{"hero", i.ornament_hero_model}, {"trivial_min", i.trivial_min_level}, {"trivial_max", i.trivial_max_level},
		{"npc_min", i.npc_min_level}, {"npc_max", i.npc_max_level}, {"lootdrop", i.lootdrop_id}};
}
LootItem LoadItem(const Json &j)
{
	LootItem i{};
	i.advanced_loot_id = TextAt(j, "id", 36);
	if (!ValidDropID(i.advanced_loot_id)) { throw std::invalid_argument("drop ID"); }
	i.item_id = NumberAt(j, "item"); i.charges = NumberAt(j, "charges", UINT16_MAX);
	const auto &slot = j.at("slot");
	if (!slot.is_number_integer() || slot.get<int64_t>() < INT16_MIN || slot.get<int64_t>() > INT16_MAX) { throw std::invalid_argument("slot"); }
	i.equip_slot = slot.get<int16>(); i.lootslot = 0xffff;
	i.aug_1 = NumberAt(j, "aug1"); i.aug_2 = NumberAt(j, "aug2"); i.aug_3 = NumberAt(j, "aug3");
	i.aug_4 = NumberAt(j, "aug4"); i.aug_5 = NumberAt(j, "aug5"); i.aug_6 = NumberAt(j, "aug6");
	i.attuned = j.at("attuned").get<bool>(); i.custom_data = TextAt(j, "custom", 65535);
	i.ornamenticon = NumberAt(j, "icon"); i.ornamentidfile = NumberAt(j, "idfile"); i.ornament_hero_model = NumberAt(j, "hero");
	i.trivial_min_level = NumberAt(j, "trivial_min", UINT16_MAX); i.trivial_max_level = NumberAt(j, "trivial_max", UINT16_MAX);
	i.npc_min_level = NumberAt(j, "npc_min", UINT16_MAX); i.npc_max_level = NumberAt(j, "npc_max", UINT16_MAX);
	i.lootdrop_id = NumberAt(j, "lootdrop");
	if (!i.item_id) { throw std::invalid_argument("item ID"); }
	return i;
}
}

std::string SaveNPCDropIDs(NPC *npc, const std::string &legacy)
{
	const auto invalid = npc->GetEntityVariable(InvalidKey);
	if (!invalid.empty()) { return invalid; }
	auto saved = Json::parse(legacy);
	Json ids = Json::array();
	for (auto item : npc->GetLootItems()) {
		if (item->advanced_loot_id.empty()) { item->advanced_loot_id = NewDropID(); }
		ids.push_back(SaveItem(*item));
	}
	if (npc->GetEntityVariable(CoinKey).empty()) { npc->SetEntityVariable(CoinKey, NewDropID()); }
	saved[NPCKey] = {{"items", ids}, {"coin_id", npc->GetEntityVariable(CoinKey)}};
	return saved.dump();
}

void StampRestoredDropIDs(NPC *npc, const std::string &raw, uint64_t state_id, int64_t created_at)
{
	if (!npc->GetEntityVariable(InvalidKey).empty()) { return; }
	try {
		const auto saved = Json::parse(raw);
		const Json *ids = saved.contains(NPCKey) ? &saved.at(NPCKey).at("items") : saved.contains(IDsKey) ? &saved.at(IDsKey).at("items") : nullptr;
		if (!ids && !saved.contains(Key) && saved.at("entries").size() != npc->GetLootItems().size()) { throw std::invalid_argument("incomplete legacy loot"); }
		if (ids && (!ids->is_array() || ids->size() != npc->GetLootItems().size())) { throw std::invalid_argument("saved drop IDs"); }
		// Legacy snapshots have no UUID. Derive a repeatable identifier from the
		// saved row and slot so replaying that same checkpoint after a crash still
		// finds its receipt. This digest is an identifier, never an authorization.
		uint8 raw_digest[16]{};
		MD5::Generate(reinterpret_cast<const uint8 *>(raw.data()), raw.size(), raw_digest);
		const auto checkpoint = EQ::Util::UUID::FromByteArray(reinterpret_cast<const char *>(raw_digest)).ToString();
		auto legacy_id = [&](size_t index, uint32 item) {
			const auto seed = fmt::format("nightcap-loot-v1|{}|{}|{}|{}|{}", state_id, created_at, index, item, checkpoint);
			uint8 digest[16]{};
			MD5::Generate(reinterpret_cast<const uint8 *>(seed.data()), seed.size(), digest);
			return Strings::ToLower(EQ::Util::UUID::FromByteArray(reinterpret_cast<const char *>(digest)).ToString());
		};
		size_t index = 0;
		for (auto item : npc->GetLootItems()) {
			if (ids) {
				const auto &entry = ids->at(index);
				if (NumberAt(entry, "item") != item->item_id) { throw std::invalid_argument("saved drop identity"); }
				item->advanced_loot_id = TextAt(entry, "id", 36);
			} else if (item->advanced_loot_id.empty()) { item->advanced_loot_id = legacy_id(index, item->item_id); }
			if (!ValidDropID(item->advanced_loot_id)) { throw std::invalid_argument("drop ID"); }
			++index;
		}
		std::string coin = saved.contains(Key) ? TextAt(saved.at(Key), "coin_id", 36) :
			saved.contains(NPCKey) ? TextAt(saved.at(NPCKey), "coin_id", 36) :
			saved.contains(IDsKey) ? TextAt(saved.at(IDsKey), "coin_id", 36) : std::string{};
		if (coin.empty()) { coin = legacy_id(index, 0); }
		if (!ValidDropID(coin)) { throw std::invalid_argument("coin ID"); }
		npc->SetEntityVariable(CoinKey, coin);
	} catch (...) {
		npc->ClearLootItems(); npc->RemoveLootCash(); npc->SetEntityVariable(InvalidKey, raw.empty() ? "invalid" : raw);
		LogError("Advanced loot: quarantined invalid saved drop IDs for NPC [{}]", npc->GetNPCTypeID());
	}
}

std::string SaveCorpseState(Corpse *c, const std::string &legacy)
{
	if (!c || !c->IsNPCCorpse()) { return legacy; }
	SaveDistribution(c);
	const auto invalid = c->GetEntityVariable(InvalidKey);
	if (!invalid.empty()) { return invalid; } // retain quarantined state for recovery
	if (c->GetEntityVariable(CoinKey).empty()) { c->SetEntityVariable(CoinKey, NewDropID()); }
	auto saved = Json::parse(legacy);
	Json items = Json::array();
	for (const auto item : c->GetLootItems()) {
		if (item->advanced_loot_id.empty()) { item->advanced_loot_id = NewDropID(); }
		items.push_back(SaveItem(*item));
	}
	saved[Key] = {{"items", items}, {"rights", c->AdvancedLootRights()}, {"rights_delay", c->AdvancedLootRightsDelay()},
		{"distribution", c->GetEntityVariable(DistributionKey)}, {"coin_id", c->GetEntityVariable(CoinKey)}, {"locked", c->IsLocked()}};
	return saved.dump();
}

RestoreState RestoreCorpseItems(NPC *npc, const std::string &raw)
{
	try {
		const auto saved = Json::parse(raw);
		if (!saved.contains(Key) && !saved.contains(NPCKey)) {
			NumberAt(saved, "copper"); NumberAt(saved, "silver"); NumberAt(saved, "gold"); NumberAt(saved, "platinum");
			if (!saved.at("entries").is_array()) { throw std::invalid_argument("legacy loot entries"); }
			for (const auto &item : saved.at("entries")) { NumberAt(item, "item_id"); NumberAt(item, "lootdrop_id"); NumberAt(item, "charges", UINT16_MAX); }
			return RestoreState::Legacy;
		}
		const auto &items = saved.at(saved.contains(Key) ? Key : NPCKey).at("items");
		if (!items.is_array() || items.size() > 100000) { throw std::invalid_argument("loot count"); }
		std::vector<LootItem> restored;
		std::set<std::string> ids;
		for (const auto &item : items) {
			auto i = LoadItem(item);
			if (!i.advanced_loot_id.empty() && !ids.insert(i.advanced_loot_id).second) { throw std::invalid_argument("duplicate drop ID"); }
			if (!database.GetItem(i.item_id)) { throw std::invalid_argument("missing saved item"); }
			restored.push_back(std::move(i));
		}
		const auto copper = NumberAt(saved, "copper"), silver = NumberAt(saved, "silver"),
			gold = NumberAt(saved, "gold"), platinum = NumberAt(saved, "platinum");
		npc->ClearLootItems(); npc->RemoveLootCash();
		npc->AddLootCash(copper, silver, gold, platinum);
		for (const auto &i : restored) {
			const auto before = npc->GetLootItems().size();
			npc->AddItem(i.item_id, i.charges, false, i.aug_1, i.aug_2, i.aug_3, i.aug_4, i.aug_5, i.aug_6);
			if (npc->GetLootItems().size() != before + 1) { throw std::runtime_error("could not restore item"); }
			*npc->GetLootItems().back() = i;
		}
		return RestoreState::Restored;
	} catch (...) {
		npc->ClearLootItems(); npc->RemoveLootCash();
		npc->SetEntityVariable(InvalidKey, raw.empty() ? "invalid" : raw);
		return RestoreState::Invalid;
	}
}

void RestoreCorpseState(Corpse *c, const std::string &raw)
{
	if (!c) { return; }
	if (!c->GetEntityVariable(InvalidKey).empty()) { c->Lock(); return; }
	try {
		const auto saved = Json::parse(raw);
		if (!saved.contains(Key)) { return; }
		const auto &state = saved.at(Key);
		const auto &members = state.at("rights");
		if (!members.is_array() || members.size() > MAX_LOOTERS) { throw std::invalid_argument("loot rights"); }
		std::vector<uint32> rights;
		for (const auto &member : members) {
			if (!member.is_number_integer() || member.get<int64_t>() < 1 || member.get<uint64_t>() > INT32_MAX) { throw std::invalid_argument("looter"); }
			rights.push_back(member.get<uint32>());
		}
		// Validate the complete item envelope too, before unlocking the restored
		// corpse. A malformed saved extension may never fall back to rerolled loot.
		if (!state.at("items").is_array() || state.at("items").size() != c->GetLootItems().size()) { throw std::invalid_argument("restored items"); }
		for (const auto &item : state.at("items")) { LoadItem(item); }
		const auto coin_id = TextAt(state, "coin_id", 36);
		if (!coin_id.empty() && !ValidDropID(coin_id)) { throw std::invalid_argument("coin ID"); }
		c->RestoreAdvancedLootRights(rights, NumberAt(state, "rights_delay"));
		c->SetEntityVariable(DistributionKey, TextAt(state, "distribution", 16 * 1024 * 1024));
		if (!coin_id.empty()) { c->SetEntityVariable(CoinKey, coin_id); }
		if (state.at("locked").get<bool>()) { c->Lock(); }
	} catch (...) {
		c->Lock(); c->SetEntityVariable(InvalidKey, raw.empty() ? "invalid" : raw);
		LogError("Advanced loot: quarantined invalid saved corpse state for NPC [{}]", c->GetNPCTypeID());
	}
}
}

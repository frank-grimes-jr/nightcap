#include "zone/advanced_loot.h"
#include "zone/advanced_loot_inventory.h"
#include "zone/advanced_loot_currency.h"
#include "zone/advanced_loot_preferences.h"
#include "zone/client.h"
#include "zone/corpse.h"
#include "zone/entity.h"
#include "zone/groups.h"
#include "zone/raids.h"
#include "zone/zone.h"
#include "common/json/json.hpp"
#include "common/seperator.h"
#include <chrono>
#include <memory>
#include <set>

extern EntityList entity_list;
extern Zone *zone;

namespace NightcapLoot {
namespace {
using Json = nlohmann::json;
constexpr const char *DistributionKey = "nightcap:advloot-distribution";
constexpr const char *GenerationKey = "nightcap:advloot-generation";
struct Drop {
	uint32 token = 0;
	LootItem *item = nullptr;
	std::string id;
	std::unique_ptr<DropPolicy> policy;
	bool claimed = false, unavailable = true, transferring = false;
	uint64 claim_retry = 0;
	std::map<uint32, uint64> retry;
	std::map<uint32, std::string> failed_inventory;
};
struct CorpseEntry {
	Corpse *corpse = nullptr;
	uint16 spawn = 0;
	std::string generation;
	Json restored = Json::object();
	bool restored_loaded = false;
	std::map<std::string, std::shared_ptr<Drop>> drops;
	bool invalid = false;
	uint64 next_coin = 0;
};
struct PendingLoot {
	std::shared_ptr<CorpseEntry> entry;
	std::shared_ptr<Drop> drop;
	std::vector<LootItem> items;
};
struct Session {
	Client *client = nullptr;
	Preferences preferences;
	Snapshot snapshot;
	std::string search, signature;
	uint64 next_command = 0;
	bool loaded = false;
	std::vector<PendingLoot> pending_no_trade;
	uint32 pending_revision = 0;
	uint64 pending_until = 0;
	void ClearConfirmation() { pending_no_trade.clear(); pending_revision = 0; pending_until = 0; }
};
std::map<Client *, Session> sessions;
std::map<Corpse *, std::shared_ptr<CorpseEntry>> corpses;
uint32 next_session = 1, next_token = 1;
uint64 next_pulse = 0;
bool pumping = false;

uint64 Now() {
	return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
}
uint32 Allocate(uint32 &counter) {
	if (!counter || counter == UINT32_MAX) { throw std::overflow_error("advanced loot identifiers exhausted"); }
	return counter++;
}
bool Alive(const CorpseEntry &entry) {
	return entity_list.GetCorpseByID(entry.spawn) == entry.corpse &&
		entry.corpse->GetEntityVariable(GenerationKey) == entry.generation;
}
bool Present(const CorpseEntry &entry, const Drop &drop) {
	if (!Alive(entry)) { return false; }
	const auto &items = entry.corpse->GetLootItems();
	return std::find(items.begin(), items.end(), drop.item) != items.end() && drop.item->advanced_loot_id == drop.id;
}
Session *Active(uint32 character) {
	const auto client = entity_list.GetClientByCharID(character);
	const auto it = sessions.find(client);
	return it != sessions.end() && it->second.loaded && client->Connected() && client->ClientDataLoaded() ? &it->second : nullptr;
}
std::string InventoryState(Client *client) {
	std::string result;
	const auto append = [&](int16 slot, const EQ::ItemInstance *item) {
		if (!item) { return; }
		result += fmt::format("{}:{}:{}:{}|", slot, item->GetID(), item->GetSerialNumber(), item->GetCharges());
		for (int i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) { result += std::to_string(item->GetAugmentItemID(i)) + ","; }
	};
	for (int16 slot = EQ::invslot::POSSESSIONS_BEGIN; slot <= EQ::invslot::POSSESSIONS_END; ++slot) {
		const auto item = client->GetInv().GetItem(slot);
		append(slot, item);
		if (item && item->IsClassBag() && EQ::InventoryProfile::SupportsContainers(slot)) {
			for (uint8 i = 0; i < EQ::invbag::SLOT_COUNT; ++i) { append(EQ::InventoryProfile::CalcSlotId(slot, i), item->GetItem(i)); }
		}
	}
	return result;
}
std::string Text(std::string value, size_t maximum = 63) {
	if (value.size() > maximum) { value.resize(maximum); }
	for (char &c : value) { if (static_cast<unsigned char>(c) < 32 || static_cast<unsigned char>(c) > 126) { c = '?'; } }
	return value.empty() ? "Unknown" : value;
}
bool Consent(const LootItem &loot) {
	const auto item = database.GetItem(loot.item_id);
	if (!item || !item->NoDrop || item->NoTransfer || loot.attuned) { return true; }
	for (auto id : {loot.aug_1, loot.aug_2, loot.aug_3, loot.aug_4, loot.aug_5, loot.aug_6}) {
		if (!id) { continue; }
		const auto augment = database.GetItem(id);
		if (!augment || !augment->NoDrop || augment->NoTransfer) { return true; }
	}
	return false;
}
bool BagChild(Corpse *corpse, LootItem *item) {
	for (const auto parent : corpse->GetLootItems()) {
		if (parent == item || !EQ::InventoryProfile::SupportsContainers(parent->equip_slot)) { continue; }
		const auto data = database.GetItem(parent->item_id);
		if (!data || data->ItemClass != EQ::item::ItemClassBag) { continue; }
		const int16 first = EQ::InventoryProfile::CalcSlotId(parent->equip_slot, 0);
		if (item->equip_slot >= first && item->equip_slot < first + EQ::invbag::SLOT_COUNT) { return true; }
	}
	return false;
}
bool RequiresConsent(Corpse *corpse, LootItem *item) {
	if (Consent(*item)) { return true; }
	const auto data = database.GetItem(item->item_id);
	if (data && data->ItemClass == EQ::item::ItemClassBag && EQ::InventoryProfile::SupportsContainers(item->equip_slot)) {
		const int16 first = EQ::InventoryProfile::CalcSlotId(item->equip_slot, 0);
		for (const auto child : corpse->GetLootItems()) {
			if (child != item && child->equip_slot >= first && child->equip_slot < first + EQ::invbag::SLOT_COUNT && Consent(*child)) { return true; }
		}
	}
	return false;
}
uint32 Master(const std::vector<uint32> &rights) {
	if (rights.empty()) { return 0; }
	for (auto character : rights) {
		const auto client = entity_list.GetClientByCharID(character);
		if (!client || !client->Connected() || !client->ClientDataLoaded()) { continue; }
		Mob *leader = client->GetRaid() ? static_cast<Mob *>(client->GetRaid()->GetLeader()) :
			client->GetGroup() ? client->GetGroup()->GetLeader() : nullptr;
		if (leader && leader->IsClient() && leader->CastToClient()->Connected() && leader->CastToClient()->ClientDataLoaded()) {
			const auto id = leader->CastToClient()->CharacterID();
			if (std::find(rights.begin(), rights.end(), id) != rights.end()) { return id; }
		}
	}
	for (auto character : rights) {
		const auto client = entity_list.GetClientByCharID(character);
		if (client && client->Connected() && client->ClientDataLoaded()) { return character; }
	}
	return 0;
}
DropPolicy::Checkpoint Decode(const Json &record) {
	const auto number = [](const Json &value, uint64 maximum) {
		if (!value.is_number_integer() || value.get<int64_t>() < 0 || value.get<uint64>() > maximum) { throw std::invalid_argument("distribution number"); }
		return static_cast<uint32>(value.get<uint64>());
	};
	DropPolicy::Checkpoint saved;
	saved.master = number(record.at("master"), INT32_MAX); saved.recipient = number(record.at("recipient"), INT32_MAX);
	saved.remaining = number(record.at("remaining"), 60000); saved.state = static_cast<Distribution>(number(record.at("state"), static_cast<uint32>(Distribution::Expired)));
	if (!record.at("members").is_array() || record.at("members").size() > 72) { throw std::invalid_argument("distribution roster"); }
	for (const auto &member : record.at("members")) {
		if (!member.is_array() || member.size() != 3) { throw std::invalid_argument("distribution member"); }
		const auto character = number(member.at(0), INT32_MAX);
		if (!saved.filters.emplace(character, static_cast<Filter>(number(member.at(1), 4))).second ||
			!saved.choices.emplace(character, static_cast<Choice>(number(member.at(2), 3))).second) { throw std::invalid_argument("duplicate member"); }
	}
	return saved;
}
Json Encode(const DropPolicy &policy, uint64 now) {
	const auto saved = policy.Save(now);
	Json members = Json::array();
	for (const auto &[character, filter] : saved.filters) { members.push_back({character, static_cast<uint32>(filter), static_cast<uint32>(saved.choices.at(character))}); }
	return {{"master", saved.master}, {"recipient", saved.recipient}, {"remaining", saved.remaining},
		{"state", static_cast<uint32>(saved.state)}, {"members", members}};
}
std::shared_ptr<CorpseEntry> Ensure(Corpse *corpse) {
	if (!corpse || !corpse->IsNPCCorpse() || corpse->IsBecomeNPCCorpse()) { return {}; }
	auto found = corpses.find(corpse);
	if (found != corpses.end() && Alive(*found->second)) { return found->second; }
	auto entry = std::make_shared<CorpseEntry>();
	entry->corpse = corpse; entry->spawn = corpse->GetID(); entry->generation = NewDropID();
	corpse->SetEntityVariable(GenerationKey, entry->generation);
	corpses[corpse] = entry;
	return entry;
}
void Reconcile(const std::shared_ptr<CorpseEntry> &entry) {
	if (!Alive(*entry) || entry->invalid) { return; }
	Corpse *corpse = entry->corpse;
	try {
		if (!entry->restored_loaded) {
			const auto raw = corpse->GetEntityVariable(DistributionKey);
			entry->restored = raw.empty() ? Json::object() : Json::parse(raw);
			entry->restored_loaded = true;
		}
		const auto &saved = entry->restored;
		if (!saved.is_object()) { throw std::invalid_argument("distribution"); }
		const auto rights = corpse->AdvancedLootRights();
		const auto master = Master(rights);
		std::map<uint32, Filter> participants;
		bool enabled = false;
		for (auto character : rights) {
			participants[character] = Filter::Ask;
			if (auto session = Active(character); session && (session->preferences.settings & Enabled)) { enabled = true; }
		}
		std::vector<LootItem *> items(corpse->GetLootItems().begin(), corpse->GetLootItems().end());
		std::set<std::string> live;
		for (auto item : items) {
			if (item->advanced_loot_id.empty()) { item->advanced_loot_id = NewDropID(); }
			if (!ValidDropID(item->advanced_loot_id) || !live.insert(item->advanced_loot_id).second) { throw std::invalid_argument("physical drop identity"); }
			auto &drop = entry->drops[item->advanced_loot_id];
			if (!drop) {
				drop = std::make_shared<Drop>(); drop->item = item; drop->id = item->advanced_loot_id; drop->token = Allocate(next_token);
				if (saved.contains(drop->id)) { drop->policy = std::make_unique<DropPolicy>(DropPolicy::Restore(Decode(saved.at(drop->id)), Now())); }
			}
			if (drop->item != item) { throw std::invalid_argument("reused drop identity"); }
			if (!drop->policy && enabled && master && !BagChild(corpse, item)) {
				drop->policy = std::make_unique<DropPolicy>(master, participants, participants.size() == 1);
			}
			if (drop->transferring) { continue; }
			if (drop->unavailable && Now() >= drop->claim_retry) {
				drop->claim_retry = Now() + 5000;
				const auto claim = ReadClaim(drop->id);
				drop->claimed = claim == ClaimStatus::Claimed;
				drop->unavailable = claim == ClaimStatus::Unavailable;
			}
			if (drop->claimed) { corpse->RemoveItem(item); continue; }
			if (drop->policy) {
				const auto owner = entity_list.GetClientByCharID(drop->policy->Master());
				if (!owner || !owner->Connected() || !owner->ClientDataLoaded() || !corpse->CanPlayerLoot(owner->CharacterID())) {
					std::vector<uint32> remaining;
					for (auto character : rights) { if (drop->policy->HasParticipant(character)) { remaining.push_back(character); } }
					drop->policy->SetMaster(Master(remaining));
				}
				for (const auto &[character, unused] : participants) {
					if (auto session = Active(character)) { drop->policy->UpdateFilter(character, session->preferences.Effective(item->item_id)); }
				}
				drop->policy->Resolve(Now(), [&](uint32 character) { const auto client = entity_list.GetClientByCharID(character); return client && client->Connected() && client->ClientDataLoaded() && corpse->CanPlayerLoot(character); },
					[](size_t count) { return static_cast<size_t>(zone->random.Int(0, count - 1)); });
			}
		}
		for (auto it = entry->drops.begin(); it != entry->drops.end();) {
			if (!live.count(it->first) || !Present(*entry, *it->second)) { it = entry->drops.erase(it); } else { ++it; }
		}
	} catch (const std::exception &error) {
		entry->invalid = true; corpse->Lock();
		LogError("Advanced loot: corpse [{}] distribution quarantined: [{}]", entry->spawn, error.what());
	}
}
bool Public(const CorpseEntry &entry, const Drop &drop) {
	return entry.corpse->AdvancedLootRights().empty() || !drop.policy || drop.policy->State() == Distribution::Left;
}
bool Visible(Session &session, const CorpseEntry &entry, const Drop &drop) {
	if (!Present(entry, drop) || entry.invalid || drop.claimed || BagChild(entry.corpse, drop.item) ||
		!entry.corpse->CanPlayerLoot(session.client->CharacterID())) { return false; }
	if (drop.policy && (drop.policy->State() == Distribution::Consumed || drop.policy->State() == Distribution::Expired || drop.policy->State() == Distribution::Left)) { return false; }
	if (session.preferences.Effective(drop.item->item_id) == Filter::Never &&
		(Public(entry, drop) || drop.policy->State() == Distribution::Personal ||
		(drop.policy->State() == Distribution::Awarded && drop.policy->Recipient() == session.client->CharacterID()))) { return false; }
	if (entry.corpse->AdvancedLootRights().empty()) {
		return DistanceSquaredNoZ(session.client->GetPosition(), entry.corpse->GetPosition()) <= 625;
	}
	return true;
}
bool CanTake(Session &session, const CorpseEntry &entry, const Drop &drop, bool classic = false) {
	if (drop.claimed || drop.unavailable || drop.transferring || entry.invalid || !Present(entry, drop)) { return false; }
	const bool classic_override = classic && entry.corpse->ClassicLootOverride(session.client);
	if ((!classic_override && session.preferences.Effective(drop.item->item_id) == Filter::Never) ||
		!entry.corpse->AdvancedLootAccessible(session.client, false, classic)) { return false; }
	if (drop.policy && (drop.policy->State() == Distribution::Quarantined || drop.policy->State() == Distribution::Consumed)) { return false; }
	return classic_override || Public(entry, drop) || drop.policy->CanTake(session.client->CharacterID());
}
Row MakeRow(Session &session, const CorpseEntry &entry, const Drop &drop) {
	const auto item = database.GetItem(drop.item->item_id);
	Row row;
	row.token = drop.token; row.corpse = entry.spawn; row.item = drop.item->item_id;
	row.quantity = item && item->Stackable ? std::max<uint32>(1, drop.item->charges) : 1;
	row.icon = item && item->Icon <= 65535 ? item->Icon : 0; row.name = Text(item ? item->Name : "Unknown item");
	row.source = Text(entry.corpse->GetCleanName()); row.filter = session.preferences.Saved(row.item);
	row.capabilities = Capability(Action::Inspect) | Capability(Action::FindCorpse) | Capability(Action::EditFilter);
	row.phase = Phase::FreeGrab;
	if (drop.policy && drop.policy->State() == Distribution::Quarantined) {
		row.phase = Phase::Shared; row.source = Text("Transfer needs review - " + row.source); return row;
	}
	if (drop.policy && !Public(entry, drop)) {
		const auto person = [](uint32 character) {
			const auto client = entity_list.GetClientByCharID(character);
			return client ? std::string(client->GetCleanName()) : std::to_string(character);
		};
		if (drop.policy->State() == Distribution::Awarded) { row.source = Text("To " + person(drop.policy->Recipient()) + " - " + row.source); }
		else if (drop.policy->State() != Distribution::Personal) { row.source = Text("ML " + person(drop.policy->Master()) + " - " + row.source); }
		switch (drop.policy->State()) {
		case Distribution::Personal: row.phase = Phase::Personal; break;
		case Distribution::Shared: row.phase = Phase::Shared; break;
		case Distribution::Rolling: row.phase = Phase::Rolling; break;
		case Distribution::Awarded: row.phase = Phase::Awarded; break;
		default: break;
		}
		const auto character = session.client->CharacterID();
		if (drop.policy->State() == Distribution::Rolling && drop.policy->HasParticipant(character)) {
			const auto choice = drop.policy->Selected(character);
			if (choice != Choice::None) { row.source = Text(std::string(choice == Choice::Need ? "Need: " : choice == Choice::Greed ? "Greed: " : "Pass: ") + row.source); }
			row.capabilities |= Capability(Action::Pass);
			if (session.preferences.Effective(row.item) != Filter::Never) { row.capabilities |= Capability(Action::Need) | Capability(Action::Greed); }
		}
		if (character == drop.policy->Master() && (row.phase == Phase::Shared || row.phase == Phase::Rolling || row.phase == Phase::Awarded || row.phase == Phase::FreeGrab)) {
			row.capabilities |= Capability(Action::Roll) | Capability(Action::FreeGrab) | Capability(Action::Assign);
		}
		if (character == drop.policy->Master() || (row.phase == Phase::Awarded && character == drop.policy->Recipient())) { row.capabilities |= Capability(Action::Leave); }
	}
	if (CanTake(session, entry, drop)) { row.capabilities |= Capability(RequiresConsent(entry.corpse, drop.item) ? Action::TakeNoTrade : Action::Take); }
	return row;
}
void Publish(Session &session, bool force) {
	if (!session.loaded || !session.client->Connected() || !session.client->ClientDataLoaded() || !zone) { return; }
	auto &snapshot = session.snapshot;
	snapshot.identity = {session.client->CharacterID(), zone->GetZoneID(), zone->GetInstanceID(), session.client->GetID(), Text(session.client->GetName())};
	snapshot.settings = session.preferences.settings;
	std::vector<Row> rows;
	if (snapshot.view == View::Filters) {
		for (const auto &[id, filter] : session.preferences.filters) {
			const auto item = database.GetItem(id);
			if (!item) { continue; }
			Row row; row.token = id; row.item = id; row.quantity = 0; row.icon = item->Icon <= 65535 ? item->Icon : 0;
			row.name = Text(item->Name); row.source = "Saved filter"; row.phase = Phase::FilterRecord; row.filter = filter;
			row.capabilities = Capability(Action::Inspect) | Capability(Action::EditFilter); rows.push_back(std::move(row));
		}
	} else {
		for (const auto &[corpse, entry] : corpses) {
			for (const auto &[id, drop] : entry->drops) {
				if (!Visible(session, *entry, *drop) || (snapshot.settings & ShowNewOnly && session.preferences.Saved(drop->item->item_id) != Filter::Ask)) { continue; }
				rows.push_back(MakeRow(session, *entry, *drop));
			}
		}
	}
	const auto search = Strings::ToLower(session.search);
	rows.erase(std::remove_if(rows.begin(), rows.end(), [&](const Row &row) { return Strings::ToLower(row.name).find(search) == std::string::npos; }), rows.end());
	std::sort(rows.begin(), rows.end(), [](const Row &a, const Row &b) { return a.token < b.token; });
	if (rows.size() > MaxResults) { rows.resize(MaxResults); }
	snapshot.total = rows.size();
	snapshot.page = std::min<uint32>(snapshot.page, rows.empty() ? 0 : (rows.size() - 1) / PageSize);
	const size_t first = snapshot.page * PageSize, last = std::min(rows.size(), first + PageSize);
	snapshot.rows.assign(rows.begin() + first, rows.begin() + last);
	Snapshot signature = snapshot; signature.revision = 0;
	std::string encoded = Begin(signature);
	for (const auto &row : signature.rows) { encoded += Item(signature, row); }
	if (!force && session.signature == encoded) { return; }
	session.signature = std::move(encoded);
	if (snapshot.revision == UINT32_MAX) { session.client->Message(Chat::Yellow, "Reconnect to renew your advanced loot session."); return; }
	// A prompt belongs to one exact published list. A changed/forced snapshot
	// invalidates it; an All request arms a new prompt only after publication.
	if (session.pending_revision) { session.ClearConfirmation(); }
	++snapshot.revision;
	const auto send = [&](const std::string &text) { if (text.size() <= MaxMessage) { session.client->Message(Chat::White, "%s", text.c_str()); } };
	send(Begin(snapshot)); for (const auto &row : snapshot.rows) { send(Item(snapshot, row)); } send(End(snapshot));
}
TransferResult Take(Session &session, const std::shared_ptr<CorpseEntry> &entry, const std::shared_ptr<Drop> &drop, bool consent, bool automatic,
	Destination destination = Destination::Inventory) {
	const bool classic = destination != Destination::Inventory;
	if (!CanTake(session, *entry, *drop, classic) || (!consent && RequiresConsent(entry->corpse, drop->item))) { return TransferResult::Declined; }
	drop->transferring = true;
	const auto transfer = [&]() { return entry->corpse->LootAdvancedItem(session.client, drop->item, consent, automatic, destination); };
	TransferResult result = TransferResult::Uncertain;
	try { result = Public(*entry, *drop) || (classic && entry->corpse->ClassicLootOverride(session.client)) ? transfer() : drop->policy->Take(session.client->CharacterID(), transfer); }
	catch (...) { session.client->QuarantineItemTransfer("Loot was interrupted. Reconnect to reload your inventory."); }
	drop->transferring = false;
	drop->claimed = result == TransferResult::Delivered;
	drop->unavailable = result != TransferResult::Delivered;
	if (Alive(*entry)) { SaveDistribution(entry->corpse); }
	return result;
}
void Discover() {
	std::vector<Corpse *> list;
	for (const auto &[id, corpse] : entity_list.GetCorpseList()) { if (corpse->IsNPCCorpse() && !corpse->IsBecomeNPCCorpse()) { list.push_back(corpse); } }
	for (auto corpse : list) { Reconcile(Ensure(corpse)); }
}
void RefreshAll(bool force = false) {
	for (auto &[client, session] : sessions) { Publish(session, force); }
}
std::vector<LootItem> PhysicalItems(const CorpseEntry &entry, const Drop &drop) {
	std::vector<LootItem> items{*drop.item};
	const auto data = database.GetItem(drop.item->item_id);
	if (data && data->ItemClass == EQ::item::ItemClassBag && EQ::InventoryProfile::SupportsContainers(drop.item->equip_slot)) {
		const int16 first = EQ::InventoryProfile::CalcSlotId(drop.item->equip_slot, 0);
		for (const auto child : entry.corpse->GetLootItems()) {
			if (child != drop.item && child->equip_slot >= first && child->equip_slot < first + EQ::invbag::SLOT_COUNT) { items.push_back(*child); }
		}
	}
	std::sort(items.begin(), items.end(), [](const LootItem &a, const LootItem &b) { return a.advanced_loot_id < b.advanced_loot_id; });
	return items;
}
bool SamePending(const PendingLoot &pending) {
	if (!Present(*pending.entry, *pending.drop)) { return false; }
	const auto current = PhysicalItems(*pending.entry, *pending.drop);
	return current.size() == pending.items.size() && std::equal(current.begin(), current.end(), pending.items.begin(), SamePhysicalLoot);
}
void LootAll(Session &session, bool confirmed) {
	auto client = session.client;
	std::vector<std::pair<std::shared_ptr<CorpseEntry>, std::shared_ptr<Drop>>> selected;
	if (confirmed) {
		if (!session.pending_revision || session.pending_revision != session.snapshot.revision ||
			Now() >= session.pending_until || session.pending_no_trade.empty() ||
			!std::all_of(session.pending_no_trade.begin(), session.pending_no_trade.end(), [&](const PendingLoot &pending) {
				return SamePending(pending) && Visible(session, *pending.entry, *pending.drop) &&
					CanTake(session, *pending.entry, *pending.drop) && RequiresConsent(pending.entry->corpse, pending.drop->item);
			})) {
			session.ClearConfirmation(); Publish(session, true);
			client->Message(Chat::Yellow, "Advanced loot: The list changed. Click Loot All to review NO TRADE items again."); return;
		}
		// Never expand consent to drops that arrived after the prompt.
		for (const auto &pending : session.pending_no_trade) { selected.emplace_back(pending.entry, pending.drop); }
	} else {
		for (const auto &[corpse, entry] : corpses) {
			for (const auto &[id, drop] : entry->drops) {
				if (!Visible(session, *entry, *drop)) { continue; }
				const auto item = database.GetItem(drop->item->item_id);
				if (!item || (session.preferences.settings & ShowNewOnly && session.preferences.Saved(item->ID) != Filter::Ask) ||
					Strings::ToLower(item->Name).find(Strings::ToLower(session.search)) == std::string::npos) { continue; }
				selected.emplace_back(entry, drop);
			}
		}
	}
	// Match the complete paged list's order and bound; never confirm drops
	// omitted by the UI result limit. Further drops appear after this batch.
	std::sort(selected.begin(), selected.end(), [](const auto &a, const auto &b) { return a.second->token < b.second->token; });
	if (selected.size() > MaxResults) { selected.resize(MaxResults); }
	// Retain the physical preimages for revalidation after each quest callback.
	const auto confirmation = session.pending_no_trade;
	// Consume a confirmation before any transfer so a replay cannot reuse it.
	session.ClearConfirmation();
	uint32 delivered = 0, unavailable = 0;
	bool uncertain = false;
	for (const auto &[entry, drop] : selected) {
		if (!Present(*entry, *drop)) { ++unavailable; continue; }
		if (confirmed && !std::any_of(confirmation.begin(), confirmation.end(), [&](const PendingLoot &pending) {
			return pending.entry == entry && pending.drop == drop && SamePending(pending);
		})) { ++unavailable; continue; }
		const auto caps = MakeRow(session, *entry, *drop).capabilities;
		if (!confirmed && (caps & Capability(Action::TakeNoTrade))) {
			session.pending_no_trade.push_back({entry, drop, PhysicalItems(*entry, *drop)}); continue;
		}
		if (!(caps & Capability(confirmed ? Action::TakeNoTrade : Action::Take))) { ++unavailable; continue; }
		const auto result = Take(session, entry, drop, confirmed, false);
		if (result == TransferResult::Delivered) { ++delivered; }
		else if (result == TransferResult::Declined) { ++unavailable; }
		else { uncertain = true; break; }
	}
	Discover(); RefreshAll(); Publish(session, true);
	if (uncertain) {
		session.ClearConfirmation();
		client->Message(Chat::Red, "Advanced loot: A transfer could not be confirmed. Reconnect before looting again.");
	} else if (!session.pending_no_trade.empty()) {
		session.pending_revision = session.snapshot.revision; session.pending_until = Now() + 30000;
		client->Message(Chat::Yellow, "Advanced loot: Confirm NO TRADE for %u item(s). Looted %u; %u unavailable.",
			static_cast<uint32>(session.pending_no_trade.size()), delivered, unavailable);
	} else if (unavailable) {
		client->Message(Chat::Yellow, "Advanced loot: Looted %u item(s); %u unavailable. Check bags, lore, cursor or group rights.", delivered, unavailable);
	} else {
		client->Message(Chat::Yellow, "Advanced loot: Looted %u item(s).", delivered);
	}
}
}

void SaveDistribution(Corpse *corpse) {
	const auto it = corpses.find(corpse);
	if (it == corpses.end() || !Alive(*it->second) || it->second->invalid) { return; }
	Json saved = Json::object();
	for (const auto &[id, drop] : it->second->drops) { if (drop->policy && Present(*it->second, *drop)) { saved[id] = Encode(*drop->policy, Now()); } }
	corpse->SetEntityVariable(DistributionKey, saved.dump());
}
void Forget(Client *client) { sessions.erase(client); }
void Forget(Corpse *corpse) { corpses.erase(corpse); }

void Pulse(Client *client) {
	if (pumping || sessions.empty() || !client || !client->Connected() || !client->ClientDataLoaded() || !zone || Now() < next_pulse) { return; }
	next_pulse = Now() + 500;
	pumping = true;
	try {
		Discover();
		std::vector<std::shared_ptr<CorpseEntry>> entries;
		for (const auto &[corpse, entry] : corpses) { entries.push_back(entry); }
		for (const auto &entry : entries) {
			if (!Alive(*entry) || entry->invalid) { continue; }
			if (!entry->corpse->IsBeingLooted() && Now() >= entry->next_coin) {
				const auto rights = entry->corpse->AdvancedLootRights();
				if (auto owner = Active(Master(rights)); owner && (owner->preferences.settings & Enabled) && entry->corpse->AdvancedLootAccessible(owner->client)) {
					entry->next_coin = Now() + 10000;
					TakeCoins(entry->corpse, owner->client, owner->preferences.settings & AutoSplitCoin);
				}
			}
			std::vector<std::shared_ptr<Drop>> drops;
			for (const auto &[id, drop] : entry->drops) { drops.push_back(drop); }
			for (const auto &drop : drops) {
				if (!Present(*entry, *drop) || !drop->policy || Public(*entry, *drop) || RequiresConsent(entry->corpse, drop->item)) { continue; }
				const auto character = drop->policy->Recipient();
				auto session = Active(character);
				if (!session || Now() < drop->retry[character]) { continue; }
				const auto failed = drop->failed_inventory.find(character);
				if (failed != drop->failed_inventory.end() && failed->second == InventoryState(session->client)) { continue; }
				const auto settings = session->preferences.settings;
				if (!drop->policy->ShouldAutoTake(character, settings & Enabled, settings & ApplyFilters, settings & AutoTakeAll) ||
					!CanTake(*session, *entry, *drop)) { continue; }
				drop->retry[character] = Now() + 10000;
				if (Take(*session, entry, drop, false, true) == TransferResult::Declined) { drop->failed_inventory[character] = InventoryState(session->client); }
			}
		}
		RefreshAll();
	} catch (const std::exception &error) { LogError("Advanced loot pulse stopped: [{}]", error.what()); }
	pumping = false;
}

bool PrepareClassic(Corpse *corpse, Client *client) {
	if (!corpse || !client || !corpse->IsNPCCorpse() || corpse->IsBecomeNPCCorpse()) { return true; }
	auto entry = Ensure(corpse); Reconcile(entry);
	return !entry->invalid && corpse->GetEntityVariable("nightcap:advloot-invalid-state").empty();
}

TransferResult TakeClassic(Corpse *corpse, Client *client, LootItem *item, bool auto_loot) {
	if (!PrepareClassic(corpse, client) || !item) { return TransferResult::Declined; }
	// Reconciliation may have removed a previously claimed saved drop.
	const auto &remaining = corpse->GetLootItems();
	if (std::find(remaining.begin(), remaining.end(), item) == remaining.end()) { return TransferResult::Declined; }
	const auto entry = Ensure(corpse);
	const auto it = entry->drops.find(item->advanced_loot_id);
	if (it == entry->drops.end()) { return TransferResult::Declined; }
	Session temporary; temporary.client = client;
	if (!LoadPreferences(client->CharacterID(), temporary.preferences)) { return TransferResult::Declined; }
	auto session = Active(client->CharacterID());
	return Take(session ? *session : temporary, entry, it->second, true, false, auto_loot ? Destination::InventoryOrCursor : Destination::Cursor);
}

void Command(Client *client, const Seperator *arguments) {
	if (!client || !client->Connected() || !client->ClientDataLoaded() || !zone || !arguments) { return; }
	auto &session = sessions[client]; session.client = client;
	if (Now() < session.next_command) {
		session.ClearConfirmation();
		client->Message(Chat::Yellow, "Advanced loot: Please wait a moment before trying again."); return;
	}
	session.next_command = Now() + 100;
	try {
		if (!session.loaded) {
			if (!LoadPreferences(client->CharacterID(), session.preferences)) { client->Message(Chat::Red, "Advanced loot settings could not be loaded. Try again shortly."); return; }
			session.loaded = true; if (!session.snapshot.session) { session.snapshot.session = Allocate(next_session); }
		}
		Discover();
		const std::string verb = arguments->arg[1];
		if (verb != "allconfirm") { session.ClearConfirmation(); }
		uint32 sid = 0, revision = 0;
		const bool refresh = arguments->argnum == 0 || (arguments->argnum == 1 && verb == "refresh");
		if (!refresh && (!Number(arguments->arg[2], sid) || !Number(arguments->arg[3], revision) ||
			sid != session.snapshot.session || revision != session.snapshot.revision)) {
			session.ClearConfirmation(); Publish(session, true);
			client->Message(Chat::Yellow, "Advanced loot: The list changed. Select the item again."); return;
		}
		uint32 a = 0, b = 0, recipient = 0;
		if (refresh) {
			for (const auto &[corpse, entry] : corpses) { for (const auto &[id, drop] : entry->drops) { drop->failed_inventory.erase(client->CharacterID()); } }
			Publish(session, true); return;
		}
		if (verb == "settings" && arguments->argnum == 4 && Number(arguments->arg[4], a) && !(a & ~AllSettings)) {
			if (SaveSettings(client->CharacterID(), a)) { session.preferences.settings = a; }
			else { session.loaded = false; client->Message(Chat::Red, "Your loot settings could not be saved. Refresh to reload them."); return; }
		} else if (verb == "filter" && arguments->argnum == 5 && Number(arguments->arg[4], a) && Number(arguments->arg[5], b) && b <= 4) {
			const auto row = std::find_if(session.snapshot.rows.begin(), session.snapshot.rows.end(), [&](const Row &r) { return r.item == a && (r.capabilities & Capability(Action::EditFilter)); });
			if (row == session.snapshot.rows.end()) { Publish(session, true); return; }
			if (!SaveFilter(client->CharacterID(), a, static_cast<Filter>(b))) { session.loaded = false; client->Message(Chat::Red, "Your loot filter could not be saved. Refresh to reload it."); return; }
			if (!b) { session.preferences.filters.erase(a); } else { session.preferences.filters[a] = static_cast<Filter>(b); }
			for (const auto &[corpse, entry] : corpses) { for (const auto &[id, drop] : entry->drops) { drop->failed_inventory.erase(client->CharacterID()); } }
		} else if (verb == "view" && arguments->argnum == 6 && Number(arguments->arg[4], a) && a <= 1 && Number(arguments->arg[5], b)) {
			std::string search;
			if (std::string(arguments->arg[6]) != "-" && !Unhex(arguments->arg[6], search, 32)) { Publish(session, true); return; }
			session.search = search; session.snapshot.view = static_cast<View>(a); session.snapshot.page = b;
		} else if ((verb == "all" || verb == "allconfirm") && arguments->argnum == 3) {
			if (session.snapshot.view != View::Drops) { session.ClearConfirmation(); Publish(session, true); return; }
			LootAll(session, verb == "allconfirm"); return;
		} else if (verb == "act" && arguments->argnum == 6 && Number(arguments->arg[4], a) && Number(arguments->arg[5], b) &&
			Number(arguments->arg[6], recipient) && b <= static_cast<uint32>(Action::EditFilter)) {
			const auto action = static_cast<Action>(b);
			if (action != Action::Assign && recipient) { Publish(session, true); return; }
			{
				const auto row = std::find_if(session.snapshot.rows.begin(), session.snapshot.rows.end(), [&](const Row &r) { return r.token == a && (r.capabilities & Capability(action)); });
				if (row == session.snapshot.rows.end()) { Publish(session, true); return; }
				if (session.snapshot.view == View::Filters) {
					if (action == Action::Inspect) { std::unique_ptr<EQ::ItemInstance> item(database.CreateItem(row->item)); if (item) { client->SendItemPacket(0, item.get(), ItemPacketViewLink); } }
					Publish(session, true); return;
				}
			}
			std::vector<std::pair<std::shared_ptr<CorpseEntry>, std::shared_ptr<Drop>>> selected;
			for (const auto &[corpse, entry] : corpses) {
				for (const auto &[id, drop] : entry->drops) { if (drop->token == a && Visible(session, *entry, *drop)) {
					selected.emplace_back(entry, drop);
				} }
			}
			for (const auto &[entry, drop] : selected) {
				if (!Present(*entry, *drop)) { continue; }
				const auto caps = MakeRow(session, *entry, *drop).capabilities;
				if (!(caps & Capability(action))) { continue; }
				const auto character = client->CharacterID();
				if (action == Action::Take || action == Action::TakeNoTrade) {
					if (Take(session, entry, drop, action == Action::TakeNoTrade, false) == TransferResult::Declined) { client->Message(Chat::Yellow, "That item could not be looted. Check your inventory, lore items and corpse access."); }
				} else if (action == Action::FindCorpse) { client->SendPath(entry->corpse); }
				else if (action == Action::Inspect) {
					const auto &i = *drop->item;
					std::unique_ptr<EQ::ItemInstance> item(database.CreateItem(i.item_id, i.charges, i.aug_1, i.aug_2, i.aug_3, i.aug_4, i.aug_5, i.aug_6, i.attuned, i.custom_data, i.ornamenticon, i.ornamentidfile, i.ornament_hero_model));
					if (item) { client->SendItemPacket(0, item.get(), ItemPacketViewLink); }
				} else if (drop->policy) {
					if (action == Action::Leave) { drop->policy->Leave(character); }
					if (action == Action::Roll) { drop->policy->StartRoll(character, Now()); }
					if (action == Action::FreeGrab) { drop->policy->OpenFreeGrab(character); }
					if (action == Action::Need || action == Action::Greed || action == Action::Pass) { drop->policy->Choose(character, action == Action::Need ? Choice::Need : action == Action::Greed ? Choice::Greed : Choice::Pass, Now()); }
					if (action == Action::Assign) {
						if (!recipient && client->GetTarget() && client->GetTarget()->IsClient()) { recipient = client->GetTarget()->CastToClient()->CharacterID(); }
						if (!recipient || !entry->corpse->CanPlayerLoot(recipient) || !drop->policy->Assign(character, recipient)) { client->Message(Chat::Yellow, "Target an eligible group or raid member to assign this item."); }
					}
				}
				if (Alive(*entry)) { SaveDistribution(entry->corpse); }
			}
		} else { client->Message(Chat::Yellow, "Use /advloot to manage loot and saved item filters."); }
		Discover(); RefreshAll(); Publish(session, true);
		if (verb == "filter") {
			client->Message(Chat::Yellow, b == static_cast<uint32>(Filter::Never) ?
				"Advanced loot: Item added to your ignore filter." : !b ?
				"Advanced loot: Item removed from your filter list." : "Advanced loot: Item rule saved.");
		}
	} catch (const std::exception &error) { LogError("Advanced loot command stopped: [{}]", error.what()); client->Message(Chat::Red, "Advanced loot could not finish that action. Refresh the window."); }
}
}

void command_advloot(Client *c, const Seperator *sep) { NightcapLoot::Command(c, sep); }

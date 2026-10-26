#include "zone/client.h"
#include "zone/command.h"
#include "zone/advanced_loot_inventory.h"
#include "common/say_link.h"
#include "common/bazaar_panel_query.h"
#include <chrono>
#include <memory>

namespace {
using namespace NightcapBazaar;
uint64 Now() { return std::chrono::duration_cast<std::chrono::seconds>(std::chrono::steady_clock::now().time_since_epoch()).count(); }
Reply BazaarQuery(const std::string &sql)
{
	auto result = database.QueryDatabase(sql, false);
	Reply reply{result.Success(), result.RowsAffected(), result.LastInsertedID(), {}};
	if (reply.ok) {
		for (auto row : result) {
			Row fields;
			for (uint32 i = 0; i < result.ColumnCount(); ++i) { fields.push_back(row[i] ? row[i] : ""); }
			reply.rows.push_back(std::move(fields));
		}
	}
	return reply;
}
std::string Hex(const std::string &text)
{
	static const char digits[] = "0123456789ABCDEF";
	std::string out;
	for (unsigned char c : text) { out += digits[c >> 4]; out += digits[c & 15]; }
	return out;
}
std::string Unhex(const std::string &text)
{
	std::string out;
	for (size_t i = 0; i < text.size(); i += 2) { out += static_cast<char>(std::stoul(text.substr(i, 2), nullptr, 16)); }
	return out;
}
Row Snapshot(uint32 character, int16 slot, const EQ::ItemInstance &item)
{
	Row row{std::to_string(character), std::to_string(slot), std::to_string(item.GetID()),
		std::to_string(item.GetCharges() < 0 ? 32767 : item.GetCharges()), std::to_string(item.GetColor())};
	for (uint8 i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) { row.push_back(std::to_string(item.GetAugmentItemID(i))); }
	row.push_back(item.IsAttuned() ? "1" : "0"); row.push_back(Hex(item.GetCustomDataString()));
	row.push_back(std::to_string(item.GetOrnamentationIcon())); row.push_back(std::to_string(item.GetOrnamentationIDFile()));
	row.push_back(std::to_string(item.GetOrnamentHeroModel())); row.push_back(std::to_string(uint32(item.GetSerialNumber())));
	return row;
}
bool Transferable(const EQ::ItemInstance *item)
{
	if (!item || !item->GetItem() || !item->GetItem()->NoDrop || !item->GetItem()->NoRent ||
		item->IsAttunedForTrade() || item->IsEvolving() || item->IsScaling()) { return false; }
	for (uint8 i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) {
		const auto augment = item->GetAugment(i);
		if (augment && !Transferable(augment)) { return false; }
	}
	return true;
}
std::unique_ptr<EQ::ItemInstance> Restore(const Row &row)
{
	if (row.size() != Columns().size()) { return {}; }
	std::unique_ptr<EQ::ItemInstance> item(database.CreateItem(Number(row[2]), Number(row[3]) == 32767 ? -1 : Number(row[3]),
		Number(row[5]), Number(row[6]), Number(row[7]), Number(row[8]), Number(row[9]), Number(row[10])));
	if (!item) { return {}; }
	item->SetCharges(Number(row[3]) == 32767 ? -1 : Number(row[3]));
	// 32767 is the native saved sentinel for unlimited charges, never a stack.
	if (item->IsStackable() && item->GetCharges() <= 0) { return {}; }
	item->SetColor(Number(row[4])); item->SetAttuned(Number(row[11]) != 0);
	item->SetCustomDataString(Unhex(row[12])); item->SetOrnamentIcon(Number(row[13]));
	item->SetOrnamentationIDFile(Number(row[14])); item->SetOrnamentHeroModel(std::stoll(row[15]));
	if (!SameItems(Rows{row}, Rows{Snapshot(Number(row[0]), Number(row[1]), *item)})) { return {}; }
	return item;
}
bool CursorSnapshot(Client *client, Rows &rows)
{
	auto &inventory = client->GetInv();
	if (std::distance(inventory.cursor_cbegin(), inventory.cursor_cend()) != 1) { return false; }
	const auto item = inventory.GetItem(EQ::invslot::slotCursor);
	if (!Transferable(item)) { return false; }
	rows.push_back(Snapshot(client->CharacterID(), EQ::invslot::slotCursor, *item));
	// Prove this exact persisted instance can be recovered before removing it.
	// Some legacy custom-data encodings do not roundtrip through native loading.
	if (!Restore(rows.back())) { return false; }
	// Filled bags are not posted: native SaveCursor shares this persisted range
	// with queued cursor objects. Never turn children into separate cursor items.
	if (item->IsClassBag()) {
		for (uint16 i = 0; i < EQ::invbag::SLOT_COUNT; ++i) { if (item->GetItem(i)) { return false; } }
	}
	return true;
}
}

bool Client::BazaarSessionReady()
{
	if (GetZoneID() != 22 || GetInstanceID() || !client_data_loaded || !m_pet_armor_transfer_valid ||
		IsDead() || IsEngaged() || auto_attack || IsCasting() || IsStunned() || IsMezzed() || IsFeared() ||
		IsAIControlled() || (trade && trade->With()) || GetTradeskillObject() || IsTrader() || IsBuyer()) {
		Message(Chat::Yellow, "Use the Commonlands market while safely out of combat and other trading in East Commonlands.");
		return false;
	}
	return true;
}

bool Client::CompleteBazaarRequest(const NightcapBazaar::Request &input)
{
	using namespace NightcapBazaar;
	if (!BazaarSessionReady()) { return false; }
	auto request = input; request.character = CharacterID();
	if (m_pp.platinum < 0 || m_pp.gold < 0 || m_pp.silver < 0 || m_pp.copper < 0) { return false; }
	request.wallet = {uint32(m_pp.platinum), uint32(m_pp.gold), uint32(m_pp.silver), uint32(m_pp.copper)};
	std::unique_ptr<EQ::ItemInstance> delivery;
	try {
		if (request.op == Operation::Post) {
			Rows current;
			if (!CursorSnapshot(this, current) || !SameItems(current, request.cursor)) {
				Message(Chat::Yellow, "Your cursor item changed. Request a new posting quote."); return false;
			}
		} else if (request.op != Operation::Collect) {
			if (m_inv.cursor_cbegin() != m_inv.cursor_cend()) { Message(Chat::Yellow, "Empty your cursor before receiving a market item."); return false; }
			auto rows = BazaarQuery("SELECT " + SelectColumns() + " FROM nightcap_bazaar_items WHERE listing_id=" + std::to_string(request.listing) + " ORDER BY slot_id");
			if (!rows.ok || rows.rows.size() != 1 || !(delivery = Restore(rows.rows[0])) || (request.op == Operation::Buy && !Transferable(delivery.get())) ||
				CheckLoreConflict(delivery->GetItem())) { Message(Chat::Yellow, "This listing cannot be delivered to your character."); return false; }
			for (uint8 i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) {
				const auto augment = delivery->GetAugment(i);
				if (augment && CheckLoreConflict(augment->GetItem())) { return false; }
			}
		}
		const auto result = Execute(BazaarQuery, request, Slots{EQ::invslot::slotCursor, EQ::invbag::CURSOR_BAG_BEGIN, EQ::invbag::CURSOR_BAG_END});
		if (result.status == Status::Uncertain) {
			QuarantineItemTransfer("The market transaction could not be confirmed. Reconnect to reload your items and money."); return false;
		}
		if (result.status != Status::Committed) { Message(Chat::Yellow, "The listing or your saved inventory changed, or the market is unavailable. Refresh and try again."); return false; }
		// All durable changes precede every session mutation and packet.
		if (request.op == Operation::Post) { DeleteItemInInventory(EQ::invslot::slotCursor, 0, true, false); }
		else if (request.op != Operation::Collect) {
			if (result.items.size() != 1 || !(delivery = Restore(result.items[0]))) {
				QuarantineItemTransfer("Your market item was saved. Reconnect to reload your inventory."); return false;
			}
			m_inv.PushCursor(*delivery); SendItemPacket(EQ::invslot::slotCursor, delivery.get(), ItemPacketLimbo);
		}
		m_pp.platinum = result.wallet[0]; m_pp.gold = result.wallet[1]; m_pp.silver = result.wallet[2]; m_pp.copper = result.wallet[3];
		SendMoneyUpdate(); RecalcWeight();
		Message(Chat::Green, request.op == Operation::Post ? "Listing %u is posted. It stays for sale while you adventure or log out." : "Market transaction complete (listing %u).", result.listing);
		return true;
	} catch (...) {
		QuarantineItemTransfer("Market state needs to be reloaded. Reconnect before trading again."); return false;
	}
}

bool Client::PrepareBazaarPost(uint64 platinum, bool quiet)
{
	using namespace NightcapBazaar;
	m_bazaar_confirmation.clear(); m_bazaar_post = {};
	if (!platinum || platinum > UINT32_MAX / 1000 || !CursorSnapshot(this, m_bazaar_post.cursor)) {
		Message(Chat::Yellow, "Put one permanent tradeable item or stack on your cursor. Empty bags first; evolving/scaling items and unsupported saved metadata cannot be posted. Use a whole-platinum price from 1 to 4294967 per item."); return false;
	}
	const auto item = m_inv.GetItem(EQ::invslot::slotCursor);
	m_bazaar_post.character = CharacterID(); m_bazaar_post.unit_price = platinum * 1000;
	m_bazaar_post.stackable = item->IsStackable(); m_bazaar_post.quantity = item->IsStackable() ? item->GetCharges() : 1;
	if (!m_bazaar_post.quantity || uint64(m_bazaar_post.unit_price) * m_bazaar_post.quantity > UINT32_MAX) { Message(Chat::Yellow, "That stack's total price exceeds the market limit."); return false; }
	m_bazaar_confirmation = NightcapLoot::NewDropID(); m_bazaar_confirmation_deadline = Now() + 60;
	if (!quiet) Message(Chat::Yellow, "Post %u x %s for %llu platinum EACH (%llu platinum total)? Confirm within 60 seconds with #bazaar confirm %s.",
		m_bazaar_post.quantity, item->GetItem()->Name, static_cast<unsigned long long>(platinum),
		static_cast<unsigned long long>(platinum * m_bazaar_post.quantity), m_bazaar_confirmation.c_str());
	return true;
}

bool Client::ConfirmBazaarPost(const std::string &nonce)
{
	if (m_bazaar_confirmation.empty() || m_bazaar_confirmation != nonce || Now() > m_bazaar_confirmation_deadline) {
		Message(Chat::Yellow, "That posting confirmation expired. Request a new quote."); return false;
	}
	m_bazaar_confirmation.clear(); return CompleteBazaarRequest(m_bazaar_post);
}

void Client::BazaarPanelCommand(const Seperator *sep)
{
	using namespace NightcapBazaar;
	namespace Panel = NightcapBazaarPanel;
	uint32 request_id = 0, page = 0;
	if (sep->argnum != 5 || !NightcapLoot::Number(sep->arg[2], request_id) || !request_id ||
		!NightcapLoot::Number(sep->arg[5], page) || page > 12) { return; }
	const auto milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
	if (uint64(milliseconds) < m_bazaar_panel_next_request) { return; }
	m_bazaar_panel_next_request = uint64(milliseconds) + 250;
	const std::string action = sep->arg[3], value = sep->arg[4];
	Panel::Snapshot snapshot;
	snapshot.request = request_id; snapshot.spawn = GetID(); snapshot.name = GetName();
	snapshot.message = "Use this market safely in public East Commonlands.";
	if (BazaarSessionReady()) {
		bool ok = false;
		try {
			if (action == "confirm") {
				if (Panel::Nonce(value)) ok = ConfirmBazaarPost(value);
			} else {
				m_bazaar_confirmation.clear();
				uint64 number = 0;
				if (Panel::Unsigned(value, number)) {
					if (action == "view" && number == 0) ok = true;
					else if (action == "post") ok = PrepareBazaarPost(number, true);
					else if ((action == "cancel" && number && number <= UINT32_MAX) || (action == "collect" && number == 0)) {
						Request request; request.op = action == "cancel" ? Operation::Cancel : Operation::Collect;
						request.listing = static_cast<uint32>(number); ok = CompleteBazaarRequest(request);
					}
				}
			}
			// Quarantined sessions must reconnect; never re-enable presentation actions.
			if (!m_pet_armor_transfer_valid) { return; }
			Panel::Snapshot read;
			const auto status = Panel::ReadSeller(BazaarQuery, CharacterID(), page, EQ::invslot::slotCursor, read);
			if (status == Status::Uncertain) { QuarantineItemTransfer("Market data could not be confirmed. Reconnect before trading again."); return; }
			if (status == Status::Committed) {
				read.request = snapshot.request; read.spawn = snapshot.spawn; read.name = snapshot.name;
				read.message = ok ? (action == "post" ? "Review this item and price, then Confirm Post within 60 seconds." : action == "view" ? "Listings stay available while you adventure or log out." : "Done. Your listings and proceeds are refreshed.") : "Request was not completed. Check the chat message, cursor and price, then refresh.";
				for (auto &row : read.rows) { const auto item = database.GetItem(row.item); row.name = item ? item->Name : "Unknown item"; }
				if (ok && action == "post" && !m_bazaar_confirmation.empty()) {
					const auto item = m_inv.GetItem(EQ::invslot::slotCursor);
					read.quote.nonce = m_bazaar_confirmation;
					read.quote.item = {0, item->GetID(), m_bazaar_post.quantity, m_bazaar_post.unit_price, item->GetItem()->Name};
				}
				snapshot = std::move(read);
			} else snapshot.message = "Market data is unavailable. Refresh before another action.";
		} catch (...) { snapshot.message = "Market data is unavailable. Refresh before another action."; }
	}
	for (const auto &message : Panel::Encode(snapshot)) { Message(Chat::White, "%s", message.c_str()); }
}

void Client::BazaarCommand(const Seperator *sep)
{
	using namespace NightcapBazaar;
	if (std::string(sep->arg[1]) == "ui") { BazaarPanelCommand(sep); return; }
	if (!BazaarSessionReady()) { return; }
	try {
		const std::string action = sep->arg[1];
		if (action == "post" && sep->argnum == 2) { PrepareBazaarPost(Number(sep->arg[2])); return; }
		if (action == "confirm" && sep->argnum == 2) { ConfirmBazaarPost(sep->arg[2]); return; }
		if (action == "collect" && sep->argnum == 1) {
			Request request; request.op = Operation::Collect; CompleteBazaarRequest(request); return;
		}
		if (action == "cancel" && sep->argnum == 2) {
			const auto id = Number(sep->arg[2]); if (!id || id > UINT32_MAX) { return; }
			Request request; request.op = Operation::Cancel; request.listing = id; CompleteBazaarRequest(request); return;
		}
		if (action == "listings" && sep->argnum == 1 && Ready(BazaarQuery)) {
			auto listings = BazaarQuery("SELECT l.id,i.item_id,l.unit_price,l.remaining FROM nightcap_bazaar_listings l JOIN nightcap_bazaar_items i ON i.listing_id=l.id AND i.slot_id=" +
				std::to_string(EQ::invslot::slotCursor) + " WHERE l.seller_id=" + std::to_string(CharacterID()) + " AND l.status='active' ORDER BY l.id LIMIT 100");
			if (!listings.ok) { return; }
			for (const auto &row : listings.rows) {
				const auto item = database.GetItem(Number(row[1]));
				Message(Chat::White, "Listing %s: %s x%s at %llu platinum each. Cancel: #bazaar cancel %s", row[0].c_str(), item ? item->Name : "Unknown item", row[3].c_str(), static_cast<unsigned long long>(Number(row[2]) / 1000), row[0].c_str());
			}
			auto credits = BazaarQuery("SELECT copper FROM nightcap_bazaar_credits WHERE character_id=" + std::to_string(CharacterID()));
			if (credits.ok && credits.rows.size() == 1) { Message(Chat::White, "Uncollected proceeds: %llu platinum and %u copper. Use #bazaar collect.", static_cast<unsigned long long>(Number(credits.rows[0][0]) / 1000), static_cast<unsigned>(Number(credits.rows[0][0]) % 1000)); }
			Message(Chat::White, "Showing up to 100 active listings. Use /bazaar to search the market."); return;
		}
	} catch (...) { Message(Chat::Yellow, "Use whole positive numbers for prices and listing IDs."); return; }
	Message(Chat::White, "Commonlands market: /bazaar searches; #bazaar post <price-pp> quotes your cursor item; #bazaar listings, #bazaar cancel <id>, #bazaar collect.");
}
void command_bazaar(Client *client, const Seperator *sep) { client->BazaarCommand(sep); }


bool Client::BazaarStorageReady()
{
	try { return NightcapBazaar::Ready(BazaarQuery); } catch (...) { return false; }
}
void Client::RememberBazaarResults(const std::vector<BazaarSearchResultsFromDB_Struct> &results)
{
	m_bazaar_quotes.clear();
	for (const auto &row : results) {
		if (row.trader_id == NightcapBazaar::BrokerID) {
			m_bazaar_quotes[row.serial_number] = {row.cost, row.item_id, row.stackable ? row.charges : 1, Now() + 120};
		}
	}
}
bool Client::HandleBazaarInspect(uint32 listing_id)
{
	if (GetZoneID() != 22 || GetInstanceID() || !BazaarStorageReady()) { return false; }
	const auto quote = m_bazaar_quotes.find(listing_id);
	if (quote == m_bazaar_quotes.end() || Now() > quote->second.deadline) { return false; }
	try {
		auto rows = BazaarQuery("SELECT " + NightcapBazaar::SelectColumns() + ",l.remaining,l.stackable FROM nightcap_bazaar_items i JOIN nightcap_bazaar_listings l ON l.id=i.listing_id WHERE l.id=" +
			std::to_string(listing_id) + " AND l.status='active' ORDER BY slot_id");
		if (!rows.ok || rows.rows.size() != 1 || rows.rows[0].size() != NightcapBazaar::Columns().size() + 2) { return false; }
		auto row = rows.rows[0]; const auto stackable = row.back() == "1"; row.pop_back();
		const auto remaining = row.back(); row.pop_back();
		if (stackable) { row[3] = remaining; }
		auto item = Restore(row);
		if (!item || item->GetID() != quote->second.item_id) { return false; }
		SendItemPacket(0, item.get(), ItemPacketViewLink); return true;
	} catch (...) { return false; }
}
bool Client::HandleBazaarPurchase(const EQApplicationPacket *app)
{
	using namespace NightcapBazaar;
	if (app->size != sizeof(TraderBuy_Struct)) { return false; }
	const auto in = reinterpret_cast<const TraderBuy_Struct *>(app->pBuffer);
	if (in->trader_id != BrokerID) { return false; }
	auto fail = [&]() { TradeRequestFailed(app); return true; };
	if (!BazaarSessionReady() || ClientVersion() < EQ::versions::ClientVersion::RoF2) { return fail(); }
	if (in->method != BazaarByDirectToInventory) {
		Message(Chat::Yellow, "Choose direct-to-inventory delivery for the Commonlands market, and empty your cursor first.");
		return fail();
	}
	try {
		// Fixed-width network strings must be terminated before parsing.
		if (in->serial_number[16] != 0) { return fail(); }
		const auto serial = Number(in->serial_number);
		if (!serial || serial > UINT32_MAX) { return fail(); }
		const auto quote = m_bazaar_quotes.find(serial);
		if (quote == m_bazaar_quotes.end() || Now() > quote->second.deadline ||
			in->price != quote->second.price || in->item_id != quote->second.item_id ||
			!in->quantity || in->quantity > quote->second.quantity || in->quantity > 32767) { return fail(); }
		Request request; request.op = Operation::Buy; request.listing = serial;
		request.unit_price = quote->second.price; request.quantity = in->quantity;
		// One purchase per search quote. A fresh search re-quotes remaining stock.
		m_bazaar_quotes.erase(quote);
		if (!CompleteBazaarRequest(request)) { return fail(); }
		ReturnTraderReq(app, in->quantity, in->item_id); return true;
	} catch (...) { return fail(); }
}

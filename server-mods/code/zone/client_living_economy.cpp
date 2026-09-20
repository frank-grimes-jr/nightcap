#include "zone/client.h"
#include "zone/npc.h"
#include "zone/zone.h"
#include "common/content/world_content_service.h"
#include "common/say_link.h"
#include <algorithm>
#include <limits>

extern Zone *zone;

namespace {
int MarketEra() { return WorldContentService::Instance()->GetCurrentExpansion(); }

bool PlainMarketItem(const EQ::ItemInstance *inst)
{
	if (!inst || !inst->GetItem()) { return false; }
	const auto item = inst->GetItem();
	if (!item->IsClassCommon() || !item->NoDrop || !item->NoRent || item->MaxCharges ||
		item->IsQuestItem() || inst->IsStackable() || inst->IsEvolving() || inst->IsScaling() ||
		inst->IsAttuned() || !inst->GetCustomDataString().empty() || inst->GetOrnamentationIcon() ||
		inst->GetOrnamentationIDFile() || inst->GetOrnamentHeroModel()) { return false; }
	for (int i = 0; i < EQ::invaug::SOCKET_COUNT; ++i) {
		if (inst->GetAugmentItemID(i)) { return false; }
	}
	return inst->GetCharges() == 0 || inst->GetCharges() == 1;
}
}

void Client::SendMarketFind(uint32 npc_id, uint32 slot)
{
	if (!zone || zone->GetInstanceID()) { return; }
	auto mob = entity_list.GetMobByNpcTypeID(npc_id);
	if (!mob || !mob->IsNPC()) { return; }
	for (const auto &entry : zone->merchanttable[mob->CastToNPC()->MerchantType]) {
		slot = std::max(slot, entry.slot + 1);
	}
	for (const auto &entry : zone->tmpmerchanttable[npc_id]) { slot = std::max(slot, entry.slot + 1); }
	const uint32 limit = (m_ClientVersionBit & EQ::versions::maskRoFAndLater) ? EQ::invtype::MERCHANT_SIZE : 80;
	if (slot > limit) { return; }
	NightcapMarket::Offer offer;
	if (!mob || !mob->IsNPC() || !NightcapMarket::ReadOffer(npc_id, zone->GetZoneID(), MarketEra(), offer) ||
		offer.kind != "find") { return; }
	std::unique_ptr<EQ::ItemInstance> inst(database.CreateItem(offer.item_id, 0));
	if (!PlainMarketItem(inst.get())) { return; }
	inst->SetMerchantCount(1);
	inst->SetMerchantSlot(slot);
	inst->SetPrice(offer.price_cp);
	SendItemPacket(slot - 1, inst.get(), ItemPacketMerchant);
	m_market_quote = offer;
	m_market_entity = mob->GetID();
	m_market_slot = slot;
}

bool Client::BuyMarketFind(uint32 npc_entity_id, uint32 slot, uint32 quantity)
{
	if (!m_market_slot || slot != m_market_slot || npc_entity_id != m_market_entity) { return false; }
	auto mob = entity_list.GetMob(npc_entity_id);
	if (!zone || quantity != 1 || !mob || !mob->IsNPC() || m_market_quote.kind != "find" ||
		GetMerchantSessionEntityID() != npc_entity_id) {
		SendMerchantEnd();
		return true;
	}
	// Native buyback stock can grow while a shop is open. Never reinterpret its
	// newly occupied slot as the previously displayed synthetic find.
	for (const auto &entry : zone->merchanttable[mob->CastToNPC()->MerchantType]) {
		if (entry.slot == slot) { SendMerchantEnd(); return true; }
	}
	for (const auto &entry : zone->tmpmerchanttable[mob->GetNPCTypeID()]) {
		if (entry.slot == slot) { SendMerchantEnd(); return true; }
	}
	CompleteMarketTrade(mob->CastToNPC(), m_market_quote);
	// Closing also removes a sold-out synthetic slot from the native shop UI.
	SendMerchantEnd();
	return true;
}

void Client::LivingEconomy(uint32 npc_entity_id, const std::string &text)
{
	if (!zone || zone->GetInstanceID()) { return; }
	auto mob = entity_list.GetMob(npc_entity_id);
	if (!mob || !mob->IsNPC() || DistanceSquared(GetPosition(), mob->GetPosition()) > USE_NPC_RANGE2) { return; }
	NightcapMarket::Offer offer;
	if (!NightcapMarket::ReadOffer(mob->GetNPCTypeID(), zone->GetZoneID(), MarketEra(), offer) || offer.kind == "find") {
		Message(Chat::NPCQuestSay, "%s says, 'All finished trading for now. Good hunting!'", mob->GetCleanName());
		return;
	}
	const std::string command = fmt::format("market {} {} {} {}", offer.epoch, offer.npc_id, offer.item_id, offer.price_cp);
	if (text == command) {
		CompleteMarketTrade(mob->CastToNPC(), offer);
		return;
	}
	if (text.rfind("market ", 0) == 0) {
		Message(Chat::NPCQuestSay, "That offer has changed. Hail me again for today's price.");
		return;
	}
	const auto item = database.GetItem(offer.item_id);
	if (!item) { return; }
	EQ::SayLinkEngine link;
	link.SetLinkType(EQ::saylink::SayLinkItemData);
	link.SetItemData(item);
	const auto item_link = link.GenerateLink();
	const bool selling = offer.kind == "sell";
	const auto action = Saylink::Silent(command, selling ? "Buy one" : "Sell one from cursor");
	Message(Chat::NPCQuestSay, "%s says, '%s %s for %u platinum. %s %s'", mob->GetCleanName(),
		selling ? "WTS" : "WTB", item_link.c_str(), offer.price_cp / 1000,
		selling ? "I've just the one. Empty your cursor first." : "Put one unmodified item on your cursor; I'll take it there.", action.c_str());
}

bool Client::CompleteMarketTrade(NPC *npc, const NightcapMarket::Offer &offer)
{
	if (!zone || zone->GetInstanceID() || !npc || npc->GetNPCTypeID() != offer.npc_id ||
		zone->GetZoneID() != offer.zone_id || DistanceSquared(GetPosition(), npc->GetPosition()) > USE_NPC_RANGE2 ||
		IsDead() || IsEngaged() || auto_attack || IsCasting() || IsStunned() || IsMezzed() || IsFeared() ||
		IsAIControlled() || (trade && trade->With()) || GetTradeskillObject()) {
		Message(Chat::Red, "Finish combat or trading, then stand beside the trader.");
		return false;
	}
	NightcapMarket::Offer current;
	if (!NightcapMarket::ReadOffer(offer.npc_id, offer.zone_id, MarketEra(), current) ||
		current.epoch != offer.epoch || current.item_id != offer.item_id ||
		current.price_cp != offer.price_cp || current.kind != offer.kind) {
		Message(Chat::Yellow, "That offer is no longer available. Hail or reopen the shop.");
		return false;
	}
	const bool buying = offer.kind != "buy";
	const auto cursor = m_inv.GetItem(EQ::invslot::slotCursor);
	const auto queue = std::distance(m_inv.cursor_cbegin(), m_inv.cursor_cend());
	std::unique_ptr<EQ::ItemInstance> purchase(buying ? database.CreateItem(offer.item_id, 0) : nullptr);
	const auto inst = buying ? purchase.get() : cursor;
	if ((buying ? queue != 0 : queue != 1) || !PlainMarketItem(inst) || inst->GetID() != offer.item_id) {
		Message(Chat::Red, buying ? "Empty your cursor before buying." : "Place exactly one unmodified requested item on your cursor.");
		return false;
	}
	if (buying && CheckLoreConflict(inst->GetItem())) {
		Message(Chat::Red, "You already own a conflicting lore item.");
		return false;
	}
	if (m_pp.platinum < 0 || m_pp.gold < 0 || m_pp.silver < 0 || m_pp.copper < 0) {
		Message(Chat::Red, "Your coin balance needs GM review before trading.");
		return false;
	}
	const uint64 carried = GetCarriedMoney();
	if (buying && carried < offer.price_cp) {
		Message(Chat::Red, "You do not have enough platinum on you.");
		return false;
	}
	const uint64 balance = buying ? carried - offer.price_cp : carried + offer.price_cp;
	if (balance / 1000 > std::numeric_limits<int32>::max()) { return false; }
	const NightcapMarket::Wallet before = {uint32(m_pp.platinum), uint32(m_pp.gold), uint32(m_pp.silver), uint32(m_pp.copper)};
	const NightcapMarket::Wallet after = {uint32(balance / 1000), uint32(balance / 100 % 10),
		uint32(balance / 10 % 10), uint32(balance % 10)};
	const NightcapMarket::Item moved = {inst->GetID(), uint32(inst->GetSerialNumber()), inst->GetColor(), inst->GetCharges()};
	const auto result = NightcapMarket::Trade(CharacterID(), offer, MarketEra(), before, after, moved);
	if (result == NightcapMarket::Result::Uncertain) {
		// Reuse the existing inventory-transfer quarantine, including disconnect hooks.
		m_pet_armor_transfer_valid = false;
		client_data_loaded = false;
		LogError("Market commit uncertain for character [{}], epoch [{}], NPC [{}]", CharacterID(), offer.epoch, offer.npc_id);
		Message(Chat::Red, "This trade could not be confirmed. Reconnect to reload your items and money.");
		if (eqs) { eqs->Close(); }
		client_state = DISCONNECTED;
		return false;
	}
	if (result != NightcapMarket::Result::Committed) {
		Message(Chat::Yellow, "The offer could not be completed. Nothing was exchanged; hail or reopen the shop.");
		return false;
	}
	m_pp.platinum = after[0]; m_pp.gold = after[1]; m_pp.silver = after[2]; m_pp.copper = after[3];
	if (buying) {
		m_inv.PushCursor(*purchase);
		SendItemPacket(EQ::invslot::slotCursor, purchase.get(), ItemPacketLimbo);
	} else {
		DeleteItemInInventory(EQ::invslot::slotCursor, 0, true, false);
	}
	SendMoneyUpdate();
	RecalcWeight();
	Message(Chat::NPCQuestSay, "%s says, 'Deal, %u platinum. Thanks!'", npc->GetCleanName(), offer.price_cp / 1000);
	LogInfo("Market trade character [{}], epoch [{}], NPC [{}], item [{}], copper [{}], kind [{}]",
		CharacterID(), offer.epoch, offer.npc_id, offer.item_id, offer.price_cp, offer.kind);
	return true;
}

void Client::MarketAnnouncement(uint32 npc_entity_id, uint32 variant)
{
	if (!zone || zone->GetZoneID() != 22 || zone->GetInstanceID()) { return; }
	auto mob = entity_list.GetMob(npc_entity_id);
	NightcapMarket::Offer offer;
	if (!mob || !mob->IsNPC() || !NightcapMarket::ReadOffer(mob->GetNPCTypeID(), 22, MarketEra(), offer) ||
		offer.kind == "find") { return; }
	const char *chatter[] = {
		"I went into Guk for an hour. That was yesterday.",
		"Anyone else carry three bags of things they might need someday?",
		"The tunnel is the only camp where my boots stay dry.",
		"Someone remind me to buy food before I leave this time.",
		"Almost had that pull. Almost is doing a lot of work there.",
		"That last group was good company. Even the corpse run."
	};
	if (variant >= 8) {
		if (DistanceSquared(GetPosition(), mob->GetPosition()) <= 200.0f * 200.0f) {
			ChannelMessageSend(mob->GetCleanName(), nullptr, ChatChannel_Say, 0, 100, "%s", chatter[(variant - 8) % 6]);
		}
		return;
	}
	const auto item = database.GetItem(offer.item_id);
	if (!item) { return; }
	EQ::SayLinkEngine link;
	link.SetLinkType(EQ::saylink::SayLinkItemData);
	link.SetItemData(item);
	const char *endings[] = {"at the tunnel. Come hail me!", "one only, near the tunnel merchants.",
		"at the tunnel. Price is firm.", "come find me in the tunnel!"};
	ChannelMessageSend(mob->GetCleanName(), nullptr, ChatChannel_Auction, 0, 100, "%s %s %upp, %s",
		offer.kind == "buy" ? "WTB" : "WTS", link.GenerateLink().c_str(), offer.price_cp / 1000, endings[variant % 4]);
}

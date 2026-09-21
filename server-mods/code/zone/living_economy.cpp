#include "zone/living_economy.h"
#include "zone/zonedb.h"
#include "common/strings.h"
#include "common/rulesys.h"

extern ZoneDatabase database;

namespace NightcapMarket {
bool Ready()
{
	static const bool ready = []() {
		auto tables = database.QueryDatabase(std::string(
			"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() "
			"AND TABLE_NAME IN ('nightcap_market_state','nightcap_market_catalog','nightcap_market_actors',"
			"'nightcap_market_offers','nightcap_market_trades','inventory','character_currency') AND ENGINE='InnoDB'"), false);
		if (!tables.Success() || tables.RowCount() != 1 || Strings::ToUnsignedInt(tables.begin()[0]) != 7) { return false; }
		auto triggers = database.QueryDatabase(std::string(
			"SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() "
			"AND EVENT_OBJECT_TABLE IN ('nightcap_market_state','nightcap_market_catalog','nightcap_market_actors',"
			"'nightcap_market_offers','nightcap_market_trades','inventory','character_currency')"), false);
		return triggers.Success() && triggers.RowCount() == 1 && Strings::ToUnsignedInt(triggers.begin()[0]) == 0;
	}();
	return ready;
}

std::vector<Offer> ReadOffers(uint32 npc_id, uint32 zone_id, int era)
{
	if (!Ready() || era < 0) { return {}; }
	auto row = database.QueryDatabase(fmt::format(
		"SELECT o.epoch,o.item_id,o.price_cp,o.kind FROM nightcap_market_offers o "
		"JOIN nightcap_market_state s ON s.id=1 AND s.enabled=1 AND s.epoch=o.epoch AND s.expansion={} "
		"JOIN nightcap_market_catalog c ON c.item_id=o.item_id AND c.min_expansion<={} "
		"AND (c.max_expansion<0 OR c.max_expansion>={}) "
		"JOIN nightcap_market_actors a ON a.npc_id=o.npc_id AND a.zone_id=o.zone_id AND a.kind=o.kind "
		"WHERE o.npc_id={} AND o.zone_id={} AND o.remaining=1 AND o.price_cp>0",
		era, era, era, npc_id, zone_id) + fmt::format(" AND s.loot_multiplier={} AND s.buy_cost_mod={}",
		RuleI(Zone, GlobalLootMultiplier), RuleR(Merchant, BuyCostMod)) + " ORDER BY o.item_id LIMIT 3", false);
	if (!row.Success() || row.RowCount() > 2) { return {}; }
	std::vector<Offer> offers;
	for (auto r : row) {
		offers.push_back({strtoull(r[0], nullptr, 10), npc_id, zone_id, Strings::ToUnsignedInt(r[1]),
			Strings::ToUnsignedInt(r[2]), r[3]});
	}
	return offers;
}

bool ReadOffer(uint32 npc_id, uint32 zone_id, int era, Offer &offer, uint32 item_id)
{
	auto offers = ReadOffers(npc_id, zone_id, era);
	if (!item_id && offers.size() != 1) { return false; }
	for (const auto &candidate : offers) {
		if (!item_id || candidate.item_id == item_id) { offer = candidate; return true; }
	}
	return false;
}

Result Trade(uint32 character_id, const Offer &offer, int era, const Wallet &before,
	const Wallet &after, const Item &item)
{
	if (!Ready() || !character_id || !offer.epoch || offer.item_id != item.id || !offer.price_cp ||
		(offer.kind != "find" && offer.kind != "sell" && offer.kind != "buy")) { return Result::Rejected; }
	const bool buying = offer.kind != "buy";
	auto total = [](const Wallet &w) { return uint64(w[0])*1000 + uint64(w[1])*100 + uint64(w[2])*10 + w[3]; };
	if (buying ? (total(before) < offer.price_cp || total(before)-offer.price_cp != total(after)) :
		(total(before)+offer.price_cp != total(after))) { return Result::Rejected; }
	auto active = database.QueryDatabase(std::string("SELECT @@in_transaction"), false);
	if (!active.Success() || active.RowCount() != 1 || Strings::ToUnsignedInt(active.begin()[0])) { return Result::Uncertain; }
	if (!database.QueryDatabase(std::string("START TRANSACTION"), false).Success()) { return Result::Uncertain; }
	auto reject = [&]() {
		return database.QueryDatabase(std::string("ROLLBACK"), false).Success() ? Result::Rejected : Result::Uncertain;
	};
	// Rotation takes the same first lock. Old windows cannot transact a new generation.
	auto state = database.QueryDatabase(fmt::format(
		"SELECT epoch FROM nightcap_market_state WHERE id=1 AND enabled=1 AND epoch={} AND expansion={} FOR UPDATE",
		offer.epoch, era), false);
	if (!state.Success() || state.RowCount() != 1) { return reject(); }
	const auto offer_where = fmt::format(
		"npc_id={} AND epoch={} AND zone_id={} AND item_id={} AND price_cp={} AND kind='{}' AND remaining=1",
		offer.npc_id, offer.epoch, offer.zone_id, offer.item_id, offer.price_cp, offer.kind);
	auto stock = database.QueryDatabase("SELECT item_id FROM nightcap_market_offers WHERE " + offer_where + " FOR UPDATE", false);
	if (!stock.Success() || stock.RowCount() != 1) { return reject(); }
	auto catalog = database.QueryDatabase(fmt::format(
		"SELECT c.item_id FROM nightcap_market_catalog c JOIN items i ON i.id=c.item_id "
		"WHERE c.item_id={} AND c.min_expansion<={} AND (c.max_expansion<0 OR c.max_expansion>={}) "
		"AND i.nodrop<>0 AND i.norent<>0 AND i.stackable=0 AND i.maxcharges=0 AND i.itemclass=0 "
		"AND i.questitemflag=0 AND i.attuneable=0 FOR UPDATE", item.id, era, era), false);
	if (!catalog.Success() || catalog.RowCount() != 1) { return reject(); }
	const auto wallet_where = fmt::format("id={} AND platinum={} AND gold={} AND silver={} AND copper={}",
		character_id, before[0], before[1], before[2], before[3]);
	auto wallet = database.QueryDatabase("SELECT id FROM character_currency WHERE " + wallet_where + " FOR UPDATE", false);
	if (!wallet.Success() || wallet.RowCount() != 1) { return reject(); }
	const auto cursor_where = fmt::format("character_id={} AND (slot_id={} OR slot_id BETWEEN {} AND {})",
		character_id, EQ::invslot::slotCursor, EQ::invbag::CURSOR_BAG_BEGIN, EQ::invbag::CURSOR_BAG_END);
	auto cursor = database.QueryDatabase("SELECT slot_id FROM inventory WHERE " + cursor_where + " FOR UPDATE", false);
	if (!cursor.Success() || cursor.RowCount() != (buying ? 0u : 1u)) { return reject(); }
	std::string item_sql;
	if (buying) {
		item_sql = fmt::format("INSERT INTO inventory(character_id,slot_id,item_id,charges,color,guid) VALUES({},{},{},{},{},{})",
			character_id, EQ::invslot::slotCursor, item.id, item.charges, item.color, item.serial);
	} else {
		item_sql = fmt::format("DELETE FROM inventory WHERE character_id={} AND slot_id={} AND item_id={} "
			"AND charges={} AND color={} AND guid={} AND instnodrop=0 AND COALESCE(custom_data,'')='' "
			"AND augment_one=0 AND augment_two=0 AND augment_three=0 AND augment_four=0 AND augment_five=0 AND augment_six=0 "
			"AND ornament_icon=0 AND ornament_idfile=0 AND ornament_hero_model=0",
			character_id, EQ::invslot::slotCursor, item.id, item.charges, item.color, item.serial);
	}
	auto moved = database.QueryDatabase(item_sql, false);
	if (!moved.Success() || moved.RowsAffected() != 1) { return reject(); }
	auto money = database.QueryDatabase(fmt::format("UPDATE character_currency SET platinum={},gold={},silver={},copper={} WHERE {}",
		after[0], after[1], after[2], after[3], wallet_where), false);
	if (!money.Success() || money.RowsAffected() != 1) { return reject(); }
	auto consumed = database.QueryDatabase("UPDATE nightcap_market_offers SET remaining=0 WHERE " + offer_where, false);
	if (!consumed.Success() || consumed.RowsAffected() != 1) { return reject(); }
	auto audit = database.QueryDatabase(fmt::format(
		"INSERT INTO nightcap_market_trades(epoch,npc_id,character_id,kind,item_id,price_cp) VALUES({},{},{},'{}',{},{})",
		offer.epoch, offer.npc_id, character_id, offer.kind, item.id, offer.price_cp), false);
	if (!audit.Success() || audit.RowsAffected() != 1) { return reject(); }
	if (!database.QueryDatabase(std::string("COMMIT"), false).Success()) {
		database.QueryDatabase(std::string("ROLLBACK"), false);
		return Result::Uncertain;
	}
	return Result::Committed;
}
}

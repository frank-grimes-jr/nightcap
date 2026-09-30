#include "zone/queryserv.h"
#include "zone/advanced_loot_currency.h"
#include "zone/advanced_loot_inventory.h"
#include "zone/client.h"
#include "zone/corpse.h"
#include "zone/groups.h"
#include "zone/raids.h"
#include "zone/string_ids.h"
#include "common/events/player_event_logs.h"
#include <array>
#include <map>

extern QueryServ *QServ;

namespace NightcapLoot {
namespace {
using Coins = std::array<uint32, 4>; // copper, silver, gold, platinum
struct Award { Client *client; Coins before, after, amount; };
Coins Purse(Client *c) { return {c->GetCopper(), c->GetSilver(), c->GetGold(), c->GetPlatinum()}; }
bool Ready() {
	auto result = database.QueryDatabase(std::string(
		"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND ENGINE='InnoDB' "
		"AND TABLE_NAME IN ('character_currency','character_advloot_claims')"), false);
	if (!result.Success() || result.RowCount() != 1 || !result.begin()[0] || atoi(result.begin()[0]) != 2) { return false; }
	auto triggers = database.QueryDatabase(std::string(
		"SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() "
		"AND EVENT_OBJECT_TABLE IN ('character_currency','character_advloot_claims')"), false);
	return triggers.Success() && triggers.RowCount() == 1 && triggers.begin()[0] && atoi(triggers.begin()[0]) == 0;
}
class Transaction {
	bool active_ = false;
public:
	bool Begin() {
		auto active = database.QueryDatabase(std::string("SELECT @@in_transaction"), false);
		if (!active.Success() || active.RowCount() != 1 || !active.begin()[0] || atoi(active.begin()[0])) { return false; }
		return active_ = database.QueryDatabase(std::string("START TRANSACTION"), false).Success();
	}
	bool Commit() {
		if (!database.QueryDatabase(std::string("COMMIT"), false).Success()) { return false; }
		active_ = false; return true;
	}
	~Transaction() { if (active_) { try { database.QueryDatabase(std::string("ROLLBACK"), false); } catch (...) {} } }
};
}

TransferResult TakeCoins(Corpse *corpse, Client *client, bool split, bool classic) {
	if (!corpse || !corpse->AdvancedLootAccessible(client, false, classic)) { return TransferResult::Declined; }
	const Coins source{corpse->GetCopper(), corpse->GetSilver(), corpse->GetGold(), corpse->GetPlatinum()};
	if (source == Coins{}) { return TransferResult::Delivered; }
	const char *key = "nightcap:advloot-coin-id";
	if (corpse->GetEntityVariable(key).empty()) { corpse->SetEntityVariable(key, NewDropID()); }
	const auto id = corpse->GetEntityVariable(key);
	const auto claim = ReadClaim(id);
	if (claim == ClaimStatus::Claimed) { corpse->RemoveCash(); if (corpse->IsEmpty()) { corpse->ResetDecayTimer(); } return TransferResult::Delivered; }
	if (claim != ClaimStatus::Available || !Ready()) { return TransferResult::Declined; }
	std::map<uint32, Client *> recipients{{client->CharacterID(), client}};
	const auto include = [&](Client *recipient) {
		if (recipient && recipient->Connected() && recipient->ClientDataLoaded()) { recipients[recipient->CharacterID()] = recipient; }
	};
	if (split && client->GetRaid()) {
		for (const auto &member : client->GetRaid()->members) { if (!member.is_bot) { include(member.member); } }
	} else if (split && client->GetGroup()) {
		for (auto member : client->GetGroup()->members) {
			if (!member || !member->IsClient()) { continue; }
			include(member->CastToClient());
		}
	}
	std::vector<Award> awards;
	for (const auto &[character, recipient] : recipients) {
		Award award{recipient, Purse(recipient), Purse(recipient), {}};
		for (size_t i = 0; i < source.size(); ++i) {
			// Each denomination is conserved. The actual looter receives leftovers;
			// bots and mercenaries do not receive or consume a share.
			award.amount[i] = source[i] / recipients.size() + (recipient == client ? source[i] % recipients.size() : 0);
			if (award.before[i] > INT32_MAX || award.amount[i] > INT32_MAX - award.before[i]) { return TransferResult::Declined; }
			award.after[i] += award.amount[i];
		}
		awards.push_back(award);
	}
	bool uncertain = false;
	try {
		Transaction transaction;
		if (!transaction.Begin()) { return TransferResult::Declined; }
		std::string audit;
		for (const auto &award : awards) {
			const auto character = award.client->CharacterID();
			auto locked = database.QueryDatabase(fmt::format(
				"SELECT copper,silver,gold,platinum FROM character_currency WHERE id={} FOR UPDATE", character), false);
			if (!locked.Success() || locked.RowCount() != 1) { return TransferResult::Declined; }
			auto row = locked.begin();
			for (size_t i = 0; i < source.size(); ++i) { uint32 value = 0; if (!row[i] || !Number(row[i], value) || value != award.before[i]) { return TransferResult::Declined; } }
			if (award.amount != Coins{}) {
				auto changed = database.QueryDatabase(fmt::format(
					"UPDATE character_currency SET copper={},silver={},gold={},platinum={} WHERE id={}",
					award.after[0], award.after[1], award.after[2], award.after[3], character), false);
				if (!changed.Success() || changed.RowsAffected() != 1) { return TransferResult::Declined; }
			}
			audit += fmt::format("{}|{}|{}|{}|{}\n", character, award.after[0], award.after[1], award.after[2], award.after[3]);
		}
		auto receipt = database.QueryDatabase(fmt::format(
			"INSERT INTO character_advloot_claims (drop_id,character_id,item_id,charges,inventory_after) VALUES ('{}',{},0,0,X'{}')",
			id, client->CharacterID(), Hex(audit)), false);
		if (!receipt.Success() || receipt.RowsAffected() != 1) { return TransferResult::Declined; }
		uncertain = true;
		if (transaction.Commit()) {
			corpse->RemoveCash();
			if (corpse->IsEmpty()) { corpse->ResetDecayTimer(); }
			for (const auto &award : awards) {
				auto &profile = award.client->GetPP();
				profile.copper = award.after[0]; profile.silver = award.after[1]; profile.gold = award.after[2]; profile.platinum = award.after[3];
				award.client->SendMoneyUpdate(); award.client->RecalcWeight();
				if (award.amount != Coins{}) {
					award.client->Message(Chat::MoneySplit, "You receive %s.", Strings::Money(award.amount[3], award.amount[2], award.amount[1], award.amount[0]).c_str());
					if (PlayerEventLogs::Instance()->IsEventEnabled(PlayerEvent::SPLIT_MONEY)) {
						auto event = PlayerEvent::SplitMoneyEvent{.copper = award.amount[0], .silver = award.amount[1], .gold = award.amount[2],
							.platinum = award.amount[3], .player_money_balance = award.client->GetCarriedMoney()};
						RecordPlayerEventLogWithClient(award.client, PlayerEvent::SPLIT_MONEY, event);
					}
				}
			}
			client->CommonBreakInvisible();
			return TransferResult::Delivered;
		}
	} catch (...) { uncertain = true; }
	if (uncertain) {
		for (const auto &award : awards) { award.client->QuarantineItemTransfer("A coin transfer could not be confirmed. Reconnect to reload your money."); }
		return TransferResult::Uncertain;
	}
	return TransferResult::Declined;
}
}

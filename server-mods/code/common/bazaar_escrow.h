#pragma once
// Server-authoritative persistent bazaar transaction engine. Query must execute
// on one connection, with automatic retries disabled. No player/session writes
// occur here: the caller installs Result only after an acknowledged commit.
#include <algorithm>
#include <array>
#include <cstdint>
#include <functional>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace NightcapBazaar {
using Row = std::vector<std::string>;
using Rows = std::vector<Row>;
using Wallet = std::array<uint64_t, 4>;
struct Reply { bool ok = false; uint64_t affected = 0, id = 0; Rows rows; };
using Query = std::function<Reply(const std::string &)>;
enum class Operation { Post, Buy, Cancel, Collect };
enum class Status { Rejected, Committed, Uncertain };
constexpr uint32_t BrokerID = 0xFFFFFFFEu;
constexpr uint64_t MaxCopper = uint64_t{2147483647} * 1000 + 999;
constexpr uint64_t MaxCredit = 9223372036854775807ULL;
struct Slots { uint32_t cursor, begin, end; }; // supplied from EQ::invslot/invbag, never client input
struct Request {
	Operation op = Operation::Post;
	uint32_t character = 0, listing = 0, unit_price = 0, quantity = 0;
	bool stackable = false; // from the authoritative item cache, never a packet
	Wallet wallet{};
	Rows cursor; // complete native cursor tree; custom_data is uppercase hex
};
struct Result {
	Status status = Status::Rejected;
	uint32_t listing = 0;
	Wallet wallet{};
	Rows items; // exact committed destination rows; GUID is the persisted value
};
inline const std::vector<std::string> &Columns()
{
	static const std::vector<std::string> columns = {"character_id", "slot_id", "item_id", "charges", "color",
		"augment_one", "augment_two", "augment_three", "augment_four", "augment_five", "augment_six", "instnodrop",
		"custom_data", "ornament_icon", "ornament_idfile", "ornament_hero_model", "guid"};
	return columns;
}
inline std::string Join(const Row &values)
{
	std::string out;
	for (const auto &v : values) { if (!out.empty()) { out += ','; } out += v; }
	return out;
}
inline std::string SelectColumns()
{
	auto columns = Columns(); columns[12] = "HEX(COALESCE(custom_data,''))";
	return Join(columns);
}
inline uint64_t Number(const std::string &value)
{
	if (value.empty() || value.find_first_not_of("0123456789") != std::string::npos) { throw std::invalid_argument("number"); }
	size_t end = 0; const auto result = std::stoull(value, &end);
	if (end != value.size()) { throw std::invalid_argument("number"); }
	return result;
}
inline bool ValidItem(const Row &row, uint32_t character)
{
	if (row.size() != Columns().size() || Number(row[0]) != character || !Number(row[2])) { return false; }
	for (size_t i = 0; i < row.size(); ++i) {
		if (i == 12) {
			if (row[i].size() % 2 || row[i].find_first_not_of("0123456789ABCDEF") != std::string::npos) { return false; }
		} else if (i == 15 && !row[i].empty() && row[i][0] == '-') {
			if (Number(row[i].substr(1)) > 2147483648ULL) { return false; }
		} else { Number(row[i]); }
	}
	return true;
}
inline bool SameItems(Rows saved, Rows memory)
{
	if (saved.size() != memory.size()) { return false; }
	for (size_t i = 0; i < saved.size(); ++i) {
		if (saved[i].size() != Columns().size() || memory[i].size() != Columns().size()) { return false; }
		saved[i][16] = memory[i][16] = "0"; // native serials regenerate on login
	}
	return saved == memory;
}
inline std::string Values(Row row)
{
	row[12] = "X'" + row[12] + "'";
	return Join(row);
}
inline uint64_t Copper(const Wallet &wallet)
{
	for (auto v : wallet) { if (v > 2147483647) { throw std::invalid_argument("wallet"); } }
	return wallet[0] * 1000 + wallet[1] * 100 + wallet[2] * 10 + wallet[3];
}
inline Wallet Split(uint64_t copper) { return {copper / 1000, copper / 100 % 10, copper / 10 % 10, copper % 10}; }
inline std::string CursorWhere(uint32_t character, Slots slots)
{
	// EQEmu canonical server slots, independent of RoF2 wire slot numbering.
	return "character_id=" + std::to_string(character) + " AND (slot_id=" + std::to_string(slots.cursor) + " OR slot_id BETWEEN " + std::to_string(slots.begin) + " AND " + std::to_string(slots.end) + ")";
}
inline bool Ready(const Query &query)
{
	const std::string tables = "'inventory','character_currency','nightcap_bazaar_state','nightcap_bazaar_listings','nightcap_bazaar_items','nightcap_bazaar_credits','nightcap_bazaar_receipts'";
	auto engines = query("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND ENGINE='InnoDB' AND TABLE_NAME IN (" + tables + ')');
	if (!engines.ok || engines.rows != Rows{{"7"}}) { return false; }
	auto triggers = query("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE IN (" + tables + ')');
	if (!triggers.ok || triggers.rows != Rows{{"0"}}) { return false; }
	auto inventory = query("SHOW COLUMNS FROM inventory");
	auto escrow = query("SHOW COLUMNS FROM nightcap_bazaar_items");
	if (!inventory.ok || !escrow.ok || inventory.rows.size() != Columns().size() || escrow.rows.size() != Columns().size() + 1) { return false; }
	if (escrow.rows[0].size() < 3 || escrow.rows[0][0] != "listing_id" || escrow.rows[0][1] != "int(10) unsigned") { return false; }
	for (size_t i = 0; i < Columns().size(); ++i) {
		const auto &a = inventory.rows[i], &b = escrow.rows[i+1];
		if (a.size() < 3 || b.size() < 3 || a[0] != Columns()[i] || b[0] != a[0] || b[1] != a[1] || b[2] != a[2]) { return false; }
	}
	return true;
}
inline Result Execute(const Query &query, const Request &request, Slots slots)
{
	Result out; out.wallet = request.wallet;
	bool started = false;
	auto finish = [&](Status status) {
		if (started) {
			try { if (!query("ROLLBACK").ok) { status = Status::Uncertain; } }
			catch (...) { status = Status::Uncertain; }
			started = false;
		}
		out.status = status; return out;
	};
	try {
		if (!slots.cursor || slots.begin <= slots.cursor || slots.end < slots.begin || !request.character || static_cast<unsigned>(request.op) > 3) { return out; }
		const auto carried = Copper(request.wallet);
		if (carried > MaxCopper) { return out; }
		for (const auto &row : request.cursor) { if (!ValidItem(row, request.character)) { return out; } }
		if (request.op == Operation::Post) {
			if (!request.unit_price || !request.quantity || request.cursor.empty() || Number(request.cursor.front()[1]) != slots.cursor ||
				uint64_t(request.unit_price) * request.quantity > UINT32_MAX ||
				(request.stackable ? (request.cursor.size() != 1 || Number(request.cursor[0][3]) != request.quantity) : request.quantity != 1)) { return out; }
			uint64_t last = slots.cursor;
			for (size_t i = 1; i < request.cursor.size(); ++i) {
				const auto slot = Number(request.cursor[i][1]);
				if (slot < slots.begin || slot > slots.end || slot <= last) { return out; } last = slot;
			}
		} else if (request.op != Operation::Collect && (!request.listing || !request.cursor.empty())) { return out; }
		if (!Ready(query)) { return out; }
		auto active = query("SELECT @@in_transaction");
		if (!active.ok || active.rows != Rows{{"0"}}) { return finish(Status::Uncertain); }
		// Mark before START so an uncertain start also attempts rollback.
		started = true;
		if (!query("START TRANSACTION").ok) { return finish(Status::Uncertain); }
		auto state = query("SELECT enabled FROM nightcap_bazaar_state WHERE id=1 AND version=1 FOR UPDATE");
		if (!state.ok) { return finish(Status::Uncertain); }
		if (state.rows.size() != 1 || state.rows[0].size() != 1 ||
			((request.op == Operation::Post || request.op == Operation::Buy) && state.rows[0][0] != "1")) { return finish(Status::Rejected); }
		const auto who = std::to_string(request.character);
		// Lock all requesting character rows, including queued cursor items.
		Rows cursor;
		if (request.op != Operation::Collect) {
			auto inventory = query("SELECT " + SelectColumns() + " FROM inventory WHERE " + CursorWhere(request.character, slots) + " ORDER BY slot_id FOR UPDATE");
			if (!inventory.ok) { return finish(Status::Uncertain); }
			cursor = inventory.rows;
			if (!SameItems(cursor, request.cursor)) { return finish(Status::Rejected); }
		}
		if (request.op == Operation::Post) {
			auto count = query("SELECT COUNT(*) FROM nightcap_bazaar_listings WHERE seller_id=" + who + " AND status='active'");
			if (!count.ok) { return finish(Status::Uncertain); }
			if (count.rows.size() != 1 || count.rows[0].size() != 1 || Number(count.rows[0][0]) >= 100) { return finish(Status::Rejected); }
			auto listing = query("INSERT INTO nightcap_bazaar_listings(seller_id,unit_price,quantity,remaining,stackable) VALUES(" +
				who + ',' + std::to_string(request.unit_price) + ',' + std::to_string(request.quantity) + ',' + std::to_string(request.quantity) + ',' + (request.stackable ? "1" : "0") + ')');
			if (!listing.ok || listing.affected != 1 || !listing.id || listing.id > UINT32_MAX) { return finish(Status::Uncertain); }
			out.listing = static_cast<uint32_t>(listing.id);
			const auto id = std::to_string(out.listing);
			// Copy the exact persisted rows, including GUID and all instance fields.
			auto copied = query("INSERT INTO nightcap_bazaar_items(listing_id," + Join(Columns()) + ") SELECT " + id + ',' + Join(Columns()) + " FROM inventory WHERE " + CursorWhere(request.character, slots));
			if (!copied.ok || copied.affected != cursor.size()) { return finish(Status::Uncertain); }
			auto removed = query("DELETE FROM inventory WHERE " + CursorWhere(request.character, slots));
			if (!removed.ok || removed.affected != cursor.size()) { return finish(Status::Uncertain); }
		} else if (request.op == Operation::Buy || request.op == Operation::Cancel) {
			out.listing = request.listing;
			const auto id = std::to_string(request.listing);
			auto listing = query("SELECT seller_id,unit_price,remaining,stackable FROM nightcap_bazaar_listings WHERE id=" + id + " AND status='active' FOR UPDATE");
			if (!listing.ok) { return finish(Status::Uncertain); }
			if (listing.rows.size() != 1 || listing.rows[0].size() != 4) { return finish(Status::Rejected); }
			const auto &l = listing.rows[0]; const auto seller = Number(l[0]), price = Number(l[1]), remaining = Number(l[2]);
			const bool buy = request.op == Operation::Buy;
			const auto quantity = buy ? request.quantity : remaining;
			if (!seller || !price || price > UINT32_MAX || !remaining || !quantity || quantity > remaining ||
				(buy ? (seller == request.character || price != request.unit_price) : seller != request.character) ||
				(l[3] != "1" && (quantity != 1 || remaining != 1)) || price * quantity > UINT32_MAX) { return finish(Status::Rejected); }
			auto escrow = query("SELECT " + SelectColumns() + " FROM nightcap_bazaar_items WHERE listing_id=" + id + " ORDER BY slot_id FOR UPDATE");
			if (!escrow.ok) { return finish(Status::Uncertain); }
			if (escrow.rows.empty() || escrow.rows[0].size() != Columns().size() || Number(escrow.rows[0][1]) != slots.cursor ||
				(l[3] == "1" && (escrow.rows.size() != 1 || Number(escrow.rows[0][3]) < remaining))) { return finish(Status::Rejected); }
			out.items = escrow.rows;
			uint64_t previous = 0;
			for (auto &row : out.items) {
				const auto slot = Number(row[1]);
				if (slot <= previous || (slot != slots.cursor && (slot < slots.begin || slot > slots.end))) { return finish(Status::Rejected); }
				previous = slot;
				if (!ValidItem(row, static_cast<uint32_t>(seller))) { return finish(Status::Rejected); }
				row[0] = who;
			}
			if (l[3] == "1") { out.items[0][3] = std::to_string(quantity); }
			if (buy) {
				const auto total = price * quantity;
				if (carried < total) { return finish(Status::Rejected); }
				out.wallet = Split(carried - total);
				auto credit = query("SELECT copper FROM nightcap_bazaar_credits WHERE character_id=" + l[0] + " FOR UPDATE");
				if (!credit.ok) { return finish(Status::Uncertain); }
				if (credit.rows.size() > 1 || (!credit.rows.empty() && (credit.rows[0].size() != 1 || Number(credit.rows[0][0]) > MaxCredit - total))) { return finish(Status::Rejected); }
				auto paid = query("INSERT INTO nightcap_bazaar_credits(character_id,copper) VALUES(" + l[0] + ',' + std::to_string(total) + ") ON DUPLICATE KEY UPDATE copper=copper+VALUES(copper)");
				if (!paid.ok || !paid.affected) { return finish(Status::Uncertain); }
			}
			for (const auto &row : out.items) {
				auto moved = query("INSERT INTO inventory(" + Join(Columns()) + ") VALUES(" + Values(row) + ')');
				if (!moved.ok || moved.affected != 1) { return finish(Status::Uncertain); }
			}
			const auto left = buy ? remaining - quantity : 0;
			auto consumed = query("UPDATE nightcap_bazaar_listings SET remaining=" + std::to_string(left) + ",status='" +
				(left ? "active" : buy ? "sold" : "cancelled") + "' WHERE id=" + id + " AND status='active'");
			if (!consumed.ok || consumed.affected != 1) { return finish(Status::Uncertain); }
		} else {
			auto credit = query("SELECT copper FROM nightcap_bazaar_credits WHERE character_id=" + who + " FOR UPDATE");
			if (!credit.ok) { return finish(Status::Uncertain); }
			if (credit.rows.size() != 1 || credit.rows[0].size() != 1) { return finish(Status::Rejected); }
			const auto earned = Number(credit.rows[0][0]);
			if (!earned || earned > MaxCredit || carried == MaxCopper) { return finish(Status::Rejected); }
			const auto collected = std::min(earned, MaxCopper - carried);
			out.wallet = Split(carried + collected);
			auto paid = query("UPDATE nightcap_bazaar_credits SET copper=copper-" + std::to_string(collected) + " WHERE character_id=" + who);
			if (!paid.ok || paid.affected != 1) { return finish(Status::Uncertain); }
		}
		if (request.op == Operation::Buy || request.op == Operation::Collect) {
			auto wallet = query("SELECT platinum,gold,silver,copper FROM character_currency WHERE id=" + who + " FOR UPDATE");
			Row expected; for (auto v : request.wallet) { expected.push_back(std::to_string(v)); }
			if (!wallet.ok) { return finish(Status::Uncertain); }
			if (wallet.rows != Rows{expected}) { return finish(Status::Rejected); }
			auto paid = query("UPDATE character_currency SET platinum=" + std::to_string(out.wallet[0]) + ",gold=" + std::to_string(out.wallet[1]) +
				",silver=" + std::to_string(out.wallet[2]) + ",copper=" + std::to_string(out.wallet[3]) + " WHERE id=" + who);
			if (!paid.ok || paid.affected != 1) { return finish(Status::Uncertain); }
		}
		const auto amount = carried > Copper(out.wallet) ? carried - Copper(out.wallet) : Copper(out.wallet) - carried;
		auto receipt = query("INSERT INTO nightcap_bazaar_receipts(character_id,listing_id,operation,copper) VALUES(" + who + ',' +
			std::to_string(out.listing) + ',' + std::to_string(static_cast<unsigned>(request.op)) + ',' + std::to_string(amount) + ')');
		if (!receipt.ok || receipt.affected != 1) { return finish(Status::Uncertain); }
		if (!query("COMMIT").ok) { return finish(Status::Uncertain); }
		started = false; out.status = Status::Committed; return out;
	} catch (...) { return finish(Status::Uncertain); }
}
}

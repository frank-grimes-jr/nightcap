#pragma once

#include "../../server-mods/code/common/advanced_loot_protocol.h"
#include <algorithm>
#include <array>
#include <unordered_set>

namespace nightcap {
inline bool NewAdvancedLoot(const NightcapLoot::Snapshot &before, const NightcapLoot::Snapshot &after,
	std::unordered_set<uint32_t> &seen) {
	if (after.view != NightcapLoot::View::Drops) { return false; }
	// A newly queued item may be beyond the visible eight rows.
	bool fresh = before.view == NightcapLoot::View::Drops && after.total > before.total;
	for (const auto &row : after.rows) { if (seen.insert(row.token).second) { fresh = true; } }
	if (seen.size() > 8192) {
		seen.clear();
		for (const auto &row : after.rows) { seen.insert(row.token); }
	}
	return fresh;
}
inline bool KeepNoTradeConfirmation(const NightcapLoot::Snapshot &before, const NightcapLoot::Snapshot &after, uint32_t token) {
	using namespace NightcapLoot;
	if (!token || before.session != after.session || !(before.identity == after.identity) ||
		before.view != View::Drops || after.view != View::Drops || before.page != after.page || before.settings != after.settings) { return false; }
	const auto old_row = std::find_if(before.rows.begin(), before.rows.end(), [=](const Row &row) { return row.token == token; });
	const auto new_row = std::find_if(after.rows.begin(), after.rows.end(), [=](const Row &row) { return row.token == token; });
	return old_row != before.rows.end() && new_row != after.rows.end() &&
		old_row->corpse == new_row->corpse && old_row->item == new_row->item && old_row->quantity == new_row->quantity &&
		old_row->phase == new_row->phase && old_row->filter == new_row->filter &&
		(old_row->capabilities & Capability(Action::TakeNoTrade)) && (new_row->capabilities & Capability(Action::TakeNoTrade));
}
class AdvancedLootState {
	NightcapLoot::Snapshot active_, pending_;
	uint32_t context_spawn_ = 0, highest_revision_ = 0, session_ = 0;
	std::string context_name_;
	bool staging_ = false, ready_ = false;
	const char *error_ = "none";

	bool Reject(const char *reason) { error_ = reason; staging_ = false; ready_ = false; pending_ = {}; return false; }
	std::string Prefix(const char *verb) const {
		return std::string("#advloot ") + verb + " " + std::to_string(active_.session) + " " + std::to_string(active_.revision);
	}
public:
	void Clear() { *this = AdvancedLootState{}; }
	void Context(uint32_t spawn, const std::string &name) {
		if (spawn != context_spawn_ || name != context_name_) {
			Clear(); context_spawn_ = spawn; context_name_ = name;
		}
	}
	bool Ready() const { return ready_ && !staging_; }
	const char *Error() const { return error_; }
	const NightcapLoot::Snapshot &Current() const { return active_; }

	// Call only for direct server metadata in the established UI channel. A
	// complete, correctly counted snapshot replaces the visible list atomically.
	bool Consume(std::string_view message) {
		using namespace NightcapLoot;
		std::vector<std::string_view> f;
		if (!Fields(message, f) || f.empty() || f[0].size() != 8 || f[0].substr(0, 7) != "[NCAL1]") { return Reject("snapshot-envelope"); }
		const char type = f[0][7];
		if ((type == 'B' && f.size() != 12) || (type == 'I' && f.size() != 13) ||
			(type == 'E' && f.size() != 4) || (type != 'B' && type != 'I' && type != 'E')) { return Reject("snapshot-fields"); }
		std::array<uint32_t, 10> v{};
		const std::size_t numeric = type == 'E' ? 3 : 10;
		for (std::size_t i = 0; i < numeric; ++i) {
			if (!Number(f[i + 1], v[i])) { return Reject("snapshot-number"); }
		}
		if (!v[0] || !v[1]) { return Reject("snapshot-zero-session"); }
		if (type == 'B') {
			std::string name;
			if (!Unhex(f[11], name) || !context_spawn_ || v[5] != context_spawn_ || name != context_name_ ||
				!v[2] || !v[3] || v[3] > 65535 || v[4] > 65535 || v[5] > 65535 ||
				(v[6] & ~AllSettings) || v[7] > 1 || v[9] > MaxResults ||
				v[8] > (v[9] ? (v[9] - 1) / PageSize : 0)) { return Reject("snapshot-context-or-header"); }
			if ((session_ && session_ != v[0]) || v[1] <= highest_revision_) { return Reject("snapshot-session-or-replay"); }
			if (active_.session && !(active_.identity == Identity{v[2], v[3], v[4], v[5], name})) { return Reject("snapshot-identity-changed"); }
			session_ = v[0]; highest_revision_ = v[1];
			pending_ = {};
			pending_.session = v[0]; pending_.revision = v[1];
			pending_.identity = {v[2], v[3], v[4], v[5], std::move(name)};
			pending_.settings = v[6]; pending_.view = static_cast<View>(v[7]);
			pending_.page = v[8]; pending_.total = v[9];
			staging_ = true; ready_ = false;
			return true;
		}
		if (!staging_ || v[0] != pending_.session || v[1] != pending_.revision) { return Reject("snapshot-sequence"); }
		if (type == 'E') {
			const auto expected = std::min<std::size_t>(PageSize, pending_.total - pending_.page * PageSize);
			if (v[2] != pending_.rows.size() || v[2] != expected) { return Reject("snapshot-row-count"); }
			active_ = std::move(pending_); pending_ = {};
			staging_ = false; ready_ = true; error_ = "none";
			return true;
		}
		if (pending_.rows.size() == PageSize || !v[2] || !v[4] || v[3] > 65535 || v[6] > 65535 ||
			v[5] > 65535 || (v[7] & ~AllCapabilities) || v[8] > 5 || v[9] > 4 ||
			std::any_of(pending_.rows.begin(), pending_.rows.end(), [&](const Row &r) { return r.token == v[2]; })) { return Reject("snapshot-row-values"); }
		const bool filter_record = pending_.view == View::Filters;
		if (filter_record ? (v[3] || v[5] || v[8] != 5) : (!v[3] || !v[5] || v[8] == 5)) { return Reject("snapshot-row-view"); }
		Row row;
		if (!Unhex(f[11], row.name) || !Unhex(f[12], row.source)) { return Reject("snapshot-row-text"); }
		row.token = v[2]; row.corpse = v[3]; row.item = v[4]; row.quantity = v[5]; row.icon = v[6];
		row.capabilities = v[7]; row.phase = static_cast<Phase>(v[8]); row.filter = static_cast<Filter>(v[9]);
		pending_.rows.push_back(std::move(row));
		return true;
	}

	std::string Command(std::size_t row, NightcapLoot::Action action, uint32_t recipient = 0) const {
		using namespace NightcapLoot;
		if (!Ready() || row >= active_.rows.size() || static_cast<uint32_t>(action) >= static_cast<uint32_t>(Action::EditFilter) ||
			!(active_.rows[row].capabilities & Capability(action)) || (action == Action::Assign && !recipient) ||
			(action != Action::Assign && recipient)) { return {}; }
		return Prefix("act") + " " + std::to_string(active_.rows[row].token) + " " +
			std::to_string(static_cast<uint32_t>(action)) + " " + std::to_string(recipient);
	}
	std::string FilterCommand(std::size_t row, NightcapLoot::Filter filter) const {
		using namespace NightcapLoot;
		if (!Ready() || row >= active_.rows.size() || static_cast<uint32_t>(filter) > 4 ||
			!(active_.rows[row].capabilities & Capability(Action::EditFilter))) { return {}; }
		return Prefix("filter") + " " + std::to_string(active_.rows[row].item) + " " + std::to_string(static_cast<uint32_t>(filter));
	}
	std::string ViewCommand(NightcapLoot::View view, uint32_t page, const std::string &search = {}) const {
		if (!Ready() || static_cast<uint32_t>(view) > 1 || page > NightcapLoot::MaxResults / NightcapLoot::PageSize || search.size() > 32) { return {}; }
		for (const unsigned char c : search) { if (c < 32 || c > 126) { return {}; } }
		return Prefix("view") + " " + std::to_string(static_cast<uint32_t>(view)) + " " + std::to_string(page) + " " +
			(search.empty() ? "-" : NightcapLoot::Hex(search));
	}
	std::string SettingsCommand(uint32_t settings) const {
		return !Ready() || (settings & ~NightcapLoot::AllSettings) ? std::string{} : Prefix("settings") + " " + std::to_string(settings);
	}
	std::string TakeAllCommand() const { return Ready() ? Prefix("all") : std::string{}; }
	std::string AssignTargetCommand(std::size_t row) const {
		if (!Ready() || row >= active_.rows.size() || !(active_.rows[row].capabilities & NightcapLoot::Capability(NightcapLoot::Action::Assign))) { return {}; }
		// Zero means resolve the server's current target, never trust a client pointer.
		return Prefix("act") + " " + std::to_string(active_.rows[row].token) + " 8 0";
	}
};
}

#pragma once
#include "advanced_loot_state.h"
#include "advanced_loot_screen.h"
#include <unordered_set>

namespace nightcap {
// Presentation/controller only. The zone validates every command and owns all
// item state. No client inventory mutation or simulated corpse-loot packets.
class AdvancedLootUI {
	using Screen = AdvancedLootScreen;
	using Send = bool (*)(const std::string &);
	using Notice = void (*)(const char *);
	inline static AdvancedLootState state_;
	inline static Send send_ = nullptr;
	inline static Notice notice_ = nullptr;
	inline static uint64_t now_ = 0, next_pulse_ = 0, next_refresh_ = 0, next_create_ = 0, sent_at_ = 0;
	inline static uint32_t selected_ = 0, confirm_ = 0, spawn_ = 0;
	inline static std::string name_, search_;
	inline static std::unordered_set<uint32_t> seen_;
	inline static std::unordered_set<void *> controls_;
	inline static bool busy_ = false, dirty_ = true, configured_ = false, want_show_ = false, failed_ = false;
	static const char *FilterName(NightcapLoot::Filter filter) {
		static const char *names[] = {"Ask", "Always loot", "Never", "Always need", "Always greed"};
		return names[static_cast<unsigned>(filter)];
	}
	static const char *PhaseName(NightcapLoot::Phase phase) {
		static const char *names[] = {"Personal", "Shared", "Rolling", "Awarded", "Free grab", "Saved filter"};
		return names[static_cast<unsigned>(phase)];
	}
	static void Text(const std::string &id, const std::string &text) { Screen::Text(Screen::Child(id), text); }
	static void Enable(const std::string &id, bool enabled) { Screen::Enable(Screen::Child(id), enabled); }
	static std::size_t Selected() {
		const auto &rows = state_.Current().rows;
		for (std::size_t i = 0; i < rows.size(); ++i) { if (rows[i].token == selected_) { return i; } }
		return rows.size();
	}
	static bool Available() { return state_.Ready() && !busy_; }
	static void Submit(const std::string &command) {
		if (!command.empty() && send_ && send_(command)) {
			busy_ = true; sent_at_ = now_; dirty_ = true; confirm_ = 0;
		}
	}
	static void Refresh() {
		if (now_ < next_refresh_) { return; }
		if (send_ && send_("#advloot refresh")) { next_refresh_ = now_ + 5000; }
	}
	static void Render() {
		using namespace NightcapLoot;
		const auto &s = state_.Current();
		const auto index = Selected();
		const Row *selected = index < s.rows.size() ? &s.rows[index] : nullptr;
		const bool ready = Available();
		Text("NCAL_Status", !state_.Ready() ? "Connecting to advanced loot..." : busy_ ? "Waiting for server..." :
			std::string(s.view == View::Drops ? "Loot" : "Saved filters") + " - " + std::to_string(s.total) +
			" items - page " + std::to_string(s.page + 1) + "/" + std::to_string((std::max)(1u, (s.total + 7) / 8)));
		for (std::size_t i = 0; i < PageSize; ++i) {
			const auto suffix = std::to_string(i);
			const bool exists = i < s.rows.size();
			Text("NCAL_Row" + suffix, !exists ? "" : (s.rows[i].token == selected_ ? "> " : "") + s.rows[i].name +
				(s.view == View::Drops ? " x" + std::to_string(s.rows[i].quantity) : ""));
			Text("NCAL_Source" + suffix, !exists ? "" : s.rows[i].source + " - " + PhaseName(s.rows[i].phase));
			Enable("NCAL_Row" + suffix, ready && exists);
		}
		Text("NCAL_Selected", !selected ? "Select an item to loot, share or change its saved filter." :
			selected->name + " | " + FilterName(selected->filter));
		Text("NCAL_Help", confirm_ ? "NO TRADE: click Confirm loot to accept this item, or select another item to cancel." :
			"Never leaves items on the corpse. Shared loot keeps the group's loot permissions.");
		static const char *actions[] = {"Take", "Leave", "Need", "Greed", "Pass", "Roll", "FreeGrab", "Inspect", "Assign", "Find"};
		for (unsigned i = 0; i < 10; ++i) {
			const uint32_t capability = Capability(static_cast<Action>(i)) | (i == 0 ? Capability(Action::TakeNoTrade) : 0);
			Enable(std::string("NCAL_") + actions[i], ready && selected && (selected->capabilities & capability));
		}
		Text("NCAL_Take", confirm_ ? "Confirm loot" : "Loot");
		for (unsigned i = 0; i < 5; ++i) {
			const std::string id = "NCAL_Filter" + std::to_string(i);
			Enable(id, ready && selected && (selected->capabilities & Capability(Action::EditFilter)));
			Text(id, std::string(selected && static_cast<unsigned>(selected->filter) == i ? "* " : "") + FilterName(static_cast<Filter>(i)));
		}
		static const char *settings[] = {"Advanced loot", "Apply filters", "Auto show", "Auto loot all", "Split coin", "New items only"};
		for (unsigned i = 0; i < 6; ++i) {
			const std::string id = "NCAL_Setting" + std::to_string(i);
			Text(id, std::string(s.settings & (1u << i) ? "[x] " : "[ ] ") + settings[i]); Enable(id, ready);
		}
		for (const char *id : {"NCAL_Drops", "NCAL_Filters", "NCAL_Search", "NCAL_Clear"}) { Enable(id, ready); }
		Enable("NCAL_Previous", ready && s.page > 0);
		Enable("NCAL_Next", ready && (s.page + 1) * PageSize < s.total);
		Enable("NCAL_All", ready && s.view == View::Drops && s.total > 0);
		dirty_ = false;
	}
	static bool Configure() {
		// A partial/outdated skin must not leave unlabeled active controls.
		controls_.clear();
		auto include = [](const std::string &id) { auto control = Screen::Child(id); if (control) { controls_.insert(control); } return control != nullptr; };
		for (const char *id : {"Status", "Selected", "Help", "Drops", "Filters", "Previous", "Next", "All", "SearchText",
			"Search", "Clear", "Refresh", "Take", "Leave", "Need", "Greed", "Pass", "Roll", "FreeGrab", "Inspect", "Assign", "Find"}) {
			if (!include(std::string("NCAL_") + id)) { return false; }
		}
		for (unsigned i = 0; i < 8; ++i) {
			if (!include("NCAL_Row" + std::to_string(i)) || !include("NCAL_Source" + std::to_string(i))) { return false; }
		}
		for (unsigned i = 0; i < 6; ++i) { if (!include("NCAL_Setting" + std::to_string(i))) { return false; } }
		for (unsigned i = 0; i < 5; ++i) { if (!include("NCAL_Filter" + std::to_string(i))) { return false; } }
		Text("NCAL_SearchText", search_);
		Screen::EditLimit(Screen::Child("NCAL_SearchText"));
		return true;
	}
public:
	static void Initialize(Send send, Notice notice) { send_ = send; notice_ = notice; }
	static void Reset() {
		state_.Clear(); selected_ = confirm_ = spawn_ = 0; name_.clear(); search_.clear(); seen_.clear();
		busy_ = false; dirty_ = true; want_show_ = false; failed_ = false; next_refresh_ = 0;
		if (configured_) { Text("NCAL_SearchText", ""); }
		Screen::Show(false);
	}
	static void Destroyed() { configured_ = false; controls_.clear(); dirty_ = true; next_create_ = now_ + 1000; }
	static void Pulse(uint64_t now, uint32_t spawn, const char *name) {
		now_ = now;
		if (!send_ || now < next_pulse_) { return; }
		next_pulse_ = now + 100;
		if (!spawn || !name || !name[0]) { if (spawn_) { Reset(); } return; }
		if (spawn != spawn_ || name_ != name) { Reset(); spawn_ = spawn; name_ = name; next_create_ = now + 1000; }
		state_.Context(spawn, name);
		if (Screen::Broken() || now < next_create_) { return; }
		if (!Screen::Create() || (!configured_ && !Configure())) {
			Screen::Destroy(); next_create_ = now + 5000;
			if (!failed_ && notice_) { notice_("Advanced loot could not load its window. Repair the Nightcap client UI if this persists."); }
			failed_ = true;
			return;
		}
		configured_ = true; failed_ = false;
		if (!state_.Ready() || (busy_ && now - sent_at_ > 5000)) { Refresh(); }
		if (dirty_) { Render(); }
		if (want_show_) { Screen::Show(true); want_show_ = false; }
	}
	static void Toggle() {
		if (!spawn_) { return; }
		if (Screen::Window()) { Screen::Show(!Screen::Visible()); }
		else { want_show_ = true; }
		Refresh();
	}
	static bool Consume(std::string_view message) {
		if (message.substr(0, 7) != "[NCAL1]") { return false; }
		const uint32_t revision = state_.Current().revision;
		state_.Consume(message); dirty_ = true;
		if (state_.Ready() && state_.Current().revision != revision) {
			busy_ = false; confirm_ = 0;
			const auto &s = state_.Current();
			bool fresh = false;
			if (s.view == NightcapLoot::View::Drops) {
				for (const auto &row : s.rows) { if (seen_.insert(row.token).second) { fresh = true; } }
				// Bound memory even during very long sessions. Tokens remain server-owned.
				if (seen_.size() > 8192) { seen_.clear(); for (const auto &row : s.rows) { seen_.insert(row.token); } }
			}
			if (fresh && (s.settings & NightcapLoot::Enabled) && (s.settings & NightcapLoot::AutoShow)) { want_show_ = true; }
			if (Selected() == s.rows.size()) { selected_ = s.rows.empty() ? 0 : s.rows[0].token; }
		}
		return true; // reserved metadata never leaks into chat, even if malformed
	}
	static bool Notify(void *sender, uint32_t message, void *) {
		using namespace NightcapLoot;
		if (!sender || !Screen::Window() || !controls_.count(sender)) { return false; }
		auto clicked = [&](const std::string &id) { return Screen::Child(id) == sender; };
		// Only our controls reach this callback. Suppress native drag/hotbutton
		// notifications, which assume the sending control belongs to a stock UI.
		if (message != 1) { return true; }
		if (clicked("NCAL_Refresh")) { Refresh(); return true; }
		if (!Available()) { Refresh(); return true; }
		const auto &s = state_.Current();
		for (std::size_t i = 0; i < s.rows.size(); ++i) {
			if (clicked("NCAL_Row" + std::to_string(i))) { selected_ = s.rows[i].token; confirm_ = 0; dirty_ = true; return true; }
		}
		auto view = [&](View target, uint32_t page) { Submit(state_.ViewCommand(target, page, search_)); };
		if (clicked("NCAL_Drops")) { view(View::Drops, 0); return true; }
		if (clicked("NCAL_Filters")) { view(View::Filters, 0); return true; }
		if (clicked("NCAL_Previous") && s.page) { view(s.view, s.page - 1); return true; }
		if (clicked("NCAL_Next") && (s.page + 1) * PageSize < s.total) { view(s.view, s.page + 1); return true; }
		if (clicked("NCAL_Search")) {
			char input[33]{};
			if (Screen::EditText(Screen::Child("NCAL_SearchText"), input)) { search_ = input; view(s.view, 0); }
			return true;
		}
		if (clicked("NCAL_Clear")) { search_.clear(); Text("NCAL_SearchText", ""); view(s.view, 0); return true; }
		if (clicked("NCAL_All")) { Submit(state_.TakeAllCommand()); return true; }
		for (unsigned i = 0; i < 6; ++i) {
			if (clicked("NCAL_Setting" + std::to_string(i))) { Submit(state_.SettingsCommand(s.settings ^ (1u << i))); return true; }
		}
		const auto index = Selected();
		if (index == s.rows.size()) { return true; }
		for (unsigned i = 0; i < 5; ++i) {
			if (clicked("NCAL_Filter" + std::to_string(i))) { Submit(state_.FilterCommand(index, static_cast<Filter>(i))); return true; }
		}
		static const char *actions[] = {"Take", "Leave", "Need", "Greed", "Pass", "Roll", "FreeGrab", "Inspect", "Assign", "Find"};
		for (unsigned i = 0; i < 10; ++i) {
			if (!clicked(std::string("NCAL_") + actions[i])) { continue; }
			auto action = static_cast<Action>(i);
			if (action == Action::Take && (s.rows[index].capabilities & Capability(Action::TakeNoTrade))) {
				if (confirm_ != selected_) { confirm_ = selected_; dirty_ = true; return true; }
				action = Action::TakeNoTrade;
			}
			Submit(action == Action::Assign ? state_.AssignTargetCommand(index) : state_.Command(index, action)); return true;
		}
		return true;
	}
};
}

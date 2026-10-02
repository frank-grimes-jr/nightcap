#pragma once
#include "advanced_loot_state.h"
#include "advanced_loot_screen.h"
#include <unordered_set>
#include <unordered_map>

namespace nightcap {
// Presentation only. The zone remains authoritative for rights and transfers.
class AdvancedLootUI {
	using Screen = AdvancedLootScreen;
	using Send = bool (*)(const std::string &);
	using Notice = void (*)(const char *);
	enum class Panel { List, Settings, Rule, More };
	enum class Fault { None, Send, Timeout, Snapshot, Search };
	inline static AdvancedLootState state_;
	inline static Send send_ = nullptr;
	inline static Notice notice_ = nullptr, trace_ = nullptr;
	inline static uint64_t now_ = 0, next_pulse_ = 0, next_refresh_ = 0, next_create_ = 0, sent_at_ = 0;
	inline static uint32_t selected_ = 0, confirm_ = 0, spawn_ = 0;
	inline static std::string name_, search_;
	inline static std::unordered_map<void *, std::string> controls_;
	inline static std::unordered_set<uint32_t> seen_;
	inline static bool busy_ = false, dirty_ = true, configured_ = false, want_show_ = false, failed_ = false;
	inline static Panel panel_ = Panel::List;
	inline static Fault fault_ = Fault::None;
	inline static NightcapLoot::View desired_view_ = NightcapLoot::View::Drops;
	static const char *FilterName(NightcapLoot::Filter filter) {
		static const char *names[] = {"Ask each time", "Always loot", "Never loot", "Always need", "Always greed"};
		return names[static_cast<unsigned>(filter)];
	}
	static void Trace(const char *event) { if (trace_) { trace_(event); } }
	static void Text(const std::string &id, const std::string &text) { Screen::Text(Screen::Child("NCAL_" + id), text); }
	static void Enable(const std::string &id, bool enabled) { Screen::Enable(Screen::Child("NCAL_" + id), enabled); }
	static void Visible(const std::string &id, bool visible) { Screen::Visible(Screen::Child("NCAL_" + id), visible); }
	static std::size_t Selected() {
		const auto &rows = state_.Current().rows;
		for (std::size_t i = 0; i < rows.size(); ++i) { if (rows[i].token == selected_) { return i; } }
		return rows.size();
	}
	static bool Available() { return state_.Ready() && !busy_ && fault_ != Fault::Snapshot && fault_ != Fault::Timeout; }
	static void SetFault(Fault fault, const char *event) { fault_ = fault; dirty_ = true; Trace(event); }
	static void Submit(const std::string &command, bool clear_confirmation = true) {
		if (command.empty()) { return; }
		if (!send_ || !send_(command)) { SetFault(Fault::Send, "send-unavailable"); return; }
		busy_ = true; sent_at_ = now_; dirty_ = true; fault_ = Fault::None;
		if (clear_confirmation) { confirm_ = 0; }
		Trace(("request-sent:" + command.substr(9, command.find(' ', 9) - 9)).c_str());
	}
	static void Refresh(bool manual = false) {
		// Never interrupt a request with a second command. A retry asks for state;
		// it never repeats a loot/assignment operation with an unknown outcome.
		if (busy_ || (!manual && now_ < next_refresh_)) { return; }
		Submit("#advloot refresh", false);
		next_refresh_ = now_ + (busy_ ? 10000 : 1000);
	}
	static void RequestView(NightcapLoot::View view) {
		desired_view_ = view; panel_ = Panel::List; selected_ = confirm_ = 0; dirty_ = true;
		if (Available()) { Submit(state_.ViewCommand(view, 0, search_)); }
		else { Refresh(); }
	}
	static void Render() {
		using namespace NightcapLoot;
		const auto &s = state_.Current();
		const auto index = Selected();
		const Row *row = index < s.rows.size() ? &s.rows[index] : nullptr;
		const bool ready = Available(), matching = s.view == desired_view_;
		if (!row && (panel_ == Panel::Rule || panel_ == Panel::More)) { panel_ = Panel::List; }
		const bool list = panel_ == Panel::List, settings = panel_ == Panel::Settings;
		const bool rule = panel_ == Panel::Rule, more = panel_ == Panel::More;
		const bool drops = desired_view_ == View::Drops;
		auto can = [&](Action action) { return row && (row->capabilities & Capability(action)); };
		std::string status;
		if (fault_ == Fault::Timeout) { status = "No reply from the server. Click Retry."; }
		else if (fault_ == Fault::Send) { status = "Could not send the request. Click Retry."; }
		else if (fault_ == Fault::Snapshot) { status = "Loot data could not be read. Click Retry."; }
		else if (fault_ == Fault::Search) { status = "Search accepts up to 32 plain-text characters."; }
		else if (busy_) { status = state_.Current().revision ? "Updating loot..." : "Connecting to loot..."; }
		else if (!state_.Ready()) { status = "Connecting to loot..."; }
		else if (!(s.settings & Enabled)) { status = "Advanced loot is off. Enable it in Settings."; }
		else { status = drops ? "Loot from your kills" : "Your saved item rules"; }
		Text("Status", status);
		Text("Refresh", fault_ == Fault::None ? "Refresh" : "Retry"); Enable("Refresh", !busy_);
		Text("Drops", std::string(list && drops ? "> " : "") + "Loot");
		Text("Filters", std::string(list && !drops ? "> " : "") + "Saved rules");
		Text("Options", std::string(settings ? "> " : "") + "Settings");
		// Local navigation never depends on a server reply.
		for (const char *id : {"Drops", "Filters", "Options", "Back"}) { Enable(id, true); }
		for (const char *id : {"SearchText", "Search", "Clear", "Previous", "Next", "Page", "Selected"}) { Visible(id, list); }
		for (const char *id : {"Search", "Clear"}) { Enable(id, ready && matching); }
		Text("Page", matching && state_.Ready() ? std::to_string(s.total) + " items  " + std::to_string(s.page + 1) + "/" +
			std::to_string((std::max)(1u, (s.total + 7) / 8)) : "");
		Enable("Previous", ready && matching && s.page > 0);
		Enable("Next", ready && matching && (s.page + 1) * PageSize < s.total);
		for (std::size_t i = 0; i < PageSize; ++i) {
			const auto suffix = std::to_string(i);
			const bool exists = matching && i < s.rows.size();
			Visible("Row" + suffix, list && exists); Visible("Source" + suffix, list && exists);
			if (!exists) { continue; }
			const auto &item = s.rows[i];
			Text("Row" + suffix, std::string(item.token == selected_ ? "> " : "") + item.name + (drops ? " x" + std::to_string(item.quantity) : ""));
			Text("Source" + suffix, drops ? item.source : FilterName(item.filter));
			Enable("Row" + suffix, true);
		}
		Visible("Empty", list && (!matching || s.rows.empty()));
		Text("Empty", !state_.Ready() || !matching ? "Waiting for the loot list..." : !search_.empty() ? "No items match your search." :
			drops ? "No items waiting. Loot from your kills appears here." : "No saved rules. Select a dropped item to create one.");
		Text("Selected", row && matching ? row->name + " - " + FilterName(row->filter) : "");
		Visible("Take", list && drops && row && matching);
		Enable("Take", ready && (can(Action::Take) || can(Action::TakeNoTrade)));
		Text("Take", confirm_ ? "Confirm NO TRADE" : "Loot item");
		Visible("Rule", list && row && matching && can(Action::EditFilter)); Enable("Rule", row != nullptr);
		Visible("More", list && row && matching); Enable("More", row != nullptr);
		Visible("All", list && drops && matching && s.total > 0); Enable("All", ready);
		Visible("Back", !list); Visible("PanelTitle", !list);
		Text("PanelTitle", settings ? "Loot settings" : row ? row->name : "");
		static const char *extras[] = {"Inspect", "Leave", "Find", "Need", "Greed", "Pass", "Roll", "FreeGrab", "Assign"};
		static const Action actions[] = {Action::Inspect, Action::Leave, Action::FindCorpse, Action::Need, Action::Greed,
			Action::Pass, Action::Roll, Action::FreeGrab, Action::Assign};
		for (unsigned i = 0; i < 9; ++i) { Visible(extras[i], more && can(actions[i])); Enable(extras[i], ready && can(actions[i])); }
		for (unsigned i = 0; i < 5; ++i) {
			const std::string suffix = std::to_string(i);
			const bool visible = rule;
			Visible("Filter" + suffix, visible); Visible("FilterHelp" + suffix, visible);
			Enable("Filter" + suffix, ready && can(Action::EditFilter));
			Text("Filter" + suffix, std::string(row && static_cast<unsigned>(row->filter) == i ? "> " : "") + FilterName(static_cast<Filter>(i)));
		}
		static const char *labels[] = {"Advanced loot", "Use saved rules", "Open on new loot", "Loot everything", "Split coin", "Unfiltered items only"};
		for (unsigned i = 0; i < 6; ++i) {
			const std::string suffix = std::to_string(i);
			Visible("Setting" + suffix, settings); Visible("SettingHelp" + suffix, settings);
			Text("Setting" + suffix, std::string(s.settings & (1u << i) ? "[On] " : "[Off] ") + labels[i]); Enable("Setting" + suffix, ready);
		}
		Text("Help", confirm_ ? "NO TRADE: click Confirm to accept. Selecting another item cancels." :
			settings ? "Settings and item rules are saved for this character." :
			rule ? "Choose how to handle this item next time. Never leaves it on the corpse." :
			more ? "Group actions appear only when your loot permissions allow them." :
			drops ? "Select an item, then Loot item. Item rule saves an Always or Never choice." :
			"Select an item to change its rule. Ask each time removes the saved rule.");
		dirty_ = false;
	}
	static bool Configure() {
		controls_.clear();
		auto include = [](const std::string &id) { auto control = Screen::Child("NCAL_" + id); if (control) { controls_.emplace(control, id); } return control != nullptr; };
		for (const char *id : {"Status", "Selected", "Help", "Drops", "Filters", "Options", "Previous", "Next", "Page", "All", "SearchText",
			"Search", "Clear", "Refresh", "Take", "Rule", "More", "Back", "PanelTitle", "Empty", "Leave", "Need", "Greed", "Pass", "Roll", "FreeGrab", "Inspect", "Assign", "Find"}) {
			if (!include(id)) { return false; }
		}
		for (unsigned i = 0; i < 8; ++i) { if (!include("Row" + std::to_string(i)) || !include("Source" + std::to_string(i))) { return false; } }
		for (unsigned i = 0; i < 6; ++i) { if (!include("Setting" + std::to_string(i)) || !include("SettingHelp" + std::to_string(i))) { return false; } }
		for (unsigned i = 0; i < 5; ++i) { if (!include("Filter" + std::to_string(i)) || !include("FilterHelp" + std::to_string(i))) { return false; } }
		Text("SearchText", search_); Screen::EditLimit(Screen::Child("NCAL_SearchText"));
		return true;
	}
	static bool Handle(void *sender, uint32_t message) {
		using namespace NightcapLoot;
		if (!sender || !Screen::Window() || !controls_.count(sender)) { return false; }
		auto clicked = [&](const std::string &id) { return Screen::Child("NCAL_" + id) == sender; };
		const bool search = (message == 1 && clicked("Search")) || (message == 6 && clicked("SearchText"));
		if (message != 1 && !search) { return true; }
		Trace(("control-click:" + controls_.at(sender)).c_str());
		if (clicked("Options")) { panel_ = Panel::Settings; confirm_ = 0; dirty_ = true; return true; }
		if (clicked("Back")) { panel_ = Panel::List; confirm_ = 0; dirty_ = true; return true; }
		if (clicked("Drops")) { RequestView(View::Drops); return true; }
		if (clicked("Filters")) { RequestView(View::Filters); return true; }
		if (clicked("Refresh")) { Refresh(true); return true; }
		const auto &s = state_.Current();
		for (std::size_t i = 0; i < s.rows.size(); ++i) {
			if (clicked("Row" + std::to_string(i))) { selected_ = s.rows[i].token; confirm_ = 0; dirty_ = true; return true; }
		}
		if (clicked("Rule") || clicked("More")) { panel_ = clicked("Rule") ? Panel::Rule : Panel::More; confirm_ = 0; dirty_ = true; return true; }
		if (!Available()) { return true; }
		if (clicked("Previous") && s.page) { Submit(state_.ViewCommand(s.view, s.page - 1, search_)); return true; }
		if (clicked("Next") && (s.page + 1) * PageSize < s.total) { Submit(state_.ViewCommand(s.view, s.page + 1, search_)); return true; }
		if (search) {
			char input[33]{};
			if (Screen::EditText(Screen::Child("NCAL_SearchText"), input)) { search_ = input; Submit(state_.ViewCommand(s.view, 0, search_)); }
			else { SetFault(Fault::Search, "search-rejected"); }
			return true;
		}
		if (clicked("Clear")) { search_.clear(); Text("SearchText", ""); Submit(state_.ViewCommand(s.view, 0)); return true; }
		if (clicked("All")) { Submit(state_.TakeAllCommand()); return true; }
		for (unsigned i = 0; i < 6; ++i) { if (clicked("Setting" + std::to_string(i))) { Submit(state_.SettingsCommand(s.settings ^ (1u << i))); return true; } }
		const auto index = Selected();
		if (index == s.rows.size()) { return true; }
		for (unsigned i = 0; i < 5; ++i) {
			if (clicked("Filter" + std::to_string(i))) { Submit(state_.FilterCommand(index, static_cast<Filter>(i))); return true; }
		}
		static const char *actions[] = {"Take", "Leave", "Need", "Greed", "Pass", "Roll", "FreeGrab", "Inspect", "Assign", "Find"};
		for (unsigned i = 0; i < 10; ++i) {
			if (!clicked(actions[i])) { continue; }
			auto action = static_cast<Action>(i);
			if (action == Action::Take && (s.rows[index].capabilities & Capability(Action::TakeNoTrade))) {
				if (confirm_ != selected_) { confirm_ = selected_; dirty_ = true; return true; }
				action = Action::TakeNoTrade;
			}
			Submit(action == Action::Assign ? state_.AssignTargetCommand(index) : state_.Command(index, action)); return true;
		}
		return true;
	}
public:
	static void Initialize(Send send, Notice notice, Notice trace = nullptr) { send_ = send; notice_ = notice; trace_ = trace; }
	static void Reset() {
		state_.Clear(); selected_ = confirm_ = spawn_ = 0; name_.clear(); search_.clear(); seen_.clear();
		busy_ = false; dirty_ = true; want_show_ = false; failed_ = false; next_refresh_ = 0;
		panel_ = Panel::List; desired_view_ = NightcapLoot::View::Drops; fault_ = Fault::None;
		if (configured_) { Text("SearchText", ""); }
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
			if (!failed_ && notice_) { notice_("Advanced loot could not load. Repair the Nightcap client UI."); }
			failed_ = true; return;
		}
		configured_ = true; failed_ = false;
		if (busy_ && now - sent_at_ >= 5000) {
			busy_ = false; next_refresh_ = now + 10000; SetFault(Fault::Timeout, "reply-timeout");
		}
		if (!busy_ && (!state_.Ready() || fault_ == Fault::Timeout || fault_ == Fault::Snapshot)) { Refresh(); }
		if (Available() && desired_view_ != state_.Current().view) { Submit(state_.ViewCommand(desired_view_, 0, search_)); }
		if (dirty_) { Render(); }
		if (want_show_) { Screen::Show(true); want_show_ = false; }
	}
	static void Toggle() {
		if (!spawn_) { return; }
		if (Screen::Window()) { Screen::Show(!Screen::Visible()); }
		else { want_show_ = true; }
		Refresh(); if (configured_ && dirty_) { Render(); }
	}
	static bool Consume(std::string_view message) {
		if (message.substr(0, 7) != "[NCAL1]") { return false; }
		const auto before = state_.Current();
		if (!state_.Consume(message)) {
			busy_ = false; next_refresh_ = now_ + 10000; SetFault(Fault::Snapshot, state_.Error()); return true;
		}
		dirty_ = true;
		if (state_.Ready() && state_.Current().revision != before.revision) {
			busy_ = false; fault_ = Fault::None; Trace("snapshot-accepted");
			const auto &s = state_.Current();
			if (!KeepNoTradeConfirmation(before, s, confirm_)) { confirm_ = 0; }
			const bool fresh = NewAdvancedLoot(before, s, seen_);
			if (fresh && (s.settings & NightcapLoot::Enabled) && (s.settings & NightcapLoot::AutoShow)) { want_show_ = true; }
			// Drop tokens and saved-rule item IDs are different namespaces. A
			// vanished selection must never retarget a pending detail-panel click.
			if (before.view != s.view || Selected() == s.rows.size()) {
				selected_ = confirm_ = 0;
				if (panel_ == Panel::Rule || panel_ == Panel::More) { panel_ = Panel::List; }
			}
		}
		return true;
	}
	static bool Notify(void *sender, uint32_t message, void *) {
		const bool handled = Handle(sender, message);
		if (handled && configured_ && dirty_) { Render(); }
		return handled;
	}
};
}

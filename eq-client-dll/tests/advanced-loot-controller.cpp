#include "../src/advanced_loot_ui.h"
#include <cassert>
#include <cstdlib>
#include <iostream>
#include <map>
#include <memory>

using namespace nightcap;
using namespace NightcapLoot;
struct Control { alignas(4) unsigned char bytes[0x280]{}; std::string text; };
static std::map<std::string, std::unique_ptr<Control>> controls;
static std::array<void *, 1 + 0x17c / 4> tables{};
static void **native = tables.data() + 1;
static std::vector<std::string> requests, events;
static uint64_t clock_ms = 1000;
static bool send_ok = true;
static bool Visible(const char *id) { return controls.at(std::string("NCAL_") + id)->bytes[0x196] != 0; }
static bool IsEnabled(const char *id) { return controls.at(std::string("NCAL_") + id)->bytes[0x1a] != 0; }
static std::string Text(const char *id) { return controls.at(std::string("NCAL_") + id)->text; }
static void *__cdecl Allocate(std::size_t size) { return std::calloc(1, size); }
static void *__fastcall Construct(void *self, void *, void *, const LootScreenString *, int, int, const char *) {
	*static_cast<void ***>(self) = native;
	*reinterpret_cast<void **>(static_cast<unsigned char *>(self) + 0x1e0) = self;
	return self;
}
static void __fastcall Children(void *, void *) {}
static LootScreenString *__fastcall Assign(LootScreenString *self, void *, const char *text) { self->rep = const_cast<char *>(text); return self; }
static void *__fastcall Child(void *, void *, const LootScreenString *name) {
	auto found = controls.find(static_cast<const char *>(name->rep));
	return found == controls.end() ? nullptr : found->second->bytes;
}
static void *__fastcall Destroy(void *self, void *, unsigned) { std::free(self); return nullptr; }
static int __fastcall NativeNotify(void *, void *, void *, uint32_t, void *) { return 0; }
static int __fastcall NativeFrame(void *, void *) { return 0; }
static int __fastcall Show(void *self, void *, bool visible, bool, bool) { static_cast<unsigned char *>(self)[0x196] = visible; return 0; }
static void __fastcall SetText(void *self, void *, const LootScreenString *text) {
	reinterpret_cast<Control *>(self)->text = static_cast<const char *>(text->rep);
}
static bool Send(const std::string &request) { if (!send_ok) { return false; } requests.push_back(request); return true; }
static void Trace(const char *event) { events.emplace_back(event); }
static void Notice(const char *) { assert(false && "Unexpected UI setup error"); }
static void Frame() {}
static void Pulse(uint64_t advance = 100) { clock_ms += advance; AdvancedLootUI::Pulse(clock_ms, 7, "Fixture"); }
static void Click(const char *id, uint32_t message = 1) {
	assert(Visible(id) && IsEnabled(id));
	auto self = AdvancedLootScreen::Window();
	auto table = *static_cast<void ***>(self);
	using Notify = int (__thiscall *)(void *, void *, uint32_t, void *);
	assert(reinterpret_cast<Notify>(table[0x88 / 4])(self, controls.at(std::string("NCAL_") + id)->bytes, message, nullptr) == 1);
}
static void SnapshotReady(Snapshot &s) {
	++s.revision;
	assert(AdvancedLootUI::Consume(Begin(s)));
	for (const auto &row : s.rows) { assert(AdvancedLootUI::Consume(Item(s, row))); }
	assert(AdvancedLootUI::Consume(End(s)));
	Pulse();
}
int main() {
	native[1] = reinterpret_cast<void *>(&Destroy);
	native[0x88 / 4] = reinterpret_cast<void *>(&NativeNotify);
	native[0xc4 / 4] = reinterpret_cast<void *>(&NativeFrame);
	native[0xd8 / 4] = reinterpret_cast<void *>(&Show);
	native[0x124 / 4] = reinterpret_cast<void *>(&SetText);
	auto add = [](const std::string &id) {
		auto control = std::make_unique<Control>();
		*reinterpret_cast<void ***>(control->bytes) = native;
		control->bytes[0x196] = control->bytes[0x1a] = 1;
		controls.emplace("NCAL_" + id, std::move(control));
	};
	for (const char *id : {"Status", "Selected", "Help", "Drops", "Filters", "Options", "Previous", "Next", "Page", "All", "SearchText", "Search", "Clear", "Refresh", "Take", "Rule", "More", "Back", "PanelTitle", "Empty", "Leave", "Need", "Greed", "Pass", "Roll", "FreeGrab", "Inspect", "Assign", "Find"}) { add(id); }
	for (unsigned i = 0; i < 8; ++i) {
		for (const char *prefix : {"Row", "Source", "Ignore", "Always", "Never"}) { add(prefix + std::to_string(i)); }
	}
	for (unsigned i = 0; i < 6; ++i) { add("Setting" + std::to_string(i)); add("SettingHelp" + std::to_string(i)); }
	for (unsigned i = 0; i < 5; ++i) { add("Filter" + std::to_string(i)); add("FilterHelp" + std::to_string(i)); }
	LootScreenAPI api{&Allocate, reinterpret_cast<LootScreenAPI::Construct>(&Construct), reinterpret_cast<LootScreenAPI::Children>(&Children),
		reinterpret_cast<LootScreenAPI::Assign>(&Assign), reinterpret_cast<LootScreenAPI::Child>(&Child), native};
	assert(AdvancedLootScreen::Bind(api, &AdvancedLootUI::Notify, &Frame, &AdvancedLootUI::Destroyed));
	AdvancedLootUI::Initialize(&Send, &Notice, &Trace);
	Pulse(); Pulse(1100);
	assert(requests.size() == 1 && requests.back() == "#advloot refresh");
	assert(!Visible("Setting0") && !Visible("Filter0") && !Visible("Roll"));
	Click("Options"); assert(Visible("Setting0") && !IsEnabled("Setting0") && !Visible("Search"));
	Pulse(5000); assert(Text("Status").find("No reply") != std::string::npos && IsEnabled("Refresh"));
	Click("Refresh"); assert(requests.size() == 2 && Text("Status") == "Connecting to loot...");
	Snapshot s; s.session = 1; s.identity = {42,22,0,7,"Fixture"}; s.settings = 7;
	SnapshotReady(s); assert(IsEnabled("Setting0") && Text("Setting0") == "[On] Advanced loot");
	Click("Setting2"); assert(requests.back() == "#advloot settings 1 1 3");
	s.settings = 3; SnapshotReady(s); assert(Text("Setting2") == "[Off] Open on new loot");
	Click("Drops"); SnapshotReady(s); assert(Visible("Empty") && !Visible("Setting0"));
	Row row; row.token = 11; row.corpse = 77; row.item = 13073; row.quantity = 2; row.name = "Bone Chips"; row.source = "a skeleton";
	row.capabilities = Capability(Action::Take) | Capability(Action::Inspect) | Capability(Action::Leave) | Capability(Action::EditFilter);
	s.rows = {row}; s.total = 1; SnapshotReady(s); assert(!Visible("Take")); Click("Row0");
	assert(Visible("Row0") && !Visible("Row1") && !Visible("Empty") && Visible("Take") && !Visible("Leave"));
	Click("Take"); assert(requests.back() == "#advloot act 1 4 11 0 0" && !IsEnabled("Take"));
	SnapshotReady(s); Click("Rule"); assert(Visible("Filter0") && Visible("Filter3") && !Visible("Row0"));
	Click("Filter2"); assert(requests.back() == "#advloot filter 1 5 13073 2");
	s.rows[0].filter = Filter::Never; SnapshotReady(s); assert(Text("Filter2") == "> Never loot");
	Click("Back"); Click("More"); assert(Visible("Inspect") && Visible("Leave") && !Visible("Need") && !Visible("Setting0"));
	Click("Inspect"); assert(requests.back() == "#advloot act 1 6 11 7 0"); SnapshotReady(s);
	Click("Back"); s.rows[0].capabilities ^= Capability(Action::Take) | Capability(Action::TakeNoTrade); SnapshotReady(s);
	const auto count = requests.size(); Click("Take"); assert(requests.size() == count && Text("Take") == "Confirm NO TRADE");
	Click("Refresh"); assert(Text("Take") == "Confirm NO TRADE");
	SnapshotReady(s); assert(Text("Take") == "Confirm NO TRADE");
	Click("Take"); assert(requests.back() == "#advloot act 1 9 11 10 0"); SnapshotReady(s);
	Click("Filters"); assert(requests.back() == "#advloot view 1 10 1 0 -");
	s.view = View::Filters; s.rows[0].token = s.rows[0].item; s.rows[0].corpse = 0; s.rows[0].quantity = 0; s.rows[0].phase = Phase::FilterRecord;
	s.rows[0].capabilities = Capability(Action::Inspect) | Capability(Action::EditFilter);
	SnapshotReady(s); assert(!Visible("Rule")); Click("Row0"); assert(!Visible("Take") && !Visible("All") && Visible("Rule"));
	Click("Rule"); assert(Visible("Filter3")); Click("Back");
	send_ok = false; Click("Refresh"); assert(Text("Status").find("Could not send") != std::string::npos);
	send_ok = true; Click("Refresh");
	AdvancedLootUI::Consume("[NCAL1]E|1|999|0"); Pulse(); assert(Text("Status").find("could not be read") != std::string::npos);
	Click("Options"); assert(Visible("Setting0") && !IsEnabled("Setting0"));
	Click("Refresh"); SnapshotReady(s); assert(IsEnabled("Setting0"));
	Click("Drops");
	s.view = View::Drops; s.rows[0].token = 11; s.rows[0].corpse = 77; s.rows[0].quantity = 2; s.rows[0].phase = Phase::Rolling;
	s.rows[0].capabilities = AllCapabilities; SnapshotReady(s); Click("Row0");
	Click("More");
	for (const auto &choice : std::vector<std::pair<const char *, unsigned>>{{"Need",2},{"Greed",3},{"Pass",4},{"Roll",5},{"FreeGrab",6},{"Assign",8},{"Find",9},{"Leave",1}}) {
		const auto expected = "#advloot act 1 " + std::to_string(s.revision) + " 11 " + std::to_string(choice.second) + " 0";
		Click(choice.first); assert(requests.back() == expected); SnapshotReady(s);
	}
	Click("Back"); Click("All"); assert(requests.back() == "#advloot all 1 " + std::to_string(s.revision)); SnapshotReady(s);
	// Direct Never needs no selected-item submenu; bulk consent needs the
	// server prompt and is cancelled by navigation, revision changes or expiry.
	s.rows[0].filter = Filter::Ask; SnapshotReady(s);
	Click("Never0"); assert(requests.back() == "#advloot filter 1 " + std::to_string(s.revision) + " 13073 2"); SnapshotReady(s);
	Click("All"); SnapshotReady(s);
	assert(!AdvancedLootUI::Consume("Advanced loot: Confirm NO TRADE for 1 item(s). Looted 0; 0 unavailable.")); Pulse();
	assert(Text("All") == "Confirm NO TRADE");
	Click("All"); assert(requests.back() == "#advloot allconfirm 1 " + std::to_string(s.revision)); SnapshotReady(s);
	Click("All"); SnapshotReady(s);
	AdvancedLootUI::Consume("Advanced loot: Confirm NO TRADE for 1 item(s). Looted 0; 0 unavailable."); Pulse();
	Click("Options"); Click("Back"); assert(Text("All") == "Loot All");
	Click("All"); SnapshotReady(s);
	AdvancedLootUI::Consume("Advanced loot: Confirm NO TRADE for 1 item(s). Looted 0; 0 unavailable."); Pulse();
	SnapshotReady(s); assert(Text("All") == "Loot All");
	Click("All"); SnapshotReady(s);
	AdvancedLootUI::Consume("Advanced loot: Confirm NO TRADE for 1 item(s). Looted 0; 0 unavailable."); Pulse(30001);
	assert(Text("All") == "Loot All");
	// A partial response must fail closed and expose Retry; never resend an award.
	Click("Take"); Click("Take");
	const auto awards = requests.size();
	++s.revision; AdvancedLootUI::Consume(Begin(s)); Pulse(5000);
	assert(requests.size() == awards && Text("Status").find("No reply") != std::string::npos);
	Click("Refresh"); assert(requests.back() == "#advloot refresh"); SnapshotReady(s);
	// Removing the selected item must close its editor without selecting a
	// replacement. Otherwise the next click can save a rule for another item.
	for (const char *panel : {"Rule", "More"}) {
		Click(panel); ++s.rows[0].token; ++s.rows[0].item; s.rows[0].name = "Another item";
		SnapshotReady(s); assert(!Visible("Back") && !Visible("Rule") && !Visible("More"));
		Click("Row0");
	}
	// Real Filters tokens equal item IDs. Colliding with an old drop token
	// cannot carry selection across views.
	const auto old_token = s.rows[0].token;
	Click("Filters"); s.view = View::Filters; s.rows[0].token = s.rows[0].item = old_token;
	s.rows[0].corpse = s.rows[0].quantity = 0; s.rows[0].phase = Phase::FilterRecord;
	s.rows[0].capabilities = Capability(Action::Inspect) | Capability(Action::EditFilter);
	SnapshotReady(s); assert(!Visible("Rule") && !Visible("More") && Text("Selected").empty());
	assert(Text("Ignore0") == "Remove"); Click("Ignore0");
	assert(requests.back() == "#advloot filter 1 " + std::to_string(s.revision) + " " + std::to_string(old_token) + " 0"); SnapshotReady(s);
	// Inline choices act on their own row without changing the selected item.
	Click("Drops"); s.view = View::Drops; s.settings = Enabled | ApplyFilters | AutoShow;
	row.token = 101; row.filter = Filter::Ask; s.rows = {row, row}; s.rows[1].token = 102; s.rows[1].item = 1068; s.total = 2;
	SnapshotReady(s); assert(AdvancedLootScreen::Visible());
	assert(Visible("Always0") && Visible("Never0") && !Visible("Ignore0") && !Visible("Always2"));
	assert(Text("Always0") == "[ ] Always Loot" && Text("Never0") == "[ ] Never Loot");
	Click("Row0"); Click("Always1");
	assert(requests.back() == "#advloot filter 1 " + std::to_string(s.revision) + " 1068 1");
	assert(Text("Always1") == "[ ] Always Loot" && !IsEnabled("Always0") && !IsEnabled("Never1"));
	const auto sent = requests.size(); AdvancedLootUI::Notify(controls.at("NCAL_Never0")->bytes, 1, nullptr);
	assert(requests.size() == sent);
	s.rows[1].filter = Filter::AlwaysTake; SnapshotReady(s);
	assert(Text("Always1") == "[x] Always Loot" && Text("Never1") == "[ ] Never Loot");
	assert(Text("Row0").find("> ") == 0 && !Visible("Back"));
	Click("Never1"); assert(requests.back() == "#advloot filter 1 " + std::to_string(s.revision) + " 1068 2");
	s.rows[1].filter = Filter::Never; SnapshotReady(s);
	assert(Text("Always1") == "[ ] Always Loot" && Text("Never1") == "[x] Never Loot");
	Click("Never1"); assert(requests.back() == "#advloot filter 1 " + std::to_string(s.revision) + " 1068 0");
	s.rows[1].filter = Filter::Ask; SnapshotReady(s);
	Click("Always1"); s.rows[1].filter = Filter::AlwaysTake; SnapshotReady(s);
	Click("Always1"); assert(requests.back() == "#advloot filter 1 " + std::to_string(s.revision) + " 1068 0"); SnapshotReady(s);
	send_ok = false; Click("Never1");
	assert(Text("Always1") == "[x] Always Loot" && Text("Never1") == "[ ] Never Loot");
	assert(Text("Status").find("Could not send") != std::string::npos);
	send_ok = true; Click("Refresh"); SnapshotReady(s);
	s.rows[1].capabilities = Capability(Action::Inspect); SnapshotReady(s);
	assert(!IsEnabled("Always1") && !IsEnabled("Never1"));
	const auto denied = requests.size(); AdvancedLootUI::Notify(controls.at("NCAL_Always1")->bytes, 1, nullptr);
	assert(requests.size() == denied);
	Click("Options"); assert(!Visible("Always0") && !Visible("Never0")); Click("Back");
	// A missing or failed award response cannot close the window. Only a
	// complete nonempty-to-empty drop snapshot may do that, across all pages.
	Click("All"); assert(AdvancedLootScreen::Visible()); SnapshotReady(s); assert(AdvancedLootScreen::Visible());
	s.rows = {row}; s.total = 9; s.page = 1; SnapshotReady(s);
	Click("All"); s.rows.clear(); s.total = s.page = 0; ++s.revision;
	assert(AdvancedLootUI::Consume(Begin(s))); assert(AdvancedLootScreen::Visible());
	assert(AdvancedLootUI::Consume(End(s))); Pulse(); assert(!AdvancedLootScreen::Visible());
	// Explicitly opening an empty window must allow settings/filter access.
	AdvancedLootUI::Toggle(); SnapshotReady(s); assert(AdvancedLootScreen::Visible());
	s.rows = {row}; s.total = 1; ++s.revision;
	AdvancedLootUI::Consume(Begin(s)); AdvancedLootUI::Consume(Item(s, row)); AdvancedLootUI::Consume(End(s));
	// Auto-show queued by new loot must be cancelled if it disappears before a frame.
	s.rows.clear(); s.total = 0; ++s.revision;
	AdvancedLootUI::Consume(Begin(s)); AdvancedLootUI::Consume(End(s)); Pulse(); assert(!AdvancedLootScreen::Visible());
	s.rows = {row}; s.total = 1; SnapshotReady(s); assert(AdvancedLootScreen::Visible());
	Click("Options"); s.rows.clear(); s.total = 0; SnapshotReady(s);
	assert(AdvancedLootScreen::Visible() && Visible("Setting0")); Click("Back");
	// Hiding rows through settings is not a completed loot operation.
	s.rows = {row}; s.total = 1; SnapshotReady(s);
	s.settings |= ShowNewOnly; s.rows.clear(); s.total = 0; SnapshotReady(s); assert(AdvancedLootScreen::Visible());
	// Navigating to Filters during an in-flight loot request keeps navigation open.
	s.settings &= ~ShowNewOnly; s.rows = {row}; s.total = 1; SnapshotReady(s);
	Click("All"); Click("Filters"); s.rows.clear(); s.total = 0; SnapshotReady(s); assert(AdvancedLootScreen::Visible());
	s.view = View::Filters; SnapshotReady(s); assert(AdvancedLootScreen::Visible() && Visible("Empty"));
	assert(!Visible("Always0") && !Visible("Never0"));
	assert(!AdvancedLootUI::Consume("ordinary chat"));
	AdvancedLootScreen::Destroy(); assert(!AdvancedLootScreen::Window());
	std::cout << "PASS: native notification ABI; panels, timeout/retry, commands, snapshots, NO TRADE, inline rule toggles and empty-queue auto-close\n";
}

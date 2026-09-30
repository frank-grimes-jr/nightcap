#include "../src/advanced_loot_state.h"
#include <cassert>
#include <iostream>

using namespace NightcapLoot;
using nightcap::AdvancedLootState;

static Snapshot Fixture(uint32_t revision = 1) {
	Snapshot s;
	s.session = 51; s.revision = revision; s.identity = {92, 22, 3, 100, "LootTester"};
	s.settings = Enabled | ApplyFilters | AutoShow; s.total = 2;
	s.rows = {
		{7, 65, 13073, 3, 501, Capability(Action::Take) | Capability(Action::EditFilter), Phase::Personal, Filter::Ask, "Bone Chips", "a skeleton"},
		{8, 66, 13073, 1, 501, Capability(Action::Need) | Capability(Action::Greed), Phase::Rolling, Filter::AlwaysNeed, "Bone Chips", "another skeleton"}
	};
	return s;
}
static void Commit(AdvancedLootState &state, const Snapshot &s) {
	assert(state.Consume(Begin(s)));
	for (const auto &row : s.rows) { assert(state.Consume(Item(s, row))); }
	assert(state.Consume(End(s)));
	assert(state.Ready());
}
static AdvancedLootState Fresh() {
	AdvancedLootState state;
	state.Context(100, "LootTester");
	return state;
}
static void RejectRow(const Row &row) {
	auto state = Fresh(); const auto s = Fixture();
	assert(state.Consume(Begin(s)));
	assert(!state.Consume(Item(s, row)));
	assert(!state.Ready());
}
int main() {
	auto state = Fresh(); auto s = Fixture();
	assert(!state.Ready() && state.Command(0, Action::Take).empty());
	Commit(state, s);
	assert(state.Current().rows.size() == 2); // same item on two corpses stays separate
	assert(state.Command(0, Action::Take) == "#advloot act 51 1 7 0 0");
	assert(state.Command(1, Action::Take).empty());
	assert(state.Command(1, Action::Need) == "#advloot act 51 1 8 2 0");
	assert(state.Command(2, Action::Take).empty());
	assert(state.Command(0, static_cast<Action>(UINT32_MAX)).empty());
	assert(state.FilterCommand(0, Filter::Never) == "#advloot filter 51 1 13073 2");
	assert(state.FilterCommand(1, Filter::Never).empty());
	assert(state.SettingsCommand(AllSettings + 1).empty());
	assert(state.ViewCommand(View::Filters, 0, "Bone Chips") == "#advloot view 51 1 1 0 426f6e65204368697073");
	assert(state.ViewCommand(View::Filters, 0, std::string(33, 'a')).empty());
	assert(state.ViewCommand(View::Filters, 0, "a\nb").empty());

	s = Fixture(2);
	assert(state.Consume(Begin(s)));
	assert(!state.Ready() && state.Current().revision == 1 && state.Command(0, Action::Take).empty());
	assert(state.Consume(Item(s, s.rows[0])));
	assert(!state.Consume(End(s))); // missing second row cannot publish a partial list
	assert(state.Current().revision == 1 && !state.Ready());
	s = Fixture(3); Commit(state, s);
	assert(state.Command(0, Action::Take) == "#advloot act 51 3 7 0 0");
	assert(!state.Consume(Begin(Fixture(2))) && state.Current().revision == 3);

	auto row = Fixture().rows[0]; row.token = 0; RejectRow(row);
	row = Fixture().rows[0]; row.corpse = 65536; RejectRow(row);
	row = Fixture().rows[0]; row.quantity = 0; RejectRow(row);
	row = Fixture().rows[0]; row.icon = 65536; RejectRow(row);
	row = Fixture().rows[0]; row.capabilities = 1u << 31; RejectRow(row);
	row = Fixture().rows[0]; row.filter = static_cast<Filter>(5); RejectRow(row);
	row = Fixture().rows[0]; row.name = std::string(64, 'a'); RejectRow(row);
	row = Fixture().rows[0]; row.name = "bad\nname"; RejectRow(row);
	row = Fixture().rows[0]; row.phase = Phase::FilterRecord; RejectRow(row);

	state = Fresh(); s = Fixture();
	assert(state.Consume(Begin(s)) && state.Consume(Item(s, s.rows[0])));
	assert(!state.Consume(Item(s, s.rows[0]))); // duplicate physical token
	assert(!state.Consume(End(s)) && !state.Ready());
	for (const auto &bad : {std::string("[NCAL1]B|4294967296|1|92|22|3|100|7|0|0|0|4c6f6f74546573746572"),
		std::string("[NCAL1]B|-1|1|92|22|3|100|7|0|0|0|4c6f6f74546573746572"),
		std::string("[NCAL1]B|51|1|92|22|3|100|7|0|0|0|00"), std::string(513, 'x')}) {
		state = Fresh(); assert(!state.Consume(bad) && !state.Ready());
	}
	for (unsigned kind = 0; kind < 8; ++kind) {
		state = Fresh(); s = Fixture();
		switch (kind) {
		case 0: s.identity.spawn = 101; break;
		case 1: s.identity.name = "OtherPlayer"; break;
		case 2: s.total = MaxResults + 1; break;
		case 3: s.page = 1; break;
		case 4: s.view = static_cast<View>(2); break;
		case 5: s.settings = 64; break;
		case 6: s.session = 0; break;
		case 7: s.revision = 0; break;
		}
		assert(!state.Consume(Begin(s)) && !state.Ready());
	}
	state = Fresh(); s = Fixture(); Commit(state, s);
	s.revision = 2; s.identity.character = 93;
	assert(!state.Consume(Begin(s)) && state.Current().identity.character == 92);
	s.identity.character = 92;
	s.session = 52; s.revision = 1;
	assert(!state.Consume(Begin(s))); // session changes only across a lifecycle reset
	state.Clear(); state.Context(100, "LootTester"); Commit(state, s);
	state.Context(101, "LootTester");
	assert(state.Current().rows.empty() && !state.Ready());

	state = Fresh(); s = Fixture(); s.rows.clear(); s.total = 0; Commit(state, s);
	assert(state.Current().rows.empty());
	state = Fresh(); s = Fixture(); s.rows.resize(1); s.total = 9; s.page = 1; s.view = View::Filters;
	s.rows[0].corpse = 0; s.rows[0].quantity = 0; s.rows[0].phase = Phase::FilterRecord;
	Commit(state, s); assert(state.Current().total == 9 && state.Current().rows.size() == 1);

	// Every truncation and corrupted frame must leave commands unavailable.
	s = Fixture();
	const auto message = Item(s, s.rows[0]);
	for (std::size_t length = 0; length < message.size(); ++length) {
		state = Fresh(); assert(state.Consume(Begin(s)));
		state.Consume(message.substr(0, length));
		assert(!state.Ready() && state.Command(0, Action::Take).empty());
	}
	// Auto-show notices a new item even when it appears on a later page.
	auto before = Fixture(); before.total = 8; before.rows.resize(8, before.rows.front());
	std::unordered_set<uint32_t> seen;
	for (uint32_t i = 0; i < 8; ++i) { before.rows[i].token = i + 1; seen.insert(i + 1); }
	auto after = before; after.revision++;
	assert(!nightcap::NewAdvancedLoot(before, after, seen));
	after.total = 9;
	assert(nightcap::NewAdvancedLoot(before, after, seen));
	after.view = View::Filters;
	assert(!nightcap::NewAdvancedLoot(before, after, seen));
	after = before; after.rows[0].token = 99;
	assert(nightcap::NewAdvancedLoot(before, after, seen));
	// Other players' choices and unrelated deaths do not cancel this confirmation.
	before = Fixture(); before.rows[0].capabilities = Capability(Action::TakeNoTrade);
	after = before; after.revision++; after.rows[1].source = "Unrelated roll update";
	assert(nightcap::KeepNoTradeConfirmation(before, after, 7));
	assert(!nightcap::KeepNoTradeConfirmation(before, after, 0));
	for (unsigned kind = 0; kind < 13; ++kind) {
		after = before;
		switch (kind) {
		case 0: after.rows[0].token++; break;
		case 1: after.rows[0].corpse++; break;
		case 2: after.rows[0].item++; break;
		case 3: after.rows[0].quantity++; break;
		case 4: after.rows[0].phase = Phase::Awarded; break;
		case 5: after.rows[0].capabilities = Capability(Action::Take); break;
		case 6: after.session++; break;
		case 7: after.identity.character++; break;
		case 8: after.view = View::Filters; break;
		case 9: after.page++; break;
		case 10: after.rows[0].filter = Filter::Never; break;
		case 11: after.rows.clear(); break;
		case 12: after.settings ^= Enabled; break;
		}
		assert(!nightcap::KeepNoTradeConfirmation(before, after, 7));
	}
	std::cout << "PASS: advanced loot snapshot identity, atomic publication, replay, capabilities, paging, auto-show, NO TRADE confirmation and malformed frames\n";
}

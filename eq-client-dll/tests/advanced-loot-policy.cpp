#include "../../server-mods/code/common/advanced_loot_policy.h"
#include <cassert>
#include <iostream>

using namespace NightcapLoot;
static bool Everyone(uint32_t) { return true; }
static std::size_t First(std::size_t count) { assert(count); return 0; }
int main() {
	unsigned transfers = 0;
	auto deliver = [&] { ++transfers; return TransferResult::Delivered; };
	DropPolicy personal(10, {{10, Filter::Ask}}, true);
	assert(!personal.CanTake(20) && personal.CanTake(10));
	assert(!personal.ShouldAutoTake(10, true, true, false));
	assert(personal.UpdateFilter(10, Filter::AlwaysTake));
	assert(personal.ShouldAutoTake(10, true, true, false));
	assert(!personal.ShouldAutoTake(10, false, true, true));
	assert(!personal.ShouldAutoTake(10, true, false, false));
	assert(personal.Take(20, deliver) == TransferResult::Declined && transfers == 0);
	assert(personal.Take(10, [] { return TransferResult::Declined; }) == TransferResult::Declined);
	assert(personal.CanTake(10)); // full inventory, lore, distance, quest veto: item stays pending
	assert(personal.Take(10, deliver) == TransferResult::Delivered && transfers == 1);
	assert(personal.Take(10, deliver) == TransferResult::Declined && transfers == 1); // replay
	assert(!personal.UpdateFilter(10, Filter::Ask));

	DropPolicy never(10, {{10, Filter::Never}}, true);
	assert(!never.CanTake(10) && !never.ShouldAutoTake(10, true, true, true));
	assert(never.State() == Distribution::Personal); // Never does not destroy the corpse item
	assert(never.UpdateFilter(10, Filter::Ask) && never.CanTake(10));
	assert(never.Leave(10) && never.State() == Distribution::Left && !never.CanTake(10));

	DropPolicy shared(10, {{10, Filter::Never}, {20, Filter::AlwaysTake}, {30, Filter::Ask}}, false);
	assert(!shared.CanTake(20) && !shared.ShouldAutoTake(20, true, true, true));
	assert(!shared.Assign(20, 20) && !shared.Assign(10, 40) && !shared.Assign(10, 10));
	assert(shared.Assign(10, 20) && shared.CanTake(20)); // master Never leaves others' access intact
	assert(!shared.Leave(30));
	assert(shared.Leave(20) && shared.State() == Distribution::Shared);
	assert(shared.OpenFreeGrab(10) && shared.CanTake(20) && shared.CanTake(30));
	assert(!shared.ShouldAutoTake(20, true, true, true)); // no auto-steal race in a shared free-grab list
	assert(shared.Take(30, deliver) == TransferResult::Delivered);
	assert(!shared.CanTake(20));

	DropPolicy roll(10, {{10, Filter::AlwaysGreed}, {20, Filter::AlwaysNeed}, {30, Filter::Ask}, {40, Filter::Never}}, false);
	assert(!roll.StartRoll(30, 100) && roll.StartRoll(10, 100));
	assert(!roll.Resolve(60099, Everyone, First));
	assert(!roll.Choose(40, Choice::Need, 200));
	assert(roll.Choose(30, Choice::Need, 200));
	assert(!roll.Choose(30, Choice::Greed, 60100));
	assert(roll.Resolve(60100, Everyone, [](std::size_t count) { assert(count == 2); return 1; }));
	assert(roll.Recipient() == 30 && roll.CanTake(30) && !roll.CanTake(20));
	assert(!roll.Resolve(60100, Everyone, First));

	DropPolicy fallback(10, {{10, Filter::AlwaysGreed}, {20, Filter::AlwaysNeed}}, false);
	assert(fallback.StartRoll(10, 0));
	assert(fallback.Resolve(60000, [](uint32_t id) { return id != 20; }, First));
	assert(fallback.Recipient() == 10); // lost current corpse rights excludes the need candidate
	DropPolicy pass(10, {{10, Filter::Never}, {20, Filter::Ask}}, false);
	assert(pass.StartRoll(10, 0));
	assert(pass.Choose(20, Choice::Pass, 1));
	assert(pass.Resolve(60000, Everyone, [](std::size_t) -> std::size_t { assert(false); return 0; }));
	assert(pass.State() == Distribution::Left);

	DropPolicy uncertain(10, {{10, Filter::Ask}}, true);
	assert(uncertain.Take(10, [] { return TransferResult::Uncertain; }) == TransferResult::Uncertain);
	assert(!uncertain.CanTake(10) && uncertain.State() == Distribution::Quarantined);
	uncertain.Invalidate(); assert(uncertain.State() == Distribution::Quarantined);
	assert(uncertain.Take(10, deliver) == TransferResult::Declined);
	DropPolicy reentry(10, {{10, Filter::Ask}}, true);
	assert(reentry.Take(10, [&] {
		assert(reentry.Take(10, deliver) == TransferResult::Declined);
		assert(!reentry.Leave(10) && !reentry.UpdateFilter(10, Filter::Never));
		return TransferResult::Delivered;
	}) == TransferResult::Delivered);
	DropPolicy throwing(10, {{10, Filter::Ask}}, true);
	try { throwing.Take(10, []() -> TransferResult { throw std::runtime_error("lost commit acknowledgement"); }); assert(false); }
	catch (const std::runtime_error &) {}
	assert(throwing.State() == Distribution::Quarantined);
	DropPolicy expired(10, {{10, Filter::Ask}}, true);
	expired.Invalidate(); assert(!expired.CanTake(10));

	bool invalid = false;
	try { DropPolicy bad(10, {{20, Filter::Ask}}, false); } catch (const std::invalid_argument &) { invalid = true; }
	assert(invalid);
	std::cout << "PASS: advanced loot personal/shared decisions, need/greed priority, access loss, replay and uncertain-transfer quarantine\n";
}

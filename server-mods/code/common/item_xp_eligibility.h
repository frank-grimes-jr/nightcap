#pragma once
#include "item_upgrade_policy.h"

namespace NightcapItemXP {
constexpr uint32_t PowerSourceMask = uint32_t{1} << 21;

inline int Tier(uint32_t id)
{
	if (NightcapHunt::IsReward(id)) { return int(id % 4); }
	if (id && id < 800000 && id % 200000) { return int(id / 200000); }
	return -1;
}

template <typename Definition>
bool Candidate(const Definition *item)
{
	return item && Tier(item->ID) >= 0 && item->ItemClass == 0 && item->NoRent && !item->Stackable &&
		!(item->Slots & PowerSourceMask) && (item->Slots || item->AugType);
}

// Resolve every tier, not just arithmetic IDs. A missing/foreign successor
// cannot be trained, and separate epic/dungeon catalogs remain separate.
template <typename Definition, typename Lookup>
int Family(const Definition *item, Lookup lookup)
{
	if (!Candidate(item)) { return -1; }
	const int tier = Tier(item->ID);
	const bool hunt = NightcapHunt::IsReward(item->ID);
	const uint32_t step = hunt ? 1 : 200000;
	const uint32_t base = item->ID - static_cast<uint32_t>(tier) * step;
	const auto first = lookup(base);
	if (!Candidate(first)) { return -1; }
	auto previous = first;
	for (uint32_t i = 1; i < 4; ++i) {
		const auto next = lookup(base + i * step);
		if (!Candidate(next) || next->ID != base + i * step || next->Slots != first->Slots ||
			next->AugType != first->AugType ||
			(hunt ? NightcapHunt::NextTier(previous->ID) != next->ID :
				!NightcapUpgrade::NamesMatch(previous->Name, next->Name, previous->ID))) { return -1; }
		previous = next;
	}
	return tier;
}
}

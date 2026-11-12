#pragma once

#include "common/raid_augment.h"
#include <bitset>

namespace NightcapRaidAug {
// A receipt can contain more than one inventory item (a trade or a mailed bag).
// Keep the seen set across that receipt while using native LORE custody for owned items.
class IncomingTrophies {
public:
	template<class Character, class Item>
	uint32_t Conflict(Character &recipient, const Item *incoming, const Item *leaving = nullptr)
	{
		return Visit(incoming, [&](const Item &trophy) {
			const auto id = trophy.GetID();
			const auto index = id - First;
			if (seen.test(index)) { return true; }
			seen.set(index);
			return recipient.CheckLoreConflict(trophy.GetItem()) &&
				!Visit(leaving, [id](const Item &outgoing) { return outgoing.GetID() == id; });
		});
	}

private:
	std::bitset<Prism - First + 1> seen;

	template<class Item, class Predicate>
	static uint32_t Visit(const Item *item, const Predicate &match)
	{
		if (!item || !item->GetItem()) { return 0; }
		if (IsReward(item->GetID()) && match(*item)) { return item->GetID(); }
		if (item->IsClassBag()) {
			for (uint8_t i = 0; i < item->GetItem()->BagSlots; ++i) {
				if (const auto id = Visit(item->GetItem(i), match)) { return id; }
			}
		} else {
			for (uint8_t i = 0; i < 6; ++i) {
				const auto *aug = item->GetAugment(i);
				if (aug && IsReward(aug->GetID()) && match(*aug)) { return aug->GetID(); }
			}
		}
		return 0;
	}
};
}

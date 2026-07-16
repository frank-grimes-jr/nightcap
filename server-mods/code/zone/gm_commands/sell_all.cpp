#include "zone/client.h"
#include "common/rulesys.h"

// #35: player-facing #sellall -- vendors everything in general inventory and
// bag contents, keeping the bags themselves. No merchant target needed; pays
// flat items.price * Merchant:BuyCostMod like a vendor sale.
// ponytail: skips the CHA/faction price mod (CalcPriceMod needs a merchant
// target) -- add a targeted-merchant mode if the ±4% ever matters.
static uint64 SellAllSlot(Client *c, int16 slot_id)
{
	EQ::ItemInstance *inst = c->GetInv().GetItem(slot_id);
	if (!inst) {
		return 0;
	}

	const EQ::ItemData *item = inst->GetItem();
	if (!item) {
		return 0;
	}

	// keep bags; skip no-drop (vendors won't buy), temporary (free money from
	// summoned gear, see #33), and worthless items
	if (item->IsClassBag() || !item->NoDrop || !item->NoRent || !item->Price) {
		return 0;
	}

	uint32 quantity = 1;
	if (inst->IsStackable() && inst->GetCharges() > 0) {
		quantity = inst->GetCharges();
	}

	auto price = (uint64)((uint64)item->Price * quantity * RuleR(Merchant, BuyCostMod) + 0.5);

	c->AddMoneyToPP(price, true);
	c->DeleteItemInInventory(slot_id, inst->IsStackable() ? inst->GetCharges() : 0, true);

	return price;
}

void command_sell_all(Client *c, const Seperator *sep)
{
	uint64 total = 0;
	int    sold  = 0;

	for (int16 i = EQ::invslot::GENERAL_BEGIN; i <= EQ::invslot::GENERAL_END; i++) {
		if ((((uint64)1 << i) & c->GetInv().GetLookup()->PossessionsBitmask) == 0) {
			continue;
		}

		for (uint8 j = EQ::invbag::SLOT_BEGIN; j <= EQ::invbag::SLOT_END; j++) {
			uint64 price = SellAllSlot(c, EQ::InventoryProfile::CalcSlotId(i, j));
			if (price) {
				total += price;
				sold++;
			}
		}

		uint64 price = SellAllSlot(c, i);
		if (price) {
			total += price;
			sold++;
		}
	}

	if (!sold) {
		c->Message(Chat::White, "Nothing sellable in your bags (bags, no-drop, and temporary items are kept).");
		return;
	}

	c->Message(
		Chat::White,
		fmt::format(
			"Sold {} item{} for {}p {}g {}s {}c.",
			sold,
			sold == 1 ? "" : "s",
			total / 1000,
			(total / 100) % 10,
			(total / 10) % 10,
			total % 10
		).c_str()
	);
}

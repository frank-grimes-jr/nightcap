#include "zone/client.h"
#include "common/rulesys.h"
#include "common/item_trade_policy.h"

// #35: player-facing #sellall -- vendors everything in general inventory and
// bag contents, keeping the bags themselves. No merchant target needed; pays
// fixed resale for former NO DROP items; ordinary items retain their flat rate.
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

	// Keep containers. The universal former-NO-DROP policy includes summoned items.
	if (item->IsClassBag() || !item->NoDrop || (!item->NoRent && !item->FixedSellPrice) || !item->Price) {
		return 0;
	}

	const uint32 quantity = EQ::ItemTradePolicy::SaleUnits(inst->IsStackable(), inst->IsCharged(),
		inst->GetCharges(), inst->IsStackable() ? inst->GetCharges() : 1);
	if (!quantity) { return 0; }

	const uint64 price = item->FixedSellPrice ? EQ::ItemTradePolicy::FixedSalePrice(*item, quantity) :
		(uint64)((uint64)item->Price * quantity * RuleR(Merchant, BuyCostMod) + 0.5);
	if (!price) { return 0; }

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
		c->Message(Chat::White, "Nothing sellable in your inventory. Containers are kept; ordinary temporary and zero-value items are skipped.");
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

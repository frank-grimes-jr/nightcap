#include "common/item_trade_policy.h"
#include <cassert>
#include <cstdint>
#include <limits>

struct Item {
	bool FreeTrade = false;
	uint32_t FixedSellPrice = 0;
	uint32_t Price = 0;
	uint8_t NoDrop = 0;
	uint8_t FVNoDrop = 1;
	bool Attuneable = true;
	bool NoTransfer = true;
};

int main()
{
	using namespace EQ::ItemTradePolicy;
	Item original;
	Apply(original, false, true);
	assert(!original.FreeTrade && original.NoDrop == 0 && original.Attuneable);
	assert(original.FixedSellPrice == 0 && original.Price == 0);
	Item converted;
	Apply(converted, true, true);
	assert(converted.FreeTrade && converted.NoDrop == 255 && converted.FVNoDrop == 0);
	assert(!converted.Attuneable && !converted.NoTransfer);
	assert(converted.FixedSellPrice == 1000 && converted.Price == 1000);
	Item expensive;
	expensive.Price = 7500000;
	Apply(expensive, true, true);
	assert(expensive.Price == 7500000 && expensive.FixedSellPrice == 1000);
	Item tradable;
	tradable.Price = 200;
	Apply(tradable, true, false);
	assert(tradable.Price == 200 && tradable.FixedSellPrice == 0 && tradable.NoDrop == 255);
	for (uint32_t price : {0u, 1u, 950u, 1000u, 2000u, 7500000u}) {
		assert(PurchasePrice(converted, price) >= 1000);
		assert(PurchasePrice(tradable, price) == price);
	}
	assert(SaleUnits(false, false, 0, 1) == 1);
	assert(SaleUnits(false, false, 0, 2) == 0);
	assert(SaleUnits(false, true, 10, 1) == 1);
	assert(SaleUnits(false, true, 10, 10) == 1);
	assert(SaleUnits(false, true, -1, 1) == 1);
	assert(SaleUnits(false, true, -1, 2) == 0);
	assert(SaleUnits(false, true, 10, 11) == 0);
	assert(SaleUnits(true, false, 20, 5) == 5);
	assert(SaleUnits(true, true, 20, 5) == 5);
	assert(SaleUnits(true, false, 20, 20) == 20);
	assert(SaleUnits(true, false, 20, 21) == 0);
	assert(SaleUnits(true, false, -1, 1) == 0);
	assert(SaleUnits(true, false, 0, 1) == 0);
	assert(SaleUnits(false, false, 0, 0) == 0);
	assert(SaleUnits(true, false, 20, std::numeric_limits<uint32_t>::max()) == 0);
	assert(FixedSalePrice(converted, 1) == 1000);
	assert(FixedSalePrice(converted, 5) == 5000);
	assert(FixedSalePrice(converted, 4000000) == 4000000000u);
	assert(FixedSalePrice(converted, 4000001) == 0);
	assert(FixedSalePrice(tradable, 1) == 0);
}

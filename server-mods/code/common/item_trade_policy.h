#pragma once

#include <algorithm>
#include <cstdint>

namespace EQ::ItemTradePolicy {

constexpr uint32_t OnePlatinum = 1000;

// Keep original catalog flags in SQL. This projection travels with shared/items.
template <typename Item>
void Apply(Item &item, bool enabled, bool originally_no_drop)
{
	item.FreeTrade = enabled;
	item.FixedSellPrice = enabled && originally_no_drop ? OnePlatinum : 0;
	if (!enabled) { return; }
	item.NoDrop = 255;
	item.FVNoDrop = 0;
	item.Attuneable = false;
	item.NoTransfer = false;
	if (item.FixedSellPrice) {
		// The native merchant UI refuses zero-value items.
		item.Price = std::max(item.Price, item.FixedSellPrice);
	}
}

template <typename Item>
uint32_t PurchasePrice(const Item &item, uint32_t calculated)
{
	// Apply after faction/charisma/sellrate so buyback cannot mint platinum.
	return std::max(calculated, item.FixedSellPrice);
}

inline uint32_t SaleUnits(bool stackable, bool charged, int charges, uint32_t requested)
{
	if (!requested) { return 0; }
	if (stackable) {
		return charges > 0 && requested <= static_cast<uint32_t>(charges) ? requested : 0;
	}
	if (requested == 1) { return 1; }
	// Clients can submit the number of charges, but the physical item sells once.
	return charged && charges > 0 && requested <= static_cast<uint32_t>(charges) ? 1 : 0;
}

template <typename Item>
uint32_t FixedSalePrice(const Item &item, uint32_t units)
{
	const uint64_t price = static_cast<uint64_t>(item.FixedSellPrice) * units;
	return price <= 4000000000ULL ? static_cast<uint32_t>(price) : 0;
}

} // namespace EQ::ItemTradePolicy

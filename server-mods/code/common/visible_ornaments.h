#pragma once

#include <cstdint>
#include <string_view>

namespace NightcapOrnaments {
constexpr uint32_t ArmorSlots = 4 | 128 | 1536 | 4096 | 131072 | 262144 | 524288;
constexpr uint32_t HandSlots = 8192 | 16384;
constexpr uint32_t RangeSlot = 2048;
constexpr uint32_t Artisan = 998946;
constexpr uint32_t FirstDesign = 1000000;
constexpr uint32_t LastDesign = 1048575;

template<typename Item>
int SocketType(const Item &item)
{
	if (item.ItemClass != 0 || item.AugType || item.ItemType == 54) { return 0; }
	if (item.ItemType == 5 && (item.Slots & RangeSlot)) { return 20; }
	if (item.Slots & HandSlots) { return 20; }
	if (item.Slots & ArmorSlots) { return 21; }
	return 0;
}

// Overlay the last empty position in the six-socket RoF2 layout. Reuse a
// matching (possibly hidden) stock socket before allocating another position.
template<typename Item>
int Socket(const Item &item)
{
	const int type = SocketType(item);
	if (!type) { return -1; }
	int spare = -1;
	int other_ornament = -1;
	for (int i = 0; i < 6; ++i) {
		if (item.AugSlotType[i] == type) { return i; }
		if (item.AugSlotType[i] == 20 || item.AugSlotType[i] == 21) { other_ornament = i; }
		if (!item.AugSlotType[i]) { spare = i; }
	}
	return spare >= 0 ? spare : other_ornament;
}

template<typename Host, typename Augment>
bool Fits(const Host &host, const Augment &augment)
{
	if (!(host.Slots & augment.Slots)) { return false; }
	if (augment.AugType == (1u << 20)) { return SocketType(host) == 21; }
	if (SocketType(host) != 20) { return false; }
	if (host.ItemType == 8 || augment.AugRestrict == 13) { return host.ItemType == 8 && augment.AugRestrict == 13; }
	if (host.ItemType == 5 || augment.AugRestrict == 12) { return host.ItemType == 5 && augment.AugRestrict == 12; }
	return true;
}

template<typename Item>
bool Design(const Item &item)
{
	return item.ID >= FirstDesign && item.ID <= LastDesign && item.ItemType == 54 &&
		(item.AugType == (1u << 19) || item.AugType == (1u << 20)) &&
		std::string_view(item.Lore) == "Nightcap appearance ornament";
}
}

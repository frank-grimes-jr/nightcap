#pragma once
#include <cstdint>

namespace NightcapRaidAug {
constexpr uint32_t First = 963200;
constexpr uint32_t Aegis = First + 13;
constexpr uint32_t Heart = First + 14;
constexpr uint32_t Prism = First + 15;
constexpr int Chest = 17, SocketType = 22, Level = 50;
constexpr bool IsReward(uint32_t id) { return id >= First && id <= Prism; }
constexpr bool IsHost(uint32_t slots) { return slots == (1u << Chest); }

// A host which also fits another equipment position would give a second active slot.
template<class Item>
bool CanInsert(const Item &host, int socket, bool replacing)
{
	if (socket < 0 || socket >= 6 || !IsHost(host.GetItem()->Slots) ||
		host.GetItem()->AugSlotType[socket] != SocketType) { return false; }
	for (int i = 0; i < 6; ++i) {
		if (IsReward(host.GetAugmentItemID(i)) && !(replacing && i == socket)) { return false; }
	}
	return true;
}
}

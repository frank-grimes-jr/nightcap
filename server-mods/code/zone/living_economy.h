#pragma once

#include "common/types.h"
#include <array>
#include <string>
#include <vector>

namespace NightcapMarket {
struct Offer {
	uint64 epoch = 0;
	uint32 npc_id = 0;
	uint32 zone_id = 0;
	uint32 item_id = 0;
	uint32 price_cp = 0;
	std::string kind;
};

struct Item {
	uint32 id = 0;
	uint32 serial = 0;
	uint32 color = 0;
	int16 charges = 0;
};

using Wallet = std::array<uint32, 4>; // platinum, gold, silver, copper
enum class Result { Rejected, Committed, Uncertain };
bool Ready();
std::vector<Offer> ReadOffers(uint32 npc_id, uint32 zone_id, int era);
bool ReadOffer(uint32 npc_id, uint32 zone_id, int era, Offer &offer, uint32 item_id = 0);
Result Trade(uint32 character_id, const Offer &offer, int era, const Wallet &before,
	const Wallet &after, const Item &item);
}

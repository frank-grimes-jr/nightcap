#pragma once
#include "common/advanced_loot_policy.h"
#include <string>
#include <vector>

class Client;
namespace EQ { class ItemInstance; }

namespace NightcapLoot {
enum class ClaimStatus { Available, Claimed, Unavailable };
enum class Destination { Inventory, Cursor, InventoryOrCursor };
std::string NewDropID();
bool ValidDropID(const std::string &id);
ClaimStatus ReadClaim(const std::string &id);

// One durable receipt per physical source item, in the same transaction as all
// inventory destinations. No cursor overflow or auto-equip side effects.
TransferResult ReceiveItem(Client *client, const EQ::ItemInstance &item, const std::vector<std::string> &drop_ids, bool quiet = false,
	Destination destination = Destination::Inventory);
}

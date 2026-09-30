#pragma once
#include "common/advanced_loot_policy.h"
class Client;
class Corpse;
namespace NightcapLoot {
TransferResult TakeCoins(Corpse *corpse, Client *client, bool split, bool classic = false);
}

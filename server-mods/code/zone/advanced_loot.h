#pragma once
namespace NightcapLoot { enum class TransferResult; }
class Client;
class Corpse;
class Seperator;
struct LootItem;

namespace NightcapLoot {
// Zone-thread only. Clients opt into the wire protocol with #advloot refresh.
void Pulse(Client *client);
void Forget(Client *client);
void Forget(Corpse *corpse);
void Command(Client *client, const Seperator *arguments);
void SaveDistribution(Corpse *corpse);
bool PrepareClassic(Corpse *corpse, Client *client);
TransferResult TakeClassic(Corpse *corpse, Client *client, LootItem *item, bool auto_loot);
}

#pragma once
class Client;
class NPC;
class Zone;
namespace NightcapHunt {
void Load(Zone &zone);
void Award(NPC &npc, bool owned_before_death, bool &rolled);
bool CanDropAugment(NPC &npc, bool owned_before_death);
int OutputHeadroom(Client &client, bool healing);
int OutputShieldBlock(Client &client);
}

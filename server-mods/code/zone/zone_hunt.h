#pragma once
class Client;
class NPC;
class Zone;
namespace NightcapHunt {
void Load(Zone &zone);
void Award(NPC &npc, bool owned_before_death, bool &rolled);
int OutputHeadroom(Client &client, bool healing);
}

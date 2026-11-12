#pragma once
#include "common/repositories/titles_repository.h"
#include <string>
#include <vector>
class Client;
class NPC;
namespace NightcapTitles {
void RecordKill(NPC *npc, Client *credit, bool excluded);
void CheckSkill(Client *client, unsigned skill);
void AppendEligible(Client *client, const std::vector<TitlesRepository::Titles> &native, std::vector<TitlesRepository::Titles> &out);
std::string Name(unsigned id, bool suffix);
void Show(Client *client, unsigned page);
}

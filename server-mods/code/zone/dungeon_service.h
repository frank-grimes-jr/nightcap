#pragma once
#include "common/dungeon_policy.h"
#include "common/repositories/spawn2_repository.h"
#include "common/repositories/zone_state_spawns_repository.h"
#include <string>
#include <vector>
#include <unordered_map>
class Client;
class NPC;
class Mob;
class Corpse;
struct TaskInformation;

namespace NightcapDungeon {
using SavedSpawn = ZoneStateSpawnsRepository::ZoneStateSpawns;
// Called before loading any NPCs. Failure prevents a managed zone from booting.
bool Boot();
void Process();
bool Managed();
// Read-only identity for run-scoped quest state. Retained after expiry or
// suspension so quest callbacks cannot fall through to public-zone behavior.
std::string RunID();
float ExperienceModifier(float ordinary);
bool RaidNPC(Mob *npc);
bool SelectSpawn(uint32_t spawn, uint32_t &npc);
void PrivateSpawns(std::vector<Spawn2Repository::Spawn2> &spawns);
void RestoreTimers(std::unordered_map<uint32_t,uint32_t> &timers);
uint32_t RespawnDelay(uint32_t spawn);
bool RequiredSpawn(uint32_t spawn);
// Called after quest death veto, before death packets/respawn timers/XP.
bool PrepareLoot(NPC *npc, bool owned);
bool BeforeDeath(NPC *npc, Mob *killer, bool owned, Corpse *corpse);
bool Keeper(Client *client, NPC *keeper, const std::string &action);
void Connected(Client *client);
void Journal(Client *client);
// Native prison-break interaction and temporary instance-only faction policy.
bool HighkeepSay(Client *client, NPC *npc, const std::string &text);
int HighkeepFaction(Mob *subject, Mob *observer); // -1: ordinary faction policy
bool HighkeepProtected(Mob *attacker, Mob *target);
bool HighkeepNoFaction(Mob *npc);
bool HighkeepHealTarget(Mob *npc);
bool HighkeepTransient(Mob *npc);
// Adapt the installed v1 journal definitions for visible RoF2 objectives.
void ConfigureJournalTask(int task_id, TaskInformation &task);
bool LoadCheckpoint(std::vector<SavedSpawn> &spawns);
bool SaveCheckpoint(const std::vector<SavedSpawn> &spawns);
}

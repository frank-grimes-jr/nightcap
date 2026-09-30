#pragma once
#include <string>
#include <cstdint>
class Corpse;
class NPC;

namespace NightcapLoot {
enum class RestoreState { Legacy, Restored, Invalid };
std::string SaveCorpseState(Corpse *corpse, const std::string &legacy);
std::string SaveNPCDropIDs(NPC *npc, const std::string &legacy);
RestoreState RestoreCorpseItems(NPC *npc, const std::string &saved);
void StampRestoredDropIDs(NPC *npc, const std::string &saved, uint64_t state_id, int64_t created_at);
void RestoreCorpseState(Corpse *corpse, const std::string &saved);
}

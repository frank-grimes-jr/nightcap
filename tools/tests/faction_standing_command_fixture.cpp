#include "common/faction_standing.h"
#include <cassert>
#include <cstdarg>
#include <map>
#include <iostream>

using int32 = int32_t;
using uint32 = uint32_t;
namespace Chat { constexpr int White = 0; }
struct FactionMods { int base, min, max, class_mod, race_mod, deity_mod; };
struct Definition { std::string name; FactionMods mods; };
struct ContentDatabase {
	std::map<uint32, Definition> rows;
	uint32 GetMaxFaction() { return rows.empty() ? 0 : rows.rbegin()->first; }
	std::string GetFactionName(uint32 id) { return rows.count(id) ? rows.at(id).name : ""; }
	bool GetFactionData(FactionMods *mods, int cls, int race, int deity, uint32 id) {
		assert(cls == 3 && race == 6 && deity == 201);
		if (!rows.count(id)) { return false; }
		*mods = rows.at(id).mods; return true;
	}
} content_db;
struct Mob {
	bool npc = true; int faction = 0;
	bool IsNPC() { return npc; }
	int GetPrimaryFaction() { return faction; }
};
struct Client {
	std::map<int, int> earned;
	std::string popup, message;
	Mob *target = nullptr;
	int spell_bonus = 0, item_bonus = 0;
	int GetClass() { return 3; }
	int GetFactionRace() { return 6; }
	int GetDeity() { return 201; }
	int32 GetCharacterFactionLevel(int32 id) { return earned.count(id) ? earned.at(id) : 0; }
	int GetFactionBonus(int32) { return spell_bonus; }
	int GetItemFactionBonus(int32) { return item_bonus; }
	int32 GetModCharacterFactionLevel(int32 faction_id);
	Mob *GetTarget() { return target; }
	void Message(int color, const char *text, ...) { assert(color == Chat::White); message = text; }
	void SendPopupToClient(const char *title, const char *text) {
		assert(std::string(title) == "Faction Standings"); popup = text; assert(popup.size() < 4096);
	}
};
// ACTUAL_GET_MOD
// Standing thresholds remain the native CalculateFaction policy, not a second table.
int CalculateFaction(FactionMods *mods, int total) { assert(mods == nullptr); return total; }
std::string FactionValueToString(int total) { return "native-total-" + std::to_string(total); }
struct Seperator { const char *argplus[2]; };
#include "zone/faction_standing.inc"

void run(Client &client, const char *input) {
	client.popup.clear(); client.message.clear();
	Seperator sep{{"#factions", input}}; command_factions(&client, &sep);
}

int main()
{
	content_db.rows = {{1, {"Zeta", {100, -2000, 2000, 50, -100, 25}}},
		{3, {"Alpha & <dark>", {-3000, -2000, 2000, 0, 0, 0}}}};
	Client caller;
	caller.earned[1] = 200; caller.spell_bonus = 40; caller.item_bonus = 10;
	const auto before = caller.earned;
	run(caller, "");
	assert(caller.popup.find("Alpha &amp; &lt;dark&gt;") < caller.popup.find("Zeta"));
	assert(caller.popup.find("Standing: 325 (native-total-325)") != std::string::npos);
	assert(caller.popup.find("Range: -1975 to 2025") != std::string::npos);
	// A faction with no personal row still has its base standing; clamp earned bounds at zero.
	assert(caller.popup.find("Standing: -2950") != std::string::npos);
	assert(caller.popup.find("Range: -2950 to 2050") != std::string::npos);
	run(caller, "ZEta"); assert(caller.popup.find("Alpha") == std::string::npos);
	Mob npc{true, 1}; caller.target = &npc;
	run(caller, "target"); assert(caller.popup.find("Zeta") != std::string::npos);
	assert(caller.popup.find("Alpha") == std::string::npos);
	caller.spell_bonus = 0;
	run(caller, "target"); assert(caller.popup.find("Standing: 285") != std::string::npos);
	npc.npc = false;
	run(caller, "target"); assert(caller.popup.empty() && !caller.message.empty());
	npc.npc = true; npc.faction = -1;
	run(caller, "target"); assert(caller.popup.empty() && !caller.message.empty());
	caller.target = nullptr;
	run(caller, "target"); assert(caller.popup.empty() && !caller.message.empty());
	run(caller, "0"); assert(caller.popup.empty() && !caller.message.empty());
	run(caller, "' OR 1=1 --"); assert(caller.popup.find("No matching factions") != std::string::npos);
	assert(caller.earned == before);
	std::cout << "Actual faction command: caller isolation, modifiers, bounds, cache gaps and refresh passed\n";
}

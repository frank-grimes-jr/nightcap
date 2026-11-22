#pragma once
#include <windows.h>
#include <cstdint>
#include <cstdio>

namespace nightcap::target_details {
constexpr int LabelType = 10040;

// Read on the UI thread while RoF2 resolves this label. Never retain a spawn
// pointer or its text across selections, zoning or a UI reload.
struct Selection { unsigned level, class_id; };

inline Selection Read(uintptr_t base) {
    __try {
        const auto game = *reinterpret_cast<const BYTE* const*>(base + 0xA67CCC);
        if (!game || *reinterpret_cast<const int*>(game + 0x5C8) != 5) return {};
        const auto target = *reinterpret_cast<const BYTE* const*>(base + 0x9D2648);
        if (!target || target[0x125] != 1 || !target[0x160]) return {};
        return {target[0x250], target[0xEB8]};
    } __except (EXCEPTION_EXECUTE_HANDLER) { return {}; }
}

inline void Format(Selection npc, char (&text)[48]) {
    static constexpr const char* classes[] = {
        "", "Warrior", "Cleric", "Paladin", "Ranger", "Shadow Knight", "Druid",
        "Monk", "Bard", "Rogue", "Shaman", "Necromancer", "Wizard", "Magician",
        "Enchanter", "Beastlord", "Berserker", "Cairnwright"
    };
    text[0] = '\0';
    if (!npc.level) return;
    const char* name = "";
    if (npc.class_id < sizeof(classes) / sizeof(classes[0])) name = classes[npc.class_id];
    if (npc.class_id >= 20 && npc.class_id <= 35) {
        sprintf_s(text, "Lv %u %s Trainer", npc.level, classes[npc.class_id - 19]);
        return;
    }
    switch (npc.class_id) {
    case 40: name = "Banker"; break;
    case 41: case 59: case 61: case 67: case 68: case 70: name = "Merchant"; break;
    case 60: name = "Recruiter"; break;
    case 62: name = "Treasure"; break;
    case 63: case 64: name = "Tribute Master"; break;
    case 66: name = "Guild Banker"; break;
    case 69: name = "Fellowship Master"; break;
    case 71: name = "Mercenary Liaison"; break;
    }
    sprintf_s(text, "Lv %u%s%s", npc.level, *name ? " " : "", name);
}
} // namespace nightcap::target_details

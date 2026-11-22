#pragma once
#include <windows.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <iterator>
#include <string>

namespace nightcap::worn_comparison {
// RoF2 possession indices, including power source before ammo.
inline constexpr const char* SlotNames[] = {
    "Charm", "Left ear", "Head", "Face", "Right ear", "Neck", "Shoulders",
    "Arms", "Back", "Left wrist", "Right wrist", "Ranged", "Hands", "Primary",
    "Secondary", "Left ring", "Right ring", "Chest", "Legs", "Feet", "Waist",
    "Power source", "Ammo"
};

enum class Width { Dword, SignedByte, Byte };
struct Field { const char* label; unsigned offset; Width width = Width::Dword; unsigned element = 0; };
// May 2013 RoF2 ItemDefinition. Compare unconditional numeric item properties.
// Focus/proc, skill-specific and bane effects depend on additional identities.
inline constexpr Field Fields[] = {
    {"AC",0x138}, {"HP",0x130}, {"Mana",0x134}, {"Endurance",0x550},
    {"Damage",0x188}, {"Delay",0x182,Width::Byte}, {"Range",0x185,Width::Byte},
    {"Backstab damage",0x18c}, {"ATK",0x554}, {"Haste",0x564},
    {"STR",0x128,Width::SignedByte}, {"STA",0x129,Width::SignedByte},
    {"AGI",0x12a,Width::SignedByte}, {"DEX",0x12b,Width::SignedByte},
    {"CHA",0x12c,Width::SignedByte}, {"INT",0x12d,Width::SignedByte}, {"WIS",0x12e,Width::SignedByte},
    {"Heroic STR",0x194}, {"Heroic STA",0x1a8}, {"Heroic AGI",0x1a0},
    {"Heroic DEX",0x1a4}, {"Heroic CHA",0x1ac}, {"Heroic INT",0x198}, {"Heroic WIS",0x19c},
    {"Cold resist",0x122,Width::SignedByte}, {"Fire resist",0x123,Width::SignedByte},
    {"Magic resist",0x124,Width::SignedByte}, {"Disease resist",0x125,Width::SignedByte},
    {"Poison resist",0x126,Width::SignedByte}, {"Corruption resist",0x127,Width::SignedByte},
    {"Heroic MR",0x1b0}, {"Heroic FR",0x1b4}, {"Heroic CR",0x1b8},
    {"Heroic DR",0x1bc}, {"Heroic PR",0x1c0}, {"Heroic corruption resist",0x1c4},
    {"Spell damage",0x1cc}, {"Heal amount",0x1c8}, {"Clairvoyance",0x5a0},
    {"HP regen",0x558}, {"Mana regen",0x55c}, {"Endurance regen",0x560},
    {"Shielding",0x4f4}, {"Spell shielding",0x50c}, {"DoT shielding",0x4fc},
    {"Damage shield",0x568}, {"DS mitigation",0x190}, {"Stun resist",0x4f8},
    {"Strikethrough",0x500}, {"Avoidance",0x510}, {"Accuracy",0x514},
    {"Combat effects",0x4f0}, {"Purity",0x58c},
    {"Magic damage",0x184,Width::Byte,1}, {"Fire damage",0x184,Width::Byte,2},
    {"Cold damage",0x184,Width::Byte,3}, {"Poison damage",0x184,Width::Byte,4},
    {"Disease damage",0x184,Width::Byte,5}, {"Chromatic damage",0x184,Width::Byte,6},
    {"Prismatic damage",0x184,Width::Byte,7}, {"Physical damage",0x184,Width::Byte,8},
    {"Corruption damage",0x184,Width::Byte,9}
};

struct Item {
    char name[64]{};
    std::array<int64_t, std::size(Fields)> stats{};
};
struct Slot { bool eligible = false; Item worn; };
struct Comparison { Item candidate; std::array<Slot, std::size(SlotNames)> slots; };

inline void AddDefinition(Item& result, const BYTE* def) {
    for (size_t i = 0; i < std::size(Fields); ++i) {
        const auto& field = Fields[i];
        if (field.element && field.element != def[0x183]) continue;
        const BYTE* at = def + field.offset;
        switch (field.width) {
        case Width::Dword: result.stats[i] += *reinterpret_cast<const int32_t*>(at); break;
        case Width::SignedByte: result.stats[i] += *reinterpret_cast<const int8_t*>(at); break;
        case Width::Byte: result.stats[i] += *at; break;
        }
    }
}

inline const BYTE* Definition(void* item) {
    using Get = const BYTE* (__thiscall*)(void*);
    return reinterpret_cast<Get>((*static_cast<void***>(item))[2])(item);
}

// Borrow from the item container only during this synchronous inspection. The
// native container accessor uses array +8, logical length +12, four-byte entries.
inline void** Entries(const BYTE* container) { return *reinterpret_cast<void** const*>(container + 8); }
inline int Count(const BYTE* container) { return *reinterpret_cast<const int*>(container + 12); }

inline bool ReadItem(Item& result, void* item, const BYTE* def) {
    if (!def || !def[0] || !memchr(def, 0, sizeof(result.name))) return false;
    memcpy(result.name, def, sizeof(result.name));
    AddDefinition(result, def);
    const BYTE* sockets = static_cast<const BYTE*>(item) + 0xa0;
    const int count = Count(sockets);
    if (count < 0 || count > 6 || (count && !Entries(sockets))) return false;
    for (int i = 0; i < count; ++i) {
        void* augment = Entries(sockets)[i];
        if (!augment) continue;
        const BYTE* aug = Definition(augment);
        if (!aug || aug[0x1d4] != 54) return false;
        AddDefinition(result, aug);
    }
    return true;
}

// POD-only native boundary. Discard the whole result on unavailable inventory,
// including faults partway through reading the second ring. Never move an item.
inline bool Read(uintptr_t base, void* window, Comparison& result) {
    __try {
        if (!base || !window) return false;
        const auto game = *reinterpret_cast<const BYTE* const*>(base + 0xa67ccc);
        if (!game || *reinterpret_cast<const int*>(game + 0x5c8) != 5) return false;
        auto character = *reinterpret_cast<BYTE**>(base + 0x9d261c);
        auto ref = reinterpret_cast<void**>(static_cast<BYTE*>(window) + 0x2b0);
        if (!character || !*ref) return false;
        const BYTE* def = Definition(*ref);
        if (!def || def[0x11a] != 0 || def[0x1d4] == 54) return false;
        using Profile = const BYTE* (__thiscall*)(void*);
        const auto vb = *reinterpret_cast<const int32_t**>(character + 8);
        if (!vb) return false;
        const auto profile = reinterpret_cast<Profile>(base + kSpellMenuProfileRva)(character + vb[1] + 12);
        if (!profile) return false;
        const auto inventory = profile + 0x18;
        const auto size = *reinterpret_cast<const uint32_t*>(inventory);
        const int stored = Count(inventory);
        if (size < std::size(SlotNames) || stored < 0 || static_cast<unsigned>(stored) > size ||
            (stored && !Entries(inventory))) return false;

        using Eligible = BYTE (__thiscall*)(void*, const void*, int, bool, bool);
        const auto can_equip = reinterpret_cast<Eligible>(base + 0x183550);
        bool found = false;
        for (int i = 0; i < static_cast<int>(std::size(SlotNames)); ++i) {
            if (!can_equip(character, ref, i, false, true)) continue;
            if (!found && !ReadItem(result.candidate, *ref, def)) return false;
            found = true;
            auto& slot = result.slots[i];
            slot.eligible = true;
            // As in the stock container accessor, unallocated trailing slots are empty.
            void* worn = i < stored ? Entries(inventory)[i] : nullptr;
            if (worn && !ReadItem(slot.worn, worn, Definition(worn))) return false;
        }
        return found;
    } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
}

inline void AppendName(std::string& text, const char* name) {
    for (; *name; ++name) {
        switch (*name) {
        case '&': text += "&amp;"; break;
        case '<': text += "&lt;"; break;
        case '>': text += "&gt;"; break;
        default: text += *name;
        }
    }
}

inline std::string Render(const Comparison& comparison) {
    std::string text = "<BR><c \"#00FFFF\">Worn item comparison</c><BR>"
        "Inspected minus worn. Listed stats include socketed augments, before level scaling and caps.<BR>";
    for (size_t i = 0; i < comparison.slots.size(); ++i) {
        const auto& slot = comparison.slots[i];
        if (!slot.eligible) continue;
        text += SlotNames[i];
        text += ": ";
        AppendName(text, slot.worn.name[0] ? slot.worn.name : "Empty");
        text += "<BR>";
        bool changed = false;
        for (size_t j = 0; j < std::size(Fields); ++j) {
            const auto delta = comparison.candidate.stats[j] - slot.worn.stats[j];
            if (!delta) continue;
            if (changed) text += ", ";
            text += Fields[j].label;
            text += delta > 0 ? " +" : " ";
            text += std::to_string(delta);
            changed = true;
        }
        if (!changed) text += "Same listed stats";
        text += "<BR>";
    }
    return text;
}
} // namespace nightcap::worn_comparison

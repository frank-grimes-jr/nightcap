#pragma once
#include <cstring>
#include <cstddef>

namespace nightcap {
namespace models {
// The opt-in is deliberately separate from stock RoF2 preferences: copied
// eqclient.ini files commonly already have every UseLuclin option enabled.
inline bool ModernOptIn(const char* value) {
    return value && (!_stricmp(value, "TRUE") || !strcmp(value, "1"));
}

inline const char* ClassicSetting(const char* section, const char* key, const char* file) {
    if (!section || !key || !file || _stricmp(section, "Defaults")) return nullptr;
    const char* name = file;
    for (const char* p = file; *p; ++p) if (*p == '/' || *p == '\\') name = p + 1;
    if (_stricmp(name, "eqclient.ini")) return nullptr;
    if (!_stricmp(key, "AllLuclinPcModelsOff")) return "TRUE";
    if (!_stricmp(key, "UseLuclinElementals") || !_stricmp(key, "LoadVeliousArmorsWithLuclin")) return "FALSE";
    static const char* const races[] = {
        "Human", "Barbarian", "Erudite", "WoodElf", "HighElf", "DarkElf",
        "HalfElf", "Dwarf", "Troll", "Ogre", "Halfling", "Gnome", "Iksar", "VahShir"
    };
    if (_strnicmp(key, "UseLuclin", 9)) return nullptr;
    const char* race = key + 9;
    for (const char* known : races) {
        const size_t length = strlen(known);
        if (!_strnicmp(race, known, length) &&
            (!_stricmp(race + length, "Male") || !_stricmp(race + length, "Female"))) return "FALSE";
    }
    return nullptr;
}

// Same truncation/count contract as RoF2's native profile-string reader.
inline unsigned CopySetting(const char* value, char* output, unsigned capacity) {
    if (!output || !capacity) return 0;
    size_t length = strlen(value);
    if (length >= capacity) length = capacity - 1;
    memcpy(output, value, length);
    output[length] = 0;
    return static_cast<unsigned>(length);
}
}
}

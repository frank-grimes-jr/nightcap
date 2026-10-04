#pragma once
#include "model_policy.h"
#include "model_catalog.h"

namespace nightcap { namespace models {
// Exact pinned x86 signatures; entry trampolines steal only complete,
// position-independent instructions. Native race/combat data is unchanged.
using ProfileString = unsigned (__cdecl *)(const char*, const char*, const char*, char*, unsigned, const char*);
using RegisterActor = int (__thiscall *)(void*, int, int, const char*, int, int);
using ActorTag = void (__thiscall *)(void*, char*, int, int);
using LoadImports = void (__thiscall *)(void*, const char*);
static ProfileString original_profile = nullptr;
static RegisterActor original_register = nullptr;
static ActorTag original_tag = nullptr;
static LoadImports original_imports = nullptr;
using AnimationSource = bool (__thiscall *)(void*, const char*, char*, bool);
static AnimationSource original_animation = nullptr;
static bool modern = false;
inline bool __fastcall AnimationHook(void* self, void*, const char* code, char* output, bool variant) {
    // The native resolver recognizes original model codes, not our aliases.
    // Resolve the underlying skeleton (ELE for every typed elemental clone),
    // retain the native return flag, and name any imported parent consistently.
    const Registration* actor = nullptr;
    if (!modern && code) for (const auto& entry : kRegistrations)
        if (!_stricmp(code, entry.alias)) { actor = &entry; break; }
    if (!actor) return original_animation(self, code, output, variant);
    const bool shared = original_animation(self, actor->skeleton, output, variant);
    if (!_stricmp(output, actor->skeleton)) {
        memcpy(output, actor->alias, 4);
    } else {
        for (const auto& parent : kRegistrations)
            if (!_stricmp(output, parent.skeleton)) {
                memcpy(output, parent.alias, 4);
                break;
            }
    }
    return shared;
}

inline const Registration* Registered(int race, int gender) {
    for (const auto& entry : kRegistrations)
        if (entry.race == race && entry.gender == gender) return &entry;
    return nullptr;
}
inline void ClassicRace(int& race, int& gender) {
    for (const auto& entry : kRemakes)
        if (entry.race == race) {
            race = entry.original;
            if (entry.gender >= 0) gender = entry.gender;
            break;
        }
    // Later humanoid NPC remakes can use the native classic PC actor registry.
    // Keep those actor codes intact for armor and weapon appearance handling.
    if (ClassicPlayerRace(race)) {
        gender = gender == 1 ? 1 : 0;
        return;
    }
    if (Registered(race, gender)) return;
    // Several old NPCs have only a neutral model, even when the newer model
    // has male/female variants. Never request an unavailable original gender.
    if (Registered(race, 2)) { gender = 2; return; }
    for (const auto& entry : kRegistrations)
        if (entry.race == race) { gender = entry.gender; return; }
}
inline unsigned __cdecl ProfileHook(const char* section, const char* key, const char* fallback,
                                    char* output, unsigned capacity, const char* file) {
    const auto value = modern ? nullptr : ClassicSetting(section, key, file);
    return value ? CopySetting(value, output, capacity) : original_profile(section, key, fallback, output, capacity, file);
}
inline int __fastcall RegisterHook(void* self, void*, int race, int gender, const char* code, int a, int b) {
    const auto entry = modern ? nullptr : Registered(race, gender);
    // Register the alias in the native table so reverse model lookups remain
    // valid as well. Later remakes resolve to this original registration.
    if (entry && code && !_stricmp(code, entry->original)) code = entry->alias;
    return original_register(self, race, gender, code, a, b);
}
inline void __fastcall TagHook(void* self, void*, char* output, int race, int gender) {
    if (!modern) ClassicRace(race, gender);
    original_tag(self, output, race, gender);
}
inline void __fastcall ImportsHook(void* self, void*, const char* filename) {
    original_imports(self, modern ? filename : "nightcap_models_chr.txt");
}
inline bool Install(uintptr_t base) {
    original_profile = reinterpret_cast<ProfileString>(client_ui::EntryHook(base+kModelProfileRva,
        kExpectedModelProfile, reinterpret_cast<void*>(&ProfileHook)));
    if (!original_profile) return false;
    original_register = reinterpret_cast<RegisterActor>(client_ui::EntryHook(base+kModelRegisterRva,
        kExpectedModelRegister, reinterpret_cast<void*>(&RegisterHook)));
    if (!original_register) return false;
    original_tag = reinterpret_cast<ActorTag>(client_ui::EntryHook(base+kModelTagRva,
        kExpectedModelTag, reinterpret_cast<void*>(&TagHook)));
    if (!original_tag) return false;
    original_animation = reinterpret_cast<AnimationSource>(client_ui::EntryHook(base+kModelAnimationRva,
        kExpectedModelAnimation, reinterpret_cast<void*>(&AnimationHook)));
    if (!original_animation) return false;
    original_imports = reinterpret_cast<LoadImports>(base+kModelImportsTargetRva);
    return true;
}
}}

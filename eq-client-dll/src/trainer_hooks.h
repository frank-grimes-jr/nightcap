#pragma once

namespace nightcap { namespace client_ui {
// Narrow trainer-only call sites. Native pricing, points, range, faction and
// server-supplied caps remain in the original caller; the server authorizes buys.
using TrainerSkillCap = int (__thiscall *)(void*, void*, int, int, int, int, int, int);
using TrainerSkillLevel = int (__thiscall *)(void*, int, int);
static TrainerSkillCap trainer_skill_cap = nullptr;
static TrainerSkillLevel trainer_skill_level = nullptr;

inline unsigned __cdecl TrainerClassForProfile(void* profile, unsigned npc_class) {
    unsigned primary = 0;
    __try { primary = *reinterpret_cast<BYTE*>(static_cast<BYTE*>(profile)+0x3374); }
    __except(EXCEPTION_EXECUTE_HANDLER) { return 0; }
    if (!CurrentIdentity()) { RequestRefresh(); return primary; }
    if (primary != state.PrimaryClass() || npc_class < 20 || npc_class > 35) return primary;
    const unsigned trained = npc_class-19;
    return (state.ClassMask() & (1u << (trained-1))) ? trained : primary;
}

// Replaces only movzx EAX,byte ptr [EAX+3374]. The next native instruction
// consumes CL, so preserve the entire ECX/EDX pair and the caller's stack.
__declspec(naked) inline void TrainerClassBridge() {
    __asm {
        push ecx
        push edx
        movzx edx, cl
        push edx
        push eax
        call TrainerClassForProfile
        add esp, 8
        pop edx
        pop ecx
        ret
    }
}

inline int __fastcall TrainerSkillCapHook(void* manager, void*, void* character,
    int level, int queried_class, int skill, int flag_a, int flag_b, int flag_c) {
    int best = trainer_skill_cap(manager, character, level, queried_class, skill, flag_a, flag_b, flag_c);
    if (!CurrentIdentity()) { RequestRefresh(); return best; }
    if (queried_class != static_cast<int>(state.PrimaryClass())) return best;
    const auto mask = state.ClassMask();
    for (int cls=1; cls<=16; ++cls) {
        if (cls == queried_class || !(mask & (1u << (cls-1)))) continue;
        const int cap = trainer_skill_cap(manager, character, level, cls, skill, flag_a, flag_b, flag_c);
        if (cap > best) best = cap;
    }
    return best;
}

inline int __fastcall TrainerSkillLevelHook(void* manager, void*, int skill, int queried_class) {
    int best = trainer_skill_level(manager, skill, queried_class);
    if (!CurrentIdentity()) { RequestRefresh(); return best; }
    if (queried_class != static_cast<int>(state.PrimaryClass())) return best;
    const auto mask = state.ClassMask();
    for (int cls=1; cls<=16; ++cls) {
        if (cls == queried_class || !(mask & (1u << (cls-1)))) continue;
        const int level = trainer_skill_level(manager, skill, cls);
        if (level > 0 && (best <= 0 || level < best)) best = level;
    }
    return best;
}

template<size_t N> inline bool TrainerCall(uintptr_t rva, const BYTE (&expected)[N], void* hook) {
    static_assert(N == 5, "native trainer call must be rel32");
    BYTE replacement[N] = {0xE8};
    const int32_t delta = static_cast<int32_t>(reinterpret_cast<uintptr_t>(hook)-(base+rva+5));
    memcpy(replacement+1, &delta, sizeof(delta));
    return WriteVerifiedPatch(reinterpret_cast<BYTE*>(base+rva), expected, replacement, N);
}

inline bool InstallTrainer() {
    // Guard all call sites before making any change. The required class_ui
    // feature aborts startup if any subsequent verified write fails.
    __try {
        if (memcmp(reinterpret_cast<void*>(base+kTrainerClassRva), kExpectedTrainerClass, sizeof(kExpectedTrainerClass)) ||
            memcmp(reinterpret_cast<void*>(base+kTrainerCapRva), kExpectedTrainerCap, sizeof(kExpectedTrainerCap)) ||
            memcmp(reinterpret_cast<void*>(base+kTrainerLevelRva), kExpectedTrainerLevel, sizeof(kExpectedTrainerLevel)) ||
            memcmp(reinterpret_cast<void*>(base+kTrainerBuyCapRva), kExpectedTrainerBuyCap, sizeof(kExpectedTrainerBuyCap)) ||
            memcmp(reinterpret_cast<void*>(base+kTrainerBuyLevelRva), kExpectedTrainerBuyLevel, sizeof(kExpectedTrainerBuyLevel)) ||
            memcmp(reinterpret_cast<void*>(base+kTrainerButtonLevelRva), kExpectedTrainerButtonLevel, sizeof(kExpectedTrainerButtonLevel)) ||
            memcmp(reinterpret_cast<void*>(base+kTrainerDisplayCapRva), kExpectedTrainerDisplayCap, sizeof(kExpectedTrainerDisplayCap)) ||
            memcmp(reinterpret_cast<void*>(base+kTrainerDisplayCap2Rva), kExpectedTrainerDisplayCap2, sizeof(kExpectedTrainerDisplayCap2)) ||
            memcmp(reinterpret_cast<void*>(base+kTrainerDisplayLevelRva), kExpectedTrainerDisplayLevel, sizeof(kExpectedTrainerDisplayLevel)) ||
            memcmp(reinterpret_cast<void*>(base+kTrainerDisplayLevel2Rva), kExpectedTrainerDisplayLevel2, sizeof(kExpectedTrainerDisplayLevel2)) ||
            memcmp(reinterpret_cast<void*>(base+kTrainerListLevelRva), kExpectedTrainerListLevel, sizeof(kExpectedTrainerListLevel))) return false;
    } __except(EXCEPTION_EXECUTE_HANDLER) { return false; }
    trainer_skill_cap = reinterpret_cast<TrainerSkillCap>(base+kTrainerCapRva);
    trainer_skill_level = reinterpret_cast<TrainerSkillLevel>(base+kTrainerLevelRva);
    BYTE expected[7]; memcpy(expected, kExpectedTrainerClass, sizeof(expected));
    BYTE replacement[7] = {0xE8,0,0,0,0,0x90,0x90};
    const int32_t delta = static_cast<int32_t>(reinterpret_cast<uintptr_t>(&TrainerClassBridge)-(base+kTrainerClassRva+5));
    memcpy(replacement+1, &delta, sizeof(delta));
    return WriteVerifiedPatch(reinterpret_cast<BYTE*>(base+kTrainerClassRva), expected, replacement, sizeof(replacement)) &&
        TrainerCall(kTrainerBuyCapRva, kExpectedTrainerBuyCap, reinterpret_cast<void*>(&TrainerSkillCapHook)) &&
        TrainerCall(kTrainerDisplayCapRva, kExpectedTrainerDisplayCap, reinterpret_cast<void*>(&TrainerSkillCapHook)) &&
        TrainerCall(kTrainerDisplayCap2Rva, kExpectedTrainerDisplayCap2, reinterpret_cast<void*>(&TrainerSkillCapHook)) &&
        TrainerCall(kTrainerBuyLevelRva, kExpectedTrainerBuyLevel, reinterpret_cast<void*>(&TrainerSkillLevelHook)) &&
        TrainerCall(kTrainerButtonLevelRva, kExpectedTrainerButtonLevel, reinterpret_cast<void*>(&TrainerSkillLevelHook)) &&
        TrainerCall(kTrainerDisplayLevelRva, kExpectedTrainerDisplayLevel, reinterpret_cast<void*>(&TrainerSkillLevelHook)) &&
        TrainerCall(kTrainerDisplayLevel2Rva, kExpectedTrainerDisplayLevel2, reinterpret_cast<void*>(&TrainerSkillLevelHook)) &&
        TrainerCall(kTrainerListLevelRva, kExpectedTrainerListLevel, reinterpret_cast<void*>(&TrainerSkillLevelHook));
}
}}

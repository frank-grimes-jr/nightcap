// =============================================================================
// Nightcap dinput8.dll proxy — B2 caster-chassis correction (issue #12, ADR 0004)
//
// RoF2 auto-loads dinput8.dll from its own folder at startup. This proxy
// forwards every DirectInput export to the real system DLL and starts one
// init thread that applies tightly guarded caster-class and server-mana
// corrections.
// The MQ2 offset survey remains temporarily available for validation. Removing
// the DLL from the client folder restores stock behavior.
//
// Build: x86 ONLY (RoF2 is a 32-bit client) — see build.bat.
// =============================================================================

#include <windows.h>
#include <bcrypt.h>
#include <tlhelp32.h>
#include <cstdarg>
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <share.h>

#pragma comment(lib, "bcrypt.lib")

// --- expected client build and B2 caster-class table --------------------------
// eqgame.exe, RoF2 May 10 2013 emu package, 8,774,656 bytes
// sha256 2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e
static const DWORD kExpectedEqgameSize = 8774656;
static const BYTE kExpectedEqgameSha256[32] = {
    0x2A, 0x87, 0x02, 0xAD, 0x9F, 0x72, 0x27, 0x04,
    0xF0, 0x13, 0x55, 0xC0, 0x75, 0x0B, 0xE7, 0xD6,
    0xF1, 0x64, 0xA8, 0xB9, 0xC9, 0x12, 0x8B, 0xA0,
    0xCF, 0x28, 0x6E, 0xA3, 0x2B, 0x40, 0x5B, 0x0E,
};

// The stock predicate indexes this table by BaseProfile.Class - 1. Its only
// zero entries are the four no-mana classes. Enabling those four entries makes
// every base class caster-capable in the client chassis while the server remains
// authoritative for whether a character actually has mana or usable spells.
static const uintptr_t kCasterClassTableRva = 0x00043F90;
static const BYTE kExpectedCasterClassTable[16] = {
    0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0,
};
static const BYTE kEnabledCasterClassTable[16] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};
static const size_t kNonCasterClassIndexes[] = { 0, 6, 8, 15 };

// CCombatAbilityWnd::CanShow indexes this table by BaseProfile.Class - 1.
// Stock RoF2 disables the window for its seven pure-caster classes. Enable the
// presentation chassis for every base class; the server remains authoritative
// for learned skills and every submitted combat ability.
static const uintptr_t kCombatAbilityClassTableRva = 0x0018238C;
static const BYTE kExpectedCombatAbilityClassTable[16] = {
    0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0,
};
static const BYTE kEnabledCombatAbilityClassTable[16] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

// CSkillsSelectWnd::SetTypesToDisplay checks CharacterZoneClient::HasSkill
// before adding an activated skill to the Actions -> Abilities picker.
// HasSkill clamps the received value through the primary class's cap, hiding
// valid secondary/tertiary skills. Redirect only the two selector calls to a
// predicate that preserves stock success and otherwise accepts a positive
// server-delivered base skill.
static const uintptr_t kActionsSkillPredicateCallRvas[] = {
    0x00356D2D,
    0x00356DA5,
};
static const BYTE kExpectedActionsSkillPredicateCalls[][5] = {
    { 0xE8, 0x7E, 0x34, 0xCF, 0xFF },
    { 0xE8, 0x06, 0x34, 0xCF, 0xFF },
};
static const uintptr_t kCharacterHasSkillRva = 0x0004A1B0;
static const uintptr_t kCharacterGetBaseSkillRva = 0x00049C80;
static const uintptr_t kSkillManagerSlotRva = 0x00A64610;
static const uintptr_t kSkillIsCombatRva = 0x001BAB10;
static const uintptr_t kSkillIsActivatedRva = 0x001BABD0;

// RoF2's non-caster EQ_Character::Max_Mana branch returns zero even after the
// server has populated LocalPlayer's authoritative raw maximum at +0x354.
// Redirect only that complete six-byte return block to the guarded stub below.
static const uintptr_t kLocalPlayerSlotRva = 0x009D2630;
static const uintptr_t kMaxManaNonCasterReturnRva = 0x00181E96;
// CPlayerWnd refreshes PlayerMana every 500 ms using a second, stock
// base-class predicate. Redirect only that predicate call so the stock HUD
// owns visibility continuously and bases it on the server-cached maximum.
static const uintptr_t kPlayerManaPredicateCallRva = 0x00318E93;
static const BYTE kExpectedPlayerManaPredicateCall[5] = {
    0xE8, 0xF8, 0x6C, 0xE8, 0xFF, // call 0x0059FB90
};
static const BYTE kExpectedMaxManaReturn[6] = {
    0x33, 0xC0,             // xor eax,eax
    0x5E,                   // pop esi
    0xC2, 0x04, 0x00,       // ret 4
};

static HMODULE g_real_dinput8 = nullptr;
static FILE*   g_log          = nullptr;
static uintptr_t g_local_player_slot = 0;
static uintptr_t g_eq_base = 0;

static void Log(const char* fmt, ...)
{
    if (!g_log) return;
    SYSTEMTIME st;
    GetLocalTime(&st);
    fprintf(g_log, "[%02d:%02d:%02d.%03d] ", st.wHour, st.wMinute, st.wSecond, st.wMilliseconds);
    va_list args;
    va_start(args, fmt);
    vfprintf(g_log, fmt, args);
    va_end(args);
    fprintf(g_log, "\n");
    fflush(g_log);
}

static bool VerifyEqgameSha256(const char* path)
{
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    BCRYPT_HASH_HANDLE hash = nullptr;
    HANDLE file = INVALID_HANDLE_VALUE;
    BYTE* hash_object = nullptr;
    BYTE digest[32] = {};
    BYTE buffer[64 * 1024];
    DWORD hash_object_size = 0;
    DWORD property_size = 0;
    DWORD bytes_read = 0;
    bool read_ok = true;
    bool matched = false;

    NTSTATUS status = BCryptOpenAlgorithmProvider(
        &algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0);
    if (status < 0) goto cleanup;

    status = BCryptGetProperty(
        algorithm, BCRYPT_OBJECT_LENGTH,
        reinterpret_cast<PUCHAR>(&hash_object_size),
        sizeof(hash_object_size), &property_size, 0);
    if (status < 0 || hash_object_size == 0) goto cleanup;

    hash_object = static_cast<BYTE*>(
        HeapAlloc(GetProcessHeap(), 0, hash_object_size));
    if (!hash_object) goto cleanup;

    status = BCryptCreateHash(
        algorithm, &hash, hash_object, hash_object_size, nullptr, 0, 0);
    if (status < 0) goto cleanup;

    file = CreateFileA(
        path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) goto cleanup;

    do {
        bytes_read = 0;
        if (!ReadFile(file, buffer, sizeof(buffer), &bytes_read, nullptr)) {
            read_ok = false;
            break;
        }
        if (bytes_read != 0) {
            status = BCryptHashData(hash, buffer, bytes_read, 0);
            if (status < 0) {
                read_ok = false;
                break;
            }
        }
    } while (bytes_read != 0);

    if (!read_ok) goto cleanup;
    status = BCryptFinishHash(hash, digest, sizeof(digest), 0);
    if (status < 0) goto cleanup;
    matched = (memcmp(digest, kExpectedEqgameSha256, sizeof(digest)) == 0);

cleanup:
    if (file != INVALID_HANDLE_VALUE) CloseHandle(file);
    if (hash) BCryptDestroyHash(hash);
    if (hash_object) HeapFree(GetProcessHeap(), 0, hash_object);
    if (algorithm) BCryptCloseAlgorithmProvider(algorithm, 0);
    return matched;
}

// Match the stock no-argument thiscall predicate used by CPlayerWnd. The
// player argument proves the HUD has a live subject; pinstLocalPlayer remains
// the authoritative object because the RoF2 OP_ManaUpdate handler writes the
// server maximum to its +0x354 field.
extern "C" __declspec(noinline) BYTE __fastcall HasServerManaForGauge(
    void* player, void* unused_edx)
{
    (void)unused_edx;
    if (!player || g_local_player_slot == 0) {
        return 0;
    }

    __try {
        BYTE* local_player = *reinterpret_cast<BYTE**>(g_local_player_slot);
        if (!local_player) {
            return 0;
        }
        return *reinterpret_cast<DWORD*>(local_player + 0x354) > 0 ? 1 : 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
}

extern "C" __declspec(noinline) BYTE __fastcall HasServerGrantedSkill(
    void* character, void* unused_edx, int skill)
{
    (void)unused_edx;
    if (!character || g_eq_base == 0 || skill < 0 || skill >= 100) {
        return 0;
    }

    typedef BYTE (__thiscall *HasSkillFn)(void*, int);
    // This exact RoF2 entrypoint has one meaningful skill argument but returns
    // with `ret 8`; preserve its second, unused stack slot to match the ABI.
    typedef int (__thiscall *GetBaseSkillFn)(void*, int, int);
    HasSkillFn stock_has_skill = reinterpret_cast<HasSkillFn>(
        g_eq_base + kCharacterHasSkillRva);
    GetBaseSkillFn get_base_skill = reinterpret_cast<GetBaseSkillFn>(
        g_eq_base + kCharacterGetBaseSkillRva);

    __try {
        const BYTE stock = stock_has_skill(character, skill);
        const int base = get_base_skill(character, skill, 0);
        const BYTE accepted = (stock || base > 0) ? 1 : 0;

        if (skill == 21 || skill == 23 || skill == 26 || skill == 30 ||
            skill == 32 || skill == 38 || skill == 52) {
            typedef BYTE (__thiscall *SkillFlagFn)(void*, int);
            BYTE activated = 0xFF;
            BYTE combat = 0xFF;
            void* skill_manager =
                *reinterpret_cast<void**>(g_eq_base + kSkillManagerSlotRva);
            if (skill_manager) {
                SkillFlagFn is_activated = reinterpret_cast<SkillFlagFn>(
                    g_eq_base + kSkillIsActivatedRva);
                SkillFlagFn is_combat = reinterpret_cast<SkillFlagFn>(
                    g_eq_base + kSkillIsCombatRva);
                activated = is_activated(skill_manager, skill);
                combat = is_combat(skill_manager, skill);
            }
            Log("G006_SELECTOR skill=%d stock=%u base=%u accepted=%u "
                "activated=%u combat=%u",
                skill, static_cast<unsigned>(stock),
                static_cast<unsigned>(base),
                static_cast<unsigned>(accepted),
                static_cast<unsigned>(activated),
                static_cast<unsigned>(combat));
        }

        return accepted;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        if (skill == 21 || skill == 23 || skill == 26 || skill == 30 ||
            skill == 32 || skill == 38 || skill == 52) {
            Log("G006_SELECTOR skill=%d exception=1", skill);
        }
        return 0;
    }
}

// Entered only from EQ_Character::Max_Mana's stock non-caster return block.
// Preserve the exact stock epilogue after returning the server-cached maximum.
extern "C" __declspec(naked) void MaxManaFromServerCache()
{
    __asm {
        mov eax, dword ptr [g_local_player_slot]
        test eax, eax
        jz no_server_value
        mov eax, dword ptr [eax]
        test eax, eax
        jz no_server_value
        mov eax, dword ptr [eax + 354h]
        jmp max_mana_return

    no_server_value:
        xor eax, eax

    max_mana_return:
        pop esi
        ret 4
    }
}

static bool ApplyMaxManaServerCacheHook(uintptr_t eq_base, bool version_ok)
{
    if (!version_ok) {
        Log("B2 mana hook DISABLED: client version guard failed");
        return false;
    }

    BYTE* site = reinterpret_cast<BYTE*>(eq_base + kMaxManaNonCasterReturnRva);
    BYTE replacement[sizeof(kExpectedMaxManaReturn)] = { 0xE9, 0, 0, 0, 0, 0x90 };
    const intptr_t relative =
        reinterpret_cast<uintptr_t>(&MaxManaFromServerCache) -
        (reinterpret_cast<uintptr_t>(site) + 5);
    const int32_t relative32 = static_cast<int32_t>(relative);
    if (static_cast<intptr_t>(relative32) != relative) {
        Log("B2 mana hook DISABLED: detour target is outside rel32 range");
        return false;
    }
    memcpy(replacement + 1, &relative32, sizeof(relative32));

    bool stock_signature = false;
    bool already_applied = false;
    __try {
        stock_signature =
            (memcmp(site, kExpectedMaxManaReturn, sizeof(kExpectedMaxManaReturn)) == 0);
        already_applied = (memcmp(site, replacement, sizeof(replacement)) == 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        Log("B2 mana hook DISABLED: Max_Mana site unreadable at rva=0x%08X",
            static_cast<unsigned>(kMaxManaNonCasterReturnRva));
        return false;
    }

    if (already_applied) {
        g_local_player_slot = eq_base + kLocalPlayerSlotRva;
        Log("B2 mana hook already active");
        return true;
    }
    if (!stock_signature) {
        Log("B2 mana hook DISABLED: Max_Mana signature mismatch at rva=0x%08X",
            static_cast<unsigned>(kMaxManaNonCasterReturnRva));
        return false;
    }

    g_local_player_slot = eq_base + kLocalPlayerSlotRva;
    DWORD old_protection = 0;
    if (!VirtualProtect(site, sizeof(replacement), PAGE_EXECUTE_READWRITE, &old_protection)) {
        g_local_player_slot = 0;
        Log("B2 mana hook FAILED: VirtualProtect");
        return false;
    }

    bool wrote = false;
    __try {
        memcpy(site, replacement, sizeof(replacement));
        FlushInstructionCache(GetCurrentProcess(), site, sizeof(replacement));
        wrote = (memcmp(site, replacement, sizeof(replacement)) == 0);
        if (!wrote) {
            memcpy(site, kExpectedMaxManaReturn, sizeof(kExpectedMaxManaReturn));
            FlushInstructionCache(GetCurrentProcess(), site, sizeof(kExpectedMaxManaReturn));
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        memcpy(site, kExpectedMaxManaReturn, sizeof(kExpectedMaxManaReturn));
        FlushInstructionCache(GetCurrentProcess(), site, sizeof(kExpectedMaxManaReturn));
        wrote = false;
    }

    DWORD ignored = 0;
    VirtualProtect(site, sizeof(replacement), old_protection, &ignored);
    if (!wrote) {
        g_local_player_slot = 0;
        Log("B2 mana hook FAILED: write did not verify; rolled back");
        return false;
    }

    Log("B2 mana hook APPLIED: non-caster Max_Mana returns the OP_ManaUpdate "
        "self maximum (site rva=0x%08X, LocalPlayer+0x354)",
        static_cast<unsigned>(kMaxManaNonCasterReturnRva));
    return true;
}

static bool ApplyPlayerManaGaugePredicateHook(uintptr_t eq_base, bool mana_hook_ok)
{
    if (!mana_hook_ok) {
        Log("B2 mana gauge DISABLED: authoritative mana hook unavailable");
        return false;
    }

    BYTE* site = reinterpret_cast<BYTE*>(eq_base + kPlayerManaPredicateCallRva);
    BYTE replacement[sizeof(kExpectedPlayerManaPredicateCall)] = { 0xE8, 0, 0, 0, 0 };
    const intptr_t relative =
        reinterpret_cast<uintptr_t>(&HasServerManaForGauge) -
        (reinterpret_cast<uintptr_t>(site) + sizeof(replacement));
    const int32_t relative32 = static_cast<int32_t>(relative);
    if (static_cast<intptr_t>(relative32) != relative) {
        Log("B2 mana gauge DISABLED: predicate target is outside rel32 range");
        return false;
    }
    memcpy(replacement + 1, &relative32, sizeof(relative32));

    bool stock_signature = false;
    bool already_applied = false;
    __try {
        stock_signature = (memcmp(
            site, kExpectedPlayerManaPredicateCall,
            sizeof(kExpectedPlayerManaPredicateCall)) == 0);
        already_applied = (memcmp(site, replacement, sizeof(replacement)) == 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        Log("B2 mana gauge DISABLED: predicate call unreadable at rva=0x%08X",
            static_cast<unsigned>(kPlayerManaPredicateCallRva));
        return false;
    }

    if (already_applied) {
        Log("B2 mana gauge already active: stock HUD predicate redirected");
        return true;
    }
    if (!stock_signature) {
        Log("B2 mana gauge DISABLED: predicate signature mismatch at rva=0x%08X",
            static_cast<unsigned>(kPlayerManaPredicateCallRva));
        return false;
    }

    DWORD old_protection = 0;
    if (!VirtualProtect(site, sizeof(replacement), PAGE_EXECUTE_READWRITE, &old_protection)) {
        Log("B2 mana gauge FAILED: VirtualProtect");
        return false;
    }

    bool wrote = false;
    __try {
        memcpy(site, replacement, sizeof(replacement));
        FlushInstructionCache(GetCurrentProcess(), site, sizeof(replacement));
        wrote = (memcmp(site, replacement, sizeof(replacement)) == 0);
        if (!wrote) {
            memcpy(site, kExpectedPlayerManaPredicateCall,
                sizeof(kExpectedPlayerManaPredicateCall));
            FlushInstructionCache(
                GetCurrentProcess(), site, sizeof(kExpectedPlayerManaPredicateCall));
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        memcpy(site, kExpectedPlayerManaPredicateCall,
            sizeof(kExpectedPlayerManaPredicateCall));
        FlushInstructionCache(
            GetCurrentProcess(), site, sizeof(kExpectedPlayerManaPredicateCall));
        wrote = false;
    }

    DWORD ignored = 0;
    VirtualProtect(site, sizeof(replacement), old_protection, &ignored);
    if (!wrote) {
        Log("B2 mana gauge FAILED: write did not verify; rolled back");
        return false;
    }

    Log("B2 mana gauge APPLIED: CPlayerWnd predicate now follows the positive "
        "OP_ManaUpdate maximum (site rva=0x%08X, LocalPlayer+0x354)",
        static_cast<unsigned>(kPlayerManaPredicateCallRva));
    return true;
}

static bool ApplyCasterClassTablePatch(uintptr_t eq_base, bool version_ok)
{
    if (!version_ok) {
        Log("B2 patch DISABLED: client version guard failed");
        return false;
    }

    BYTE* table = reinterpret_cast<BYTE*>(eq_base + kCasterClassTableRva);
    bool stock_signature = false;
    bool already_applied = false;
    __try {
        stock_signature =
            (memcmp(table, kExpectedCasterClassTable, sizeof(kExpectedCasterClassTable)) == 0);
        already_applied =
            (memcmp(table, kEnabledCasterClassTable, sizeof(kEnabledCasterClassTable)) == 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        Log("B2 patch DISABLED: caster-class table unreadable at rva=0x%08X",
            static_cast<unsigned>(kCasterClassTableRva));
        return false;
    }

    if (already_applied) {
        Log("B2 patch already active: caster-class table enabled");
        return true;
    }
    if (!stock_signature) {
        Log("B2 patch DISABLED: caster-class table signature mismatch at rva=0x%08X",
            static_cast<unsigned>(kCasterClassTableRva));
        return false;
    }

    DWORD old_protection = 0;
    if (!VirtualProtect(
            table, sizeof(kExpectedCasterClassTable),
            PAGE_EXECUTE_READWRITE, &old_protection)) {
        Log("B2 patch FAILED: VirtualProtect on caster-class table");
        return false;
    }

    bool wrote = false;
    __try {
        for (size_t index : kNonCasterClassIndexes) {
            table[index] = 1;
        }
        FlushInstructionCache(
            GetCurrentProcess(), table, sizeof(kExpectedCasterClassTable));
        wrote =
            (memcmp(table, kEnabledCasterClassTable, sizeof(kEnabledCasterClassTable)) == 0);
        if (!wrote) {
            for (size_t index : kNonCasterClassIndexes) {
                table[index] = 0;
            }
            FlushInstructionCache(
                GetCurrentProcess(), table, sizeof(kExpectedCasterClassTable));
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        for (size_t index : kNonCasterClassIndexes) {
            table[index] = 0;
        }
        FlushInstructionCache(
            GetCurrentProcess(), table, sizeof(kExpectedCasterClassTable));
        wrote = false;
    }

    DWORD ignored = 0;
    VirtualProtect(
        table, sizeof(kExpectedCasterClassTable), old_protection, &ignored);

    if (!wrote) {
        Log("B2 patch FAILED: caster-class table write did not verify; rolled back");
        return false;
    }

    Log("B2 patch APPLIED: WAR/MNK/ROG/BER enabled in caster-class table "
        "(4 data bytes; 5 known client consumers)");
    return true;
}

static bool ApplyCombatAbilityClassTablePatch(uintptr_t eq_base, bool version_ok)
{
    if (!version_ok) {
        Log("G006 combat-ability patch DISABLED: client version guard failed");
        return false;
    }

    BYTE* table = reinterpret_cast<BYTE*>(
        eq_base + kCombatAbilityClassTableRva);
    BYTE original[sizeof(kExpectedCombatAbilityClassTable)] = {};
    bool stock_signature = false;
    __try {
        memcpy(original, table, sizeof(original));
        stock_signature =
            (memcmp(original, kExpectedCombatAbilityClassTable,
                sizeof(original)) == 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        Log("G006 combat-ability patch DISABLED: class table unreadable "
            "at rva=0x%08X",
            static_cast<unsigned>(kCombatAbilityClassTableRva));
        return false;
    }

    if (!stock_signature) {
        Log("G006 combat-ability patch DISABLED: class table signature mismatch "
            "at rva=0x%08X",
            static_cast<unsigned>(kCombatAbilityClassTableRva));
        return false;
    }

    DWORD old_protection = 0;
    if (!VirtualProtect(
            table, sizeof(kExpectedCombatAbilityClassTable),
            PAGE_EXECUTE_READWRITE, &old_protection)) {
        Log("G006 combat-ability patch FAILED: VirtualProtect");
        return false;
    }

    // Re-read after changing protection to detect a table change during the
    // protection transition. This is not atomic against a hostile concurrent
    // writer; supported injected modules must not mutate this patch site.
    bool pre_write_signature = false;
    __try {
        pre_write_signature = (memcmp(
            table, original, sizeof(original)) == 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        pre_write_signature = false;
    }

    const bool write_attempted = pre_write_signature;
    bool wrote = false;
    if (write_attempted) {
        __try {
            memcpy(
                table, kEnabledCombatAbilityClassTable,
                sizeof(kEnabledCombatAbilityClassTable));
            FlushInstructionCache(GetCurrentProcess(), table, sizeof(original));
            wrote = (memcmp(
                table, kEnabledCombatAbilityClassTable,
                sizeof(kEnabledCombatAbilityClassTable)) == 0);
        } __except (EXCEPTION_EXECUTE_HANDLER) {
            wrote = false;
        }
    }

    bool rollback_ok = true;
    if (write_attempted && !wrote) {
        rollback_ok = false;
        __try {
            memcpy(table, original, sizeof(original));
            FlushInstructionCache(GetCurrentProcess(), table, sizeof(original));
            rollback_ok = (memcmp(table, original, sizeof(original)) == 0);
        } __except (EXCEPTION_EXECUTE_HANDLER) {
            rollback_ok = false;
        }
    }

    DWORD ignored = 0;
    bool protection_restored = VirtualProtect(
        table, sizeof(original), old_protection, &ignored) != FALSE;
    if (!protection_restored) {
        // Do not leave an applied patch on a writable executable page. The
        // guarded rollback is independent of the original write handler.
        if (write_attempted) {
            rollback_ok = false;
            __try {
                memcpy(table, original, sizeof(original));
                FlushInstructionCache(
                    GetCurrentProcess(), table, sizeof(original));
                rollback_ok = (memcmp(table, original, sizeof(original)) == 0);
            } __except (EXCEPTION_EXECUTE_HANDLER) {
                rollback_ok = false;
            }
        }

        DWORD retry_ignored = 0;
        const bool retry_restored = VirtualProtect(
            table, sizeof(original), old_protection, &retry_ignored) != FALSE;
        Log("G006 combat-ability patch FAILED: protection restore failed; "
            "rollback=%s retry=%s",
            rollback_ok ? "verified" : "FAILED",
            retry_restored ? "restored" : "FAILED");
        return false;
    }

    if (!write_attempted) {
        Log("G006 combat-ability patch DISABLED: class table changed before write");
        return false;
    }
    if (!wrote) {
        Log("G006 combat-ability patch FAILED: write/precondition failed; "
            "rollback=%s",
            rollback_ok ? "verified" : "FAILED");
        return false;
    }

    Log("G006 combat-ability patch APPLIED: all base classes can open "
        "CCombatAbilityWnd (7 data bytes; page protection restored)");
    return true;
}

static bool ApplyActionsSkillPredicatePatch(uintptr_t eq_base, bool version_ok)
{
    if (!version_ok) {
        Log("G006 Actions skill patch DISABLED: client version guard failed");
        return false;
    }

    const size_t site_count =
        sizeof(kActionsSkillPredicateCallRvas) /
        sizeof(kActionsSkillPredicateCallRvas[0]);
    BYTE originals[site_count][5] = {};
    BYTE replacements[site_count][5] = {};
    BYTE* first_site = reinterpret_cast<BYTE*>(
        eq_base + kActionsSkillPredicateCallRvas[0]);
    BYTE* last_site = reinterpret_cast<BYTE*>(
        eq_base + kActionsSkillPredicateCallRvas[site_count - 1]);
    const size_t protected_span = (last_site + 5) - first_site;

    for (size_t i = 0; i < site_count; ++i) {
        BYTE* site = reinterpret_cast<BYTE*>(
            eq_base + kActionsSkillPredicateCallRvas[i]);
        __try {
            memcpy(originals[i], site, sizeof(originals[i]));
        } __except (EXCEPTION_EXECUTE_HANDLER) {
            Log("G006 Actions skill patch DISABLED: call site unreadable "
                "at rva=0x%08X",
                static_cast<unsigned>(kActionsSkillPredicateCallRvas[i]));
            return false;
        }
        if (memcmp(
                originals[i], kExpectedActionsSkillPredicateCalls[i],
                sizeof(originals[i])) != 0) {
            Log("G006 Actions skill patch DISABLED: signature mismatch "
                "at rva=0x%08X",
                static_cast<unsigned>(kActionsSkillPredicateCallRvas[i]));
            return false;
        }

        replacements[i][0] = 0xE8;
        const intptr_t displacement =
            reinterpret_cast<BYTE*>(&HasServerGrantedSkill) - (site + 5);
        if (displacement < INT32_MIN || displacement > INT32_MAX) {
            Log("G006 Actions skill patch DISABLED: hook out of rel32 range");
            return false;
        }
        const int32_t relative32 = static_cast<int32_t>(displacement);
        memcpy(replacements[i] + 1, &relative32, sizeof(relative32));
    }

    DWORD old_protection = 0;
    if (!VirtualProtect(
            first_site, protected_span, PAGE_EXECUTE_READWRITE,
            &old_protection)) {
        Log("G006 Actions skill patch FAILED: VirtualProtect");
        return false;
    }

    bool pre_write_signatures = true;
    for (size_t i = 0; i < site_count; ++i) {
        BYTE* site = reinterpret_cast<BYTE*>(
            eq_base + kActionsSkillPredicateCallRvas[i]);
        __try {
            if (memcmp(site, originals[i], sizeof(originals[i])) != 0) {
                pre_write_signatures = false;
            }
        } __except (EXCEPTION_EXECUTE_HANDLER) {
            pre_write_signatures = false;
        }
    }

    bool wrote = false;
    if (pre_write_signatures) {
        __try {
            for (size_t i = 0; i < site_count; ++i) {
                BYTE* site = reinterpret_cast<BYTE*>(
                    eq_base + kActionsSkillPredicateCallRvas[i]);
                memcpy(site, replacements[i], sizeof(replacements[i]));
            }
            FlushInstructionCache(
                GetCurrentProcess(), first_site, protected_span);
            wrote = true;
            for (size_t i = 0; i < site_count; ++i) {
                BYTE* site = reinterpret_cast<BYTE*>(
                    eq_base + kActionsSkillPredicateCallRvas[i]);
                if (memcmp(
                        site, replacements[i], sizeof(replacements[i])) != 0) {
                    wrote = false;
                }
            }
        } __except (EXCEPTION_EXECUTE_HANDLER) {
            wrote = false;
        }
    }

    bool rollback_ok = true;
    if (!wrote) {
        rollback_ok = false;
        __try {
            for (size_t i = 0; i < site_count; ++i) {
                BYTE* site = reinterpret_cast<BYTE*>(
                    eq_base + kActionsSkillPredicateCallRvas[i]);
                memcpy(site, originals[i], sizeof(originals[i]));
            }
            FlushInstructionCache(
                GetCurrentProcess(), first_site, protected_span);
            rollback_ok = true;
            for (size_t i = 0; i < site_count; ++i) {
                BYTE* site = reinterpret_cast<BYTE*>(
                    eq_base + kActionsSkillPredicateCallRvas[i]);
                if (memcmp(site, originals[i], sizeof(originals[i])) != 0) {
                    rollback_ok = false;
                }
            }
        } __except (EXCEPTION_EXECUTE_HANDLER) {
            rollback_ok = false;
        }
    }

    DWORD ignored = 0;
    bool protection_restored = VirtualProtect(
        first_site, protected_span, old_protection, &ignored) != FALSE;
    if (!protection_restored) {
        rollback_ok = false;
        __try {
            for (size_t i = 0; i < site_count; ++i) {
                BYTE* site = reinterpret_cast<BYTE*>(
                    eq_base + kActionsSkillPredicateCallRvas[i]);
                memcpy(site, originals[i], sizeof(originals[i]));
            }
            FlushInstructionCache(
                GetCurrentProcess(), first_site, protected_span);
            rollback_ok = true;
            for (size_t i = 0; i < site_count; ++i) {
                BYTE* site = reinterpret_cast<BYTE*>(
                    eq_base + kActionsSkillPredicateCallRvas[i]);
                if (memcmp(site, originals[i], sizeof(originals[i])) != 0) {
                    rollback_ok = false;
                }
            }
        } __except (EXCEPTION_EXECUTE_HANDLER) {
            rollback_ok = false;
        }
        DWORD retry_ignored = 0;
        const bool retry_restored = VirtualProtect(
            first_site, protected_span, old_protection,
            &retry_ignored) != FALSE;
        Log("G006 Actions skill patch FAILED: protection restore failed; "
            "rollback=%s retry=%s",
            rollback_ok ? "verified" : "FAILED",
            retry_restored ? "restored" : "FAILED");
        return false;
    }

    if (!wrote) {
        Log("G006 Actions skill patch FAILED: write/precondition failed; "
            "rollback=%s",
            rollback_ok ? "verified" : "FAILED");
        return false;
    }

    Log("G006 Actions skill patch APPLIED: selector accepts positive "
        "server-delivered base skills (2 guarded call sites)");
    return true;
}

// MQ2/the client environment caused every Sleep() in the first successful
// survey to return in ~5ms, collapsing a 15-minute poll into 8ms. Wait on a
// private, never-signaled event instead, then verify elapsed wall-clock time.
// The final yield loop is a defensive fallback if another hook short-circuits
// the kernel wait too.
static void ReliableWait(DWORD milliseconds)
{
    const ULONGLONG started = GetTickCount64();
    HANDLE blocker = CreateEventA(nullptr, TRUE, FALSE, nullptr);
    if (blocker) {
        WaitForSingleObject(blocker, milliseconds);
        CloseHandle(blocker);
    } else {
        // A process object is unsignaled until the process exits, so this is
        // equivalent to a timeout-only wait while the survey is alive.
        WaitForSingleObject(GetCurrentProcess(), milliseconds);
    }

    ULONGLONG elapsed = GetTickCount64() - started;
    if (elapsed + 100 < milliseconds) {
        Log("wait anomaly: requested=%lums actual=%llums; enforcing wall-clock deadline",
            milliseconds, elapsed);
        while (GetTickCount64() - started < milliseconds) {
            SwitchToThread();
        }
    }
}

// --- forwarded exports -------------------------------------------------------
// Resolved lazily from the REAL system dinput8.dll (absolute path, so we never
// recursively load ourselves).

static FARPROC Real(const char* name)
{
    if (!g_real_dinput8) {
        char path[MAX_PATH];
        GetSystemDirectoryA(path, MAX_PATH);
        strcat_s(path, "\\dinput8.dll");
        g_real_dinput8 = LoadLibraryA(path);
    }
    return g_real_dinput8 ? GetProcAddress(g_real_dinput8, name) : nullptr;
}

extern "C" {

HRESULT WINAPI DirectInput8Create(HINSTANCE hinst, DWORD dwVersion, REFIID riid, LPVOID* ppvOut, LPUNKNOWN punkOuter)
{
    typedef HRESULT(WINAPI* Fn)(HINSTANCE, DWORD, REFIID, LPVOID*, LPUNKNOWN);
    auto fn = (Fn)Real("DirectInput8Create");
    return fn ? fn(hinst, dwVersion, riid, ppvOut, punkOuter) : E_FAIL;
}

HRESULT WINAPI DllCanUnloadNow()
{
    typedef HRESULT(WINAPI* Fn)();
    auto fn = (Fn)Real("DllCanUnloadNow");
    return fn ? fn() : S_FALSE;
}

HRESULT WINAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, LPVOID* ppv)
{
    typedef HRESULT(WINAPI* Fn)(REFCLSID, REFIID, LPVOID*);
    auto fn = (Fn)Real("DllGetClassObject");
    return fn ? fn(rclsid, riid, ppv) : E_FAIL;
}

HRESULT WINAPI DllRegisterServer()
{
    typedef HRESULT(WINAPI* Fn)();
    auto fn = (Fn)Real("DllRegisterServer");
    return fn ? fn() : E_FAIL;
}

HRESULT WINAPI DllUnregisterServer()
{
    typedef HRESULT(WINAPI* Fn)();
    auto fn = (Fn)Real("DllUnregisterServer");
    return fn ? fn() : E_FAIL;
}

LPCVOID WINAPI GetdfDIJoystick()
{
    typedef LPCVOID(WINAPI* Fn)();
    auto fn = (Fn)Real("GetdfDIJoystick");
    return fn ? fn() : nullptr;
}

} // extern "C"

// --- B2 step 1: offset survey via MQ2Main exports ----------------------------
// MQ2-emu computes every eqgame static address at load time and stores it in
// its exported DWORD variables (pinstCSpellBookWnd etc.). We share the process,
// so once MQ2Main.dll is loaded we can walk its export table and log every
// export whose stored DWORD lands inside eqgame.exe — a complete, build-exact
// offset map with zero reversing. HITL: launch game with MQ2 as usual, log in.

static bool GuardedReadDword(const void* p, DWORD* out)
{
    __try {
        *out = *(const DWORD*)p;
        return true;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

static void GetModuleRange(HMODULE mod, uintptr_t* base, uintptr_t* size)
{
    *base = (uintptr_t)mod;
    auto dos = (IMAGE_DOS_HEADER*)mod;
    auto nt  = (IMAGE_NT_HEADERS*)(*base + dos->e_lfanew);
    *size = nt->OptionalHeader.SizeOfImage;
}

// Symbols we re-poll with dereferenced instance pointers, so the HITL session
// shows whether the client CREATES these windows for a melee base (patchable
// by force-show) or never constructs them at all (needs the creation path).
static const char* kWatchlist[] = {
    "pinstCSpellBookWnd", "pinstCCastSpellWnd", "pinstCSpellGemWnd",
    "pinstPCData", "pinstCharData", "pinstLocalPlayer", "pinstControlledPlayer",
};

static unsigned CountInitializedWatchSlots(HMODULE mq2, uintptr_t eq_base, uintptr_t eq_size)
{
    unsigned ready = 0;
    for (const char* name : kWatchlist) {
        auto var = (DWORD*)GetProcAddress(mq2, name);
        DWORD slot_va = 0;
        if (var && GuardedReadDword(var, &slot_va) &&
            slot_va >= eq_base && slot_va < eq_base + eq_size) {
            ready++;
        }
    }
    return ready;
}

// Log every module loaded in the process, so a session that never sees MQ2 still
// tells us exactly what IS injected (and under what name).
static void DumpModules(const char* when)
{
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, 0);
    if (snap == INVALID_HANDLE_VALUE) { Log("modules (%s): snapshot failed", when); return; }
    MODULEENTRY32 me; me.dwSize = sizeof(me);
    Log("modules (%s):", when);
    if (Module32First(snap, &me)) {
        do {
            Log("  %-24s base=0x%08X size=0x%08X", me.szModule, (unsigned)(uintptr_t)me.modBaseAddr, me.modBaseSize);
        } while (Module32Next(snap, &me));
    }
    CloseHandle(snap);
}

// Does the PE image at `base` export a symbol containing `needle`? Guarded — many
// regions aren't valid PEs. Returns true and confirms this is MQ2Main.
static bool ImageExportsSymbol(uintptr_t base, const char* needle)
{
    __try {
        auto dos = (IMAGE_DOS_HEADER*)base;
        if (dos->e_magic != IMAGE_DOS_SIGNATURE) return false;
        auto nt = (IMAGE_NT_HEADERS*)(base + dos->e_lfanew);
        if (nt->Signature != IMAGE_NT_SIGNATURE) return false;
        DWORD exp_rva = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT].VirtualAddress;
        if (!exp_rva) return false;
        auto exp   = (IMAGE_EXPORT_DIRECTORY*)(base + exp_rva);
        auto names = (DWORD*)(base + exp->AddressOfNames);
        for (DWORD i = 0; i < exp->NumberOfNames; i++) {
            const char* n = (const char*)(base + names[i]);
            if (strstr(n, needle)) return true;
        }
        return false;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return false;
    }
}

// Find MQ2's main image even when it's unlinked from the loader module list
// (MQ2 hides its module). 1) GetModuleHandle, 2) Toolhelp, 3) raw VirtualQuery
// walk looking for a mapped image that exports the eqgame offset symbols.
static HMODULE FindMq2()
{
    HMODULE h = GetModuleHandleA("MQ2Main.dll");
    if (h) return h;

    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, 0);
    if (snap != INVALID_HANDLE_VALUE) {
        MODULEENTRY32 me; me.dwSize = sizeof(me);
        HMODULE found = nullptr;
        if (Module32First(snap, &me)) {
            do {
                if (_strnicmp(me.szModule, "MQ2", 3) == 0) { found = me.hModule; break; }
            } while (Module32Next(snap, &me));
        }
        CloseHandle(snap);
        if (found) return found;
    }

    // Memory scan: MQ2's image is still mapped (plugins run), just unlinked.
    MEMORY_BASIC_INFORMATION mbi;
    uintptr_t addr = 0x10000;
    const uintptr_t kMax = 0x7FFF0000;
    while (addr < kMax && VirtualQuery((LPCVOID)addr, &mbi, sizeof(mbi))) {
        uintptr_t region = (uintptr_t)mbi.BaseAddress;
        if (mbi.State == MEM_COMMIT &&
            (mbi.Type == MEM_IMAGE || mbi.Type == MEM_PRIVATE) &&
            !(mbi.Protect & PAGE_GUARD) && (mbi.Protect & 0xFF) != PAGE_NOACCESS) {
            if (ImageExportsSymbol(region, "pinstCSpellBookWnd")) {
                return (HMODULE)region;
            }
        }
        addr = region + (mbi.RegionSize ? mbi.RegionSize : 0x1000);
    }
    return nullptr;
}

static unsigned SurveyMq2Exports(HMODULE mq2, uintptr_t eq_base, uintptr_t eq_size)
{
    uintptr_t mq_base, mq_size;
    GetModuleRange(mq2, &mq_base, &mq_size);

    auto dos = (IMAGE_DOS_HEADER*)mq2;
    auto nt  = (IMAGE_NT_HEADERS*)(mq_base + dos->e_lfanew);
    DWORD exp_rva = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT].VirtualAddress;
    if (!exp_rva) {
        Log("survey: MQ2Main has no export directory?");
        return 0;
    }

    auto exp    = (IMAGE_EXPORT_DIRECTORY*)(mq_base + exp_rva);
    auto names  = (DWORD*)(mq_base + exp->AddressOfNames);
    auto ords   = (WORD*)(mq_base + exp->AddressOfNameOrdinals);
    auto funcs  = (DWORD*)(mq_base + exp->AddressOfFunctions);

    Log("survey: eqgame base=0x%08X size=0x%08X | MQ2Main base=0x%08X exports=%lu",
        (unsigned)eq_base, (unsigned)eq_size, (unsigned)mq_base, exp->NumberOfNames);
    Log("survey: columns = name | stored VA | RVA (VA - eqgame base)");

    unsigned hits = 0;
    for (DWORD i = 0; i < exp->NumberOfNames; i++) {
        const char* name = (const char*)(mq_base + names[i]);
        uintptr_t addr = mq_base + funcs[ords[i]];
        DWORD stored;
        if (!GuardedReadDword((void*)addr, &stored)) continue;
        // keep only exports whose stored DWORD points into eqgame.exe
        if (stored >= eq_base && stored < eq_base + eq_size) {
            Log("OFFSET %s = 0x%08X (rva 0x%08X)", name, stored, (unsigned)(stored - eq_base));
            hits++;
        }
    }
    Log("survey: %u eqgame-resident offsets captured", hits);
    return hits;
}

static void PollWatchlist(HMODULE mq2, unsigned sample, ULONGLONG elapsed_seconds)
{
    for (const char* name : kWatchlist) {
        auto var = (DWORD*)GetProcAddress(mq2, name);
        if (!var) {
            Log("watch sample=%02u elapsed=%llus: %s (not exported)",
                sample, elapsed_seconds, name);
            continue;
        }
        DWORD slot_va;
        if (!GuardedReadDword(var, &slot_va)) continue;
        DWORD instance = 0;
        bool ok = GuardedReadDword((void*)(uintptr_t)slot_va, &instance);
        Log("watch sample=%02u elapsed=%llus: %s slot=0x%08X instance=%s0x%08X",
            sample, elapsed_seconds, name, slot_va, ok ? "" : "<unreadable> ", instance);
        if (ok && instance && strcmp(name, "pinstLocalPlayer") == 0) {
            DWORD raw_current_mana = 0;
            DWORD raw_max_mana = 0;
            bool current_ok = GuardedReadDword(
                reinterpret_cast<void*>(static_cast<uintptr_t>(instance) + 0x494),
                &raw_current_mana);
            bool max_ok = GuardedReadDword(
                reinterpret_cast<void*>(static_cast<uintptr_t>(instance) + 0x354),
                &raw_max_mana);
            Log("watch sample=%02u elapsed=%llus: local spawn raw mana current=%s%lu max=%s%lu",
                sample, elapsed_seconds,
                current_ok ? "" : "<unreadable> ", raw_current_mana,
                max_ok ? "" : "<unreadable> ", raw_max_mana);
        }
    }
}

static DWORD WINAPI InitThread(LPVOID)
{
    const DWORD pid = GetCurrentProcessId();
    char log_name[MAX_PATH];
    sprintf_s(log_name, "nightcap_dll_%lu.log", pid);
    g_log = _fsopen(log_name, "w", _SH_DENYNO);
    if (!g_log) {
        return 0;
    }
    Log("Nightcap proxy loaded (B2 caster-chassis correction + offset survey)");
    Log("pid: %lu | log: %s", pid, log_name);

    char exe_path[MAX_PATH];
    GetModuleFileNameA(nullptr, exe_path, MAX_PATH);
    Log("host process: %s", exe_path);

    // A patch is permitted only when both immutable client checks pass.
    WIN32_FILE_ATTRIBUTE_DATA fad;
    bool size_ok = false;
    if (GetFileAttributesExA(exe_path, GetFileExInfoStandard, &fad)) {
        size_ok = (fad.nFileSizeLow == kExpectedEqgameSize && fad.nFileSizeHigh == 0);
        Log("client size check: %s (%lu bytes)", size_ok ? "OK" : "MISMATCH",
            fad.nFileSizeLow);
    } else {
        Log("client size check: UNREADABLE");
    }

    uintptr_t eq_base, eq_size;
    GetModuleRange(GetModuleHandleA(nullptr), &eq_base, &eq_size);
    g_eq_base = eq_base;
    bool hash_ok = size_ok && VerifyEqgameSha256(exe_path);
    Log("client sha256 check: %s", hash_ok ? "OK" : "MISMATCH OR UNREADABLE");
    ApplyCasterClassTablePatch(eq_base, size_ok && hash_ok);
    ApplyCombatAbilityClassTablePatch(eq_base, size_ok && hash_ok);
    ApplyActionsSkillPredicatePatch(eq_base, size_ok && hash_ok);
    const bool mana_hook_ok =
        ApplyMaxManaServerCacheHook(eq_base, size_ok && hash_ok);
    ApplyPlayerManaGaugePredicateHook(eq_base, mana_hook_ok);

    // Wait for MQ2 (user launches MacroQuest2.exe as usual); survey once, then
    // poll the watchlist so the HITL session captures instance lifecycles
    // (login caster -> windows non-null; camp to melee -> created or null?).
    HMODULE mq2 = nullptr;
    const ULONGLONG start_tick = GetTickCount64();
    bool dumped_early = false;
    while (!mq2 && GetTickCount64() - start_tick < 300000) {
        mq2 = FindMq2();
        if (mq2) break;
        ULONGLONG elapsed = GetTickCount64() - start_tick;
        if (!dumped_early && elapsed >= 8000) { DumpModules("early, MQ2 not yet seen"); dumped_early = true; }
        Log("waiting for MQ2... elapsed %llus", elapsed / 1000);
        ReliableWait(5000);
    }
    if (!mq2) {
        DumpModules("final, MQ2 never appeared");
        Log("MQ2 not found after %llus (scanned loader list + raw memory). If MQ2 was "
            "actually active in-game this session, it's memory-mapped in a way the scan "
            "missed; tell me and I'll widen it. Otherwise MQ2 wasn't injected into this "
            "eqgame process.", (GetTickCount64() - start_tick) / 1000);
        return 0;
    }
    Log("MQ2 found at base=0x%08X after %llus",
        (unsigned)(uintptr_t)mq2, (GetTickCount64() - start_tick) / 1000);

    // Finding the image and MQ2 finishing its exported offset initialization are
    // separate moments. Wait until most targeted exports hold eqgame addresses,
    // then give the remaining export table a real five-second settling period.
    const ULONGLONG ready_started = GetTickCount64();
    unsigned ready_slots = 0;
    do {
        ready_slots = CountInitializedWatchSlots(mq2, eq_base, eq_size);
        Log("MQ2 offset readiness: %u/%u watch slots initialized",
            ready_slots, (unsigned)(sizeof(kWatchlist) / sizeof(kWatchlist[0])));
        if (ready_slots >= 5) break;
        ReliableWait(1000);
    } while (GetTickCount64() - ready_started < 30000);

    ReliableWait(5000);

    unsigned hits = 0;
    for (unsigned attempt = 1; attempt <= 5; attempt++) {
        Log("survey attempt %u/5", attempt);
        hits = SurveyMq2Exports(mq2, eq_base, eq_size);
        if (hits >= 10) break;
        Log("survey captured only %u offset(s); retrying after MQ2 settles", hits);
        ReliableWait(2000);
    }

    const ULONGLONG polling_started = GetTickCount64();
    for (unsigned i = 1; i <= 60; i++) {             // 15 min of lifecycle polling
        PollWatchlist(mq2, i, (GetTickCount64() - polling_started) / 1000);
        if (i < 60) {
            ReliableWait(15000);
        }
    }
    Log("survey session complete: offsets=%u polling_elapsed=%llus",
        hits, (GetTickCount64() - polling_started) / 1000);
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE hinst, DWORD reason, LPVOID)
{
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hinst);
        // no loader-lock-unsafe work in DllMain; everything happens on the thread
        HANDLE t = CreateThread(nullptr, 0, InitThread, nullptr, 0, nullptr);
        if (t) CloseHandle(t);
    } else if (reason == DLL_PROCESS_DETACH) {
        if (g_log) { Log("Nightcap proxy unloading"); fclose(g_log); g_log = nullptr; }
        if (g_real_dinput8) { FreeLibrary(g_real_dinput8); g_real_dinput8 = nullptr; }
    }
    return TRUE;
}

// =============================================================================
// Nightcap dinput8.dll proxy — B2 caster-chassis correction (issue #12, ADR 0004)
//
// RoF2 auto-loads dinput8.dll from its own folder at startup. This proxy
// gates DirectInput forwarding on synchronous configuration/version/patch
// validation, then forwards to the real system DLL. Required failures stop
// startup and publish versioned health; optional MQ2 survey defaults off.
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
#include <process.h>
#include <intrin.h>
#include <io.h>
#include <fcntl.h>
#include "equipment_scope.h"
#include "patch_catalog.h"
#include "runtime_health.h"
#include "verified_patch.h"
#include "ui_hooks.h"
#include "model_hooks.h"

#pragma comment(lib, "bcrypt.lib")

// --- expected client build and B2 caster-class table --------------------------
// eqgame.exe, RoF2 May 10 2013 emu package, 8,774,656 bytes
// sha256 2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e

// The stock predicate indexes this table by BaseProfile.Class - 1. Its only
// zero entries are the four no-mana classes. Enabling those four entries makes
// every base class caster-capable in the client chassis while the server remains
// authoritative for whether a character actually has mana or usable spells.

static const BYTE kEnabledCasterClassTable[16] = {
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
};

// CCombatAbilityWnd::CanShow indexes this table by BaseProfile.Class - 1.
// Stock RoF2 disables the window for its seven pure-caster classes. Enable the
// presentation chassis for every base class; the server remains authoritative
// for learned skills and every submitted combat ability.

static const BYTE kEnabledCombatAbilityClassTable[16] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
};

// CSkillsSelectWnd::SetTypesToDisplay checks CharacterZoneClient::HasSkill
// before adding an activated skill to the Actions -> Abilities picker.
// HasSkill clamps the received value through the primary class's cap, hiding
// valid secondary/tertiary skills. Redirect only the two selector calls to a
// predicate that preserves stock success and otherwise accepts a positive
// server-delivered base skill.

// CHotButton refresh uses HasSkill to decide whether a type-9 skill button is
// usable. CharacterZoneClient::UseSkill separately calls GetSkill and rejects
// a non-positive result before sending anything to the server.

// Type-9 hotbuttons normally enter CharacterZoneClient::UseSkill. Stock RoF2
// intentionally leaves direct handlers empty for the six basic combat attacks;
// its internal special-attack submitter is the path that owns their target,
// animation, reuse, and OP_CombatAbility packet behavior.

// The stock special-attack submitter has one HasSkill call that repeats the
// primary-class clamp. Redirect only that exact call for server-granted skills.

static const uintptr_t kCharacterUseSkillRva = 0x0005B2D0;

static const uintptr_t kSkillManagerSlotRva = 0x00A64610;

static const uintptr_t kSkillTimerIndexRva = 0x001BA2B0;
static const uintptr_t kSkillReuseBeginRva = 0x001BADA0;
static const uintptr_t kSkillReuseCommitRva = 0x001BAC50;

// RoF2's non-caster EQ_Character::Max_Mana branch returns zero even after the
// server has populated LocalPlayer's authoritative raw maximum at +0x354.
// Redirect only that complete six-byte return block to the guarded stub below.
static const uintptr_t kLocalPlayerSlotRva = 0x009D2630;

// CPlayerWnd refreshes PlayerMana every 500 ms using a second, stock
// base-class predicate. Redirect only that predicate call so the stock HUD
// owns visibility continuously and bases it on the server-cached maximum.

// #13: CanEquipItem -> CanUseItem and its class-mask accessor. These calls
// scope a permissive class result to equip submission, never global item data.

static HMODULE g_real_dinput8 = nullptr;
static FILE*   g_log          = nullptr;
static uintptr_t g_local_player_slot = 0;
static uintptr_t g_eq_base = 0;

static bool IsMonkCombatAttack(int skill);
static void EnsureInitialized();
static unsigned __stdcall SurveyThread(void*);
static INIT_ONCE g_initialize_once = INIT_ONCE_STATIC_INIT;
static volatile LONG g_initialize_owner = 0;
static volatile LONG g_initialize_state = 0;
static wchar_t g_client_directory[MAX_PATH] = {};
static nightcap::RuntimeConfig g_config;
static nightcap::RuntimeHealth g_health;
static FARPROC g_real_exports[6] = {};
static const char* const kRealExportNames[] = {"DirectInput8Create","DllCanUnloadNow","DllGetClassObject","DllRegisterServer","DllUnregisterServer","GetdfDIJoystick"};


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

static bool VerifyFileSha256(const wchar_t* path, const BYTE* expected)
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

    file = CreateFileW(
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
    matched = (memcmp(digest, expected, sizeof(digest)) == 0);

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

// The stock special-attack gate is execution-sensitive, so keep its fallback
// narrower than the presentation predicate: only the six held-Monk attacks
// may use a positive server-delivered value after a stock-negative result.
extern "C" __declspec(noinline) BYTE __fastcall HasServerGrantedMonkAttack(
    void* character, void* unused_edx, int skill)
{
    (void)unused_edx;
    if (!character || g_eq_base == 0 || skill < 0 || skill >= 100) {
        return 0;
    }

    typedef BYTE (__thiscall *HasSkillFn)(void*, int);
    typedef int (__thiscall *GetBaseSkillFn)(void*, int, int);
    HasSkillFn stock_has_skill = reinterpret_cast<HasSkillFn>(
        g_eq_base + kCharacterHasSkillRva);
    GetBaseSkillFn get_base_skill = reinterpret_cast<GetBaseSkillFn>(
        g_eq_base + kCharacterGetBaseSkillRva);

    __try {
        const BYTE stock = stock_has_skill(character, skill);
        if (stock || !IsMonkCombatAttack(skill)) {
            return stock ? 1 : 0;
        }
        return get_base_skill(character, skill, 0) > 0 ? 1 : 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        Log("G006_MONK_GATE skill=%d exception=1", skill);
        return 0;
    }
}

// Preserve the stock adjusted value when it is positive. A held-class skill
// that the primary-class cap clamps to zero falls back to the raw value sent by
// the server. UseSkill still owns every subsequent state/target/timer check,
// and the server remains authoritative for the submitted activation.
extern "C" __declspec(noinline) int __fastcall GetServerGrantedSkill(
    void* character, void* unused_edx, int skill)
{
    (void)unused_edx;
    if (!character || g_eq_base == 0 || skill < 0 || skill >= 100) {
        return 0;
    }

    typedef int (__thiscall *GetSkillFn)(void*, int);
    typedef int (__thiscall *GetBaseSkillFn)(void*, int, int);
    GetSkillFn get_skill = reinterpret_cast<GetSkillFn>(
        g_eq_base + kCharacterGetSkillRva);
    GetBaseSkillFn get_base_skill = reinterpret_cast<GetBaseSkillFn>(
        g_eq_base + kCharacterGetBaseSkillRva);

    __try {
        const int adjusted = get_skill(character, skill);
        if (adjusted > 0) {
            return adjusted;
        }
        const int base = get_base_skill(character, skill, 0);
        return base > 0 ? base : 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        if (skill == 21 || skill == 23 || skill == 26 || skill == 30 ||
            skill == 32 || skill == 38 || skill == 52) {
            Log("G006_USE_SKILL skill=%d exception=1", skill);
        }
        return 0;
    }
}

static bool IsMonkCombatAttack(int skill)
{
    return skill == 21 || // Dragon Punch / Tail Rake
        skill == 23 ||    // Eagle Strike
        skill == 26 ||    // Flying Kick
        skill == 30 ||    // Kick
        skill == 38 ||    // Round Kick
        skill == 52;      // Tiger Claw
}

// Match CharacterZoneClient::UseSkill's two-argument thiscall ABI at the
// CHotButtonWnd call site. Non-Monk skills remain entirely stock. The six
// basic attacks enter the exact stock submitter that UseSkill itself calls for
// special attacks, after requiring a positive server-delivered skill value.
extern "C" __declspec(noinline) void __fastcall ActivateServerGrantedSkill(
    void* character, void* unused_edx, int skill, void* target)
{
    (void)unused_edx;
    if (g_eq_base == 0) {
        return;
    }

    typedef void (__thiscall *UseSkillFn)(void*, int, void*);
    UseSkillFn use_skill = reinterpret_cast<UseSkillFn>(
        g_eq_base + kCharacterUseSkillRva);

    if (!IsMonkCombatAttack(skill)) {
        use_skill(character, skill, target);
        return;
    }

    if (!character || GetServerGrantedSkill(character, nullptr, skill) <= 0) {
        Log("G006_MONK_ATTACK skill=%d submitted=0 reason=no-server-skill", skill);
        return;
    }

    typedef BYTE (__thiscall *SubmitSpecialAttackFn)(
        void*, int, int, void*);
    SubmitSpecialAttackFn submit_special_attack =
        reinterpret_cast<SubmitSpecialAttackFn>(
            g_eq_base + kSpecialAttackSubmitRva);

    __try {
        void* player = *reinterpret_cast<void**>(
            static_cast<BYTE*>(character) + 0x08);
        if (!player) {
            Log("G006_MONK_ATTACK skill=%d submitted=0 reason=no-player", skill);
            return;
        }
        const BYTE submitted = submit_special_attack(
            player, 100, skill, target);
        if (submitted) {
            void* skill_manager =
                *reinterpret_cast<void**>(g_eq_base + kSkillManagerSlotRva);
            if (skill_manager) {
                typedef void (__thiscall *SkillReuseFn)(void*, int, DWORD);
                typedef int (__thiscall *SkillTimerIndexFn)(void*, int);
                SkillReuseFn begin_reuse = reinterpret_cast<SkillReuseFn>(
                    g_eq_base + kSkillReuseBeginRva);
                SkillTimerIndexFn timer_index =
                    reinterpret_cast<SkillTimerIndexFn>(
                        g_eq_base + kSkillTimerIndexRva);
                SkillReuseFn commit_reuse = reinterpret_cast<SkillReuseFn>(
                    g_eq_base + kSkillReuseCommitRva);

                // This is the exact stock post-submit sequence at 0x45D93C.
                begin_reuse(skill_manager, skill, 0);
                const int index = timer_index(skill_manager, skill);
                if (index >= 0 && index < 100) {
                    const DWORD reuse_end = *reinterpret_cast<DWORD*>(
                        static_cast<BYTE*>(player) + 0x390 + index * 4);
                    commit_reuse(skill_manager, skill, reuse_end);
                }
            }
        }
        Log("G006_MONK_ATTACK skill=%d target=%p submitted=%u",
            skill, target, static_cast<unsigned>(submitted));
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        Log("G006_MONK_ATTACK skill=%d submitted=0 exception=1", skill);
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

    g_local_player_slot = eq_base + kLocalPlayerSlotRva;
    if (!nightcap::WriteVerifiedPatch(site, kExpectedMaxManaReturn, replacement, sizeof(replacement))) {
        g_local_player_slot = 0;
        Log("B2 mana hook FAILED: guarded write/cache/protection check");
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

    if (!nightcap::WriteVerifiedPatch(site, kExpectedPlayerManaPredicateCall, replacement, sizeof(replacement))) {
        Log("B2 mana gauge FAILED: guarded write/cache/protection check");
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
    if (!nightcap::WriteVerifiedPatch(table, kExpectedCasterClassTable,
            kEnabledCasterClassTable, sizeof(kExpectedCasterClassTable))) {
        Log("B2 patch FAILED: guarded write/cache/protection check");
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
            wrote = FlushInstructionCache(GetCurrentProcess(), table, sizeof(original)) != FALSE &&
                (memcmp(
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
            rollback_ok = FlushInstructionCache(GetCurrentProcess(), table, sizeof(original)) != FALSE &&
                (memcmp(table, original, sizeof(original)) == 0);
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
                rollback_ok = FlushInstructionCache(
                    GetCurrentProcess(), table, sizeof(original)) != FALSE &&
                (memcmp(table, original, sizeof(original)) == 0);
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
            wrote = FlushInstructionCache(
                GetCurrentProcess(), first_site, protected_span) != FALSE;
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
            rollback_ok = FlushInstructionCache(
                GetCurrentProcess(), first_site, protected_span) != FALSE;
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
            rollback_ok = FlushInstructionCache(
                GetCurrentProcess(), first_site, protected_span) != FALSE;
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

static bool ApplyGuardedRelativeCall(
    uintptr_t eq_base,
    uintptr_t call_rva,
    const BYTE expected[5],
    uintptr_t target,
    const char* label)
{
    BYTE* site = reinterpret_cast<BYTE*>(eq_base + call_rva);
    BYTE replacement[5] = { 0xE8, 0, 0, 0, 0 };
    const intptr_t displacement =
        static_cast<intptr_t>(target) -
        reinterpret_cast<intptr_t>(site + sizeof(replacement));
    if (displacement < INT32_MIN || displacement > INT32_MAX) {
        Log("%s DISABLED: hook target is outside rel32 range", label);
        return false;
    }
    const int32_t relative32 = static_cast<int32_t>(displacement);
    memcpy(replacement + 1, &relative32, sizeof(relative32));

    bool stock_signature = false;
    __try {
        stock_signature = (memcmp(site, expected, 5) == 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        Log("%s DISABLED: call unreadable at rva=0x%08X", label,
            static_cast<unsigned>(call_rva));
        return false;
    }
    if (!stock_signature) {
        Log("%s DISABLED: signature mismatch at rva=0x%08X", label,
            static_cast<unsigned>(call_rva));
        return false;
    }

    DWORD old_protection = 0;
    if (!VirtualProtect(
            site, 5, PAGE_EXECUTE_READWRITE, &old_protection)) {
        Log("%s FAILED: VirtualProtect", label);
        return false;
    }

    bool pre_write_signature = false;
    __try {
        pre_write_signature = (memcmp(site, expected, 5) == 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        pre_write_signature = false;
    }
    const bool write_attempted = pre_write_signature;

    bool wrote = false;
    if (write_attempted) {
        __try {
            memcpy(site, replacement, sizeof(replacement));
            wrote = FlushInstructionCache(
                GetCurrentProcess(), site, sizeof(replacement)) != FALSE &&
                (memcmp(site, replacement, sizeof(replacement)) == 0);
        } __except (EXCEPTION_EXECUTE_HANDLER) {
            wrote = false;
        }
    }

    bool rollback_ok = true;
    if (write_attempted && !wrote) {
        rollback_ok = false;
        __try {
            memcpy(site, expected, 5);
            rollback_ok = FlushInstructionCache(GetCurrentProcess(), site, 5) != FALSE &&
                (memcmp(site, expected, 5) == 0);
        } __except (EXCEPTION_EXECUTE_HANDLER) {
            rollback_ok = false;
        }
    }

    DWORD ignored = 0;
    bool protection_restored = VirtualProtect(
        site, 5, old_protection, &ignored) != FALSE;
    if (!protection_restored) {
        if (write_attempted) {
            rollback_ok = false;
            __try {
                memcpy(site, expected, 5);
                rollback_ok = FlushInstructionCache(GetCurrentProcess(), site, 5) != FALSE &&
                (memcmp(site, expected, 5) == 0);
            } __except (EXCEPTION_EXECUTE_HANDLER) {
                rollback_ok = false;
            }
        }
        DWORD retry_ignored = 0;
        const bool retry_restored = VirtualProtect(
            site, 5, old_protection, &retry_ignored) != FALSE;
        Log("%s FAILED: protection restore failed; rollback=%s retry=%s",
            label,
            rollback_ok ? "verified" : "FAILED",
            retry_restored ? "restored" : "FAILED");
        return false;
    }

    if (!write_attempted) {
        Log("%s DISABLED: call changed before write", label);
        return false;
    }
    if (!wrote) {
        Log("%s FAILED: write/precondition failed; rollback=%s", label,
            rollback_ok ? "verified" : "FAILED");
        return false;
    }

    Log("%s APPLIED: call redirected at rva=0x%08X", label,
        static_cast<unsigned>(call_rva));
    return true;
}

static bool ApplyUseSkillValuePatch(uintptr_t eq_base, bool version_ok)
{
    if (!version_ok) {
        Log("G006 UseSkill value patch DISABLED: client version guard failed");
        return false;
    }
    return ApplyGuardedRelativeCall(
        eq_base,
        kUseSkillValueCallRva,
        kExpectedUseSkillValueCall,
        reinterpret_cast<uintptr_t>(&GetServerGrantedSkill),
        "G006 UseSkill value patch");
}

static bool ApplyHotButtonSkillPredicatePatch(
    uintptr_t eq_base, bool use_skill_ok)
{
    if (!use_skill_ok) {
        Log("G006 hotbutton skill patch DISABLED: UseSkill correction unavailable");
        return false;
    }
    return ApplyGuardedRelativeCall(
        eq_base,
        kHotButtonSkillPredicateCallRva,
        kExpectedHotButtonSkillPredicateCall,
        reinterpret_cast<uintptr_t>(&HasServerGrantedSkill),
        "G006 hotbutton skill patch");
}

static bool RestoreGuardedRelativeCall(
    uintptr_t eq_base,
    uintptr_t call_rva,
    const BYTE expected[5],
    uintptr_t target,
    const char* label)
{
    BYTE* site = reinterpret_cast<BYTE*>(eq_base + call_rva);
    BYTE replacement[5] = { 0xE8, 0, 0, 0, 0 };
    const intptr_t displacement =
        static_cast<intptr_t>(target) -
        reinterpret_cast<intptr_t>(site + sizeof(replacement));
    if (displacement < INT32_MIN || displacement > INT32_MAX) {
        Log("%s ROLLBACK FAILED: hook target is outside rel32 range", label);
        return false;
    }
    const int32_t relative32 = static_cast<int32_t>(displacement);
    memcpy(replacement + 1, &relative32, sizeof(relative32));

    bool replacement_present = false;
    __try {
        replacement_present = (memcmp(site, replacement, 5) == 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        replacement_present = false;
    }
    if (!replacement_present) {
        Log("%s ROLLBACK FAILED: patched call no longer matches", label);
        return false;
    }

    DWORD old_protection = 0;
    if (!VirtualProtect(site, 5, PAGE_EXECUTE_READWRITE, &old_protection)) {
        Log("%s ROLLBACK FAILED: VirtualProtect", label);
        return false;
    }

    bool restored = false;
    __try {
        if (memcmp(site, replacement, 5) == 0) {
            memcpy(site, expected, 5);
            const bool flushed = FlushInstructionCache(GetCurrentProcess(), site, 5) != FALSE;
            restored = flushed && (memcmp(site, expected, 5) == 0);
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        restored = false;
    }

    DWORD ignored = 0;
    const bool protection_restored = VirtualProtect(
        site, 5, old_protection, &ignored) != FALSE;
    Log("%s ROLLBACK: bytes=%s protection=%s", label,
        restored ? "restored" : "FAILED",
        protection_restored ? "restored" : "FAILED");
    return restored && protection_restored;
}

static bool ApplyMonkAttackActivationPatches(
    uintptr_t eq_base, bool hotbutton_skill_ok)
{
    if (!hotbutton_skill_ok) {
        Log("G006 Monk attack activation DISABLED: hotbutton skill correction unavailable");
        return false;
    }

    const bool predicate_ok = ApplyGuardedRelativeCall(
        eq_base,
        kSpecialAttackSkillPredicateCallRva,
        kExpectedSpecialAttackSkillPredicateCall,
        reinterpret_cast<uintptr_t>(&HasServerGrantedMonkAttack),
        "G006 special-attack skill predicate patch");
    if (!predicate_ok) {
        return false;
    }

    const bool activation_ok = ApplyGuardedRelativeCall(
        eq_base,
        kHotButtonSkillActivationCallRva,
        kExpectedHotButtonSkillActivationCall,
        reinterpret_cast<uintptr_t>(&ActivateServerGrantedSkill),
        "G006 Monk hotbutton activation patch");
    if (!activation_ok) {
        const bool rollback_ok = RestoreGuardedRelativeCall(
            eq_base,
            kSpecialAttackSkillPredicateCallRva,
            kExpectedSpecialAttackSkillPredicateCall,
            reinterpret_cast<uintptr_t>(&HasServerGrantedMonkAttack),
            "G006 special-attack skill predicate patch");
        Log("G006 Monk attack activation DISABLED: activation redirect failed; "
            "predicate rollback=%s", rollback_ok ? "verified" : "FAILED");
        return false;
    }

    Log("G006 Monk attack activation APPLIED: six held Monk attacks use the "
        "stock special-attack submitter");
    return true;
}

// The first redirect is neutral until the equip caller establishes an item
// scope. Every non-class predicate and the final stock result remain native.
extern "C" __declspec(noinline) uint32_t __fastcall EquipScopedItemClasses(
    void* item, void* unused_edx, bool flag1, bool flag2)
{
    (void)unused_edx;
    typedef uint32_t (__thiscall *ItemClassesFn)(void*, bool, bool);
    const auto original = reinterpret_cast<ItemClassesFn>(g_eq_base + kItemClassesRva);
    const uint32_t stock = original(item, flag1, flag2);
    if (item == nightcap::client_ui::ActiveSpellItem()) {
        return nightcap::client_ui::ScribeClassMask(stock,item,flag1,flag2);
    }
    return nightcap::EquipClassMask(stock, item, flag1, flag2);
}

extern "C" __declspec(noinline) BYTE __fastcall CanUseItemForEquip(
    void* character, void* unused_edx, const void* item_ref,
    bool use_required_level, bool output)
{
    (void)unused_edx;
    const void* item = nullptr;
    if (!character || !item_ref) return 0;
    __try {
        item = *reinterpret_cast<const void* const*>(item_ref);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 0;
    }
    if (!item) return 0;
    typedef BYTE (__thiscall *CanUseItemFn)(void*, const void*, bool, bool);
    const auto original = reinterpret_cast<CanUseItemFn>(g_eq_base + kCanUseItemRva);
    const void* previous = nightcap::SetActiveEquipItem(item);
    BYTE result = 0;
    __try {
        result = original(character, item_ref, use_required_level, output);
    } __finally {
        // Also restore nested scope on native SEH exceptions, not just C++ unwind.
        nightcap::SetActiveEquipItem(previous);
    }
    return result;
}

static bool ApplyEquipSubmissionPatches(uintptr_t eq_base, bool version_ok)
{
    if (!version_ok) {
        Log("G013 equip submission DISABLED: client version guard failed");
        return false;
    }
    __try {
        if (memcmp(reinterpret_cast<void*>(eq_base + kEquipCanUseItemCallRva), kExpectedEquipCanUseItemCall, 5) != 0 ||
            memcmp(reinterpret_cast<void*>(eq_base + kEquipClassMaskCallRva), kExpectedEquipClassMaskCall, 5) != 0 ||
            memcmp(reinterpret_cast<void*>(eq_base + kCanUseItemRva), kExpectedCanUseItemEntry, 7) != 0 ||
            memcmp(reinterpret_cast<void*>(eq_base + kItemClassesRva), kExpectedItemClassesEntry, 6) != 0) {
            Log("G013 equip submission DISABLED: complete pair/helper signature mismatch");
            return false;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        Log("G013 equip submission DISABLED: unreadable pair/helper signature");
        return false;
    }
    const bool accessor_ok = ApplyGuardedRelativeCall(
        eq_base, kEquipClassMaskCallRva, kExpectedEquipClassMaskCall,
        reinterpret_cast<uintptr_t>(&EquipScopedItemClasses), "G013 equip class accessor");
    if (!accessor_ok) return false;
    const bool caller_ok = ApplyGuardedRelativeCall(
        eq_base, kEquipCanUseItemCallRva, kExpectedEquipCanUseItemCall,
        reinterpret_cast<uintptr_t>(&CanUseItemForEquip), "G013 equip caller");
    if (!caller_ok) {
        const bool rollback_ok = RestoreGuardedRelativeCall(
            eq_base, kEquipClassMaskCallRva, kExpectedEquipClassMaskCall,
            reinterpret_cast<uintptr_t>(&EquipScopedItemClasses), "G013 equip class accessor");
        Log("G013 equip submission DISABLED: caller failed; accessor rollback=%s",
            rollback_ok ? "verified" : "FAILED");
        return false;
    }
    Log("G013 equip submission APPLIED: item/thread-scoped class check; native restrictions and server authorization retained");
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
    EnsureInitialized();
    for (size_t i = 0; i < 6; ++i) if (strcmp(name,kRealExportNames[i]) == 0) return g_real_exports[i];
    return nullptr;
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
    // Active hooks and the optional survey retain pointers into this module.
    return S_FALSE;
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

__declspec(noreturn) static void StopClient(const char* reason)
{
    InterlockedExchange(&g_initialize_state,-1);
    Log("REQUIRED STARTUP FAILURE: %s",reason);
    nightcap::WriteHealth(g_client_directory,g_health,"failed",reason);
    OutputDebugStringA("Nightcap required client initialization failed; see nightcap health/log files.\n");
    TerminateProcess(GetCurrentProcess(),0x4E430001);
    __fastfail(7); // A failed/redirected termination must never permit forwarding.
}

static void RequirePatch(size_t index, bool applied)
{
    if (!applied) StopClient(nightcap::kRequiredFeatures[index]);
    g_health.applied_mask |= uint32_t(1) << index;
}

static BOOL CALLBACK InitializeRuntime(PINIT_ONCE, PVOID, PVOID*)
{
    InterlockedExchange(&g_initialize_owner,static_cast<LONG>(GetCurrentThreadId()));
    // Pin before creating callbacks or writing a single hook. No dynamic unload.
    HMODULE self = nullptr;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,
            reinterpret_cast<LPCWSTR>(&InitializeRuntime),&self)) StopClient("module_pin");
    wchar_t module_path[MAX_PATH],exe_path[MAX_PATH];
    const DWORD module_length=GetModuleFileNameW(self,module_path,MAX_PATH);
    const DWORD exe_length=GetModuleFileNameW(nullptr,exe_path,MAX_PATH);
    if (!module_length||module_length>=MAX_PATH||!exe_length||exe_length>=MAX_PATH) StopClient("client_path");
    wchar_t* separator=wcsrchr(module_path,L'\\');
    const wchar_t* exe_separator=wcsrchr(exe_path,L'\\');
    if (!separator||!exe_separator) StopClient("client_path");
    const size_t directory_length=separator-module_path+1;
    if (directory_length!=static_cast<size_t>(exe_separator-exe_path+1) ||
        CompareStringOrdinal(module_path,static_cast<int>(directory_length),exe_path,static_cast<int>(directory_length),TRUE)!=CSTR_EQUAL) StopClient("proxy_location");
    wcsncpy_s(g_client_directory,module_path,directory_length);
    g_health.pid=GetCurrentProcessId();
    FILETIME created,exited,kernel,user;
    if (!GetProcessTimes(GetCurrentProcess(),&created,&exited,&kernel,&user)) StopClient("process_identity");
    g_health.process_created=(static_cast<unsigned long long>(created.dwHighDateTime)<<32)|created.dwLowDateTime;
    const DWORD nonce_size=GetEnvironmentVariableA("NIGHTCAP_LAUNCH_NONCE",g_health.nonce,sizeof(g_health.nonce));
    if (nonce_size && (nonce_size!=32 || !nightcap::IsLowerHex(g_health.nonce,32))) {g_health.nonce[0]=0;StopClient("launch_nonce");}
    wchar_t log_name[MAX_PATH];
    if (swprintf_s(log_name,L"%snightcap_dll_%lu_%llu.log",g_client_directory,g_health.pid,g_health.process_created)<0) StopClient("log_path");
    HANDLE log_file=CreateFileW(log_name,GENERIC_WRITE,FILE_SHARE_READ,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL|FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
    if (log_file==INVALID_HANDLE_VALUE) StopClient("log_open");
    const int log_fd=_open_osfhandle(reinterpret_cast<intptr_t>(log_file),_O_WRONLY|_O_TEXT);
    if (log_fd==-1) {CloseHandle(log_file);StopClient("log_open");}
    g_log=_fdopen(log_fd,"w");
    if (!g_log) {_close(log_fd);StopClient("log_open");}
    Log("Nightcap proxy %s initializing; pid=%lu",nightcap::kProxyVersion,g_health.pid);
    if (!nightcap::WriteHealth(g_client_directory,g_health,"initializing","")) StopClient("health_write");
    wchar_t config_path[MAX_PATH];
    if (swprintf_s(config_path,L"%snightcap-patches.cfg",g_client_directory)<0) StopClient("configuration_path");
    HANDLE config_file=CreateFileW(config_path,GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
    if (config_file==INVALID_HANDLE_VALUE) StopClient("configuration_open");
    BY_HANDLE_FILE_INFORMATION config_info;
    char bytes[4097];DWORD count=0;
    bool read_ok=GetFileInformationByHandle(config_file,&config_info)!=FALSE &&
        !(config_info.dwFileAttributes&(FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY)) &&
        config_info.nFileSizeHigh==0 && config_info.nFileSizeLow<=4096 &&
        ReadFile(config_file,bytes,sizeof(bytes),&count,nullptr)!=FALSE && count==config_info.nFileSizeLow;
    if (!CloseHandle(config_file)) read_ok=false;
    if (!read_ok) StopClient("configuration_read");
    if (!nightcap::DigestBytes(reinterpret_cast<BYTE*>(bytes),count,g_health.config_sha256)) StopClient("configuration_hash");
    const char* config_reason=nullptr;
    const bool config_ok=nightcap::ParseRuntimeConfig(bytes,count,g_config,config_reason);
    g_health.enabled_mask=g_config.enabled_mask;
    if (!config_ok) StopClient(config_reason);

    WIN32_FILE_ATTRIBUTE_DATA attributes;
    const bool size_ok=GetFileAttributesExW(exe_path,GetFileExInfoStandard,&attributes)!=FALSE &&
        attributes.nFileSizeHigh==0 && attributes.nFileSizeLow==kExpectedEqgameSize;
    const bool hash_ok=size_ok && VerifyFileSha256(exe_path,kExpectedEqgameSha256);
    if (!size_ok||!hash_ok) StopClient("unsupported_executable");
    uintptr_t eq_base,eq_size;
    GetModuleRange(GetModuleHandleW(nullptr),&eq_base,&eq_size);
    g_eq_base=eq_base;
    // Resolve every system export before any patch write or successful health.
    wchar_t system_path[MAX_PATH];
    const UINT system_length=GetSystemDirectoryW(system_path,MAX_PATH);
    if (!system_length||system_length>=MAX_PATH||wcscat_s(system_path,L"\\dinput8.dll")) StopClient("system_library_path");
    g_real_dinput8=LoadLibraryExW(system_path,nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!g_real_dinput8||g_real_dinput8==self) StopClient("system_library");
    for (size_t i=0;i<6;++i) {g_real_exports[i]=GetProcAddress(g_real_dinput8,kRealExportNames[i]);if(!g_real_exports[i])StopClient("system_export");}
    RequirePatch(nightcap::Feature_caster_chassis,ApplyCasterClassTablePatch(eq_base,size_ok && hash_ok));
    RequirePatch(nightcap::Feature_combat_ability_window,ApplyCombatAbilityClassTablePatch(eq_base,size_ok && hash_ok));
    RequirePatch(nightcap::Feature_actions_skills,ApplyActionsSkillPredicatePatch(eq_base,size_ok && hash_ok));
    const bool use_skill_ok=ApplyUseSkillValuePatch(eq_base,size_ok && hash_ok);
    RequirePatch(nightcap::Feature_skill_value,use_skill_ok);
    const bool hotbutton_skill_ok=ApplyHotButtonSkillPredicatePatch(eq_base,use_skill_ok);
    RequirePatch(nightcap::Feature_hotbutton_skills,hotbutton_skill_ok);
    RequirePatch(nightcap::Feature_monk_attacks,ApplyMonkAttackActivationPatches(eq_base,hotbutton_skill_ok));
    RequirePatch(nightcap::Feature_equipment,ApplyEquipSubmissionPatches(eq_base,size_ok && hash_ok));
    const bool mana_hook_ok=ApplyMaxManaServerCacheHook(eq_base,size_ok && hash_ok);
    RequirePatch(nightcap::Feature_mana_cache,mana_hook_ok);
    RequirePatch(nightcap::Feature_mana_gauge,ApplyPlayerManaGaugePredicateHook(eq_base,mana_hook_ok));
    const bool class_ui_ok = nightcap::client_ui::Install(eq_base);
    if (!class_ui_ok) Log("Class UI initialization failed at %s; image base=0x%08X", nightcap::client_ui::install_failure, static_cast<unsigned>(eq_base));
    RequirePatch(nightcap::Feature_class_ui,class_ui_ok && nightcap::client_ui::InstallTrainer());
    RequirePatch(nightcap::Feature_pet_armor,nightcap::client_ui::InstallPetArmor());
    RequirePatch(nightcap::Feature_merchant_sell_all,nightcap::client_ui::InstallMerchantSellAll());
    RequirePatch(nightcap::Feature_tradeskill_repeat,nightcap::client_ui::InstallTradeskillRepeat());
    const bool advanced_loot_ok = nightcap::client_ui::InstallAdvancedLoot([](const char* event) { Log("ADVLOOT %s", event); });
    if (!advanced_loot_ok) Log("Advanced loot initialization failed at %s", nightcap::client_ui::install_failure);
    RequirePatch(nightcap::Feature_advanced_loot,advanced_loot_ok);
    // Guard every accessor before installing any multiclass redirection.
    bool spell_access_ok = false;
    __try {
        spell_access_ok = !memcmp(reinterpret_cast<void*>(eq_base+kItemTypeRva), kExpectedItemType, sizeof(kExpectedItemType)) &&
            !memcmp(reinterpret_cast<void*>(eq_base+kItemSpellRva), kExpectedItemSpell, sizeof(kExpectedItemSpell));
    } __except(EXCEPTION_EXECUTE_HANDLER) { spell_access_ok = false; }
    if (spell_access_ok) {
        nightcap::client_ui::original_spell_level = reinterpret_cast<nightcap::client_ui::SpellLevel>(
            nightcap::client_ui::EntryHook(eq_base+kSpellLevelRva,kExpectedSpellLevel,
                reinterpret_cast<void*>(&nightcap::client_ui::SpellLevelHook)));
        spell_access_ok = nightcap::client_ui::original_spell_level &&
            ApplyGuardedRelativeCall(eq_base,kMerchantLevelMaskRva,kExpectedMerchantLevelMask,
                reinterpret_cast<uintptr_t>(&nightcap::client_ui::MerchantClassesHook),"Merchant spell class levels") &&
            ApplyGuardedRelativeCall(eq_base,kMerchantUsableMaskRva,kExpectedMerchantUsableMask,
                reinterpret_cast<uintptr_t>(&nightcap::client_ui::MerchantClassesHook),"Merchant usable classes") &&
            ApplyGuardedRelativeCall(eq_base,kScribeCanUseRva,kExpectedScribeCanUse,
                reinterpret_cast<uintptr_t>(&nightcap::client_ui::CanUseSpellItem),"Spellbook scribe classes") &&
            ApplyGuardedRelativeCall(eq_base,kScribeLevelRva,kExpectedScribeLevel,
                reinterpret_cast<uintptr_t>(&nightcap::client_ui::ScribeSpellLevelHook),"Spellbook early scribing") &&
            ApplyGuardedRelativeCall(eq_base,kScrollPlacementCanUseRva,kExpectedScrollPlacementCanUse,
                reinterpret_cast<uintptr_t>(&nightcap::client_ui::CanUseSpellItem),"Scroll inventory placement classes") &&
            ApplyGuardedRelativeCall(eq_base,kInspectionClassesRva,kExpectedInspectionClasses,
                reinterpret_cast<uintptr_t>(&nightcap::client_ui::InspectionClassesHook),"Scroll inspection classes") &&
            ApplyGuardedRelativeCall(eq_base,kInspectionLevelRva,kExpectedInspectionLevel,
                reinterpret_cast<uintptr_t>(&nightcap::client_ui::InspectionSpellLevelHook),"Scroll inspection class levels") &&
            ApplyGuardedRelativeCall(eq_base,kInspectionClasses2Rva,kExpectedInspectionClasses2,
                reinterpret_cast<uintptr_t>(&nightcap::client_ui::InspectionClassesHook),"Scroll inspection classes (second path)") &&
            ApplyGuardedRelativeCall(eq_base,kInspectionLevel2Rva,kExpectedInspectionLevel2,
                reinterpret_cast<uintptr_t>(&nightcap::client_ui::InspectionSpellLevelHook),"Scroll inspection class levels (second path)") &&
            nightcap::client_ui::InstallSpellMenu();
        if (spell_access_ok) Log("Spell selection menu refresh APPLIED: accepted class snapshots rebuild cached labels and ordering on the native frame");
    }
    RequirePatch(nightcap::Feature_multiclass_spell_access,spell_access_ok);
    nightcap::client_ui::skin_assign = reinterpret_cast<nightcap::client_ui::AssignString>(eq_base+kUIStringAssignRva);
    RequirePatch(nightcap::Feature_auto_ui,
        ApplyGuardedRelativeCall(eq_base,kUIExplicitSkinRva,kExpectedUIExplicitSkin,
            reinterpret_cast<uintptr_t>(&nightcap::client_ui::SkinHook),"Automatic UI explicit load") &&
        ApplyGuardedRelativeCall(eq_base,kUISavedSkinRva,kExpectedUISavedSkin,
            reinterpret_cast<uintptr_t>(&nightcap::client_ui::SkinHook),"Automatic UI saved load"));
    wchar_t preference_path[MAX_PATH] = {}, preference[32] = {};
    if (swprintf_s(preference_path,L"%seqclient.ini",g_client_directory)<0) StopClient("model_preference_path");
    GetPrivateProfileStringW(L"Nightcap",L"UseModernModels",L"",preference,_countof(preference),preference_path);
    nightcap::models::modern = !_wcsicmp(preference,L"TRUE") || !wcscmp(preference,L"1");
    for (const auto& asset : nightcap::models::kAssets) {
        wchar_t path[MAX_PATH] = {};
        WIN32_FILE_ATTRIBUTE_DATA info = {};
        if (swprintf_s(path,L"%s%s",g_client_directory,asset.name)<0 ||
            !GetFileAttributesExW(path,GetFileExInfoStandard,&info) || info.nFileSizeHigh ||
            info.nFileSizeLow != asset.size || !VerifyFileSha256(path,asset.sha256))
            StopClient("classic_model_assets");
    }
    RequirePatch(nightcap::Feature_classic_models,
        nightcap::models::Install(eq_base) &&
        ApplyGuardedRelativeCall(eq_base,kModelImportsCallRva,kExpectedModelImportsCall,
            reinterpret_cast<uintptr_t>(&nightcap::models::ImportsHook),"Classic model imports"));
    Log("Model policy: %s",nightcap::models::modern ? "modern INI opt-in" : "classic defaults");
    if (g_health.applied_mask!=nightcap::kRequiredMask) StopClient("incomplete_patches");
    if (g_config.mq2_survey) {
        const uintptr_t thread=_beginthreadex(nullptr,0,SurveyThread,nullptr,0,nullptr);
        g_health.mq2_survey=thread!=0;
        if(thread)CloseHandle(reinterpret_cast<HANDLE>(thread));
        else Log("Optional MQ2 survey disabled: thread creation failed");
    }
    if (!nightcap::WriteHealth(g_client_directory,g_health,"ready","")) StopClient("health_write");
    InterlockedExchange(&g_initialize_state,1);
    InterlockedExchange(&g_initialize_owner,0);
    return TRUE;
}

static void EnsureInitialized()
{
    if (static_cast<DWORD>(InterlockedCompareExchange(&g_initialize_owner,0,0))==GetCurrentThreadId()) StopClient("recursive_initialization");
    if (!InitOnceExecuteOnce(&g_initialize_once,InitializeRuntime,nullptr,nullptr) ||
        InterlockedCompareExchange(&g_initialize_state,0,0)!=1) StopClient("initialization_failed");
}

// The x86 bootstrap calls this only after the loader has completed and while
// the executable's original entrypoint is stopped. It never bypasses the same
// required guards used by DirectInput forwarding.
extern "C" DWORD WINAPI NightcapInitialize(void*)
{
    EnsureInitialized();
    return 0;
}

static unsigned __stdcall SurveyThread(void*)
{
    uintptr_t eq_base,eq_size;
    GetModuleRange(GetModuleHandleW(nullptr),&eq_base,&eq_size);
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

BOOL WINAPI DllMain(HINSTANCE, DWORD, LPVOID)
{
    // /MT and static TLS need CRT thread notifications. No loader-lock work,
    // worker startup, pinning, logging, waiting, or detach cleanup belongs here.
    return TRUE;
}

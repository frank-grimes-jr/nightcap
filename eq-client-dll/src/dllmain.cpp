// =============================================================================
// Nightcap dinput8.dll proxy — B2 caster-window correction (issue #12, ADR 0004)
//
// RoF2 auto-loads dinput8.dll from its own folder at startup. This proxy
// forwards every DirectInput export to the real system DLL and starts one
// init thread that applies two tightly guarded caster-window corrections. The
// MQ2 offset survey remains temporarily available for validation. Removing the
// DLL from the client folder fully restores stock behavior.
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

#pragma comment(lib, "bcrypt.lib")

// --- expected client build and B2 patch sites --------------------------------
// eqgame.exe, RoF2 May 10 2013 emu package, 8,774,656 bytes
// sha256 2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e
static const DWORD kExpectedEqgameSize = 8774656;
static const BYTE kExpectedEqgameSha256[32] = {
    0x2A, 0x87, 0x02, 0xAD, 0x9F, 0x72, 0x27, 0x04,
    0xF0, 0x13, 0x55, 0xC0, 0x75, 0x0B, 0xE7, 0xD6,
    0xF1, 0x64, 0xA8, 0xB9, 0xC9, 0x12, 0x8B, 0xA0,
    0xCF, 0x28, 0x6E, 0xA3, 0x2B, 0x40, 0x5B, 0x0E,
};

// Each signature is the call to the stock caster-class predicate, its result
// test, and the conditional branch that hides the window for WAR/MNK/ROG/BER.
// We replace only the final two-byte branch with NOPs. All other CanShow checks
// and every other consumer of the shared caster predicate remain stock.
struct WindowGatePatch {
    const char* name;
    uintptr_t signature_rva;
    BYTE expected[9];
};

static const WindowGatePatch kWindowGatePatches[] = {
    { "CastSpellWnd", 0x00248867, { 0xE8, 0xE4, 0xB6, 0xDF, 0xFF, 0x85, 0xC0, 0x74, 0xE7 } },
    { "SpellBookWnd", 0x0035C97F, { 0xE8, 0xCC, 0x75, 0xCE, 0xFF, 0x85, 0xC0, 0x74, 0x66 } },
};
static const BYTE kDisabledBranch[2] = { 0x90, 0x90 };

static HMODULE g_real_dinput8 = nullptr;
static FILE*   g_log          = nullptr;

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

enum PatchState {
    PATCH_EXPECTED,
    PATCH_ALREADY_APPLIED,
    PATCH_SIGNATURE_MISMATCH,
};

static PatchState GetPatchState(uintptr_t eq_base, const WindowGatePatch& patch)
{
    const BYTE* signature = reinterpret_cast<const BYTE*>(eq_base + patch.signature_rva);
    __try {
        if (memcmp(signature, patch.expected, sizeof(patch.expected)) == 0) {
            return PATCH_EXPECTED;
        }
        if (memcmp(signature, patch.expected, 7) == 0 &&
            memcmp(signature + 7, kDisabledBranch, sizeof(kDisabledBranch)) == 0) {
            return PATCH_ALREADY_APPLIED;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return PATCH_SIGNATURE_MISMATCH;
    }
    return PATCH_SIGNATURE_MISMATCH;
}

static bool WriteWindowGateBranch(
    uintptr_t eq_base, const WindowGatePatch& patch, const BYTE bytes[2])
{
    BYTE* branch = reinterpret_cast<BYTE*>(eq_base + patch.signature_rva + 7);
    DWORD old_protection = 0;
    if (!VirtualProtect(branch, 2, PAGE_EXECUTE_READWRITE, &old_protection)) {
        return false;
    }

    bool wrote = false;
    __try {
        memcpy(branch, bytes, 2);
        FlushInstructionCache(GetCurrentProcess(), branch, 2);
        wrote = (memcmp(branch, bytes, 2) == 0);
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        wrote = false;
    }

    DWORD ignored = 0;
    VirtualProtect(branch, 2, old_protection, &ignored);
    return wrote;
}

static bool ApplyCasterWindowGatePatches(uintptr_t eq_base, bool version_ok)
{
    if (!version_ok) {
        Log("B2 patch DISABLED: client version guard failed");
        return false;
    }

    PatchState states[sizeof(kWindowGatePatches) / sizeof(kWindowGatePatches[0])];
    bool changed[sizeof(kWindowGatePatches) / sizeof(kWindowGatePatches[0])] = {};

    for (size_t i = 0; i < sizeof(kWindowGatePatches) / sizeof(kWindowGatePatches[0]); ++i) {
        states[i] = GetPatchState(eq_base, kWindowGatePatches[i]);
        if (states[i] == PATCH_SIGNATURE_MISMATCH) {
            Log("B2 patch DISABLED: %s signature mismatch at rva=0x%08X",
                kWindowGatePatches[i].name,
                static_cast<unsigned>(kWindowGatePatches[i].signature_rva));
            return false;
        }
    }

    for (size_t i = 0; i < sizeof(kWindowGatePatches) / sizeof(kWindowGatePatches[0]); ++i) {
        if (states[i] == PATCH_ALREADY_APPLIED) {
            Log("B2 patch site already active: %s", kWindowGatePatches[i].name);
            continue;
        }
        if (!WriteWindowGateBranch(eq_base, kWindowGatePatches[i], kDisabledBranch)) {
            Log("B2 patch FAILED while writing %s; rolling back this load",
                kWindowGatePatches[i].name);
            for (size_t rollback = 0; rollback < i; ++rollback) {
                if (changed[rollback]) {
                    WriteWindowGateBranch(
                        eq_base, kWindowGatePatches[rollback],
                        kWindowGatePatches[rollback].expected + 7);
                }
            }
            return false;
        }
        changed[i] = true;
    }

    Log("B2 patch APPLIED: CastSpellWnd and SpellBookWnd class gates disabled "
        "(4 bytes; remaining CanShow checks preserved)");
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
    }
}

static DWORD WINAPI InitThread(LPVOID)
{
    const DWORD pid = GetCurrentProcessId();
    char log_name[MAX_PATH];
    sprintf_s(log_name, "nightcap_dll_%lu.log", pid);
    if (fopen_s(&g_log, log_name, "w") != 0 || !g_log) {
        return 0;
    }
    Log("Nightcap proxy loaded (B2 caster-window correction + offset survey)");
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
    bool hash_ok = size_ok && VerifyEqgameSha256(exe_path);
    Log("client sha256 check: %s", hash_ok ? "OK" : "MISMATCH OR UNREADABLE");
    ApplyCasterWindowGatePatches(eq_base, size_ok && hash_ok);

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

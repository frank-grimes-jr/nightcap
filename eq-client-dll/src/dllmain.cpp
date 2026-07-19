// =============================================================================
// Nightcap dinput8.dll proxy — B1 skeleton (issue #12, ADR 0004)
//
// RoF2 auto-loads dinput8.dll from its own folder at startup. This proxy
// forwards every DirectInput export to the real system DLL and starts one
// init thread that only writes a log file — no game memory is touched yet
// (that's B2). Removing the DLL from the client folder fully restores stock
// behavior.
//
// Build: x86 ONLY (RoF2 is a 32-bit client) — see build.bat.
// =============================================================================

#include <windows.h>
#include <tlhelp32.h>
#include <cstdio>
#include <cstdint>

// --- expected client build (version guard scaffolding for B3) ---------------
// eqgame.exe, RoF2 May 10 2013 emu package, 8,774,656 bytes
// sha256 2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e
static const DWORD kExpectedEqgameSize = 8774656;

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

static void SurveyMq2Exports(HMODULE mq2, uintptr_t eq_base, uintptr_t eq_size)
{
    uintptr_t mq_base, mq_size;
    GetModuleRange(mq2, &mq_base, &mq_size);

    auto dos = (IMAGE_DOS_HEADER*)mq2;
    auto nt  = (IMAGE_NT_HEADERS*)(mq_base + dos->e_lfanew);
    DWORD exp_rva = nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT].VirtualAddress;
    if (!exp_rva) { Log("survey: MQ2Main has no export directory?"); return; }

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
}

static void PollWatchlist(HMODULE mq2)
{
    for (const char* name : kWatchlist) {
        auto var = (DWORD*)GetProcAddress(mq2, name);
        if (!var) { Log("watch: %s (not exported)", name); continue; }
        DWORD slot_va;
        if (!GuardedReadDword(var, &slot_va)) continue;
        DWORD instance = 0;
        bool ok = GuardedReadDword((void*)(uintptr_t)slot_va, &instance);
        Log("watch: %s slot=0x%08X instance=%s0x%08X", name, slot_va, ok ? "" : "<unreadable> ", instance);
    }
}

static DWORD WINAPI InitThread(LPVOID)
{
    fopen_s(&g_log, "nightcap_dll.log", "w");
    Log("Nightcap proxy loaded (B2 offset survey build, no patches active)");

    char exe_path[MAX_PATH];
    GetModuleFileNameA(nullptr, exe_path, MAX_PATH);
    Log("host process: %s", exe_path);

    // version guard scaffolding: warn (do not patch) on unexpected client size
    WIN32_FILE_ATTRIBUTE_DATA fad;
    bool size_ok = false;
    if (GetFileAttributesExA(exe_path, GetFileExInfoStandard, &fad)) {
        size_ok = (fad.nFileSizeLow == kExpectedEqgameSize && fad.nFileSizeHigh == 0);
        Log("client size check: %s (%lu bytes)", size_ok ? "OK" : "MISMATCH - survey only, never patch",
            fad.nFileSizeLow);
    }

    uintptr_t eq_base, eq_size;
    GetModuleRange(GetModuleHandleA(nullptr), &eq_base, &eq_size);

    // Wait for MQ2 (user launches MacroQuest2.exe as usual); survey once, then
    // poll the watchlist so the HITL session captures instance lifecycles
    // (login caster -> windows non-null; camp to melee -> created or null?).
    HMODULE mq2 = nullptr;
    const DWORD start_tick = GetTickCount();
    const DWORD deadline   = start_tick + 300000;    // wait up to 5 min for MQ2
    bool dumped_early = false;
    while (!mq2 && GetTickCount() < deadline) {
        mq2 = FindMq2();
        if (mq2) break;
        DWORD elapsed = GetTickCount() - start_tick;
        if (!dumped_early && elapsed >= 8000) { DumpModules("early, MQ2 not yet seen"); dumped_early = true; }
        Log("waiting for MQ2... elapsed %lus", elapsed / 1000);
        Sleep(5000);
    }
    if (!mq2) {
        DumpModules("final, MQ2 never appeared");
        Log("MQ2 not found after %lus (scanned loader list + raw memory). If MQ2 was "
            "actually active in-game this session, it's memory-mapped in a way the scan "
            "missed; tell me and I'll widen it. Otherwise MQ2 wasn't injected into this "
            "eqgame process.", (GetTickCount() - start_tick) / 1000);
        return 0;
    }
    Log("MQ2 found at base=0x%08X after %lus", (unsigned)(uintptr_t)mq2, (GetTickCount() - start_tick) / 1000);
    Sleep(5000); // let MQ2 finish its own offset init
    SurveyMq2Exports(mq2, eq_base, eq_size);

    for (int i = 0; i < 60; i++) {                   // 15 min of lifecycle polling
        PollWatchlist(mq2);
        Sleep(15000);
    }
    Log("survey session complete");
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

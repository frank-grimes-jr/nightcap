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

// --- init thread -------------------------------------------------------------
// B1: log-only. B2 will apply the UI-unlock patches here, after the version
// guard passes.

static DWORD WINAPI InitThread(LPVOID)
{
    fopen_s(&g_log, "nightcap_dll.log", "w");
    Log("Nightcap proxy loaded (B1 skeleton, no patches active)");

    char exe_path[MAX_PATH];
    GetModuleFileNameA(nullptr, exe_path, MAX_PATH);
    Log("host process: %s", exe_path);

    // version guard scaffolding: warn (do not patch) on unexpected client size
    WIN32_FILE_ATTRIBUTE_DATA fad;
    if (GetFileAttributesExA(exe_path, GetFileExInfoStandard, &fad)) {
        if (fad.nFileSizeLow == kExpectedEqgameSize && fad.nFileSizeHigh == 0) {
            Log("client size check: OK (%lu bytes)", fad.nFileSizeLow);
        } else {
            Log("client size check: MISMATCH (%lu bytes, expected %lu) - refusing to patch",
                fad.nFileSizeLow, kExpectedEqgameSize);
        }
    }

    Log("init complete");
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

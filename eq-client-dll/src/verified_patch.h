#pragma once
#include <windows.h>
#include <cstring>

namespace nightcap {
// Internal single-site writer. Caller must stop startup on false; no partially
// applied generation may continue. Never adopt a patch left by another module.
inline bool WriteVerifiedPatch(BYTE* site, const BYTE* original,
    const BYTE* replacement, size_t size,
    decltype(&VirtualProtect) protect = &VirtualProtect,
    decltype(&FlushInstructionCache) flush = &FlushInstructionCache)
{
    __try {
        if (memcmp(site, original, size) != 0) return false;
    } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
    DWORD previous = 0;
    if (!protect(site, size, PAGE_EXECUTE_READWRITE, &previous)) return false;
    bool attempted = false, okay = false;
    __try {
        if (memcmp(site, original, size) == 0) {
            attempted = true;
            memcpy(site, replacement, size);
            okay = flush(GetCurrentProcess(), site, size) != FALSE &&
                memcmp(site, replacement, size) == 0;
        }
    } __except (EXCEPTION_EXECUTE_HANDLER) { okay = false; }
    if (attempted && !okay) {
        __try {
            memcpy(site, original, size);
            flush(GetCurrentProcess(), site, size);
        } __except (EXCEPTION_EXECUTE_HANDLER) { /* caller terminates */ }
    }
    DWORD ignored = 0;
    if (!protect(site, size, previous, &ignored)) {
        if (attempted) {
            __try {
                memcpy(site, original, size);
                flush(GetCurrentProcess(), site, size);
            } __except (EXCEPTION_EXECUTE_HANDLER) { /* caller terminates */ }
        }
        protect(site, size, previous, &ignored);
        return false;
    }
    return okay;
}
}

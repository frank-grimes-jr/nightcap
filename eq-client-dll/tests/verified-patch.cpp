#include "../src/verified_patch.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>
static unsigned protect_calls, flush_calls, fail_protect;
static bool fail_flush, mutate;
static BOOL WINAPI Protect(void* address, SIZE_T size, DWORD desired, DWORD* previous) {
    ++protect_calls;
    if (protect_calls == fail_protect) return FALSE;
    const BOOL okay = VirtualProtect(address, size, desired, previous);
    if (okay && mutate && protect_calls == 1) *static_cast<BYTE*>(address) = 7;
    return okay;
}
static BOOL WINAPI Flush(HANDLE process, const void* address, SIZE_T size) {
    ++flush_calls;
    if (fail_flush) return FALSE;
    return FlushInstructionCache(process, address, size);
}
int main() {
    BYTE original[16] = {}, replacement[16];
    memset(replacement, 1, sizeof(replacement));
    unsigned cases = 0;
    for (size_t size : {size_t(5), size_t(6), size_t(16)}) {
        for (unsigned mode = 0; mode < 7; ++mode) {
            BYTE* site = static_cast<BYTE*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
            assert(site);
            memcpy(site,original,size);
            if (mode == 4) memcpy(site,replacement,size); // foreign patch
            DWORD ignored;
            assert(VirtualProtect(site,4096,mode == 6 ? PAGE_NOACCESS : PAGE_EXECUTE_READ,&ignored));
            protect_calls=flush_calls=0;
            fail_protect=mode == 1 ? 1 : mode == 2 ? 2 : 0;
            fail_flush=mode == 3;
            mutate=mode == 5;
            const bool okay=nightcap::WriteVerifiedPatch(site,original,replacement,size,Protect,Flush);
            assert(okay == (mode == 0));
            MEMORY_BASIC_INFORMATION info;
            assert(VirtualQuery(site,&info,sizeof(info)) == sizeof(info));
            assert(info.Protect == static_cast<DWORD>(mode == 6 ? PAGE_NOACCESS : PAGE_EXECUTE_READ));
            if (mode != 6) {
                if (mode == 5) assert(site[0] == 7); // precondition change preserved
                else assert(memcmp(site,mode == 0 || mode == 4 ? replacement : original,size) == 0);
            }
            if (mode == 1 || mode == 4 || mode == 5 || mode == 6) assert(flush_calls == 0);
            assert(VirtualFree(site,0,MEM_RELEASE));
            ++cases;
        }
    }
    printf("PASS: %u native patch write/failure cases\n",cases);
}

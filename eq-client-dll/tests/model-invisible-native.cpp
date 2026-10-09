#include <windows.h>
#include <wincrypt.h>
#include <fstream>
#include <iterator>
#include <vector>
#include <iostream>
#include "../src/patch_catalog.h"
#include "../src/ui_hooks.h"
#include "../src/model_hooks.h"
#pragma comment(lib, "advapi32.lib")

static void Check(bool okay, const char* message) {
    if (!okay) { std::cerr << "FAIL: " << message << "\n"; ExitProcess(1); }
}
// The native block reads the actor name through EBP. Only its two outgoing
// branches are replaced with boolean returns in a private executable buffer.
// No DLL initialization, renderer, imports or game process is executed.
__declspec(naked) static int NativeExclusion(void*, const char*) {
    __asm {
        push ebp
        mov ebp, dword ptr [esp+12]
        call dword ptr [esp+8]
        pop ebp
        ret
    }
}
static const char* captured;
static int __fastcall Capture(void*, void*, int, int, const char* code, int, int) {
    captured = code;
    return 1;
}
int main(int argc, char** argv) {
    Check(argc == 2, "usage: model-invisible-native EQGraphicsDX9.dll");
    std::ifstream input(argv[1], std::ios::binary);
    Check(bool(input), "open graphics input");
    std::vector<char> raw((std::istreambuf_iterator<char>(input)), {});
    HCRYPTPROV provider = 0; HCRYPTHASH hash = 0;
    Check(CryptAcquireContext(&provider, nullptr, nullptr, PROV_RSA_AES, CRYPT_VERIFYCONTEXT) != 0, "SHA provider");
    Check(CryptCreateHash(provider, CALG_SHA_256, 0, 0, &hash) != 0, "SHA create");
    Check(CryptHashData(hash, reinterpret_cast<const BYTE*>(raw.data()), static_cast<DWORD>(raw.size()), 0) != 0, "SHA data");
    BYTE digest[32]; DWORD length = sizeof(digest);
    Check(CryptGetHashParam(hash, HP_HASHVAL, digest, &length, 0) != 0, "SHA result");
    CryptDestroyHash(hash); CryptReleaseContext(provider, 0);
    const BYTE expected[] = {0xad,0xe5,0x56,0xb6,0x8e,0x98,0xf6,0xf3,0x9c,0x55,0x78,0xf7,0x04,0x31,0xe1,0x1c,
                            0x0b,0x9b,0xab,0xcc,0x15,0xb8,0x57,0x1e,0xb2,0x2c,0xf1,0xe2,0xb6,0x54,0x41,0x7e};
    Check(!memcmp(digest, expected, sizeof(expected)), "unsupported graphics hash");
    auto dos = reinterpret_cast<const IMAGE_DOS_HEADER*>(raw.data());
    auto nt = reinterpret_cast<const IMAGE_NT_HEADERS32*>(raw.data()+dos->e_lfanew);
    auto sections = IMAGE_FIRST_SECTION(nt);
    const DWORD rva = 0x44ea2, size = 0x1f, excluded = 0x44f76-rva;
    const BYTE* source = nullptr;
    for (unsigned i = 0; i < nt->FileHeader.NumberOfSections; ++i)
        if (rva >= sections[i].VirtualAddress && rva+size <= sections[i].VirtualAddress+sections[i].SizeOfRawData)
            source = reinterpret_cast<const BYTE*>(raw.data()+sections[i].PointerToRawData+rva-sections[i].VirtualAddress);
    Check(source != nullptr, "native prefix block");
    auto code = static_cast<BYTE*>(VirtualAlloc(nullptr, 4096, MEM_COMMIT|MEM_RESERVE, PAGE_EXECUTE_READWRITE));
    Check(code != nullptr, "native block allocation");
    memcpy(code, source, size);
    const BYTE no[] = {0x33,0xc0,0xc3};
    const BYTE yes[] = {0xb8,1,0,0,0,0xc3};
    memcpy(code+size, no, sizeof(no));
    memcpy(code+excluded, yes, sizeof(yes));
    FlushInstructionCache(GetCurrentProcess(), code, 4096);
    Check(NativeExclusion(code, "IVM_ACTORDEF") == 1, "native invisible male exclusion");
    Check(NativeExclusion(code, "IVF_ACTORDEF") == 1, "native invisible female exclusion");
    Check(NativeExclusion(code, "ZBB_ACTORDEF") == 0, "published alias reproduces bypassed native exclusion");
    Check(NativeExclusion(code, "ELM_ACTORDEF") == 0, "ordinary actor remains outside exclusion");
    using namespace nightcap::models;
    original_register = reinterpret_cast<RegisterActor>(&Capture);
    modern = false;
    RegisterHook(nullptr, nullptr, 127, 0, "IVM", 0, 1);
    Check(NativeExclusion(code, captured) == 1, "registered Enchanter pet must retain native invisible-actor exclusion");
    int race = 600, gender = 0;
    ClassicRace(race, gender);
    Check(race == 600 && gender == 0, "native invisible-man race 600 remains unchanged");
    RegisterHook(nullptr, nullptr, 22, 2, "BET", 0, 1);
    Check(!strcmp(captured, "ZEC"), "beetle alias and existing animation repair retained");
    modern = true;
    RegisterHook(nullptr, nullptr, 127, 0, "IVM", 0, 1);
    Check(NativeExclusion(code, captured) == 1, "modern mode keeps original invisible identity");
    VirtualFree(code, 0, MEM_RELEASE);
    std::cout << "PASS: native IVM/IVF exclusion; published alias regression; registered pet identity; remake and beetle preservation\n";
}

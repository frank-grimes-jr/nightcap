#include <windows.h>
#include <wincrypt.h>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
#include "../src/patch_catalog.h"
#include "../src/ui_hooks.h"
#pragma comment(lib, "advapi32.lib")

// Exercise the actual pinned right-click comparison, including its branch and
// register contract. Only its two exits are replaced with return sentinels; no
// graphics, networking, client entrypoint or imports run. The baseline define
// deliberately leaves the native primary-class gate intact for RED evidence.
static void Check(bool okay, const char* message) {
    if (!okay) { std::cerr << "FAIL: " << message << '\n'; ExitProcess(1); }
}
static BYTE* LoadClient(const char* path) {
    std::ifstream file(path, std::ios::binary);
    Check(bool(file), "open read-only exact client");
    std::vector<char> raw((std::istreambuf_iterator<char>(file)), {});
    Check(raw.size() == 8774656, "supported client size");
    HCRYPTPROV provider=0; HCRYPTHASH hash=0;
    Check(CryptAcquireContext(&provider,nullptr,nullptr,PROV_RSA_AES,CRYPT_VERIFYCONTEXT)!=0,"SHA provider");
    Check(CryptCreateHash(provider,CALG_SHA_256,0,0,&hash)!=0,"SHA create");
    Check(CryptHashData(hash,reinterpret_cast<const BYTE*>(raw.data()),static_cast<DWORD>(raw.size()),0)!=0,"SHA data");
    BYTE digest[32]; DWORD length=sizeof(digest);
    Check(CryptGetHashParam(hash,HP_HASHVAL,digest,&length,0)!=0,"SHA result");
    CryptDestroyHash(hash); CryptReleaseContext(provider,0);
    Check(!memcmp(digest,kExpectedEqgameSha256,sizeof(digest)),"supported client hash");
    auto dos=reinterpret_cast<IMAGE_DOS_HEADER*>(raw.data());
    auto nt=reinterpret_cast<IMAGE_NT_HEADERS32*>(raw.data()+dos->e_lfanew);
    auto image=static_cast<BYTE*>(VirtualAlloc(nullptr,nt->OptionalHeader.SizeOfImage,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    Check(image!=nullptr,"allocate native image");
    memcpy(image,raw.data(),nt->OptionalHeader.SizeOfHeaders);
    auto sec=IMAGE_FIRST_SECTION(nt);
    for(unsigned i=0;i<nt->FileHeader.NumberOfSections;++i)
        memcpy(image+sec[i].VirtualAddress,raw.data()+sec[i].PointerToRawData,sec[i].SizeOfRawData);
    // The comparison slice contains no absolute addresses or external calls.
    // Its internal relative rejection branch remains valid in this image.
    return image;
}
static bool Compare(BYTE* site, BYTE* profile, unsigned npc_class) {
    const DWORD expected_ecx=0x5A7C0000u|npc_class;
    DWORD result=0, after_ecx=0, after_edx=0, before_stack=0, after_stack=0;
    __asm {
        mov before_stack, esp
        mov eax, profile
        mov ecx, expected_ecx
        mov edx, 087654321h
        call site
        mov result, eax
        mov after_ecx, ecx
        mov after_edx, edx
        mov after_stack, esp
    }
    Check(before_stack==after_stack,"right-click stack balanced");
    Check(after_ecx==expected_ecx,"CL trainer class and ECX survive bridge");
    Check(after_edx==npc_class,"native movzx EDX,CL preserved");
    return result!=0;
}
static void SkillNativeABI(BYTE* image, BYTE* player) {
    using namespace nightcap::client_ui;
    using Cap=int (__thiscall*)(void*,void*,int,int,int,int,int,int);
    using Level=int (__thiscall*)(void*,int,int);
    // A synthetic skill definition and cap table feed the *real* native pure
    // accessors. This is deliberately not a replacement implementation of them.
    std::vector<BYTE> manager(0x180000,0), definition(0x200,0);
    constexpr int skill=26;
    *reinterpret_cast<void**>(manager.data()+skill*4)=definition.data();
    *reinterpret_cast<int*>(definition.data()+0x24+7*4)=30;
    *reinterpret_cast<int*>(manager.data()+0x190+((7*100+skill)*101+100)*4)=200;
    auto stock_cap=reinterpret_cast<Cap>(image+0x1BAEC0);
    auto stock_level=reinterpret_cast<Level>(image+0x1BAA20);
    Check(stock_cap(manager.data(),nullptr,100,3,skill,1,1,1)==0,"native Paladin lacks Monk skill cap");
    Check(stock_cap(manager.data(),nullptr,100,7,skill,1,1,1)==200,"native Monk skill cap fixture");
    Check(stock_level(manager.data(),3,3)==0,"unused skill absent");
    Check(stock_level(manager.data(),skill,3)==0,"native Paladin training level absent");
    Check(stock_level(manager.data(),skill,7)==30,"native Monk training level fixture");
#ifdef NIGHTCAP_TRAINER_BASELINE
    const auto cap=stock_cap;
    const auto level=stock_level;
#else
    const auto cap=reinterpret_cast<Cap>(&TrainerSkillCapHook);
    const auto level=reinterpret_cast<Level>(&TrainerSkillLevelHook);
#endif
    state.Clear();
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    Check(state.Consume("[NCUI1]S|1|19|22|0|7|3|1|7|Palwar"),"skill fixture identity");
    for(int repeat=0;repeat<1000;++repeat) {
        Check(cap(manager.data(),nullptr,100,3,skill,1,1,1)==200,"held Monk cap passes native trainer availability gate");
        Check(level(manager.data(),skill,3)==30,"held Monk minimum positive training level retained");
    }
    Check(level(manager.data(),skill,2)==0,"other queried class does not borrow held levels");
    Check(cap(manager.data(),nullptr,100,2,skill,1,1,1)==0,"other queried class does not borrow held caps");
    *reinterpret_cast<int*>(definition.data()+0x24+1*4)=5;
    *reinterpret_cast<int*>(manager.data()+0x190+((1*100+skill)*101+100)*4)=125;
    Check(level(manager.data(),skill,3)==5,"earliest positive held-class train level wins");
    Check(cap(manager.data(),nullptr,100,3,skill,1,1,1)==200,"largest held-class cap wins");
    Check(state.Consume("[NCUI1]S|2|19|22|0|7|3|1|0|Palwar"),"skill Monk release");
    Check(cap(manager.data(),nullptr,100,3,skill,1,1,1)==125,"released Monk cap no longer borrowed");
    *reinterpret_cast<uint32_t*>(player+0x148)=8;
    Check(level(manager.data(),skill,3)==0,"stale identity preserves native training level");
    Check(cap(manager.data(),nullptr,100,3,skill,1,1,1)==0,"stale identity preserves native cap");
}
int main(int argc,char** argv) {
    Check(argc==2,"usage: trainer-native eqgame.exe");
    using namespace nightcap::client_ui;
    BYTE* image=LoadClient(argv[1]);
    base=reinterpret_cast<uintptr_t>(image);
    const BYTE native[]={0x0f,0xb6,0x80,0x74,0x33,0,0,0x0f,0xb6,0xd1,0x83,0xc0,0x13,0x3b,0xc2,0x0f,0x85,0x7e,1,0,0};
    Check(!memcmp(image+0x1374AC,native,sizeof(native)),"pinned trainer comparison bytes");
    const BYTE accepted[]={0xb8,1,0,0,0,0xc3};
    const BYTE rejected[]={0x33,0xc0,0xc3};
    memcpy(image+0x1374C1,accepted,sizeof(accepted));
    memcpy(image+0x13763F,rejected,sizeof(rejected));
#ifndef NIGHTCAP_TRAINER_BASELINE
    // Implementation installs the guarded seven-byte class projection here.
    Check(InstallTrainer(),"install trainer hooks");
#endif
    alignas(4) BYTE eq[0x600]={},player[0x150]={},profile[0x3410]={};
    *reinterpret_cast<void**>(image+0xA67CCC)=eq;
    *reinterpret_cast<void**>(image+0x9D2630)=player;
    *reinterpret_cast<int*>(eq+0x5C8)=5;
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    memcpy(player+0xA4,"Palwar",7);
    profile[0x3374]=3;
    Check(state.Consume("[NCUI1]S|1|19|22|0|7|3|1|7|Palwar"),"Palwar identity fixture");
    Check(Compare(image+0x1374AC,profile,22),"Paladin primary trainer stays usable");
    Check(!Compare(image+0x1374AC,profile,21),"unheld Cleric trainer stays rejected");
    Check(Compare(image+0x1374AC,profile,26),"Palwar must reach Joren Monk training request");
    Check(Compare(image+0x1374AC,profile,20),"Palwar must reach held Warrior training request");
    Check(profile[0x3374]==3,"trainer projection never mutates primary class");
    Check(state.Consume("[NCUI1]S|2|19|22|0|7|3|1|0|Palwar"),"Monk release fixture");
    Check(!Compare(image+0x1374AC,profile,26),"released Monk trainer rejected");
    Check(state.Consume("[NCUI1]S|3|19|22|0|7|3|1|7|Palwar"),"Monk re-adoption fixture");
    *reinterpret_cast<uint32_t*>(player+0x148)=8;
    Check(!Compare(image+0x1374AC,profile,26),"stale identity cannot expose Monk trainer");
    Check(Compare(image+0x1374AC,profile,22),"stale metadata preserves native primary trainer");
    state.Clear();
    Check(!Compare(image+0x1374AC,profile,26),"missing metadata cannot expose Monk trainer");
    SkillNativeABI(image,player);
    VirtualFree(image,0,MEM_RELEASE);
    std::cout << "PASS: native trainer comparison, held/released classes, identity and ABI\n";
}

#include "../src/dllmain.cpp"
#include <wincrypt.h>
#include "../../server-mods/code/common/equipment_race_policy.h"
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
#pragma comment(lib, "advapi32.lib")

// Test the production hooks and pinned native CanUseItem/CanEquipItem and
// inspection color instructions in an isolated process. Never launch eqgame.
static unsigned failures=0, checks=0;
static void Check(bool okay,const char* message) {
    if (!okay) { std::cerr << "FIXTURE: " << message << '\n'; ExitProcess(2); }
}
static void Expect(bool okay,const char* message) {
    ++checks;
    if (!okay) { ++failures; std::cerr << "FAIL: " << message << '\n'; }
}
static BYTE* LoadClient(const char* path) {
    std::ifstream file(path,std::ios::binary);
    Check(bool(file),"open pinned client read-only");
    std::vector<char> raw((std::istreambuf_iterator<char>(file)),{});
    Check(raw.size()==kExpectedEqgameSize,"client size");
    HCRYPTPROV provider=0; HCRYPTHASH hash=0;
    Check(CryptAcquireContext(&provider,nullptr,nullptr,PROV_RSA_AES,CRYPT_VERIFYCONTEXT)!=0,"hash provider");
    Check(CryptCreateHash(provider,CALG_SHA_256,0,0,&hash)!=0,"hash create");
    Check(CryptHashData(hash,reinterpret_cast<const BYTE*>(raw.data()),static_cast<DWORD>(raw.size()),0)!=0,"hash data");
    BYTE digest[32]; DWORD length=sizeof(digest);
    Check(CryptGetHashParam(hash,HP_HASHVAL,digest,&length,0)!=0,"hash result");
    CryptDestroyHash(hash); CryptReleaseContext(provider,0);
    Check(!memcmp(digest,kExpectedEqgameSha256,32),"pinned client SHA256");
    auto dos=reinterpret_cast<IMAGE_DOS_HEADER*>(raw.data());
    auto nt=reinterpret_cast<IMAGE_NT_HEADERS32*>(raw.data()+dos->e_lfanew);
    auto image=static_cast<BYTE*>(VirtualAlloc(nullptr,nt->OptionalHeader.SizeOfImage,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    Check(image!=nullptr,"image allocation");
    memcpy(image,raw.data(),nt->OptionalHeader.SizeOfHeaders);
    auto sections=IMAGE_FIRST_SECTION(nt);
    for(unsigned i=0;i<nt->FileHeader.NumberOfSections;++i)
        memcpy(image+sections[i].VirtualAddress,raw.data()+sections[i].PointerToRawData,sections[i].SizeOfRawData);
    const auto reloc=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_BASERELOC];
    for(DWORD pos=reloc.VirtualAddress;pos<reloc.VirtualAddress+reloc.Size;) {
        auto block=reinterpret_cast<IMAGE_BASE_RELOCATION*>(image+pos);
        Check(block->SizeOfBlock>=8,"relocation block");
        auto entries=reinterpret_cast<WORD*>(block+1);
        for(unsigned i=0;i<(block->SizeOfBlock-8)/2;++i)
            if(entries[i]>>12==IMAGE_REL_BASED_HIGHLOW)
                *reinterpret_cast<DWORD*>(image+block->VirtualAddress+(entries[i]&4095)) +=
                    reinterpret_cast<DWORD>(image)-nt->OptionalHeader.ImageBase;
        pos+=block->SizeOfBlock;
    }
    return image;
}
static void Jump(BYTE* site,const void* target) {
    site[0]=0xe9;
    *reinterpret_cast<int32_t*>(site+1)=static_cast<int32_t>(reinterpret_cast<uintptr_t>(target)-reinterpret_cast<uintptr_t>(site+5));
}
static unsigned adjusted_calls=0;
static DWORD __fastcall Adjust(void*,void*,DWORD duration,int) {
    ++adjusted_calls;
    return duration/2;
}
static DWORD attack_clock=100000;
static bool submit_fault=false;
static BYTE __fastcall SubmitBoundary(void* player,void*,int,int skill,void*) {
    auto image=reinterpret_cast<BYTE*>(g_eq_base);
    using Index=int(__thiscall*)(void*,int);
    auto manager=*reinterpret_cast<void**>(image+0xA64610);
    const int index=reinterpret_cast<Index>(image+0x1ba2b0)(manager,skill);
    auto started=reinterpret_cast<DWORD*>(static_cast<BYTE*>(player)+0x390+index*4);
    auto duration=reinterpret_cast<DWORD*>(static_cast<BYTE*>(player)+0x368+index*4);
    if(submit_fault) RaiseException(0xe0000123,0,0,nullptr);
    if(attack_clock-*started<*duration/2) return 0;
    *started=attack_clock;
    *duration=10000;
    using Set=void(__thiscall*)(void*,int,DWORD);
    reinterpret_cast<Set>(image+0x1bacf0)(manager,skill,*duration);
    return 1;
}
static void SubmitWithFault(BYTE* image,void* player) {
    using Submit=BYTE(__thiscall*)(void*,int,int,void*);
    __try { reinterpret_cast<Submit>(image+0x1a5000)(player,100,21,nullptr); }
    __except(EXCEPTION_EXECUTE_HANDLER) {}
}
int main(int argc,char** argv) {
    Check(argc==2,"pass pinned eqgame path");
    BYTE* image=LoadClient(argv[1]);
    g_eq_base=reinterpret_cast<uintptr_t>(image);
    using namespace nightcap::client_ui;
    base=g_eq_base;
    alignas(4) BYTE eq[0x600]={},player[0x500]={},character[0x3000]={};
    std::vector<BYTE> manager(0x2c7000),records(100*32);
    *reinterpret_cast<void**>(image+0xA67CCC)=eq;
    *reinterpret_cast<void**>(image+0x9D2630)=player;
    *reinterpret_cast<void**>(image+0x9D261C)=character;
    *reinterpret_cast<void**>(character+0x2dd0)=player;
    *reinterpret_cast<void**>(image+0xA64610)=manager.data();
    *reinterpret_cast<int*>(eq+0x5C8)=5;
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    memcpy(player+0xA4,"Palwar",7);
    Check(state.Consume("[NCUI1]S|1|19|22|0|7|3|1|7|Palwar"),"held Monk identity");
    const int skills[]={21,23,26,30,38,52};
    for(int skill:skills) {
        *reinterpret_cast<void**>(manager.data()+skill*4)=records.data()+skill*32;
        *reinterpret_cast<int*>(records.data()+skill*32+0x14)=2;
    }
    using Set=void(__thiscall*)(void*,int,DWORD);
    using Get=DWORD(__thiscall*)(void*,int);
    using Ready=BYTE(__thiscall*)(void*,int);
    auto start=reinterpret_cast<Set>(image+0x1bac50);
    auto duration=reinterpret_cast<Set>(image+0x1bacf0);
    auto begin=reinterpret_cast<Set>(image+0x1bada0);
    auto get_start=reinterpret_cast<Get>(image+0x1baca0);
    auto get_duration=reinterpret_cast<Get>(image+0x1bad40);
    auto ready=reinterpret_cast<Ready>(image+0x1bae40);
#ifndef NIGHTCAP_MONK_REUSE_BASELINE
    Check(InstallMonkReuse(),"install guarded Monk reuse hooks");
    Check(ApplyMonkAttackActivationPatches(g_eq_base,true),"install all Monk activation call sites");
#endif
    Jump(image+0x1a2c20,&Adjust);
    for(int skill:skills) { duration(manager.data(),skill,1000+skill*2); start(manager.data(),skill,2000+skill); begin(manager.data(),skill,0); }
    for(int skill:skills) {
        Expect(get_start(manager.data(),skill)==static_cast<DWORD>(2000+skill),"separate native start timestamp");
        Expect(get_duration(manager.data(),skill)==static_cast<DWORD>(500+skill),"separate native duration with original haste adjustment");
        Expect(!ready(manager.data(),skill),"used skill remains cooling down");
    }
    begin(manager.data(),21,1);
    Expect(ready(manager.data(),21)!=0,"expired Dragon Punch becomes ready");
    Expect(!ready(manager.data(),38),"Dragon Punch expiry must not ready Round Kick");
    Expect(get_duration(manager.data(),38)==538,"Dragon Punch expiry must not clear Round Kick duration");
    Expect(adjusted_calls>=7,"native haste adjust called");
#ifndef NIGHTCAP_MONK_REUSE_BASELINE
    // The real submitter indexes two player fields. Scope exchanges only that
    // one slot, lets native code update it, and restores the unrelated group.
    *reinterpret_cast<DWORD*>(player+0x368)=777;
    *reinterpret_cast<DWORD*>(player+0x390)=888;
    for(int skill:skills) {
        MonkReuseScope scope={};
        BeginMonkReuseScope(scope,player,skill);
        const int index=skill==52?1:0;
        Expect(*reinterpret_cast<DWORD*>(player+0x390+index*4)==static_cast<DWORD>(2000+skill),"submit sees skill's own start");
        *reinterpret_cast<DWORD*>(player+0x390+index*4)=3000+skill;
        EndMonkReuseScope(scope);
        Expect(get_start(manager.data(),skill)==static_cast<DWORD>(3000+skill),"submit preserves skill's updated timestamp");
    }
    Expect(*reinterpret_cast<DWORD*>(player+0x368)==777 && *reinterpret_cast<DWORD*>(player+0x390)==888,"submit restores shared non-Monk timer");
    ResetMonkReuse();
    Expect(ready(manager.data(),38)!=0 && get_start(manager.data(),38)==0,"zone/character transition resets client display state");
    // Execute the installed native submitter entry and the redirected stock
    // caller commit, with only targeting/damage/time at a controlled boundary.
    original_combat_submit=reinterpret_cast<SubmitCombatAttack>(&SubmitBoundary);
    auto submit=reinterpret_cast<SubmitCombatAttack>(image+0x1a5000);
    auto native_commit=reinterpret_cast<Set>(image+0x5d971+*reinterpret_cast<int32_t*>(image+0x5d96d));
    for(int skill:skills) {
        Expect(submit(player,100,skill,nullptr)==1,"every native submission path has an independent slot");
        const int index=skill==52?1:0;
        native_commit(manager.data(),skill,*reinterpret_cast<DWORD*>(player+0x390+index*4));
        Expect(get_start(manager.data(),skill)==attack_clock,"stock post-submit must retain captured timestamp");
        Expect(submit(player,100,skill,nullptr)==0,"same native skill rejects before expiry");
    }
    Expect(*reinterpret_cast<DWORD*>(player+0x368)==777 && *reinterpret_cast<DWORD*>(player+0x390)==888,"native submitter restores unrelated shared fields");
    submit_fault=true;
    SubmitWithFault(image,player);
    submit_fault=false;
    Expect(*reinterpret_cast<DWORD*>(player+0x368)==777 && *reinterpret_cast<DWORD*>(player+0x390)==888,"native exception restores shared fields");
    attack_clock+=5001;
    Expect(submit(player,100,21,nullptr)==1,"native skill becomes usable after its own expiry");
#endif
    state.Clear();
    duration(manager.data(),21,900); start(manager.data(),21,1234); begin(manager.data(),21,0);
    Expect(get_start(manager.data(),38)==1234,"missing identity uses original native grouping");
    Expect(get_duration(manager.data(),38)==450,"missing identity preserves native adjustment");
    Check(state.Consume("[NCUI1]S|2|19|22|0|7|3|1|0|Palwar"),"non-Monk identity");
    Expect(get_start(manager.data(),38)==1234,"non-Monk uses original native grouping");
    VirtualFree(image,0,MEM_RELEASE);
    std::cout<<"native Monk reuse checks="<<checks<<" failures="<<failures<<'\n';
    return failures?1:0;
}

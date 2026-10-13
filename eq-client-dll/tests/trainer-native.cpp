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
    const auto relocation=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_BASERELOC];
    for(DWORD pos=relocation.VirtualAddress;pos<relocation.VirtualAddress+relocation.Size;) {
        auto block=reinterpret_cast<IMAGE_BASE_RELOCATION*>(image+pos);
        Check(block->SizeOfBlock>=8,"native relocation block");
        auto entries=reinterpret_cast<WORD*>(block+1);
        for(unsigned i=0;i<(block->SizeOfBlock-8)/2;++i)
            if(entries[i]>>12==IMAGE_REL_BASED_HIGHLOW)
                *reinterpret_cast<DWORD*>(image+block->VirtualAddress+(entries[i]&4095)) +=
                    reinterpret_cast<DWORD>(image)-nt->OptionalHeader.ImageBase;
        pos+=block->SizeOfBlock;
    }
    return image;
}
static BYTE* purchase_profile=nullptr;
static void* __fastcall PurchaseProfile(void*,void*) { return purchase_profile; }
static int __fastcall PurchaseLevel(void*,void*) { return 4; }
static int __fastcall NoBonus(void*,void*,int,int,int,int,int) { return 0; }
static int __fastcall TradeskillCap(void*,void*,void*,int,int,int,int,int,int) { return 250; }
static int __fastcall NoSkillBonus(void*,void*,int) { return 0; }
static void* __fastcall NoCharacter(void*,void*) { return nullptr; }
static void Jump(BYTE* site,const void* target) {
    site[0]=0xe9;
    *reinterpret_cast<int32_t*>(site+1)=static_cast<int32_t>(reinterpret_cast<uintptr_t>(target)-reinterpret_cast<uintptr_t>(site+5));
}
static void PurchaseCurrentCap(BYTE* image,BYTE* player) {
    using namespace nightcap::client_ui;
    // Native buy validator calls this predicate at 0x585955. It must reject
    // only current value >= the held-class cap at the character's CURRENT
    // level; the separate level-100 availability hook does not establish that.
    using AtCap=bool (__thiscall*)(void*,int);
    const auto call=image+0x185955;
    Check(call[0]==0xe8,"native purchase current-cap call");
    const auto at_cap=reinterpret_cast<AtCap>(call+5+*reinterpret_cast<int32_t*>(call+1));
    std::vector<BYTE> manager(0x180000,0), definition(0x200,0), character(0x3400,0), profile(0x3500,0);
    uintptr_t vtable[32]={};
    vtable[0x68/4]=reinterpret_cast<uintptr_t>(&PurchaseLevel);
    *reinterpret_cast<void**>(character.data()+8)=vtable;
    purchase_profile=profile.data();
    profile[0x3374]=3;
    *reinterpret_cast<void**>(image+0xA64610)=manager.data();
    Jump(image+0x3DB210,reinterpret_cast<void*>(&PurchaseProfile));
    Jump(image+0x38990,reinterpret_cast<void*>(&NoBonus));
    Check(FlushInstructionCache(GetCurrentProcess(),image,0x400000)!=0,"purchase fixture instruction cache");
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    state.Clear();
    Check(state.Consume("[NCUI1]S|1|19|22|0|7|3|1|7|Palwar"),"purchase Palwar identity");
    for(int skill : {22,30}) { // Dual Wield and Kick
        *reinterpret_cast<void**>(manager.data()+skill*4)=definition.data();
        definition[0x21]=1;
        *reinterpret_cast<int*>(profile.data()+0x30A0+skill*4)=1;
        *reinterpret_cast<int*>(manager.data()+0x190+((7*100+skill)*101+4)*4)=25;
        Check(!at_cap(character.data(),skill),"Palwar skill1 below held Monk level4 cap25 must allow trainer buy");
        Check(TrainerPurchaseCharacter()==nullptr,"purchase scope restored after native call");
        Check(reinterpret_cast<AtCap>(image+0x184E50)(character.data(),skill),"non-trainer native current-cap caller stays primary-only");
        *reinterpret_cast<int*>(profile.data()+0x30A0+skill*4)=25;
        Check(at_cap(character.data(),skill),"trainer still rejects value at effective current-level cap");
    }
    *reinterpret_cast<int*>(profile.data()+0x30A0+22*4)=1;
    Check(state.Consume("[NCUI1]S|2|19|22|0|7|3|1|0|Palwar"),"purchase released Monk");
    Check(at_cap(character.data(),22),"released skill cannot use former Monk cap");
    Check(state.Consume("[NCUI1]S|3|19|22|0|7|3|1|7|Palwar"),"purchase Monk restored");
    *reinterpret_cast<uint32_t*>(player+0x148)=8;
    Check(at_cap(character.data(),22),"stale purchase identity preserves primary cap");
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    // Native cross-tradeskill restrictions must still overrule a generous
    // held-class cap. Stub only that cap service; execute the native restriction.
    auto previous_cap=trainer_skill_cap;
    trainer_skill_cap=reinterpret_cast<TrainerSkillCap>(&TradeskillCap);
    *reinterpret_cast<void**>(manager.data()+60*4)=definition.data();
    definition[0x21]=0;
    *reinterpret_cast<int*>(profile.data()+0x30A0+60*4)=201;
    *reinterpret_cast<int*>(profile.data()+0x30A0+61*4)=201;
    Check(at_cap(character.data(),60),"native one-tradeskill-over200 restriction preserved");
    *reinterpret_cast<int*>(profile.data()+0x30A0+60*4)=199;
    Check(!at_cap(character.data(),60),"native restricted tradeskill still trainable below200");
    *reinterpret_cast<int*>(profile.data()+0x30A0+60*4)=201;
    *reinterpret_cast<int*>(profile.data()+0x30A0+61*4)=0;
    Check(!at_cap(character.data(),60),"native first tradeskill can use cap250");
    trainer_skill_cap=previous_cap;
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
static bool RunOffhand(BYTE* site,void* character) {
    DWORD result=0,before=0,after=0;
    __asm {
        push edi
        mov before,esp
        mov edi,character
        call site
        movzx eax,al
        mov result,eax
        mov after,esp
        pop edi
    }
    Check(before==after,"offhand native caller stack balance");
    return result!=0;
}
static void OffhandDualWield(BYTE* image,BYTE* player) {
    using namespace nightcap::client_ui;
    std::vector<BYTE> manager(0x180000,0),definition(0x200,0),character(0x3000,0),profile(0x3500,0);
    uintptr_t vtable[32]={};
    vtable[0x68/4]=reinterpret_cast<uintptr_t>(&PurchaseLevel);
    vtable[0x4c/4]=reinterpret_cast<uintptr_t>(&NoCharacter);
    void* zone=character.data()+0x2dc8;
    *reinterpret_cast<void**>(character.data()+0x2dc8+4)=vtable;
    purchase_profile=profile.data();
    profile[0x3374]=3;
    *reinterpret_cast<void**>(manager.data()+22*4)=definition.data();
    *reinterpret_cast<int*>(profile.data()+0x30a0+22*4)=1;
    *reinterpret_cast<int*>(definition.data()+0x24+7*4)=1;
    *reinterpret_cast<int*>(manager.data()+0x190+((7*100+22)*101+100)*4)=200;
    *reinterpret_cast<int*>(manager.data()+0x190+((7*100+22)*101+4)*4)=25;
    *reinterpret_cast<int*>(manager.data()+0x190+((1*100+22)*101+100)*4)=200;
    *reinterpret_cast<void**>(image+0xA64610)=manager.data();
    Jump(image+0x3DB210,reinterpret_cast<void*>(&PurchaseProfile));
    Jump(image+0x44BD0,reinterpret_cast<void*>(&NoSkillBonus));
    using Has=bool (__thiscall*)(void*,int);
    using Base=int (__thiscall*)(void*,int,int);
    Check(reinterpret_cast<Base>(image+0x49C80)(zone,22,0)==1,"native raw Dual Wield is1");
    Check(!reinterpret_cast<Has>(image+0x4A1B0)(zone,22),"native primary-only HasSkill hides raw Dual Wield");
    const BYTE accepted[]={0xb0,1,0xc3},rejected[]={0x32,0xc0,0xc3};
    memcpy(image+0x183452,accepted,sizeof(accepted));
    memcpy(image+0x18350A,rejected,sizeof(rejected));
    Check(FlushInstructionCache(GetCurrentProcess(),image,0x400000)!=0,"offhand fixture instruction cache");
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    state.Clear();
    Check(state.Consume("[NCUI1]S|1|19|22|0|7|3|1|7|Palwar"),"offhand Palwar identity");
    Check(RunOffhand(image+0x18343D,character.data()),"offhand weapon must pass with server-granted Dual Wield1");
    *reinterpret_cast<int*>(profile.data()+0x30a0+22*4)=0;
    Check(!RunOffhand(image+0x18343D,character.data()),"offhand weapon rejected without server Dual Wield");
    *reinterpret_cast<int*>(profile.data()+0x30a0+22*4)=1;
    Check(state.Consume("[NCUI1]S|2|19|22|0|7|3|1|0|Palwar"),"offhand released Monk");
    Check(!RunOffhand(image+0x18343D,character.data()),"released Monk cannot borrow future Warrior cap for stale raw Dual Wield");
    Check(state.Consume("[NCUI1]S|3|19|22|0|7|3|1|7|Palwar"),"offhand Monk restored");
    *reinterpret_cast<uint32_t*>(player+0x148)=8;
    Check(!RunOffhand(image+0x18343D,character.data()),"offhand stale identity fails closed");
    state.Clear();
    Check(!RunOffhand(image+0x18343D,character.data()),"offhand missing identity fails closed");
    profile[0x3374]=7;
    Check(RunOffhand(image+0x18343D,character.data()),"stock Monk offhand allowed without multiclass metadata");
}
int main(int argc,char** argv) {
    Check(argc==2||(argc==3&&!strcmp(argv[2],"--offhand-only")),"usage: trainer-native eqgame.exe [--offhand-only]");
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
    if(argc!=3) PurchaseCurrentCap(image,player);
    OffhandDualWield(image,player);
    VirtualFree(image,0,MEM_RELEASE);
    std::cout << "PASS: native trainer comparison, held/released classes, identity and ABI\n";
}

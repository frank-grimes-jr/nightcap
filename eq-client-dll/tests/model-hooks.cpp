#include <windows.h>
#include <cassert>
#include <iostream>
#include "../src/patch_catalog.h"
#include "../src/ui_hooks.h"
#include "../src/model_hooks.h"

static const char* captured_code;
static int captured_race, captured_gender, captured_a, captured_b;
static int __fastcall RegisterCapture(void*, void*, int race, int gender, const char* code, int a, int b) {
    captured_code=code; captured_race=race; captured_gender=gender; captured_a=a; captured_b=b;
    return 123;
}
static const char* captured_import;
static void __fastcall ImportCapture(void*,void*,const char* name) { captured_import=name; }

int main() {
    using namespace nightcap::models;
    auto memory=static_cast<BYTE*>(VirtualAlloc(nullptr,0x470000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    assert(memory);
    // Execute real x86 trampolines at a nonpreferred base. Fixture tails balance
    // the exact stolen prologues and preserve each native stack-pop contract.
    memcpy(memory+kModelProfileRva,kExpectedModelProfile,sizeof(kExpectedModelProfile));
    const BYTE profile_tail[]={0x5e,0xb8,0x7b,0,0,0,0xc3};
    memcpy(memory+kModelProfileRva+5,profile_tail,sizeof(profile_tail));
    memcpy(memory+kModelRegisterRva,kExpectedModelRegister,sizeof(kExpectedModelRegister));
    const BYTE register_tail[]={0x83,0xc4,4,0x5e,0x5d,0x5b,0xb8,0x7b,0,0,0,0xc2,0x14,0};
    memcpy(memory+kModelRegisterRva+5,register_tail,sizeof(register_tail));
    memcpy(memory+kModelTagRva,kExpectedModelTag,sizeof(kExpectedModelTag));
    const BYTE tag_tail[]={0x89,0x19,0x8b,0x44,0x24,0x10,0x89,0x41,4,0x5b,0xc2,0x0c,0};
    memcpy(memory+kModelTagRva+5,tag_tail,sizeof(tag_tail));
    memcpy(memory+kModelAnimationRva,kExpectedModelAnimation,sizeof(kExpectedModelAnimation));
    const BYTE animation_tail[]={0x5e,0x5b,0xb0,1,0xc2,0x0c,0};
    memcpy(memory+kModelAnimationRva+6,animation_tail,sizeof(animation_tail));
    assert(Install(reinterpret_cast<uintptr_t>(memory)));
    const auto profile=reinterpret_cast<ProfileString>(memory+kModelProfileRva);
    const auto registration=reinterpret_cast<RegisterActor>(memory+kModelRegisterRva);
    const auto lookup=reinterpret_cast<ActorTag>(memory+kModelTagRva);
    char output[16]={}; int seen[2]={};
    for(int i=0;i<1000;++i) {
        modern=false;
        assert(profile("Defaults","UseLuclinElementals","TRUE",output,sizeof(output),"eqclient.ini")==5);
        assert(!strcmp(output,"FALSE"));
        assert(profile("Defaults","WindowedMode","TRUE",output,sizeof(output),"eqclient.ini")==123);
        assert(registration(seen,60,2,"SKE",7,9)==123);
        lookup(seen,output,484,0); assert(seen[0]==60 && seen[1]==2);
        lookup(seen,output,606,1); assert(seen[0]==161 && seen[1]==2);
        lookup(seen,output,485,2); assert(seen[0]==85 && seen[1]==2);
        lookup(seen,output,566,1); assert(seen[0]==1 && seen[1]==1);
        lookup(seen,output,624,2); assert(seen[0]==10 && seen[1]==0);
        lookup(seen,output,678,0); assert(seen[0]==3 && seen[1]==0);
        lookup(seen,output,481,2); assert(seen[0]==42 && seen[1]==1);
        modern=true;
        assert(profile("Defaults","UseLuclinElementals","TRUE",output,sizeof(output),"eqclient.ini")==123);
        lookup(seen,output,484,0); assert(seen[0]==484 && seen[1]==0);
        lookup(seen,output,566,1); assert(seen[0]==566 && seen[1]==1);
        lookup(seen,output,481,2); assert(seen[0]==481 && seen[1]==2);
    }
    original_register=reinterpret_cast<RegisterActor>(&RegisterCapture);
    original_imports=reinterpret_cast<LoadImports>(&ImportCapture);
    modern=false;
    for(const auto& entry:kRegistrations) {
        assert(RegisterHook(seen,nullptr,entry.race,entry.gender,entry.original,7,9)==123);
        assert(!strcmp(captured_code,entry.alias));
        assert(captured_race==entry.race && captured_gender==entry.gender && captured_a==7 && captured_b==9);
    }
    for(const auto& entry:kRemakes) for(int sex=0;sex<3;++sex) {
        int race=entry.race,gender=sex; ClassicRace(race,gender);
        assert(race==entry.original && (Registered(race,gender) || (ClassicPlayerRace(race) && (gender==0 || gender==1))));
        if (entry.gender >= 0) assert(gender==entry.gender);
    }
    ImportsHook(seen,nullptr,"Resources\\GlobalLoad_chr.txt"); assert(!strcmp(captured_import,"nightcap_models_chr.txt"));
    modern=true;
    RegisterHook(seen,nullptr,60,2,"SKE",7,9); assert(!strcmp(captured_code,"SKE"));
    ImportsHook(seen,nullptr,"Resources\\GlobalLoad_chr.txt"); assert(!strcmp(captured_import,"Resources\\GlobalLoad_chr.txt"));
    // No silent trampoline installation over unexpected original instructions.
    memory[kModelProfileRva]=0xcc;
    assert(!Install(reinterpret_cast<uintptr_t>(memory)));
    VirtualFree(memory,0,MEM_RELEASE);
    std::cout << "PASS: x86 model hooks, rebase, classic mapping, opt-in and guarded failure\n";
}

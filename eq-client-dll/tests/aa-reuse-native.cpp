// Execute pinned RoF2 AA packet/store/readiness routines in a separate process.
// Never launches or writes eqgame. Only focus, clock and UI refresh are boundaries.
// Default verifies the native contract and safe 0..99 slot projection. Pass
// --reproduce to assert unrelated families sharing raw slot 1 stay ready: RED.
#define NOMINMAX
#include <windows.h>
#include <wincrypt.h>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
#include "../src/patch_catalog.h"
#include "../../server-mods/code/common/quick_buff.h"
#pragma comment(lib,"advapi32.lib")

static unsigned checks=0,failures=0;
static void Check(bool ok,const char* message) {
    if(!ok){std::cerr<<"FIXTURE: "<<message<<'\n';ExitProcess(2);}
}
static void Expect(bool ok,const char* message) {
    ++checks;if(!ok){++failures;std::cerr<<"FAIL: "<<message<<'\n';}
}
static BYTE* LoadClient(const char* path) {
    std::ifstream file(path,std::ios::binary);
    Check(bool(file),"open pinned client read-only");
    std::vector<char> raw((std::istreambuf_iterator<char>(file)),{});
    Check(raw.size()==kExpectedEqgameSize,"pinned client size");
    HCRYPTPROV provider=0;HCRYPTHASH hash=0;
    Check(CryptAcquireContext(&provider,nullptr,nullptr,PROV_RSA_AES,CRYPT_VERIFYCONTEXT)!=0,"hash provider");
    Check(CryptCreateHash(provider,CALG_SHA_256,0,0,&hash)!=0,"hash create");
    Check(CryptHashData(hash,reinterpret_cast<const BYTE*>(raw.data()),static_cast<DWORD>(raw.size()),0)!=0,"hash data");
    BYTE digest[32];DWORD length=sizeof(digest);
    Check(CryptGetHashParam(hash,HP_HASHVAL,digest,&length,0)!=0,"hash result");
    CryptDestroyHash(hash);CryptReleaseContext(provider,0);
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
static int native_clock=1000000,focus_reduction=0;
static int __cdecl Clock() {return native_clock;}
static int __fastcall Focus(void*,void*,int,int,int,int,int) {return focus_reduction;}
using Get=int(__thiscall*)(void*,int);
using Set=void(__thiscall*)(void*,int,int);
using Ready=BYTE(__thiscall*)(void*,void*,void*,int*,int*);
using HasTimers=BYTE(__thiscall*)(void*,BYTE);
using Calculated=int(__thiscall*)(void*,void*,void*);
struct Packet {int begin,ability,end;};
// Execute the pinned Make Hotkey positive-reuse predicate. Rank lookup and
// ownership are established before this slice in the native window routine.
static int __declspec(naked) __cdecl HotkeyReuseGate(void*,void*) {
    __asm {
        push ebx
        mov eax,[esp+12]
        xor ebx,ebx
        call dword ptr [esp+8]
        pop ebx
        ret
    }
}
using Receive=void(__cdecl*)(const Packet*);
static DWORD GetterException(Get get,void* character,int id) {
    __try {get(character,id);return 0;}
    __except(EXCEPTION_EXECUTE_HANDLER){return GetExceptionCode();}
}
static DWORD SetterException(Set set,void* character,int id,int value) {
    __try {set(character,id,value);return 0;}
    __except(EXCEPTION_EXECUTE_HANDLER){return GetExceptionCode();}
}
static DWORD ReadyException(Ready ready,void* manager,void* character,void* ability) {
    __try {ready(manager,character,ability,nullptr,nullptr);return 0;}
    __except(EXCEPTION_EXECUTE_HANDLER){return GetExceptionCode();}
}
static void Group(BYTE* ability,int* groups,int count,int reuse,int id) {
    *reinterpret_cast<int*>(ability+0x20)=id;
    *reinterpret_cast<int*>(ability+0x54)=count;
    *reinterpret_cast<int**>(ability+0x58)=groups;
    *reinterpret_cast<int*>(ability+0x64)=reuse;
}
int main(int argc,char** argv) {
    Check(argc==2 || argc==3,"pass pinned eqgame path and optional --reproduce");
    const bool reproduce=argc==3 && strcmp(argv[2],"--reproduce")==0;
    BYTE* image=LoadClient(argv[1]);
    Jump(image+0x408b50,&Clock);
    Jump(image+0x038990,&Focus);
    alignas(4) BYTE character[0x3000]={},profile[0x7000]={},manager[4]={};
    alignas(4) BYTE first[0x100]={},second[0x100]={};
    DWORD vbtable[2]={0,0};
    DWORD node[4]={7,reinterpret_cast<DWORD>(profile),0,0};
    *reinterpret_cast<DWORD**>(character+8)=vbtable;
    *reinterpret_cast<DWORD**>(character+12)=node;
    *reinterpret_cast<DWORD*>(character+16)=7;
    *reinterpret_cast<void**>(image+0x9d261c)=character;
    *reinterpret_cast<void**>(image+0x91fc20)=nullptr; // No live AA window.
    auto get=reinterpret_cast<Get>(image+0x3c46c0);
    auto set=reinterpret_cast<Set>(image+0x3c46f0);
    auto ready=reinterpret_cast<Ready>(image+0x0a3880);
    auto has=reinterpret_cast<HasTimers>(image+0x0a2100);
    auto calculated=reinterpret_cast<Calculated>(image+0x0a3840);
    auto receive=reinterpret_cast<Receive>(image+0x0b5bd0);
    auto send=[&](int slot,int begin,int server_now){Packet packet{begin,slot,server_now};receive(&packet);};
    int raw_group=1,independent_group=2,remaining=-1,total=-1;
    // Captured rank258 Rampage:600s; rank233 Purify Body:1800s; both raw group1.
    Group(first,&raw_group,1,600,258);Group(second,&raw_group,1,1800,233);
    Expect(ready(manager,character,first,&remaining,&total)!=0,"unused AA is ready");
    send(1,2000000,2000000);
    Expect(get(character,1)==native_clock,"AA packet translates server start to native clock");
    Expect(!ready(manager,character,first,&remaining,&total) && remaining==600 && total==600,"used AA retains own duration");
    const bool second_ready=ready(manager,character,second,&remaining,&total)!=0;
    Expect(!second_ready && remaining==1800,"baseline raw shared group blocks the other AA");
    if(reproduce)Expect(second_ready,"Rampage must not start Purify Body cooldown through raw shared group1");
    Group(second,&independent_group,1,1800,233);
    Expect(ready(manager,character,second,&remaining,&total)!=0,"projected unrelated slot remains ready");
    send(2,2000000,2000000);
    Expect(!ready(manager,character,second,&remaining,&total) && remaining==1800,"second projected AA owns its own duration");
    native_clock+=601;
    Expect(ready(manager,character,first,&remaining,&total)!=0,"first projected AA expires independently");
    Expect(!ready(manager,character,second,&remaining,&total) && remaining==1199,"second projected AA remains on cooldown");
    focus_reduction=30;
    Expect(calculated(manager,character,first)==570,"native focus reduction is preserved");
    focus_reduction=0;
    // Future start = now + remaining - own duration preserves a longer legacy
    // remaining cooldown without changing this family's catalog duration.
    send(1,2000000+900-600,2000000);
    Expect(get(character,1)==native_clock+300,"AA packet accepts translated future start");
    Expect(!ready(manager,character,first,&remaining,&total) && remaining==900 && total==600,"future start preserves longer legacy remaining time");
    focus_reduction=30;
    send(1,2000000+900-570,2000000);
    Expect(!ready(manager,character,first,&remaining,&total) && remaining==900 && total==570,"future start translation must use focused effective reuse");
    focus_reduction=600;
    Expect(calculated(manager,character,first)==0,"equal focus yields native effective reuse zero");
    send(1,2000000+300,2000000);
    Expect(ready(manager,character,first,&remaining,&total)!=0,"native zero effective reuse bypasses future stored start");
    focus_reduction=1000;
    Expect(calculated(manager,character,first)==-400,"excess focus retains signed negative native effective reuse");
    send(1,2000000+300-(-400),2000000);
    Expect(!ready(manager,character,first,&remaining,&total) && remaining==300 && total==-400,"native signed negative effective reuse preserves projected remaining time");
    send(1,2000000+300,2000000);
    Expect(ready(manager,character,first,&remaining,&total)!=0,"clamping negative effective reuse during projection loses the active native cooldown");
    focus_reduction=0;
    send(1,0,2000000);
    Expect(ready(manager,character,first,&remaining,&total)!=0,"begin0 with current server time resets an AA slot");
    send(1,0,0);
    Expect(!ready(manager,character,first,&remaining,&total) && remaining==600,"begin0 end0 starts now rather than resetting");
    send(0,2000000,2000000);send(99,2000000,2000000);
    Expect(get(character,0)==native_clock && get(character,99)==native_clock,"packet accepts native boundary slots0 and99");
    const DWORD sentinel=0x12345678;
    *reinterpret_cast<DWORD*>(profile+0x6d7c)=sentinel;
    send(100,2000000,2000000);send(-1,2000000,2000000);
    Expect(*reinterpret_cast<DWORD*>(profile+0x6d7c)==sentinel,"packet rejects invalid slots before storage");
    int invalid=100;Group(second,&invalid,1,1800,233);
    Expect(ready(manager,character,second,&remaining,&total)!=0,"native readiness incorrectly treats first slot100 as ready");
    Expect(!has(second,0),"native ability timer-list validation rejects slot100");
    Expect(GetterException(get,character,100)==EXCEPTION_BREAKPOINT,"direct getter guards fixed100-entry storage");
    Expect(SetterException(set,character,100,55)==EXCEPTION_BREAKPOINT,"direct setter guards fixed100-entry storage");
    Expect(*reinterpret_cast<DWORD*>(profile+0x6d7c)==sentinel,"out-of-range traps prevent fixture neighbor overwrite");
    int mixed[2]={1,100};Group(second,mixed,2,1800,233);
    Expect(ReadyException(ready,manager,character,second)==EXCEPTION_BREAKPOINT,"every timer-list entry must fit native storage");
    Group(second,&independent_group,1,1800,233);
    for(int id=0;id<100;++id)send(id,0,2000000);
    Expect(ready(manager,character,first,&remaining,&total)!=0 && ready(manager,character,second,&remaining,&total)!=0,"clearing all100 slots removes stale projected identities");
    send(2,2000000,2000000);
    Expect(ready(manager,character,first,&remaining,&total)!=0 && !ready(manager,character,second,&remaining,&total),"deadline resend after clear restores only assigned family");
    const BYTE expected_gate[]={0x39,0x58,0x64,0x0F,0x8E,0x2E,0x01,0x00,0x00};
    Check(!memcmp(image+0x2081E4,expected_gate,sizeof(expected_gate)),"pinned Make Hotkey reuse predicate");
    const BYTE allowed[]={0xB8,0x01,0x00,0x00,0x00,0xC3},rejected[]={0x33,0xC0,0xC3};
    memcpy(image+0x2081ED,allowed,sizeof(allowed));memcpy(image+0x20831B,rejected,sizeof(rejected));
    int quick_group=4;Group(first,&quick_group,1,0,48);
    Expect(!HotkeyReuseGate(image+0x2081E4,first),"native zero reuse reproduces disabled Make Hotkey");
    const int wire_reuse=NightcapQuickBuff::ClientPresentationReuse(48,0);
    Group(first,&quick_group,1,wire_reuse,48);
    Expect(HotkeyReuseGate(image+0x2081E4,first)!=0,"Quick Buff presentation must enable native Make Hotkey");
    Group(first,&quick_group,1,1,48);send(4,0,0);
    Expect(!ready(manager,character,first,&remaining,&total) && remaining==1,"positive presentation plus start packet creates an unwanted wait");
    for(int press=0;press<3;++press) {
        send(4,0,2000000);
        Expect(ready(manager,character,first,&remaining,&total)!=0,"Quick Buff reset is ready immediately without advancing native clock");
    }
    Expect(NightcapQuickBuff::ClientPresentationReuse(109,600)==600 && NightcapQuickBuff::ClientPresentationReuse(1,0)==0,
           "unrelated AA presentation remains unchanged");
    VirtualFree(image,0,MEM_RELEASE);
    std::cout<<"native AA reuse checks="<<checks<<" failures="<<failures<<'\n';
    return failures?1:0;
}

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
struct Item { uint32_t Classes=33225,Slots=4196352,Races=65535,AugType=0,ItemClass=0; int type=19,spell=0; };
static BYTE* native_profile=nullptr;
static bool deity_ok=true,level_ok=true,restriction_ok=true;
static void* __fastcall Profile(void*,void*) { return native_profile; }
static int __fastcall ItemClass(void*,void*) { return 0; }
static int __fastcall ItemType(void* self,void*) { return static_cast<Item*>(self)->type; }
static int __fastcall ItemSpell(void* self,void*,int) { return static_cast<Item*>(self)->spell; }
static uint32_t __fastcall Classes(void* self,void*,bool,bool) { return static_cast<Item*>(self)->Classes; }
static uint32_t __fastcall Slots(void* self,void*,bool) { return static_cast<Item*>(self)->Slots; }
static int __fastcall Range(void*,void*,bool) { return 205; }
static BYTE __fastcall SlotAvailable(void*,void*,int slot) { return slot>=0&&slot<=22&&slot!=21; }
static BYTE __fastcall Deity(void*,void*,const void*,bool) { return deity_ok; }
static BYTE __fastcall Level(void*,void*,const void*,bool) { return level_ok; }
static uint32_t __fastcall Races(void* self,void*,bool,bool) { return static_cast<Item*>(self)->Races; }
// Supply object access/lifetime at the fixture boundary; native slot, weapon,
// race-mask and inspection branches execute unmodified.
static Item* worn[23]={};
static bool dual_wield=true;
static void* __fastcall Inventory(void*,void*,void** out,int slot) { *out=worn[slot];return out; }
static void* __fastcall Assign(void** self,void*,void** src) { *self=*src;return self; }
static void __fastcall Release(void** self,void*) { *self=nullptr; }
static BYTE __fastcall Weapon(Item* self,void*) { return self->type==0||self->type==45; }
static BYTE __fastcall HasSkill(void*,void*,int skill) { return skill==22&&dual_wield; }
static BYTE __fastcall Restriction(void*,void*,const void*,bool,bool) { return restriction_ok; }
static __declspec(naked) void InspectNative(BYTE*,void*,void*) {
    __asm {
        push ebx
        push esi
        push edi
        push ebp
        mov eax,[esp+20]
        mov edx,[esp+24]
        mov esi,[esp+28]
        sub esp,0x1c8
        mov [esp+0x1c0],edx
        mov ebp,edx
        xor ebx,ebx
        mov edi,edx
        call eax
        add esp,0x1c8
        pop ebp
        pop edi
        pop esi
        pop ebx
        ret
    }
}
static DWORD Inspect(BYTE* site,void* item_ref) {
    alignas(4) BYTE window[0x318]={},label[0x130]={};
    *reinterpret_cast<void**>(window+0x314)=label;
    InspectNative(site,item_ref,window);
    return *reinterpret_cast<DWORD*>(label+0x12c);
}
int main(int argc,char** argv) {
    Check(argc==2,"usage: equipment-native eqgame.exe");
    using namespace nightcap::client_ui;
    BYTE* image=LoadClient(argv[1]);
    g_eq_base=base=reinterpret_cast<uintptr_t>(image);
    Check(ApplyEquipSubmissionPatches(base,true),"install actual production equipment pair");
    // The inventory placement redirect is installed with the spell UI group.
    Check(ApplyGuardedRelativeCall(base,kScrollPlacementCanUseRva,kExpectedScrollPlacementCanUse,
        reinterpret_cast<uintptr_t>(&CanUseInventoryItem),"inventory fixture"),"install inventory redirect");
    Check(ApplyGuardedRelativeCall(base,kInspectionCanUseRva,kExpectedInspectionCanUse,
        reinterpret_cast<uintptr_t>(&CanUseInventoryItem),"inspection fixture"),"install inspection redirect");
    alignas(4) BYTE eq[0x600]={},player[0x150]={},character[0x3000]={},profile[0x3450]={};
    int32_t vbtable[2]={};
    *reinterpret_cast<void**>(character+8)=vbtable;
    *reinterpret_cast<void**>(character+0x2dcc)=vbtable;
    *reinterpret_cast<void**>(image+0x9D261C)=character;
    *reinterpret_cast<void**>(image+0xA67CCC)=eq;
    *reinterpret_cast<void**>(image+0x9D2630)=player;
    *reinterpret_cast<int*>(eq+0x5c8)=5;
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    memcpy(player+0xa4,"Palwar",7);
    native_profile=profile; profile[0x3374]=3;
    *reinterpret_cast<uint32_t*>(profile+0x3370)=7; // Palwar is Half Elf
    *reinterpret_cast<uint32_t*>(profile+0x341c)=0x7fffff;
    Check(state.Consume("[NCUI1]S|1|29|22|0|7|3|1|7|Palwar"),"Palwar identity");
    Jump(image+kItemClassesRva,reinterpret_cast<void*>(&Classes));
    Jump(image+kItemTypeRva,reinterpret_cast<void*>(&ItemType));
    Jump(image+kItemSpellRva,reinterpret_cast<void*>(&ItemSpell));
    Jump(image+0x3affd0,reinterpret_cast<void*>(&ItemClass));
    Jump(image+0x3b2210,reinterpret_cast<void*>(&Slots));
    Jump(image+0x3ba8b0,reinterpret_cast<void*>(&Range));
    Jump(image+0x3db210,reinterpret_cast<void*>(&Profile));
    Jump(image+0x3e6fc0,reinterpret_cast<void*>(&SlotAvailable));
    Jump(image+0x462c0,reinterpret_cast<void*>(&Deity));
    Jump(image+0x46190,reinterpret_cast<void*>(&Level));
    Jump(image+0x3b4e30,reinterpret_cast<void*>(&Races));
    Jump(image+0x2dec0,reinterpret_cast<void*>(&Inventory));
    Jump(image+0x2dc90,reinterpret_cast<void*>(&Assign));
    Jump(image+0x4630,reinterpret_cast<void*>(&Release));
    Jump(image+0x3b03c0,reinterpret_cast<void*>(&Weapon));
    Jump(image+0x4a1b0,reinterpret_cast<void*>(&HasSkill));
    Jump(image+0x46380,reinterpret_cast<void*>(&Restriction));
    image[0x2a9de0]=0xc3; // stop after native color write, before UI/string work
    Check(FlushInstructionCache(GetCurrentProcess(),image,0x400000)!=0,"instruction cache");
    using CanUse=BYTE (__thiscall*)(void*,const void*,bool,bool);
    auto call=image+kScrollPlacementCanUseRva;
    auto placement=reinterpret_cast<CanUse>(call+5+*reinterpret_cast<int32_t*>(call+1));
    using Equip=BYTE (__thiscall*)(void*,const void*,int,bool,bool);
    auto equip=reinterpret_cast<Equip>(image+0x183550);
    Item item; void* ref=&item;
    Expect(placement(character+0x2dc8,&ref,false,false)!=0,"Forged Javelin inventory placement accepts held Warrior/Monk");
    Expect(equip(character,&ref,11,false,true)!=0,"Forged Javelin ranged slot accepts held classes");
    Expect(equip(character,&ref,22,false,true)!=0,"Forged Javelin ammo slot accepts held classes");
    Expect(!equip(character,&ref,17,false,true),"Forged Javelin wrong slot remains rejected");
    Expect(Inspect(image+0x2a9d07,&ref)==0xff00ff00,"legal Forged Javelin inspection is green");
    item.Classes=1u<<10; // an unheld Necromancer-only ranged item
    Expect(!placement(character+0x2dc8,&ref,false,false),"unheld item inventory placement is rejected");
    Expect(!equip(character,&ref,11,false,true),"unheld item equip check is rejected");
    Expect(Inspect(image+0x2a9d07,&ref)==0xffff0000,"unheld item inspection is red instead of green");
    item.Classes=33225;
    for(int type : {1,4,8,35,54}) {
        item.type=type;
        Expect(Inspect(image+0x2a9d07,&ref)==0xff00ff00,"held item uses native direct inspection branch");
        item.Classes=1u<<10;
        Expect(Inspect(image+0x2a9d07,&ref)==0xffff0000,"unheld item uses native direct inspection branch");
        item.Classes=33225;
    }
    item.type=19;
    for(bool* gate : {&deity_ok,&level_ok,&restriction_ok}) {
        *gate=false;
        Expect(!equip(character,&ref,11,false,true),"native non-class restriction remains enforced");
        Expect(Inspect(image+0x2a9d07,&ref)!=0xff00ff00,"native restriction cannot produce green inspection");
        *gate=true;
    }
    item.Races=1;
    Expect(!equip(character,&ref,11,false,true),"actual native race helper rejects excluded Half Elf");
    Expect(Inspect(image+0x2a9d07,&ref)==0xffff0000,"excluded race is red");
    item=Item{}; item.Classes=16448;item.Slots=8192;item.Races=62219;item.type=45;
    Expect(!equip(character,&ref,13,false,true),"raw Bronze Knuckles reproduces Half Elf rejection");
    Expect(Inspect(image+0x2a9d07,&ref)==0xffff0000,"raw Bronze Knuckles is red");
    NightcapEquipment::ApplyRacePolicy(item);
    Expect(equip(character,&ref,13,false,true)!=0,"projected Bronze Knuckles accepts held Monk in primary");
    Expect(!equip(character,&ref,14,false,true),"Bronze Knuckles remains primary-only");
    Expect(Inspect(image+0x2a9d07,&ref)==0xff00ff00,"projected Bronze Knuckles is green");
    for(unsigned race : {1u,2u,3u,4u,5u,6u,7u,8u,9u,10u,11u,12u,128u,130u,330u,522u}) {
        *reinterpret_cast<uint32_t*>(profile+0x3370)=race;
        Expect(equip(character,&ref,13,false,true)!=0,"all sixteen playable races pass native projected mask");
    }
    *reinterpret_cast<uint32_t*>(profile+0x3370)=7;
    for(unsigned race : {0u,65536u}) {
        item.Races=race;NightcapEquipment::ApplyRacePolicy(item);
        Expect(!equip(character,&ref,13,false,true),"non-player race sentinel stays blocked");
        Expect(Inspect(image+0x2a9d07,&ref)==0xffff0000,"non-player gear stays red");
    }
    item.Races=65535;item.Classes=1u<<10;
    Expect(!equip(character,&ref,13,false,true),"race relaxation cannot grant unheld class");
    Expect(Inspect(image+0x2a9d07,&ref)==0xffff0000,"unheld martial item stays red");
    item.Classes=64; item.Slots=(1u<<13)|(1u<<14);
    Expect(equip(character,&ref,14,false,true)!=0,"legal martial offhand passes native weapon branch");
    dual_wield=false;
    Expect(!equip(character,&ref,14,false,true),"native offhand branch still requires Dual Wield");
    dual_wield=true;
    Item other;other.type=8;worn[14]=&other;
    Expect(equip(character,&ref,13,false,true)!=0,"Bronze Knuckles can replace primary while shield is worn");
    for(int type : {1,4,35}) {
        item.type=type;
        Expect(!equip(character,&ref,13,false,true),"two-handed primary conflicts with occupied secondary");
        worn[14]=nullptr;
        Expect(equip(character,&ref,13,false,true)!=0,"two-handed primary passes with empty secondary");
        worn[14]=&other;other.type=type;worn[13]=&other;item.type=45;
        Expect(!equip(character,&ref,14,false,true),"offhand conflicts with two-handed primary");
    }
    worn[13]=worn[14]=nullptr;
    item.type=10;item.Slots=1u<<2;
    Expect(equip(character,&ref,2,false,true)!=0,"held Monk armor uses native worn slot path");
    Expect(!equip(character,&ref,13,false,true),"armor wrong slot remains blocked");
    item=Item{};
    item.Classes=0;
    Expect(!equip(character,&ref,11,false,true),"zero class/augment mask stays rejected");
    item.Classes=33225;
    Check(state.Consume("[NCUI1]S|2|29|22|0|7|3|0|1|Palwar"),"Warrior in slot3");
    Expect(placement(character+0x2dc8,&ref,false,false)!=0,"tertiary Warrior allows inventory placement");
    *reinterpret_cast<uint32_t*>(player+0x148)=8;
    Expect(!placement(character+0x2dc8,&ref,false,false),"stale identity cannot grant inventory placement");
    Expect(Inspect(image+0x2a9d07,&ref)==0xffff0000,"stale identity cannot make off-primary item green");
    *reinterpret_cast<uint32_t*>(player+0x148)=7;
    Check(state.Consume("[NCUI1]S|3|29|22|0|7|3|0|0|Palwar"),"release secondary classes");
    Expect(!equip(character,&ref,11,false,true),"released classes revoke equip eligibility");
    Expect(Inspect(image+0x2a9d07,&ref)==0xffff0000,"released classes revoke green inspection");
    item.type=20; item.Classes=65535; item.spell=4;
    Expect(!placement(character+0x2dc8,&ref,false,false),"scroll placement rejects unheld canonical spell despite broad item mask");
    Check(state.Consume("[NCUI1]S|4|29|22|0|7|3|13|0|Palwar"),"held Magician");
    Expect(placement(character+0x2dc8,&ref,false,false)!=0,"scroll placement retains held canonical spell policy");
    item.type=19; item.Classes=33225;
    state.Clear();
    Expect(!equip(character,&ref,11,false,true),"missing identity cannot grant off-primary equip");
    item.Classes=4;
    Expect(equip(character,&ref,11,false,true)!=0,"missing metadata preserves native primary eligibility");
    Expect(nightcap::ActiveEquipItem()==nullptr&&ActiveSpellItem()==nullptr,"scopes restored");
    std::cout << checks << " native equipment checks; " << failures << " failures\n";
    VirtualFree(image,0,MEM_RELEASE);
    return failures?1:0;
}

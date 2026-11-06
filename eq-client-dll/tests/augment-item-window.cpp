#include "../src/dllmain.cpp"
#include <wincrypt.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
#pragma comment(lib,"advapi32.lib")
static unsigned failures=0,checks=0;
static void Check(bool okay,const char* text) { if (!okay) { std::cerr<<text<<"\n";ExitProcess(2); } }
static void Expect(bool okay,const char* text) { ++checks;if(!okay){++failures;std::cerr<<"FAIL: "<<text<<"\n";} }
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

using nightcap::client_ui::EqString;
static std::string rendered;
static void __fastcall Capture(void*,void*,EqString text,bool,void*) {
 const auto rep=static_cast<const BYTE*>(text.rep);
 rendered=rep?reinterpret_cast<const char*>(rep+0x14):"";
 if(rep)InterlockedDecrement(reinterpret_cast<volatile LONG*>(text.rep));
}
static void __fastcall Title(void*,void*,const EqString*) {}
static void __fastcall Release(void*,void*,void* value) { InterlockedDecrement(static_cast<volatile LONG*>(value)); }
struct Text {
 std::vector<BYTE> bytes;
 explicit Text(const char* s):bytes(0x14+strlen(s)+1,0){
  *reinterpret_cast<LONG*>(bytes.data())=1;
  *reinterpret_cast<uint32_t*>(bytes.data()+4)=static_cast<uint32_t>(strlen(s)+1);
  *reinterpret_cast<uint32_t*>(bytes.data()+8)=static_cast<uint32_t>(strlen(s));
  memcpy(bytes.data()+0x14,s,strlen(s)+1);
 }
};
static std::vector<std::unique_ptr<Text>> assigned;
static EqString* __fastcall Assign(EqString* self,void*,const char* value) {
 assigned.emplace_back(new Text(value));self->rep=assigned.back()->bytes.data();return self;
}
static BYTE definition[0x300]={};
static void* __fastcall Definition(void*,void*) { return definition; }
int main(int argc,char** argv) {
 Check(argc==2,"read-only client path required");auto image=LoadClient(argv[1]);
 Jump(image+0x483e10,reinterpret_cast<void*>(&Capture));
 Jump(image+0x405b20,reinterpret_cast<void*>(&Release));
 BYTE window[0x600]={}; void* table[0x130/4]={};
 table[0x124/4]=reinterpret_cast<void*>(&Title);*reinterpret_cast<void***>(window)=table;
 *reinterpret_cast<void**>(window+0x220)=window;
 *reinterpret_cast<uint32_t*>(definition+0xec)=940282;
 void* item_table[3]={nullptr,nullptr,reinterpret_cast<void*>(&Definition)};void** item=item_table;
 *reinterpret_cast<void**>(window+0x2b0)=&item;
 Text info("AC: 5<BR>HP: 114<BR>This Augmentation fits in slot types: 22");
 *reinterpret_cast<void**>(window+0x294)=info.bytes.data();
 using Update=void(__thiscall*)(void*);
 nightcap::client_ui::original_item_description = reinterpret_cast<Update>(nightcap::client_ui::EntryHook(
  reinterpret_cast<uintptr_t>(image)+kItemDescriptionUpdateRva,kExpectedItemDescriptionUpdate,reinterpret_cast<void*>(&nightcap::client_ui::ItemDescriptionHook)));
 Check(nightcap::client_ui::original_item_description!=nullptr,"guarded item-description hook");
 nightcap::client_ui::item_description_assign=reinterpret_cast<nightcap::client_ui::AssignString>(&Assign);
 reinterpret_cast<Update>(image+0x29ae30)(window);
 Expect(rendered.find("Shield Block: +1%")!=std::string::npos,"Exalted shield block must be visible in native Description");
 Expect(rendered.find("not Shielding")!=std::string::npos,"distinguishes Shielding");
 Expect(rendered.find("usable shield")!=std::string::npos,"shield requirement visible");
 Expect(rendered.find("socketed in worn armor")!=std::string::npos,"equipped socket requirement visible");
 Expect(rendered.find("strongest Hunt")!=std::string::npos,"stacking rule visible");
 const auto once=rendered;reinterpret_cast<Update>(image+0x29ae30)(window);
 Expect(rendered==once,"repeated native refresh is idempotent");
 Expect(rendered.find("AC: 5<BR>HP: 114")!=std::string::npos,"ordinary Description retained");
 for(uint32_t base:{940040u,940280u,940528u})for(uint32_t tier=0;tier<4;++tier){
  *reinterpret_cast<uint32_t*>(definition+0xec)=base+tier;
  *reinterpret_cast<void**>(window+0x294)=info.bytes.data();
  reinterpret_cast<Update>(image+0x29ae30)(window);
  const int bonus=tier==0?0:tier==3?2:1;
  Expect(bonus?rendered.find("Shield Block: +"+std::to_string(bonus)+"%")!=std::string::npos:rendered.find("Shield Block")==std::string::npos,"all shield-block families/tiers match server");
 }
 *reinterpret_cast<uint32_t*>(definition+0xec)=940282;
 *reinterpret_cast<void**>(window+0x294)=info.bytes.data();
 reinterpret_cast<Update>(image+0x29ae30)(window);
 *reinterpret_cast<uint32_t*>(definition+0xec)=940100;
 reinterpret_cast<Update>(image+0x29ae30)(window);
 Expect(rendered.find("Shield Block")==std::string::npos,"window reuse clears old annotation");
 *reinterpret_cast<void**>(window+0x294)=info.bytes.data();
 *reinterpret_cast<void**>(window+0x2b0)=nullptr;
 reinterpret_cast<Update>(image+0x29ae30)(window);
 Expect(rendered==reinterpret_cast<const char*>(info.bytes.data()+0x14),"missing item keeps native Description");
 char copy[16385]={};uint32_t id=0;
 Expect(!nightcap::client_ui::SnapshotItemDescription(nullptr,id,copy),"null window rejected");
 *reinterpret_cast<void**>(window+0x2b0)=&item;
 *reinterpret_cast<uint32_t*>(info.bytes.data()+12)=1;
 Expect(!nightcap::client_ui::SnapshotItemDescription(window,id,copy),"unsupported native string encoding rejected");
 *reinterpret_cast<uint32_t*>(info.bytes.data()+12)=0;
 *reinterpret_cast<uint32_t*>(info.bytes.data()+8)=16385;
 Expect(!nightcap::client_ui::SnapshotItemDescription(window,id,copy),"oversized string rejected");
 *reinterpret_cast<uint32_t*>(info.bytes.data()+8)=static_cast<uint32_t>(strlen("AC: 5<BR>HP: 114<BR>This Augmentation fits in slot types: 22"));
 Expect(!nightcap::client_ui::EntryHook(reinterpret_cast<uintptr_t>(image)+kItemDescriptionUpdateRva,kExpectedItemDescriptionUpdate,reinterpret_cast<void*>(&nightcap::client_ui::ItemDescriptionHook)),"foreign/repeated patch rejected");
 std::cout<<checks<<" checks, "<<failures<<" failures\n";return failures?1:0;
}

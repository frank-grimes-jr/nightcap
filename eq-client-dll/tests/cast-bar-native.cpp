// Read-only exact-client cast-gauge regression; no game process is launched.
#define NOMINMAX
#include <windows.h>
#include <wincrypt.h>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
#include <map>
#include <sstream>
#include <string>
#include "../src/patch_catalog.h"
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

// Execute the unmodified personal cast gauge in a private mapped PE. Only spell
// lookup, profile lookup and the item-cast predicate are fixture boundaries.
static BYTE spell[0x200]={},profile[0x4000]={};
static BYTE __cdecl ValidSpell(int) {return 1;}
static void* __fastcall Lookup(void*,void*,int) {return spell;}
static void* __fastcall Profile(void*,void*) {return profile;}
static BYTE __fastcall IsItem(void*,void*) {return 0;}
static BYTE* mapped_image=nullptr;
static LONG WINAPI Fault(EXCEPTION_POINTERS* error) {
    if(error->ExceptionRecord->ExceptionCode==EXCEPTION_ACCESS_VIOLATION) {
        std::cerr<<"FIXTURE native access violation at RVA "<<std::hex
            <<error->ContextRecord->Eip-reinterpret_cast<DWORD>(mapped_image)
            <<" address "<<error->ExceptionRecord->ExceptionInformation[1]<<'\n';
        ExitProcess(2);
    }
    return EXCEPTION_CONTINUE_SEARCH;
}
static std::map<int,int> Durations(const char* path) {
    std::ifstream file(path);Check(bool(file),"open supplied spell data read-only");
    std::map<int,int> result;std::string line;
    while(std::getline(file,line)) {
        std::istringstream input(line);std::string field;int id=-1,count=0,duration=-1;
        while(std::getline(input,field,'^')) {
            if(count==0)id=std::stoi(field);
            if(count==13)duration=std::stoi(field);
            ++count;
        }
        Check(count==237 && id>=0 && duration>=0,"237-field spell definition");
        Check(result.emplace(id,duration).second,"unique spell identity");
    }
    return result;
}
int main(int argc,char** argv) {
    Check(argc==4,"pass pinned eqgame, spell file, reviewed timing CSV");
    BYTE* image=LoadClient(argv[1]);
    mapped_image=image;AddVectoredExceptionHandler(1,&Fault);
    Jump(image+0x0ad150,&ValidSpell);
    Jump(image+0x3db210,&Profile);
    Jump(image+0x041e30,&IsItem);
    BYTE player[0x500]={},character[0x40]={},clock[0x200]={};
    int vbase[2]={};void* vtable[4]={nullptr,nullptr,nullptr,reinterpret_cast<void*>(&Lookup)};
    void** manager=vtable;
    *reinterpret_cast<void***>(character+8)=reinterpret_cast<void**>(vbase);
    *reinterpret_cast<void**>(image+0x9d2630)=player;
    *reinterpret_cast<void**>(image+0x9d261c)=character;
    *reinterpret_cast<void**>(image+0x9d2660)=clock;
    *reinterpret_cast<void**>(image+0xa646b0)=&manager;
    profile[0x3374]=12;
    using Gauge=int(__cdecl*)();const auto gauge=reinterpret_cast<Gauge>(image+0x361fb0);
    const auto durations=Durations(argv[2]);
    std::ifstream catalog(argv[3]);Check(bool(catalog),"open reviewed timing catalog");
    std::string line;std::getline(catalog,line);unsigned spells=0;
    while(std::getline(catalog,line)) {
        const int id=std::stoi(line.substr(0,line.find(',')));
        const int duration=std::stoi(line.substr(line.rfind(',')+1));
        Check(durations.count(id)==1,"reviewed spell present");++spells;
        *reinterpret_cast<int*>(player+0x448)=id;
        *reinterpret_cast<int*>(spell+0x10)=durations.at(id);
        *reinterpret_cast<int*>(player+0x444)=1000000+duration;
        for(int percent : {0,25,50,75,99,100}) {
            const int elapsed=duration*percent/100;
            *reinterpret_cast<int*>(clock+0x154)=1000000+elapsed;
            const int expected=duration ? (duration-elapsed)*1000/duration : -1;
            const int actual=gauge();
            ++checks;
            if(actual!=expected) {
                ++failures;
                if(failures<=12)std::cerr<<"FAIL spell="<<id<<" elapsed="<<elapsed
                    <<" file_ms="<<durations.at(id)<<" expected="<<expected<<" actual="<<actual<<'\n';
            }
        }
        *reinterpret_cast<int*>(clock+0x154)=1000001+duration;
        Expect(gauge()==-1,"expired cast has no active gauge");
        *reinterpret_cast<int*>(player+0x444)=0;
        Expect(gauge()==-1,"cancelled cast has no active gauge");
    }
    Check(spells==638,"complete reviewed scope");
    *reinterpret_cast<void**>(image+0x9d2630)=nullptr;
    Expect(gauge()==-1,"no local player retains native empty gauge");
    std::cout<<"cast gauge: "<<spells<<" spells, "<<checks<<" checks, "<<failures<<" failures\n";
    return failures?1:0;
}

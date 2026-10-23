// Runs exact RoF2 AA controls in a separate test image; reference client read-only.
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
#include "../src/ui_hooks.h"
#pragma comment(lib,"advapi32.lib")
using namespace nightcap::client_ui;
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

static BYTE* character=nullptr;
static int submitted=-1,submit_count=0,refreshes=0,enabled=-1;
static void* refreshed_window=nullptr;
static void __cdecl Submit(){submitted=character[0x2081];++submit_count;}
static void __fastcall Update(void* self,void*){refreshed_window=self;++refreshes;}
static void __fastcall Enable(void*,void*,int value,int){enabled=value&255;}
static EqString* __fastcall Assign(EqString* s,void*,const char* value){s->rep=const_cast<char*>(value);return s;}
static void* __fastcall Child(void*,void*,const EqString*){return nullptr;}
// Execute a real UpdateAA slice with the same stack locals and live registers.
// Native instructions return at their original join point in this test image.
static void __declspec(naked) __cdecl Gate(void*,int,int,int,void*) {
    __asm {
        push ebp
        mov ebp,esp
        push ebx
        push esi
        sub esp,0x20
        mov esi,[ebp+8]
        mov ebx,[ebp+12]
        mov eax,[ebp+16]
        mov byte ptr [esp+0x13],al
        mov eax,[ebp+20]
        mov byte ptr [esp+0x14],al
        call dword ptr [ebp+24]
        add esp,0x20
        pop esi
        pop ebx
        pop ebp
        ret
    }
}
int main(int argc,char** argv) {
    Check(argc==2,"pass pinned eqgame path");
    BYTE* image=LoadClient(argv[1]);base=reinterpret_cast<uintptr_t>(image);
    BYTE profile[0x2100]={},window[0x300]={},minus[0x200]={},plus[0x200]={};
    character=profile;
    *reinterpret_cast<BYTE**>(image+0x9D261C)=profile;
    *reinterpret_cast<void**>(window+0x24C)=minus;
    *reinterpret_cast<void**>(window+0x250)=plus;
    image[0x9E09C2]=1;image[0x9E09C3]=image[0x9E09C6]=0;
    Check(MatchAAAllocationControls(),"all original control guards match relocated image");
    image[kUIAAExpMinusNativeRva]^=1;
    Expect(!MatchAAAllocationControls(),"arithmetic drift fails closed");
    image[kUIAAExpMinusNativeRva]^=1;
    Jump(image+0x207C40,reinterpret_cast<void*>(&Submit));
    Jump(image+0x209F90,reinterpret_cast<void*>(&Update));
    Jump(image+0x466610,reinterpret_cast<void*>(&Enable));
    Jump(image+kUIStringAssignRva,reinterpret_cast<void*>(&Assign));
    Jump(image+kUIChildRva,reinterpret_cast<void*>(&Child));
    image[0x20A148]=image[0x20A206]=image[0x20A261]=0xC3;
    auto reset_gate=image+0x20A11B;
    auto minus_gate=image+0x20A1C5;
    auto plus_gate=image+0x20A21F;
    profile[0x2081]=50;submitted=-1;
    Gate(window,50,1,1,reset_gate);
    Expect(profile[0x2081]==0 && submitted==0,"original client reproduces reset below51");
    enabled=-1;Gate(window,50,1,1,minus_gate);
    Expect(enabled==0,"original client reproduces disabled minus at1");
    enabled=-1;Gate(window,50,1,1,plus_gate);
    Expect(enabled==0,"original client reproduces disabled plus at1");
    Check(InstallAAAllocationControls(),"guarded level1 control patch installs");
    for(auto level:{0,1,50,51}) {
        for(auto percent:{0,1,5,10,50,95,99,100}) {
            profile[0x2081]=static_cast<BYTE>(percent);submitted=-1;
            Gate(window,percent,level,1,reset_gate);
            Expect(profile[0x2081]==(level==0?0:percent),"refresh preserves allocation from level1");
            enabled=-1;Gate(window,percent,level,1,minus_gate);
            Expect(enabled==int(level>=1 && percent>0),"native minus enable bounds");
            enabled=-1;Gate(window,percent,level,1,plus_gate);
            Expect(enabled==int(level>=1 && percent<100),"native plus enable bounds");
        }
    }
    image[0x9E09C2]=0;enabled=-1;Gate(window,50,1,1,plus_gate);
    Expect(enabled==0,"native entitlement checks preserved");
    image[0x9E09C2]=1;enabled=-1;Gate(window,50,1,0,plus_gate);
    Expect(enabled==-1,"native unavailable-AA state preserves branch");
    original_aa_notify=reinterpret_cast<InventoryNotify>(image+kUIAANotifyRva);
    for(auto percent:{0,1,5,10,50,95,99,100}) {
        for(bool increment:{false,true}) {
            profile[0x2081]=static_cast<BYTE>(percent);submit_count=refreshes=0;submitted=-1;
            const int expected=increment?std::min(100,percent+10):std::max(0,percent-10);
            const auto ret=AANotifyHook(window,nullptr,increment?plus:minus,1,nullptr);
            Expect(ret==1 && profile[0x2081]==expected,"hook delegates real native +/- with saturation");
            Expect(refreshes==1 && refreshed_window==window,"native refresh uses original window");
            Expect(submit_count==int(expected!=percent),"native submit occurs only for changed allocation");
            if(expected!=percent) Expect(submitted==expected,"native submission carries saturated percentage");
        }
    }
    profile[0x2081]=5;
    for(int i=0;i<15;++i) AANotifyHook(window,nullptr,plus,1,nullptr);
    Expect(profile[0x2081]==100,"repeated plus stops at100");
    for(int i=0;i<15;++i) AANotifyHook(window,nullptr,minus,1,nullptr);
    Expect(profile[0x2081]==0,"repeated minus stops at0");
    profile[0x2081]=95; // server correction/profile restore
    AANotifyHook(window,nullptr,minus,1,nullptr);
    Expect(profile[0x2081]==85,"server-corrected percentage remains authoritative");
    VirtualFree(image,0,MEM_RELEASE);base=0;
    std::cout<<checks<<" exact-client checks, "<<failures<<" failures\n";
    return failures?1:0;
}

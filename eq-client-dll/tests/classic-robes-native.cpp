#include <windows.h>
#include <cassert>
#include <fstream>
#include <iterator>
#include <vector>
#include <iostream>
#include <cstring>
#include "../src/patch_catalog.h"
// Executes the pinned wear-material decision and normalization in a mapped PE.
// Name lookup and graphics/material callbacks are fixture boundaries.
// No game entry point, login, installed-client writes or renderer run.
#include <wincrypt.h>
#pragma comment(lib, "advapi32.lib")
static void Check(bool okay, const char* message) {
 if (!okay) { std::cerr << "FAIL: " << message << "\n"; ExitProcess(1); }
}

static int chosen=-1;static unsigned calls=0;static const char* actorCode;
static int expectedPattern=-1;static unsigned patternCalls=0;
static void* __cdecl ActorName() {return nullptr;}
static void __fastcall NameDone(void*,void*,char* output,int,int) {strcpy(output,actorCode);}
static bool __fastcall Body(void*,void*,int variant,const char* code) {
 Check(!strcmp(code,actorCode),"actor identity retained"); chosen=variant;++calls;return true;
}
static bool __fastcall Materials(void*,void*,const char*,const char*,void*,int,int) {return true;}
static bool __fastcall RobePattern(void*,void*,int pattern,unsigned*) {
 Check(pattern==expectedPattern,"native robe pattern equals material minus six");++patternCalls;return true;
}
static bool __fastcall Reset(void*,void*,const char*) {return true;}
static void Patch(BYTE* image,unsigned rva,void* target) {
 image[rva]=0xe9;*reinterpret_cast<DWORD*>(image+rva+1)=reinterpret_cast<DWORD>(target)-reinterpret_cast<DWORD>(image+rva+5);
}

static LONG CALLBACK Fault(EXCEPTION_POINTERS* e) {
 std::cerr << "native fault " << std::hex << e->ExceptionRecord->ExceptionCode << " at " << e->ContextRecord->Eip << " access " << e->ExceptionRecord->ExceptionInformation[1] << "\n";
 return EXCEPTION_CONTINUE_SEARCH;
}
int main(int argc,char** argv) {
 AddVectoredExceptionHandler(1,Fault);
 Check(argc==2,"usage: classic-robes-native eqgame.exe");
 std::ifstream file(argv[1],std::ios::binary);assert(file);
 std::vector<char> raw((std::istreambuf_iterator<char>(file)),{});
 Check(raw.size()==8774656, "unsupported client size");
 HCRYPTPROV provider=0; HCRYPTHASH hash=0;
 Check(CryptAcquireContext(&provider,nullptr,nullptr,PROV_RSA_AES,CRYPT_VERIFYCONTEXT)!=0,"SHA provider");
 Check(CryptCreateHash(provider,CALG_SHA_256,0,0,&hash)!=0,"SHA create");
 Check(CryptHashData(hash,reinterpret_cast<const BYTE*>(raw.data()),static_cast<DWORD>(raw.size()),0)!=0,"SHA data");
 BYTE digest[32];DWORD length=sizeof(digest);
 Check(CryptGetHashParam(hash,HP_HASHVAL,digest,&length,0)!=0,"SHA result");
 CryptDestroyHash(hash);CryptReleaseContext(provider,0);
 Check(!memcmp(digest,kExpectedEqgameSha256,sizeof(digest)),"unsupported client hash");
 auto dos=reinterpret_cast<IMAGE_DOS_HEADER*>(raw.data());
 auto nt=reinterpret_cast<IMAGE_NT_HEADERS32*>(raw.data()+dos->e_lfanew);
 auto image=static_cast<BYTE*>(VirtualAlloc(nullptr,nt->OptionalHeader.SizeOfImage,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));assert(image);
 memcpy(image,raw.data(),nt->OptionalHeader.SizeOfHeaders);
 auto sec=IMAGE_FIRST_SECTION(nt);
 for(unsigned i=0;i<nt->FileHeader.NumberOfSections;++i)memcpy(image+sec[i].VirtualAddress,raw.data()+sec[i].PointerToRawData,sec[i].SizeOfRawData);
 auto dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_BASERELOC];
 for(DWORD pos=dir.VirtualAddress;pos<dir.VirtualAddress+dir.Size;) {
  auto block=reinterpret_cast<IMAGE_BASE_RELOCATION*>(image+pos);assert(block->SizeOfBlock>=8);
  auto entries=reinterpret_cast<WORD*>(block+1);
  for(unsigned i=0;i<(block->SizeOfBlock-8)/2;++i) if(entries[i]>>12==IMAGE_REL_BASED_HIGHLOW) {
   auto target=reinterpret_cast<DWORD*>(image+block->VirtualAddress+(entries[i]&4095));
   *target+=reinterpret_cast<DWORD>(image)-nt->OptionalHeader.ImageBase;
  }
  pos+=block->SizeOfBlock;
 }


 Patch(image,0x10f070,reinterpret_cast<void*>(&ActorName));
 Patch(image,0x10a2d0,reinterpret_cast<void*>(&NameDone));
 Patch(image,0x4dc12f,reinterpret_cast<void*>(&sprintf));


 DWORD vtable[128]={};vtable[0x144/4]=reinterpret_cast<DWORD>(&Body);
 vtable[0x13c/4]=reinterpret_cast<DWORD>(&RobePattern);vtable[0x140/4]=reinterpret_cast<DWORD>(&Reset);vtable[0xe4/4]=reinterpret_cast<DWORD>(&Materials);
 DWORD graphics=reinterpret_cast<DWORD>(vtable);BYTE object[0x200]={};BYTE model[0x80]={};
 *reinterpret_cast<DWORD*>(object+0x178)=reinterpret_cast<DWORD>(&graphics);
 *reinterpret_cast<DWORD*>(object+0x180)=reinterpret_cast<DWORD>(model);
 using Wear=bool(__thiscall*)(void*,int,int,int,unsigned,int,int,bool);
 auto wear=reinterpret_cast<Wear>(image+0x99f0);
 const int races[]={1,2,3,4,5,6,7,8,9,10,11,12};
 const char* codes[][2]={{"HUM","HUF"},{"BAM","BAF"},{"ERM","ERF"},{"ELM","ELF"},{"HIM","HIF"},{"DAM","DAF"},{"HAM","HAF"},{"DWM","DWF"},{"TRM","TRF"},{"OGM","OGF"},{"HOM","HOF"},{"GNM","GNF"}};
 unsigned checks=0;
 for(int r=0;r<12;++r) for(int gender=0;gender<2;++gender) {
  *reinterpret_cast<int*>(object+0x10)=races[r];object[0x15]=static_cast<BYTE>(gender);actorCode=codes[r][gender];
  for(int texture=10;texture<=16;++texture) {
   chosen=-1;calls=0;patternCalls=0;expectedPattern=texture-6;
   wear(object,1,0,texture,0x0060a0d0,0,0,false);
   Check(calls==1 && chosen==1,"equipping a robe selects alternate body 01");++checks;
   Check(patternCalls==1,"equipping applies exactly one robe pattern");
   chosen=-1;calls=0;patternCalls=0;expectedPattern=-1;
   wear(object,1,texture,0,0,0,0,false);
   Check(calls==1 && chosen==0,"removing a robe selects the original body");++checks;
   Check(patternCalls==0,"removing does not apply a robe pattern");
  }
 }
 std::cout << "PASS: " << checks << " native robe equip/remove selections across 12 races, both genders, materials 10..16; graphics/material/name boundaries mocked\n";
 VirtualFree(image,0,MEM_RELEASE);
}

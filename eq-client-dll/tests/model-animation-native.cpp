#include <windows.h>
#include <cassert>
#include <fstream>
#include <iterator>
#include <vector>
#include <iostream>
#include <cstring>
#include "../src/patch_catalog.h"
#include "../src/ui_hooks.h"
#include "../src/model_hooks.h"
// Executes only the pinned, pure native animation-family resolver in a relocated
// image. No client entry point, imports, login, graphics or game state runs.
#include <wincrypt.h>
#pragma comment(lib, "advapi32.lib")
static void Check(bool okay, const char* message) {
 if (!okay) { std::cerr << "FAIL: " << message << "\n"; ExitProcess(1); }
}
int main(int argc,char** argv) {
 Check(argc==2 || (argc==3 && !strcmp(argv[2],"--unpatched")),"usage: model-animation-native eqgame.exe [--unpatched]");
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
 image[0x4dc33a]=0xe9;
 *reinterpret_cast<DWORD*>(image+0x4dc33b)=reinterpret_cast<DWORD>(&_strnicmp)-reinterpret_cast<DWORD>(image+0x4dc33f);
 using Resolver=bool(__thiscall*)(void*,const char*,char*,bool);
 auto resolver=reinterpret_cast<Resolver>(image+0x6a60);
 using namespace nightcap::models;
 if(argc==2) original_animation=reinterpret_cast<AnimationSource>(nightcap::client_ui::EntryHook(
  reinterpret_cast<uintptr_t>(image)+kModelAnimationRva,kExpectedModelAnimation,reinterpret_cast<void*>(&AnimationHook)));
 else original_animation=resolver;
 Check(original_animation!=nullptr,"native animation trampoline install");
 auto native_resolver=original_animation;
 modern=false;
 char output[128]={};
 Check(!resolver(nullptr,"ZEC",output,false) && !strcmp(output,"ZCH"),"beetle must inherit imported spider animation family");
 Check(resolver(nullptr,"ZBB",output,false) && !strcmp(output,"ELM"),"invisible-man pet must inherit native elf family and flag");
 unsigned count=0;
 for(const auto& entry:kRegistrations) for(int mode=0;mode<2;++mode) {
  char native[128]={},actual[128]={};
  const bool expected_flag=native_resolver(nullptr,entry.skeleton,native,mode!=0);
  const char* expected=native;
  if(!strcmp(native,entry.skeleton)) expected=entry.alias;
  else for(const auto& parent:kRegistrations)
   if(!strcmp(native,parent.skeleton)) { expected=parent.alias;break; }
  modern=false;
  Check(resolver(nullptr,entry.alias,actual,mode!=0)==expected_flag,"native sharing flag");
  Check(!strcmp(actual,expected),"native sharing family");
  modern=true;
  char untouched[128]={};
  const bool untouched_flag=native_resolver(nullptr,entry.alias,untouched,mode!=0);
  Check(resolver(nullptr,entry.alias,actual,mode!=0)==untouched_flag && !strcmp(actual,untouched),"modern alias passthrough");
  modern=false;
  Check(resolver(nullptr,entry.skeleton,actual,mode!=0)==expected_flag && !strcmp(actual,native),"native code passthrough");
  ++count;
 }
 modern=false;
 Check(!resolver(nullptr,"ZQV",output,false) && !strcmp(output,"ZQV"),"typed water elemental keeps ELE skeleton family");
 std::cout << "PASS: beetle, enchanter, elemental and " << count << " native family/flag cases; modern/native passthrough\n";
 VirtualFree(image,0,MEM_RELEASE);
}

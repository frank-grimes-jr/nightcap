#include "../src/dllmain.cpp"
#include <wincrypt.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
#pragma comment(lib, "advapi32.lib")
static void Check(bool okay,const char* message) {
 if(!okay){std::cerr<<"FAIL: "<<message<<'\n';ExitProcess(2);}
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
struct Definition { BYTE bytes[0x63c] = {}; };
struct Counts { volatile LONG all=2, strong=1; };
struct Handle { Counts* counts; Definition* data; };
struct Node { Counts* counts; Definition* data; uint32_t id; Node* next=nullptr; };
struct Cache { Node** buckets; uint32_t size=1, used=1, count=1; };
static LONG WINAPI Increment(volatile LONG* p){return InterlockedIncrement(p);}
static LONG WINAPI Decrement(volatile LONG* p){return InterlockedDecrement(p);}
static LONG WINAPI CompareExchange(volatile LONG* p,LONG n,LONG old){return InterlockedCompareExchange(p,n,old);}
static int freed=0;
static void* allocated=nullptr;
static void __cdecl FreeNativeControl(void* p,int flags) {
 Check(p==allocated&&flags==0,"unexpected native control deletion");
 auto c=static_cast<Counts*>(p);Check(c->all==0&&c->strong==0,"premature native destruction");
 ++freed;Check(HeapFree(GetProcessHeap(),0,p)!=FALSE,"control free");allocated=nullptr;
}
static void* parser_tail=nullptr;
__declspec(naked) static void DeserializeDefinitionTail(void*) {
 __asm {
  push ebp
  push ebx
  push edi
  sub esp,40h
  mov ebx,dword ptr [esp+50h]
  lea edi,[ebx+140h]
  call dword ptr [parser_tail]
  add esp,40h
  pop edi
  pop ebx
  pop ebp
  ret
 }
}
int main(int argc,char** argv) {
 AddVectoredExceptionHandler(1,[](PEXCEPTION_POINTERS p)->LONG {
  std::cerr << "native exception " << std::hex << p->ExceptionRecord->ExceptionCode << " RVA " << (p->ContextRecord->Eip-g_eq_base) << " ESP " << p->ContextRecord->Esp << " EBX " << p->ContextRecord->Ebx << " EDI " << p->ContextRecord->Edi << '\n';
  return EXCEPTION_CONTINUE_SEARCH;
 });
 Check(argc==2,"pass pinned eqgame.exe");
 BYTE* image=LoadClient(argv[1]);g_eq_base=reinterpret_cast<uintptr_t>(image);
 *reinterpret_cast<void**>(image+0x5c0190)=reinterpret_cast<void*>(&Increment);
 *reinterpret_cast<void**>(image+0x5c0194)=reinterpret_cast<void*>(&Decrement);
 *reinterpret_cast<void**>(image+0x5c0188)=reinterpret_cast<void*>(&CompareExchange);
 using Intern=Handle* (__thiscall*)(Cache*,Handle*,Handle*);
 auto original=reinterpret_cast<Intern>(image+0x156610);
 using Release=void (__thiscall*)(Handle*);
 auto release=reinterpret_cast<Release>(image+0xd6bb0);
 Check(!ApplyPaladinGripDefinitionPatch(g_eq_base,false),"version guard ignored");
 const BYTE saved=image[kGripDefinitionInternCallRva];image[kGripDefinitionInternCallRva]=0x90;
 Check(!ApplyPaladinGripDefinitionPatch(g_eq_base,true),"wrong patch bytes accepted");
 image[kGripDefinitionInternCallRva]=saved;
 Check(ApplyPaladinGripDefinitionPatch(g_eq_base,true),"install production hook");
 parser_tail=image+0x155738;
 // Only stop the parser after its real intern/copy/release block. All calls,
 // shared-reference branches and the patched CALL itself execute unchanged.
 image[0x155794]=0xc3;
 const unsigned ids[]={5504,205504,405504,605504,11050,211050,411050,611050,10099,810099};
 for(auto id:ids) for(unsigned current=0;current<2;++current) {
  Definition old_definition,new_definition;
  *reinterpret_cast<unsigned*>(old_definition.bytes+0xec)=id;
  *reinterpret_cast<unsigned*>(new_definition.bytes+0xec)=id;
  old_definition.bytes[0x1d4]=static_cast<BYTE>(current);
  new_definition.bytes[0x1d4]=static_cast<BYTE>(1-current);
  Counts old_counts,new_counts;new_counts.all=1;
  Node node{&old_counts,&old_definition,id};Node* bucket=&node;Cache cache{&bucket};
  Handle incoming{&new_counts,&new_definition},out{};
  Check(original(&cache,&out,&incoming)==&out,"native cache return ABI");
  Check(out.data==&old_definition,"stock reproducer must reuse same-ID stale definition");
  release(&out);Check(old_counts.all==2&&old_counts.strong==1,"stock reference balance");
  KeepPaladinGripDefinition(&cache,nullptr,reinterpret_cast<GripDefinitionRef*>(&out),reinterpret_cast<GripDefinitionRef*>(&incoming));
  Check(out.data==&new_definition,"same-ID toggle retained cached old grip");
  Check(old_definition.bytes[0x1d4]==current,"other same-ID instance changed");
  Check(new_counts.all==2&&new_counts.strong==2,"incoming definition not retained correctly");
  Check(node.data==&old_definition,"shared cache mutated");
  release(&out);Check(new_counts.all==1&&new_counts.strong==1,"hook reference leak");
  BYTE item[0x150]={};*reinterpret_cast<void**>(item)=image+0x5caf74;
  *reinterpret_cast<Handle*>(item+0x140)=incoming;
  *reinterpret_cast<void**>(image+0xa63958)=&cache;
  DeserializeDefinitionTail(item);
  using ItemType=int (__thiscall*)(void*);
  Check(reinterpret_cast<ItemType>(image+kItemTypeRva)(item)==int(1-current),"native item-type accessor retained old grip");
  Check(reinterpret_cast<Handle*>(item+0x140)->data==&new_definition,"parser replaced instance definition");
  Check(new_counts.all==1&&new_counts.strong==1,"parser/reference lifetime imbalance");
  Check(old_counts.all==2&&old_counts.strong==1,"cached peer/reference count changed");
  // Execute the stock parser too, retaining a second owning reference so its
  // replacement of this stack-backed fixture cannot free it. Stock must keep
  // the old grip; the production call patch must make the opposite result.
  Check(RestoreGuardedRelativeCall(g_eq_base,kGripDefinitionInternCallRva,kExpectedGripDefinitionInternCall,
      reinterpret_cast<uintptr_t>(&KeepPaladinGripDefinition),"stock regression control"),"restore stock call");
  Increment(&new_counts.all);Increment(&new_counts.strong);
  DeserializeDefinitionTail(item);
  Check(reinterpret_cast<ItemType>(image+kItemTypeRva)(item)==int(current),"stock parser did not reproduce stale grip");
  Check(new_counts.all==1&&new_counts.strong==1,"stock parser did not release replaced definition");
  release(reinterpret_cast<Handle*>(item+0x140));
  Check(old_counts.all==2&&old_counts.strong==1,"stock parser cached peer lifetime");
  Check(ApplyPaladinGripDefinitionPatch(g_eq_base,true),"restore production hook");
  // Unrelated weapons still use the unmodified native interning routine.
  node.id=5379;*reinterpret_cast<unsigned*>(new_definition.bytes+0xec)=5379;
  KeepPaladinGripDefinition(&cache,nullptr,reinterpret_cast<GripDefinitionRef*>(&out),reinterpret_cast<GripDefinitionRef*>(&incoming));
  Check(out.data==&old_definition,"unrelated item bypassed native cache");release(&out);
 }
 // Run native final release too, with the native inline control/data layout.
 auto deletion=image+0x5fee0;deletion[0]=0xe9;
 *reinterpret_cast<int32_t*>(deletion+1)=static_cast<int32_t>(reinterpret_cast<uintptr_t>(&FreeNativeControl)-reinterpret_cast<uintptr_t>(deletion+5));
 for(auto id:ids) {
  allocated=HeapAlloc(GetProcessHeap(),HEAP_ZERO_MEMORY,8+sizeof(Definition));Check(allocated!=nullptr,"control allocate");
  auto counts=static_cast<Counts*>(allocated);counts->all=counts->strong=1;
  auto data=reinterpret_cast<Definition*>(static_cast<BYTE*>(allocated)+8);
  *reinterpret_cast<unsigned*>(data->bytes+0xec)=id;
  Handle incoming{counts,data},out{};
  KeepPaladinGripDefinition(nullptr,nullptr,reinterpret_cast<GripDefinitionRef*>(&out),reinterpret_cast<GripDefinitionRef*>(&incoming));
  release(&incoming);Check(counts->all==1&&counts->strong==1,"one owner release freed retained item");
  release(&out);Check(allocated==nullptr,"final native release leaked");
 }
 Check(freed==10,"final native destruction count");
 puts("PASS: native cache reproducer and per-instance grip isolation in both directions for all ten IDs");
 VirtualFree(image,0,MEM_RELEASE);return 0;
}

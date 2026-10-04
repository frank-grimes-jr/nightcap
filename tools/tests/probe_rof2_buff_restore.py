"""Exercise RoF2's actual OP_Buff handler with the repository's mode translation.

Reads the pinned original executable; never changes or launches the game.
The copied handler runs in a separate x86 test process with slot/refresh stubs.
This proves the packet boundary, not a complete interactive login.
"""
import argparse
import hashlib
import os
from pathlib import Path
import struct
import subprocess


def pe_bytes(raw, va, count):
    pe = struct.unpack_from('<I', raw, 0x3c)[0]
    sections, opt_size = struct.unpack_from('<H', raw, pe + 6)[0], struct.unpack_from('<H', raw, pe + 20)[0]
    base = struct.unpack_from('<I', raw, pe + 24 + 28)[0]
    for i in range(sections):
        off = pe + 24 + opt_size + 40 * i
        size, rva, raw_size, pos = struct.unpack_from('<IIII', raw, off + 8)
        if rva <= va-base and va-base+count <= rva+raw_size:
            return raw[pos+va-base-rva:pos+va-base-rva+count]
    raise ValueError('Native code range is not mapped')


CPP = r'''
#include <windows.h>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <stdexcept>
#include "handler.h"
struct Buff {
 uint8_t type,level,u2,u3; float modifier; uint32_t spell; int32_t duration;
 uint32_t caster,hits; float y,x,z; uint32_t u36; int32_t slot_data[12];
};
struct Packet { uint32_t entity; Buff buff; uint32_t slotid,bufffade; };
static_assert(sizeof(Buff)==88 && sizeof(Packet)==100, "RoF2 layout changed");
Buff slots[97] = {};
int refreshes=0;
unsigned char client[0x4000] = {};
uintptr_t client_ptr=reinterpret_cast<uintptr_t>(client);
uintptr_t spell_vtable[4]={}; uintptr_t* spell_manager=spell_vtable;
uintptr_t spell_manager_ptr=reinterpret_cast<uintptr_t>(&spell_manager);
unsigned char spell[0x300]={};
Buff* __fastcall GetSlot(void*,void*,unsigned i) { if(i>=97) ExitProcess(7); return &slots[i]; }
int __fastcall Count(void*,void*) { return 97; }
int __fastcall Refresh(void*,void*,int) { ++refreshes; return 0; }
void* __fastcall GetSpell(void*,void*,unsigned) { return spell; }
void __fastcall Remove(void*,void*,Buff* b,int,int) { *b={}; }
int __fastcall PlayerType(void*,void*) { return 0; }
void* handler=nullptr;
__declspec(naked) void Run(int,int,Packet*) {
 __asm {
  push ebp
  mov ebp,esp
  sub esp,1000h
  mov byte ptr [esp],0
  sub esp,1000h
  mov byte ptr [esp],0
  sub esp,1000h
  mov byte ptr [esp],0
  sub esp,1000h
  mov byte ptr [esp],0
  sub esp,1000h
  mov byte ptr [esp],0
  sub esp,500h
  mov byte ptr [esp],0
  push ebx
  push esi
  push edi
  call dword ptr [handler]
  pop edi
  pop esi
  pop ebx
  mov esp,ebp
  pop ebp
  ret
 }
}
void check(bool ok,const char* msg) { if(!ok) throw std::runtime_error(msg); }
void InitializeHandler() {
 auto p=static_cast<unsigned char*>(VirtualAlloc(nullptr,sizeof(native_handler)+1,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
 check(p!=nullptr,"allocation failed"); memcpy(p,native_handler,sizeof(native_handler));
 constexpr uintptr_t origin=0x4c7430;
 // Only external object accessors and the dispatcher's exit are replaced.
 // The native mode branches, matching loop, 88-byte copies and refresh calls remain.
 auto call=[&](uintptr_t va,void* target) {
  check(p[va-origin]==0xe8,"unexpected native call");
  *reinterpret_cast<int32_t*>(p+va-origin+1)=static_cast<int32_t>(reinterpret_cast<uintptr_t>(target)-reinterpret_cast<uintptr_t>(p+va-origin+5));
 };
 call(0x4c7465,GetSlot); call(0x4c74a1,Refresh); call(0x4c74c5,PlayerType);
 call(0x4c74ea,Count); call(0x4c7544,GetSlot); call(0x4c75a1,Remove); call(0x4c75c9,Refresh);
 for(size_t i=0;i+4<=sizeof(native_handler);++i) {
  auto v=reinterpret_cast<uint32_t*>(p+i);
  if(*v==0xdd261c) *v=reinterpret_cast<uint32_t>(&client_ptr);
  else if(*v==0xe646b0) *v=reinterpret_cast<uint32_t>(&spell_manager_ptr);
 }
 check(p[0x4c75d3-origin]==0xe9,"unexpected dispatcher exit");
 *reinterpret_cast<int32_t*>(p+0x4c75d4-origin)=0;
 p[sizeof(native_handler)]=0xc3;
 DWORD old; check(VirtualProtect(p,sizeof(native_handler)+1,PAGE_EXECUTE_READ,&old)!=0,"code protection failed");
 FlushInstructionCache(GetCurrentProcess(),p,sizeof(native_handler)+1);
 spell_vtable[3]=reinterpret_cast<uintptr_t>(GetSpell); handler=p;
}
uint32_t EncodeMode(uint32_t mode) {
 struct Canonical { uint32_t bufffade; struct { uint32_t counters; } buff; };
 Canonical input={}; Packet output={}; input.bufffade=mode; input.buff.counters=42;
 auto emu=&input; auto eq=&output;
 ENCODER_BODY
 if(mode==3 && output.bufffade==3) check(output.buff.slot_data[0]==42,"restore counter lost in translation");
 return output.bufffade;
}
int main() {
 try {
  InitializeHandler();
  Packet p={}; p.buff.type=2; p.buff.level=50; p.buff.modifier=1;
  p.buff.spell=278; p.buff.duration=-1; p.buff.caster=123; p.slotid=2;
  p.bufffade=EncodeMode(0); Run(0,0,&p);
  check(slots[2].type==0 && refreshes==0,"ordinary update unexpectedly installed absent effect");
  p.bufffade=EncodeMode(3); Run(0,0,&p);
  check(memcmp(&slots[2],&p.buff,sizeof(Buff))==0,"reconnect packet failed to restore native effect");
  check(refreshes==1,"restore did not refresh native effects");
  // Repeat for Matron/Magus's full rank ladder, finite/permanent durations,
  // metadata/counter preservation, sparse slots and the short-buff boundary.
  for(auto id : {26,89,144,145,174,202,219,244,263,278,312,421,422,423,697,21030}) {
   for(auto slot : {0,2,41,42,96}) for(auto duration : {-1000,-1,60,2400}) {
    p.slotid=slot; p.buff.spell=id; p.buff.duration=duration; p.buff.hits=7;
    p.buff.slot_data[0]=42; p.buff.y=2; p.buff.x=3; p.buff.z=4;
    slots[slot]={}; Run(0,0,&p);
    check(memcmp(&slots[slot],&p.buff,sizeof(Buff))==0,"restore lost buff fields");
    Run(0,0,&p);
    check(memcmp(&slots[slot],&p.buff,sizeof(Buff))==0,"repeat restore changed state");
   }
  }
  p.bufffade=EncodeMode(0); p.buff.duration=19; Run(0,0,&p);
  check(slots[p.slotid].duration==19,"existing duration update broken");
  p.bufffade=EncodeMode(1); Run(0,0,&p);
  check(slots[p.slotid].type==0,"fade no longer removes effects");
  puts("PASS: exact RoF2 handler; 320 restoration cases plus update/fade/idempotence controls");
 } catch(const std::exception& e) { fprintf(stderr,"%s\n",e.what()); return 1; }
}
'''.replace('#include <cstdio>', '#include <cstdio>\n#include <initializer_list>')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--client', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args=ap.parse_args()
    raw=args.client.read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e', 'Unverified client'
    code=pe_bytes(raw,0x4c7430,0x4c75d8-0x4c7430)
    src=(args.repo/'server-mods/code/common/patches/rof2.cpp').read_text()
    start=src.index('if (emu->bufffade == 1)',src.index('ENCODE(OP_Buff)'))
    end=src.index('// Bit of a hack.',start)
    body=src[start:end]
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'handler.h').write_text('const unsigned char native_handler[]={'+','.join(map(str,code))+'};\n')
    (args.out/'probe.cpp').write_text(CPP.replace('ENCODER_BODY',body))
    (args.out/'build.cmd').write_text('@echo off\ncall "C:\\BuildTools\\VC\\Auxiliary\\Build\\vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /std:c++17 probe.cpp /Fe:probe.exe >build.log 2>&1\nexit /b %errorlevel%\n')
    env=dict(os.environ,TEMP=str(args.out.resolve()),TMP=str(args.out.resolve()))
    build=subprocess.run(['cmd','/d','/c',str((args.out/'build.cmd').resolve())],cwd=args.out,env=env)
    if build.returncode: raise RuntimeError((args.out/'build.log').read_text())
    result=subprocess.run([str((args.out/'probe.exe').resolve())],capture_output=True,text=True)
    print(result.stdout+result.stderr,end='')
    (args.out/'result.txt').write_text(result.stdout+result.stderr+f'Exit code: {result.returncode}\n')
    raise SystemExit(result.returncode)


if __name__=='__main__': main()

"""Run pinned RoF2 buff expiry/tick bytes against actual server duration helpers.

Reads the original client executable, spells_us.txt, and repository source.
It builds an isolated x86 probe; it never runs or modifies the game client.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import struct
import subprocess

SHA256 = '2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e'
BLESSINGS = (26, 89, 144, 145, 174, 202, 219, 244, 263, 278, 312, 421, 422, 423, 697, 21030)


def pe_bytes(raw, va, count):
    pe = struct.unpack_from('<I', raw, 0x3c)[0]
    sections, opt_size = struct.unpack_from('<H', raw, pe + 6)[0], struct.unpack_from('<H', raw, pe + 20)[0]
    base = struct.unpack_from('<I', raw, pe + 24 + 28)[0]
    for i in range(sections):
        off = pe + 24 + opt_size + 40 * i
        _, rva, raw_size, pos = struct.unpack_from('<IIII', raw, off + 8)
        if rva <= va - base and va - base + count <= rva + raw_size:
            return raw[pos + va - base - rva:pos + va - base - rva + count]
    raise ValueError('Native code range is not mapped')


def method(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 0
    for i in range(opening, len(source)):
        depth += (source[i] == '{') - (source[i] == '}')
        if depth == 0:
            return source[start:i + 1]
    raise ValueError('Unclosed source method')


def spell_formulas(path):
    found = {}
    for row in path.open(encoding='utf-8', errors='replace'):
        fields = row.rstrip('\n').split('^')
        if fields[0].isdigit() and int(fields[0]) in BLESSINGS:
            found[int(fields[0])] = int(fields[16])
    assert set(found) == set(BLESSINGS), 'Missing installed blessing spells'
    return found


CPP = r'''
#include <windows.h>
#include <cstdint>
#include <cstring>
#include <cstdio>
#include <initializer_list>
using int32 = int32_t;
#define PERMANENT_BUFF_DURATION -1000
namespace EQ { namespace versions { enum class ClientVersion { RoF, RoF2 }; } }
struct Mob { static int32 BuffDurationForClient(int32); };
struct Client : Mob {
 EQ::versions::ClientVersion version=EQ::versions::ClientVersion::RoF2;
 EQ::versions::ClientVersion ClientVersion() const { return version; }
 int32 BuffEffectDurationForClient(int32) const;
};
OLD_HELPER
NEW_HELPER
static const unsigned char decisionSource[] = {DECISION};
static const unsigned char tickSource[] = {TICK};
static void* decision;
static void* tick;
extern "C" __declspec(naked) int Decide(void*, void*) {
 __asm {
  push ebp
  push edi
  push ebx
  sub esp,32
  mov byte ptr [esp+0x0e],0
  mov ebp,[esp+48]
  mov edi,[esp+52]
  mov eax,[decision]
  call eax
  movzx eax,byte ptr [esp+0x0e]
  add esp,32
  pop ebx
  pop edi
  pop ebp
  ret
 }
}
extern "C" __declspec(naked) void Tick(void*) {
 __asm {
  push ebp
  mov ebp,[esp+8]
  mov eax,[tick]
  call eax
  pop ebp
  ret
 }
}
void install(const unsigned char* src,size_t n,void** target) {
 auto p=(unsigned char*)VirtualAlloc(nullptr,n+1,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
 if(!p) ExitProcess(2);
 memcpy(p,src,n);p[n]=0xc3;
 DWORD old=0;if(!VirtualProtect(p,n+1,PAGE_EXECUTE_READ,&old)) ExitProcess(3);
 FlushInstructionCache(GetCurrentProcess(),p,n+1);*target=p;
}
void test(int formula,int oldWire,int newWire,int expectedNew,int id) {
 unsigned char spell[0x30]={},buff[0x30]={};
 memcpy(spell+0x1c,&formula,4);
 memcpy(buff+0x0c,&oldWire,4);
 int red=Decide(buff,spell);
 if(red!=(formula!=50)) {printf("FAIL old id=%d formula=%d wire=%d expire=%d\n",id,formula,oldWire,red);ExitProcess(4);}
 memcpy(buff+0x0c,&newWire,4);
 int green=Decide(buff,spell);
 if(green!=expectedNew) {printf("FAIL new id=%d formula=%d wire=%d expire=%d expected=%d\n",id,formula,newWire,green,expectedNew);ExitProcess(5);}
 for(int i=0;i<5;i++) Tick(buff);
 int after=0;memcpy(&after,buff+0x0c,4);
 if(after!=newWire) {printf("FAIL countdown id=%d wire=%d after=%d\n",id,newWire,after);ExitProcess(6);}
}
int main() {
 install(decisionSource,sizeof(decisionSource),&decision);
 install(tickSource,sizeof(tickSource),&tick);
 Client c;
 if(Mob::BuffDurationForClient(-1000)!=-1 || c.BuffEffectDurationForClient(-1000)!=-1000) return 7;
 for(int duration : {-4,-1,0,1,2,19,2400,2147483647})
  if(c.BuffEffectDurationForClient(duration)!=duration) return 8;
 int cases=0;
 struct SpellCase {int id;int formula;};
 static const SpellCase installed[] = {SPELLS};
 for(const auto& s : installed) {
  if(s.id==21030) {
   // Magus's XP draught explicitly lasts 2400 ticks; it is not permanent.
   unsigned char spell[0x30]={},buff[0x30]={};
   int duration=2400;memcpy(spell+0x1c,&s.formula,4);memcpy(buff+0x0c,&duration,4);
   if(c.BuffEffectDurationForClient(duration)!=duration || Decide(buff,spell)) return 13;
   Tick(buff);int after=0;memcpy(&after,buff+0x0c,4);
   if(after!=2399 || Decide(buff,spell)) return 14;
  } else {
   test(s.formula,Mob::BuffDurationForClient(-1000),c.BuffEffectDurationForClient(-1000),0,s.id);
  }
  c.version=EQ::versions::ClientVersion::RoF;
  if(c.BuffEffectDurationForClient(-1000)!=-1) return 9;
  c.version=EQ::versions::ClientVersion::RoF2;
  ++cases;
 }
 for(int formula : {3,10,11,50,3600}) for(int duration : {-1000,-4,-1,0,1,2,2147483647}) {
  unsigned char spell[0x30]={},buff[0x30]={};memcpy(spell+0x1c,&formula,4);memcpy(buff+0x0c,&duration,4);
  int first=Decide(buff,spell);
  if(first!=(duration==0 || (duration==-1 && formula!=50))) return 10;
  Tick(buff);int after=0;memcpy(&after,buff+0x0c,4);
  if(after!=(duration>0?duration-1:duration)) return 11;
  int second=Decide(buff,spell);
  if(second!=(after==0 || (after==-1 && formula!=50))) return 12;
  ++cases;
 }
 printf("PASS %d pinned native expiry/tick cases; 16 installed blessing formulas; old mapping red, RoF2 effect mapping green\n",cases);
}
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--client', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    raw = args.client.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SHA256, 'Unverified RoF2 client'
    decision = pe_bytes(raw, 0x43caff, 0x43cb1f - 0x43caff)
    tick = pe_bytes(raw, 0x43cb44, 0x43cb4f - 0x43cb44)
    assert decision.hex() == '8b450c85c07505c64424120183f8ff750f85ff740b837f1c327405c644241201'
    assert tick.hex() == '8b450c85c07e044889450c'
    source = (args.repo/'server-mods/code/zone/spells.cpp').read_text(encoding='utf-8')
    old = method(source, 'int32 Mob::BuffDurationForClient(int32 duration)')
    new = method(source, 'int32 Client::BuffEffectDurationForClient(int32 duration) const')
    spells = spell_formulas(args.client.parent/'spells_us.txt')
    initializer = ','.join('{'+str(i)+','+str(spells[i])+'}' for i in BLESSINGS)
    cpp = CPP.replace('OLD_HELPER', old).replace('NEW_HELPER', new)
    cpp = cpp.replace('DECISION', ','.join(map(str, decision))).replace('TICK', ','.join(map(str, tick)))
    cpp = cpp.replace('SPELLS', initializer)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/'probe.cpp').write_text(cpp)
    (args.out/'build.cmd').write_text('@echo off\ncall "C:\\BuildTools\\VC\\Auxiliary\\Build\\vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /std:c++17 probe.cpp /Fe:probe.exe >build.log 2>&1\nexit /b %errorlevel%\n')
    env = dict(os.environ, TEMP=str(args.out.resolve()), TMP=str(args.out.resolve()))
    build = subprocess.run(['cmd','/d','/c',str((args.out/'build.cmd').resolve())], cwd=args.out, env=env)
    if build.returncode:
        raise RuntimeError((args.out/'build.log').read_text())
    run = subprocess.run([str((args.out/'probe.exe').resolve())], cwd=args.out, capture_output=True, text=True)
    print(run.stdout+run.stderr,end='')
    (args.out/'result.txt').write_text(run.stdout+run.stderr+f'Exit code: {run.returncode}\n')
    raise SystemExit(run.returncode)


if __name__ == '__main__':
    main()

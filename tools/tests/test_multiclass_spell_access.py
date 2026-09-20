import subprocess
import tempfile
import unittest
from pathlib import Path
from test_gameplay_policies import ROOT, ZONE, function


class SpellAccess(unittest.TestCase):
    def test_cast_rechecks_current_classes_and_bounds_before_indexing(self):
        source = (ZONE/'client_packet.cpp').read_text()
        start = source.index('\t/* Memorized Spell */',source.index('void Client::Handle_OP_CastSpell('))
        body = source[start:source.index('\t/* Spell Slot or Potion Belt Slot */',start)]
        fixture = r'''
#include <cassert>
#include <cstdint>
#include "spell_class_catalog.h"
using uint16=uint16_t;
namespace EQ { namespace spells { enum { SPELL_GEM_COUNT=12 }; } }
namespace Chat { enum { Red=13 }; }
bool IsValidSpell(uint16 id) { return NightcapSpellClasses::Find(id)!=nullptr; }
struct Slots { int reads=0; uint16 values[12]={4};
 uint16 operator[](unsigned n) { assert(n<12); ++reads; return values[n]; }
};
struct Client {
 struct { unsigned slot=0; uint16 spell_id=4; unsigned target_id=0; } request;
 struct { Slots mem_spells; } m_pp;
 unsigned casts=0,interrupts=0,level=17,held=13;
 uint8_t GetSpellMinLevel(uint16 id) { return NightcapSpellClasses::Level(id,held); }
 unsigned GetLevel() { return level; }
 void InterruptSpell(uint16=0) { ++interrupts; }
 void CastSpell(uint16,unsigned,unsigned) { ++casts; }
 void Message(int,const char*) {}
 void Handle() { auto castspell=&request; auto slot=request.slot;
'''
        controls = r'''
 }};
int main() {
 Client c; c.Handle(); assert(c.casts==1 && c.interrupts==0);
 c.held=2; c.Handle(); assert(c.casts==1 && c.interrupts==1);
 c.held=13;c.level=16;c.Handle();assert(c.casts==1 && c.interrupts==2);
 c.level=17;c.request.spell_id=5;c.Handle();assert(c.casts==1);
 c.request.spell_id=4;
 for(unsigned slot : {12u,16u,255u,65535u}) {
  auto reads=c.m_pp.mem_spells.reads;c.request.slot=slot;c.Handle();
  assert(c.m_pp.mem_spells.reads==reads && c.casts==1);
 }
}
'''
        self.compile_and_run('#include <initializer_list>\n'+fixture+body+controls)

    def compile_and_run(self, code):
        with tempfile.TemporaryDirectory(prefix='nightcap-spell-gate-') as tmp:
            out=Path(tmp)
            (out/'test.cpp').write_text(code)
            include=ROOT/'server-mods/code/common'
            (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /std:c++17 /I"'+str(include)+'" test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
            build=subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
            self.assertEqual(build.returncode,0,(out/'build.log').read_text())
            result=subprocess.run([out/'test.exe'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_native_held_class_levels_ignore_legacy_global_widening(self):
        source = (ZONE/'client_mods.cpp').read_text()
        bodies = '\n'.join(function(source, sig) for sig in (
            'uint8 Client::GetSpellMinLevel(', 'uint8 Client::BestCasterClassFor('))
        fixture = r'''
#include <cassert>
#include <cstdint>
#include <vector>
#include "spell_class_catalog.h"
using uint8=uint8_t; using uint16=uint16_t;
namespace Class { enum { PLAYER_CLASS_COUNT=16 }; }
struct Spell { uint8 classes[16]={}; } spells[50000];
bool IsValidSpell(uint16 id) { return id>0 && id<45000; }
struct Client {
 std::vector<uint8> held;
 std::vector<uint8> GetMulticlassList() const { return held; }
 uint8 GetSpellMinLevel(uint16) const;
 uint8 BestCasterClassFor(uint16) const;
};
'''
        controls = r'''
int main() {
 // Summon Waterstone is originally MAG 17. Simulate globally widened DB rows.
 for(auto &level : spells[4].classes) level=1;
 Client monktest{{2,13,11}}, cleric{{2}}, reversed{{11,2,13}};
 assert(monktest.GetSpellMinLevel(4)==17 && monktest.BestCasterClassFor(4)==13);
 assert(reversed.GetSpellMinLevel(4)==17 && reversed.BestCasterClassFor(4)==13);
 assert(cleric.GetSpellMinLevel(4)==255 && cleric.BestCasterClassFor(4)==0);
 monktest.held={2,11}; assert(monktest.GetSpellMinLevel(4)==255);
 assert(monktest.GetSpellMinLevel(65535)==255 && monktest.GetSpellMinLevel(44999)==255);
 for(const auto &spell : NightcapSpellClasses::Catalog) {
  for(unsigned c=1;c<=16;++c) {
   Client single{{static_cast<uint8>(c)}};
   assert(single.GetSpellMinLevel(static_cast<uint16>(spell.id))==spell.levels[c-1]);
  }
 }
}
'''
        with tempfile.TemporaryDirectory(prefix='nightcap-spell-access-') as tmp:
            out=Path(tmp)
            (out/'test.cpp').write_text(fixture+bodies+controls)
            include=ROOT/'server-mods/code/common'
            (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /std:c++17 /I"'+str(include)+'" test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
            build=subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
            self.assertEqual(build.returncode,0,(out/'build.log').read_text())
            result=subprocess.run([out/'test.exe'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

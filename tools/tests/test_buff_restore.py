"""Compile actual reconnect/packet methods; dependency fakes do not simulate login."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_gameplay_policies import function

ROOT = Path(__file__).resolve().parents[2]
ZONE = ROOT / 'server-mods/code/zone'

FIXTURE = r'''
#include <cstdint>
#include <cstring>
#include <vector>
#include <stdexcept>
#include <iostream>
namespace EQ { namespace versions { enum class ClientVersion { UF, RoF, RoF2 }; } }
struct Buffs_Struct {
 int spellid=65535, casterlevel=0, instrument_mod=10, ticsremaining=0;
 int dot_rune=0, magic_rune=0, melee_rune=0, counters=0;
 int casterid=0, hit_number=0; float caston_y=0, caston_x=0, caston_z=0;
};
struct SpellBuff_Struct {
 int effect_type=0, level=0, bard_modifier=0, spellid=0, duration=0;
 int counters=0, player_id=0, num_hits=0; float y=0,x=0,z=0;
};
struct SpellBuffPacket_Struct { int entityid=0; SpellBuff_Struct buff; int slotid=0,bufffade=0; };
using int32 = int32_t;
constexpr int PERMANENT_BUFF_DURATION=-1000;
constexpr int OP_Buff=1;
struct EQApplicationPacket {
 unsigned char *pBuffer;
 EQApplicationPacket(int, size_t size):pBuffer(new unsigned char[size]()) {}
 ~EQApplicationPacket() { delete[] pBuffer; }
};
bool IsValidSpell(int id) { return id>0 && id<45000; }
struct Client {
 EQ::versions::ClientVersion version=EQ::versions::ClientVersion::RoF2;
 Buffs_Struct buffs[100]; std::vector<SpellBuffPacket_Struct> packets;
 auto ClientVersion() const { return version; }
 int GetMaxTotalSlots() const { return 100; }
 int GetID() const { return 123; } int GetLevel() const { return 30; }
 static int BuffDurationForClient(int duration) { return duration==-1000 ? -1 : duration; }
 int32 BuffEffectDurationForClient(int32 duration) const;
 void RestoreBuffEffects();
 void SendBuffDurationPacket(Buffs_Struct &buff, int slot, bool restore=false);
 void FastQueuePacket(EQApplicationPacket **p) {
  packets.push_back(*reinterpret_cast<SpellBuffPacket_Struct*>((*p)->pBuffer));
  delete *p; *p=nullptr;
 }
};
void check(bool ok,const char *why) { if(!ok) throw std::runtime_error(why); }
'''

CONTROLS = r'''
int main() {
 try {
  Client c;
  for(int duration : {-4,-1,0,1,19,2400}) check(c.BuffEffectDurationForClient(duration)==duration,"non-policy duration changed");
  check(c.BuffDurationForClient(-1000)==-1,"icon countdown encoding changed");
  c.RestoreBuffEffects(); check(c.packets.empty(),"empty slots emitted packets");
  for(int slot : {0,2,41,42,96,99}) {
   auto &b=c.buffs[slot]; b.spellid=278; b.casterlevel=50; b.ticsremaining=-1000;
   b.instrument_mod=15; b.casterid=456; b.hit_number=7; b.counters=42;
   b.caston_y=2; b.caston_x=3; b.caston_z=4;
  }
  c.buffs[1].spellid=0; c.buffs[3].spellid=45000;
  Buffs_Struct before[100]; std::memcpy(before,c.buffs,sizeof before);
  c.RestoreBuffEffects(); check(c.packets.size()==6,"valid sparse slots not restored");
  for(const auto &p : c.packets) {
   check(p.entityid==123 && p.bufffade==3,"wrong target/mode");
   check(p.buff.spellid==278 && p.buff.effect_type==2 && p.buff.level==50,"spell/level changed");
   check(p.buff.duration==-1000 && p.buff.bard_modifier==15,"native lifetime sentinel lost; finite-formula -1 expires on next tick");
   check(p.buff.counters==42 && p.buff.player_id==456 && p.buff.num_hits==7,"saved state lost");
   check(p.buff.y==2 && p.buff.x==3 && p.buff.z==4,"coordinates lost");
   check(IsValidSpell(c.buffs[p.slotid].spellid),"slot mapping changed");
  }
  c.RestoreBuffEffects(); check(c.packets.size()==12,"repeat restore missing");
  check(std::memcmp(before,c.buffs,sizeof before)==0,"restore mutated authoritative buff state");
  c.packets.clear();
  c.SendBuffDurationPacket(c.buffs[0],0);
  check(c.packets.back().bufffade==0 && c.packets.back().buff.duration==-1000,"deferred permanent duration update expires native effect");
  c.packets.clear(); c.version=EQ::versions::ClientVersion::RoF;
  c.RestoreBuffEffects(); check(c.packets.empty(),"older client received restore");
  c.SendBuffDurationPacket(c.buffs[0],0,true); check(c.packets.back().bufffade==0 && c.packets.back().buff.duration==-1,"older packet duration/mode changed");
  c.version=EQ::versions::ClientVersion::RoF2;
  auto &b=c.buffs[0]; b.ticsremaining=19; b.casterlevel=0;
  c.SendBuffDurationPacket(b,0); auto p=c.packets.back();
  check(p.bufffade==0 && p.buff.duration==19 && p.buff.level==30,"ordinary update changed");
  b.melee_rune=12; c.SendBuffDurationPacket(b,0,true); check(c.packets.back().buff.counters==12,"melee rune lost");
  b.magic_rune=13; c.SendBuffDurationPacket(b,0,true); check(c.packets.back().buff.counters==13,"magic rune lost");
  b.dot_rune=14; c.SendBuffDurationPacket(b,0,true); check(c.packets.back().buff.counters==14,"dot rune lost");
  std::cout << "PASS: reconnect packet state, sparse slots, repeat restore and legacy/update controls\n";
 } catch(const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
'''


class BuffRestore(unittest.TestCase):
    def test_actual_native_methods(self):
        source=(ZONE/'spells.cpp').read_text()
        bodies='\n'.join(function(source,s) for s in (
            'int32 Client::BuffEffectDurationForClient(', 'void Client::RestoreBuffEffects()', 'void Client::SendBuffDurationPacket('))
        with tempfile.TemporaryDirectory(prefix='nightcap-buff-restore-') as tmp:
            out=Path(tmp)
            (out/'test.cpp').write_text(FIXTURE+bodies+CONTROLS)
            if os.name=='nt':
                (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /WX /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
                result=subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
                self.assertEqual(result.returncode,0,(out/'build.log').read_text())
                exe=out/'test.exe'
            else:
                exe=out/'test'
                subprocess.run([shutil.which('c++'),'-std=c++17',str(out/'test.cpp'),'-o',str(exe)],check=True)
            result=subprocess.run([str(exe)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_profile_effects_use_native_duration_but_icons_keep_countdown_encoding(self):
        profile=(ZONE/'client_packet.cpp').read_text(encoding='utf-8')
        self.assertIn('m_pp.buffs[i].duration = BuffEffectDurationForClient(buffs[i].ticsremaining);',profile)
        source=(ZONE/'spells.cpp').read_text(encoding='utf-8')
        self.assertIn('sbf->buff.duration = BuffEffectDurationForClient(buff.ticsremaining);',source)
        for statement in (
            'bi->entries[0].tics_remaining = BuffDurationForClient(buff.ticsremaining);',
            'pbs->ticsremaining[buffslot] = BuffDurationForClient(buffs[buffslot].ticsremaining);',
            'buff->entries[index].tics_remaining = BuffDurationForClient(buffs[i].ticsremaining);'):
            self.assertIn(statement,source)

    def test_restore_after_ready_queue_before_quest_events(self):
        body=function((ZONE/'client_packet.cpp').read_text(),'void Client::CompleteConnect()')
        self.assertEqual(body.count('RestoreBuffEffects();'),1)
        self.assertLess(body.index('client_state = CLIENT_CONNECTED'),body.index('SendAllPackets();'))
        self.assertLess(body.index('SendAllPackets();'),body.index('RestoreBuffEffects();'))
        self.assertLess(body.index('RestoreBuffEffects();'),body.index('EVENT_CONNECT'))


if __name__=='__main__': unittest.main()

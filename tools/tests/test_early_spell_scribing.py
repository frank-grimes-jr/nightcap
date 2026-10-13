"""Execute the production packet/scroll methods with isolated inventory state."""
from test_gameplay_policies import ZONE, function
import unittest
import test_multiclass_spell_access


class EarlyScribing(unittest.TestCase):
    compile_and_run = test_multiclass_spell_access.SpellAccess.compile_and_run
    def test_scribing_and_memorization(self):
        methods = '\n'.join(function((ZONE / name).read_text(), sig) for name, sig in (
            ('client_process.cpp', 'void Client::OPMemorizeSpell('),
            ('effects.cpp', 'bool Client::MemorizeSpellFromItem('),
            ('client_mods.cpp', 'uint8 Client::GetSpellMinLevel(')))
        fixture = r'''
#include <cassert>
#include <cstdint>
#include <string>
#include <vector>
#include "spell_class_catalog.h"
using uint8=uint8_t; using uint16=uint16_t; using uint32=uint32_t; using int32=int32_t;
namespace Class { enum { PLAYER_CLASS_COUNT=16 }; }
namespace Chat { enum { Red=13 }; }
namespace EQ { namespace invslot { enum { slotCursor=0 }; }
 namespace spells { enum { SPELLBOOK_SIZE=720 }; }
 namespace item { enum { ItemTypeSpell=20 }; } }
namespace PlayerEvent { enum { POSSIBLE_HACK }; struct PossibleHackEvent { std::string message; }; }
namespace fmt { template<class... T> std::string format(const char* s,T...) { return s; } }
namespace Strings { bool BeginsWith(const std::string& s,const char* p) { return s.find(p)==0; } }
enum { memSpellScribing=0,memSpellMemorize=1,memSpellForget=2,SPELL_LEVEL_TO_LOW,CANNOT_USE_ITEM,SPDAT_RECORDS=50000 };
struct MemorizeSpell_Struct { uint32 slot=0,spell_id=4,scribing=0; };
struct EQApplicationPacket { unsigned size=sizeof(MemorizeSpell_Struct); void* pBuffer; };
struct Spell { const char* name="test"; } spells[SPDAT_RECORDS];
bool IsValidSpell(uint32 id) { return id>0 && id<45000; }
bool IsPlayerClass(unsigned id) { return id>=1 && id<=16; }
template<class... T> void LogError(T...) {}
void DumpPacket(const EQApplicationPacket*) {}
bool restrict_scribing=true;
#define RuleB(a,b) restrict_scribing
struct Item { uint32 Classes=65535; int ItemType=20; const char* Name="Spell: Test";
 struct { int32 Effect=4; } Scroll; bool IsClassCommon() const { return true; } } item;
struct Inst { bool IsClassCommon() const { return true; } const Item* GetItem() const { return &item; } } inst;
struct Database { const Item* GetItem(uint32) { return &item; } } database;
struct Client {
 std::vector<uint8> held={2,13,11}; unsigned level=1; bool equip=true,known=false;
 int next_slot=0; Inst* m_inv[1]={&inst}; unsigned scribes=0,deletes=0,mems=0,forgets=0,refunds=0;
 uint8 GetSpellMinLevel(uint16) const;
 std::vector<uint8> GetMulticlassList() const { return held; }
 unsigned GetClass() { return held[0]; } unsigned GetLevel() { return level; }
 template<class... T> void Message(T...) {} template<class... T> void MessageString(T...) {}
 template<class... T> void RecordPlayerEventLog(T...) {}
 bool CanEquipItem(const Item*) { return equip; }
 void ScribeSpell(uint32,int) { ++scribes; known=true; }
 void DeleteItemInInventory(int,int,bool) { ++deletes; }
 bool HasSpellScribed(uint32) { return known; }
 int GetNextAvailableSpellBookSlot() { return next_slot; }
 void MemSpell(uint32,uint32) { ++mems; } void UnmemSpell(uint32) { ++forgets; }
 void SummonItem(uint32) { ++refunds; } void Save() {}
 void OPMemorizeSpell(const EQApplicationPacket*);
 bool MemorizeSpellFromItem(uint32);
 void Packet(unsigned action=0,unsigned spell=4,unsigned slot=0) {
  MemorizeSpell_Struct request{slot,spell,action}; EQApplicationPacket app{sizeof(request),&request};
  OPMemorizeSpell(&app);
 }
};
'''
        controls = r'''
int main() {
 for(auto held : {std::vector<uint8>{13}, {2,13}, {2,11,13}}) {
  Client c; c.held=held; c.Packet(); assert(c.scribes==1 && c.deletes==1);
  c.Packet(memSpellMemorize); assert(c.mems==0);
  c.level=16;c.Packet(memSpellMemorize);assert(c.mems==0);
  c.level=17;c.Packet(memSpellMemorize);assert(c.mems==1);
  c.held={2,11};c.Packet(memSpellMemorize);assert(c.mems==1);
  c.Packet(memSpellForget);assert(c.forgets==1);
  Client item_client;item_client.held=held;
  assert(item_client.MemorizeSpellFromItem(1) && item_client.scribes==1 && item_client.mems==0);
 }
 for(bool restriction : {false,true}) {
  restrict_scribing=restriction;
  for(unsigned level : {1u,50u,255u}) {
   Client c;c.held={2,11};c.level=level;c.Packet();
   assert(c.scribes==0 && c.deletes==0);
   assert(!c.MemorizeSpellFromItem(1) && c.refunds==1);
   c.known=true;c.Packet(memSpellMemorize);assert(c.mems==0);
  }
 }
 Client mismatch; item.Scroll.Effect=5;mismatch.Packet();assert(!mismatch.deletes);item.Scroll.Effect=4;
 Client missing;missing.m_inv[0]=nullptr;missing.Packet();assert(!missing.scribes && !missing.deletes);
 Client restricted;restricted.equip=false;restricted.Packet();assert(!restricted.deletes);
 Client unknown;unknown.Packet(0,44999);assert(!unknown.scribes && !unknown.deletes);
 Client invalid;invalid.Packet(0,65535);assert(!invalid.scribes && !invalid.deletes);
 Client duplicate;duplicate.known=true;assert(!duplicate.MemorizeSpellFromItem(1) && duplicate.refunds==1);
 Client full;full.next_slot=-1;assert(!full.MemorizeSpellFromItem(1) && full.refunds==1);
 Client unscribed;unscribed.level=17;unscribed.Packet(memSpellMemorize);assert(!unscribed.mems);
}
'''
        self.compile_and_run(fixture + methods + controls, standard='c++20')

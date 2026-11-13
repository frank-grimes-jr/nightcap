"""Compile the actual native reagent block, including one-shot Bard delivery."""
import unittest
from test_pet_equipment import ROOT, compile_run
from test_gameplay_policies import function

class Reagents(unittest.TestCase):
    def test_native_instruments_and_ordinary_reagents(self):
        source=(ROOT/'server-mods/code/zone/spells.cpp').read_text(encoding='utf-8')
        region=source[source.index('// Quick Buff delivers songs once,'):]
        mode=region[region.index('const bool bard_component_mode'):region.index('// Check for consumables')]
        block=function(region,'if(IsClient())')
        fixture=r'''
#include <cassert>
#include <cstring>
namespace Chat {enum {Red,White};}
namespace SpellEffect {enum {SummonPet,NecPet};}
enum {INSTRUMENT_HAND_DRUM=13000,INSTRUMENT_WOODEN_FLUTE=13001,INSTRUMENT_LUTE=13011,INSTRUMENT_HORN=13012,
 SONG_NEEDS_DRUM,SONG_NEEDS_WIND,SONG_NEEDS_STRINGS,SONG_NEEDS_BRASS,MISSING_SPELL_COMP,MISSING_SPELL_COMP_ITEM,
 focusReagentCost,invWhereWorn=1,invWherePersonal=2};
namespace EQ {struct ItemData {const char* Name="component";int CastTime=1;};}
struct Database {EQ::ItemData value;const EQ::ItemData* GetItem(int){return &value;}} database;
struct Item {EQ::ItemData value;const EQ::ItemData* GetItem(){return &value;}};
enum class CastingSlot {AltAbility,Item,PotionBelt};
struct Spell {int component[4]={-1,-1,-1,-1},component_count[4]={1,0,0,0},no_expend_reagent[4]={-1,-1,-1,-1};} spells[2000];
bool IsBardSong(int s){return s==719||s==1448;}
bool IsEffectInSpell(int,int){return false;}
struct Random {bool Roll(int){return false;}};
struct Zone {Random random;} actual_zone;auto* zone=&actual_zone;
#define RuleB(group,key) true
#define LogSpells(...) ((void)0)
struct Client {
 bool failed=false,completed=false;int primary=2,deleted=0;
 struct Bonuses {int percussionMod=0,windMod=0,stringedMod=0,brassMod=0;} itembonuses;
 struct Inventory {bool has=false;int queries=0;int HasItem(int,int,int){++queries;return has?1:-1;}} inventory;
 bool IsClient(){return true;}Client* CastToClient(){return this;}
 int GetFocusEffect(int,int){return 0;}bool GetGM(){return false;}
 Inventory& GetInv(){return inventory;}
 template<class...T>void MessageString(T...){}template<class...T>void Message(T...){}
 void InterruptSpell(){failed=true;}void DeleteItemInInventory(int,int,bool){++deleted;}
 void run(int spell_id,bool quick_buff){
  bool bard_song_mode=false;Item* item=nullptr;auto slot=CastingSlot::AltAbility;
// MODE
// BLOCK
  assert(!bard_song_mode);completed=true;
 }
};
int main(){
 for(int primary:{2,8}){
  spells[719].component[0]=13001;spells[719].no_expend_reagent[0]=13001;
  Client wind;wind.primary=primary;wind.itembonuses.windMod=20;wind.run(719,true);
  assert(wind.completed&&!wind.failed&&wind.deleted==0&&wind.inventory.queries==0);
  Client missing;missing.primary=primary;missing.run(719,true);assert(missing.failed&&!missing.completed);
  spells[1448].component[0]=13011;spells[1448].no_expend_reagent[0]=13011;
  Client strings;strings.primary=primary;strings.itembonuses.stringedMod=20;strings.run(1448,true);
  assert(strings.completed&&strings.deleted==0&&strings.inventory.queries==0);
 }
 spells[1].component[0]=100;Client caster;caster.inventory.has=true;caster.run(1,true);
 assert(caster.completed&&caster.deleted==1&&caster.inventory.queries==2);
 Client missing;missing.run(1,true);assert(missing.failed&&!missing.completed&&missing.deleted==0);
 Client ordinary;ordinary.itembonuses.windMod=20;ordinary.run(719,false);
 assert(ordinary.failed&&ordinary.inventory.queries==1);
}
'''
        compile_run('#include <initializer_list>\n'+fixture.replace('// MODE',mode).replace('// BLOCK',block))

if __name__=='__main__':unittest.main()

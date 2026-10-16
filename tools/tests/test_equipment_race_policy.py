"""Compile the actual item-loader restriction block with native policy controls."""
import unittest
import test_free_trade as native


class EquipmentRacePolicyTests(unittest.TestCase):
    compile_run = native.FreeTradeTests.compile_run

    def test_actual_swap_validation_in_both_directions(self):
        source = (native.CODE/'common/inventory_profile.cpp').read_text(encoding='utf-8')
        function = native.body(source, 'bool EQ::InventoryProfile::SwapItem(').replace('EQ::InventoryProfile::SwapItem', 'SwapItem')
        # Item storage, race/class lookup and persistence are fixture boundaries;
        # the real production SwapItem validation and both move directions run.
        self.compile_run(r'''
#include <cassert>
#include <cstdint>
#include <map>
#include "common/equipment_race_policy.h"
using int16=int16_t;using uint8=uint8_t;using uint16=uint16_t;using uint32=uint32_t;using uint64=uint64_t;
namespace EQ {
 bool ValueWithin(int value,int low,int high) { return value>=low && value<=high; }
 namespace invslot { enum {POSSESSIONS_BEGIN=0,POSSESSIONS_END=33,GENERAL_BEGIN=23,
  BANK_BEGIN=2000,BANK_END=2023,EQUIPMENT_BEGIN=0,EQUIPMENT_END=22}; }
 namespace invbag { enum {GENERAL_BAGS_BEGIN=251,GENERAL_BAGS_END=350,SLOT_COUNT=10,
  BANK_BAGS_BEGIN=2031,BANK_BAGS_END=2270}; }
}
using namespace EQ;
namespace Deity { unsigned GetBitmask(unsigned id) { assert(id==208);return 256; } }
enum SwapItemFailState {swapInvalid,swapNotAllowed,swapNullData,swapRaceClass,swapDeity,swapLevel,swapPass};
struct Item {
 unsigned ItemClass=0,Classes=16448,Races=62219,Slots=8192,AugType=0,Deity=0,ReqLevel=0;
 bool IsRaceEquipable(unsigned race) const { assert(race==7);return (Races&64)!=0; }
 bool IsEquipable(unsigned race,unsigned cls) const {return IsRaceEquipable(race)&&(Classes&(1u<<(cls-1)));}
};
struct ItemInstance {
 Item* data;
 bool IsSlotAllowed(int slot) const {return slot>=23||(data&&(data->Slots&(1u<<slot)));}
 void SetEvolveEquipped(bool) {}
 Item* GetItem() { return data; }
 int IsEvolving() {return 0;}
};
struct Lookup {uint64 PossessionsBitmask=~uint64{0};struct {int Bank=24;} InventoryTypeSize;} lookup;
Lookup* m_lookup=&lookup;
std::map<int,ItemInstance*> inventory;
ItemInstance* GetItem(int slot) {return inventory[slot];}
void _PutItem(int slot,ItemInstance* item) {inventory[slot]=item;}
''' + function + r'''
int main() {
 for(bool reverse : {false,true}) {
  Item bronze;ItemInstance instance{&bronze};SwapItemFailState fail;
  int16 source=reverse?13:33,destination=reverse?33:13;
  auto reset=[&]() {inventory.clear();inventory[33]=&instance;};
  auto move=[&](unsigned mask=69) {return SwapItem(source,destination,fail,7,3,208,14,mask);};
  reset();assert(!move()&&fail==swapRaceClass&&inventory[33]==&instance);
  NightcapEquipment::ApplyRacePolicy(bronze);
  reset();assert(move()&&fail==swapPass&&inventory[13]==&instance&&inventory[33]==nullptr);
  reset();assert(!move(5)&&fail==swapRaceClass); // Monk released
  bronze.Classes=4;reset();assert(move(0)); // native primary remains valid
  bronze.Classes=16448;
  for(unsigned races : {0u,65536u}) {
   bronze.Races=races;NightcapEquipment::ApplyRacePolicy(bronze);
   reset();assert(!move()&&fail==swapRaceClass);
  }
  bronze.Races=65535;bronze.Classes=0;reset();assert(!move()&&fail==swapRaceClass);
  bronze.Classes=16448;bronze.Deity=128;reset();assert(!move()&&fail==swapDeity);
  bronze.Deity=256;reset();assert(move());
  bronze.ReqLevel=15;reset();assert(!move()&&fail==swapLevel);
  bronze.ReqLevel=14;reset();assert(move());
  bronze.Slots=1u<<14;reset();assert(!move()&&fail==swapNotAllowed);
 }
}
''')

    def test_loaded_equipment_uses_class_not_race(self):
        source = (native.CODE/'common/shareddb.cpp').read_text(encoding='utf-8')
        block = source.split('// Restrictions\n', 1)[1].split('// Skill Modifier', 1)[0]
        self.compile_run(r'''
#include <cassert>
#include <cstdint>
#include <initializer_list>
#if __has_include("common/equipment_race_policy.h")
#include "common/equipment_race_policy.h"
#endif
using uint8=uint8_t;
struct Row {
 unsigned augrestrict=0,classes=16448,deity=0,itemclass=0,races=62219;
 unsigned reclevel=0,recskill=0,reqlevel=0,slots=8192,augtype=0,itemtype=45;
};
struct Item {
 unsigned AugRestrict=0,Classes=0,Deity=0,ItemClass=0,Races=0,RecLevel=0,RecSkill=0,ReqLevel=0,Slots=0,AugType=0,ItemType=0;
};
Item load(Row e) {
 Item item;item.AugType=e.augtype;item.ItemType=e.itemtype;
''' + block + r'''
 return item;
}
int main() {
 Row bronze;
 const auto loaded=load(bronze);
 assert((loaded.Classes & 69)!=0); // PAL/WAR/MNK includes Monk
 assert((loaded.Races & 64)!=0);   // Half Elf no longer rejected
 assert(loaded.Slots==8192 && loaded.Deity==0 && loaded.ReqLevel==0);
 for(unsigned classes : {0u,1u,4u,64u,16448u,65535u}) {
  for(unsigned races : {0u,1u,64u,62219u,65535u}) {
   for(unsigned type : {0u,1u,2u,3u,4u,5u,7u,8u,19u,27u,28u,35u,45u,54u}) {
    Row row;row.classes=classes;row.races=races;row.itemtype=type;
    row.deity=256;row.reqlevel=50;row.reclevel=60;row.recskill=10;row.augrestrict=7;
    const auto item=load(row);
    assert(item.Races==((classes && races)?65535:races) && item.Classes==classes);
    assert(item.Deity==256 && item.ReqLevel==50 && item.RecLevel==60 && item.RecSkill==10);
    assert(item.AugRestrict==7 && item.ItemType==type && item.Slots==8192);
    assert(row.races==races); // persisted input is unchanged
   }
  }
 }
 for(unsigned slot=0;slot<23;++slot) {
  Row row;row.slots=1u<<slot;assert(load(row).Races==65535);
 }
 Row augment;augment.slots=0;augment.itemtype=54;augment.augtype=1u<<21;
 assert(load(augment).Races==65535 && load(augment).AugType==(1u<<21));
 Row inventory;inventory.slots=0;inventory.itemtype=20;assert(load(inventory).Races==62219);
 inventory.itemtype=15;assert(load(inventory).Races==62219);
 for(unsigned itemclass : {1u,2u}) {
  Row other;other.itemclass=itemclass;assert(load(other).Races==62219);
 }
 for(unsigned races : {0u,65536u,0x80000000u}) {
  Row nonplayer;nonplayer.races=races;assert(load(nonplayer).Races==races);
 }
 Row nonplayer;nonplayer.classes=65536;assert(load(nonplayer).Races==62219);
}
''')


if __name__ == '__main__':
    unittest.main()

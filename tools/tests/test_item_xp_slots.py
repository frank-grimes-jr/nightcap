"""Exercise actual native slot methods, including disabled-rule recovery."""
import unittest
import test_free_trade as native


class ItemXPSlotTests(unittest.TestCase):
    def test_native_slot_admission(self):
        source = (native.CODE/'common/item_instance.cpp').read_text(encoding='utf-8')
        methods = '\n'.join(native.body(source, signature) for signature in (
            'bool EQ::ItemInstance::IsEquipable(int16 slot_id)',
            'bool EQ::ItemInstance::IsSlotAllowed(int16 slot_id)'))
        native.FreeTradeTests.compile_run(self, r'''
#include "common/item_xp_eligibility.h"
#include <cstdio>
#include <cstdlib>
using int16=int16_t;
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"line %d: %s\n",__LINE__,#x); std::exit(1); } } while(false)
bool enabled=false;
#define RuleB(category,rule) enabled
namespace EQ {
namespace invslot {constexpr int16 slotPowerSource=21,EQUIPMENT_BEGIN=0,EQUIPMENT_END=22;}
struct InventoryProfile {static bool SupportsContainers(int16 slot){return slot==23;}};
struct Definition {
 uint32_t ID=1001,Slots=4,AugType=0;uint8_t ItemClass=0,NoRent=255;bool Stackable=false;
};
struct ItemInstance {
 const Definition* m_item=nullptr;bool evolving=false,scaling=false;
 bool IsEvolving()const{return evolving;}bool IsScaling()const{return scaling;}
 bool IsEquipable(int16 slot_id)const;bool IsSlotAllowed(int16 slot_id)const;
};
}
''' + methods + r'''
int main() {
 EQ::Definition definition;EQ::ItemInstance item;item.m_item=&definition;
 CHECK(item.IsEquipable(2));CHECK(!item.IsEquipable(21));CHECK(!item.IsSlotAllowed(21));
 enabled=true;CHECK(item.IsEquipable(21));CHECK(item.IsSlotAllowed(21));
 CHECK(!item.IsEquipable(3));CHECK(!item.IsSlotAllowed(3));
 item.evolving=true;CHECK(!item.IsEquipable(21));CHECK(!item.IsSlotAllowed(21));
 item.evolving=false;item.scaling=true;CHECK(!item.IsEquipable(21));CHECK(!item.IsSlotAllowed(21));
 item.scaling=false;definition.Stackable=true;CHECK(!item.IsEquipable(21));CHECK(!item.IsSlotAllowed(21));
 definition.Stackable=false;definition.Slots=0;definition.AugType=1;
 CHECK(item.IsEquipable(21));CHECK(item.IsSlotAllowed(21));
 enabled=false;CHECK(!item.IsEquipable(21));CHECK(!item.IsSlotAllowed(21));
 CHECK(item.IsSlotAllowed(23)); // removal to a normal inventory slot remains legal
 definition.Slots=NightcapItemXP::PowerSourceMask;definition.ID=900001;
 CHECK(item.IsEquipable(21));CHECK(item.IsSlotAllowed(21)); // native power source
 enabled=true;CHECK(item.IsEquipable(21));CHECK(item.IsSlotAllowed(21));
 item.m_item=nullptr;CHECK(!item.IsEquipable(21));CHECK(!item.IsSlotAllowed(21));
}
''')


if __name__ == '__main__':
    unittest.main()

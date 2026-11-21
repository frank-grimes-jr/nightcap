import sys
import unittest
from pathlib import Path

import test_free_trade as native

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ornament_catalog import ARMOR_MASKS, HANDS, RANGE, classify


def definition(**fields):
    return dict(dict(itemclass=0, itemtype=10, slots=4, idfile="IT63", augtype=0,
                     augrestrict=0, material=3, elitematerial=0, herosforgemodel=0,
                     color=0xff114477, icon=640, bagtype=0, charmfile=""), **fields)


class VisibleOrnaments(unittest.TestCase):
    def test_appearance_fields(self):
        models, tags = {10, 63}, {2000: 4}
        for slot in ARMOR_MASKS:
            look = classify(definition(slots=slot), models, tags)
            self.assertEqual((look.socket, look.slots, look.color, look.material), (21, slot, 0xff114477, 3))
        for kind, slots, restriction in [(5,RANGE,12), (8,16384,13), (0,HANDS,5)]:
            look = classify(definition(itemtype=kind, slots=slots, idfile="IT10"), models, tags)
            self.assertEqual((look.socket,look.slots,look.restriction,look.model), (20,slots,restriction,10))
        self.assertIsNone(classify(definition(slots=2), models, tags))
        self.assertIsNone(classify(definition(itemtype=5,slots=RANGE,idfile="IT99999"), models, tags))
        self.assertIsNone(classify(definition(itemtype=54,augtype=1<<20,material=0), models, tags))
        self.assertIsNone(classify(definition(itemclass=1,bagtype=55,charmfile="ITEMTransfigBow"),models,tags))
        bow = classify(definition(itemclass=1,bagtype=55,charmfile="ITEMTransfigBow",idfile="IT10"),models,tags)
        self.assertEqual((bow.slots,bow.restriction), (RANGE,12))

    def test_native_socket_and_uniform_loot_boundaries(self):
        award = native.body((native.CODE / "zone/zone_hunt.cpp").read_text(encoding="utf8"), "void AwardOrnament(")
        fixture = r'''
#include "common/visible_ornaments.h"
#include <cassert>
#include <vector>
using uint32 = uint32_t;
struct Item {
    int ItemClass=0, AugType=0, ItemType=10, Slots=4, AugSlotType[6]={7,22,0,0,0,0}, AugRestrict=0;
};
struct Entry { int item_charges=0, equip_item=1; };
struct LootdropEntriesRepository { static Entry NewNpcEntity() { return {}; } };
struct NPC {
    bool pet=false,restored=false; int id=0,body=1,drops=0;
    bool HasOwner(){return pet;} bool IsMerc(){return false;} bool GetSwarmInfo(){return false;}
    bool GetSwarmOwner(){return false;} bool IsQueuedForCorpse(){return restored;}
    bool GetInvul(){return false;} uint32 GetNPCTypeID(){return 1;} int GetBodyType(){return body;}
    void AddLootDrop(int item,Entry entry,bool equip){id=item; ++drops; assert(!equip && !entry.equip_item && entry.item_charges==1);}
};
struct Random { int chance=1, index=0; int Int(int lo,int hi) {
    int value=lo==1 ? chance : index; assert(value>=lo && value<=hi); return value;
}};
struct Zone {Random random;} z; Zone *zone=&z;
struct Database {int GetItem(int id){return id;}} database;
std::vector<uint32> ornament_pool={17,23,97};
''' + award + r'''
int main() {
    Item host,aug;
    assert(NightcapOrnaments::Socket(host)==5);
    host.AugSlotType[2]=21; assert(NightcapOrnaments::Socket(host)==2);
    host.Slots=8192; host.ItemType=4;
    for(int &type:host.AugSlotType) type=7;
    host.AugSlotType[4]=21; assert(NightcapOrnaments::Socket(host)==4);
    aug.Slots=24576; aug.AugType=1<<19; assert(NightcapOrnaments::Fits(host,aug));
    host.Slots=16384;host.ItemType=8;assert(!NightcapOrnaments::Fits(host,aug));
    aug.AugRestrict=13;assert(NightcapOrnaments::Fits(host,aug));
    host.Slots=2048;host.ItemType=5;assert(!NightcapOrnaments::Fits(host,aug));
    aug.Slots=2048;aug.AugRestrict=12;assert(NightcapOrnaments::Fits(host,aug));
    for(int i=0;i<3;i++){NPC npc;bool rolled=false;zone->random.index=i;
        AwardOrnament(npc,false,rolled);AwardOrnament(npc,false,rolled);
        assert(rolled && npc.drops==1 && npc.id==int(ornament_pool[i]));
    }
    NPC npc;bool rolled=false; AwardOrnament(npc,true,rolled);assert(!rolled && !npc.drops);
    npc.restored=true;AwardOrnament(npc,false,rolled);assert(!rolled && !npc.drops);
    npc.restored=false;zone->random.chance=2;AwardOrnament(npc,false,rolled);assert(rolled && !npc.drops);
}
'''
        native.FreeTradeTests.compile_run(self, fixture)


if __name__ == "__main__":
    unittest.main()

"""Compile the actual #sellall command and shared resale policy; no server writes.

Run: python tools/tests/test_sell_all.py (requires a C++17 compiler via CXX).
--source and --policy allow validation of a retained production build tree.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, default=ROOT/'server-mods/code/zone/gm_commands/sell_all.cpp')
parser.add_argument('--policy', type=Path, default=ROOT/'server-mods/code/common/item_trade_policy.h')
args = parser.parse_args()
native = '\n'.join(line for line in args.source.read_text(encoding='utf-8').splitlines() if not line.startswith('#include'))
policy = args.policy.read_text(encoding='utf-8').replace('#pragma once', '')
harness = r'''
#include <cstdint>
#include <iostream>
#include <map>
#include <string>
using uint64=uint64_t; using uint32=uint32_t; using int16=int16_t; using uint8=uint8_t;
namespace EQ {
namespace item { enum { ItemTypeFood=14, ItemTypeDrink=15 }; }
namespace invslot { constexpr int GENERAL_BEGIN=23, GENERAL_END=24; }
namespace invbag { constexpr int SLOT_BEGIN=0, SLOT_END=1; }
struct ItemData {
    uint32 ID=100, Price=100, FixedSellPrice=0;
    int ItemType=0; bool NoDrop=true, NoRent=true, bag=false;
    bool IsClassBag() const { return bag; }
};
struct ItemInstance {
    ItemData item; int charges=3; bool stack=true, charged=false;
    const ItemData* GetItem() { return &item; }
    bool IsStackable() { return stack; }
    bool IsCharged() { return charged; }
    int GetCharges() { return charges; }
};
struct InventoryProfile { static int CalcSlotId(int i,int j) { return i*100+j; } };
}
struct Inventory {
    std::map<int,EQ::ItemInstance*> items;
    struct Lookup { uint64 PossessionsBitmask=(uint64(1)<<23)|(uint64(1)<<24); } lookup;
    EQ::ItemInstance* GetItem(int16 slot) { auto i=items.find(slot); return i==items.end()?nullptr:i->second; }
    Lookup* GetLookup() { return &lookup; }
};
namespace Chat { constexpr int White=0; }
namespace fmt { template<typename... T> std::string format(const char*,T...) { return "sold"; } }
struct Seperator {};
struct Client {
    Inventory inv; uint64 money=0; int deleted=0; std::string message;
    Inventory& GetInv() { return inv; }
    void AddMoneyToPP(uint64 value,bool) { money+=value; }
    void DeleteItemInInventory(int16 slot,int quantity,bool) {
        deleted+=quantity ? quantity : 1; inv.items.erase(slot);
    }
    void Message(int,const char* text) { message=text; }
};
struct Spell { int component[4]={-1,-1,-1,-1}; int no_expend_reagent[4]={-1,-1,-1,-1}; };
Spell records[4]; const Spell* spells=records; int SPDAT_RECORDS=4;
#define RuleR(category,name) 1.0
''' + policy + '\n' + native + r'''
int main() {
    records[0].component[0]=13073;
    records[1].component[3]=200;
    records[2].no_expend_reagent[0]=300;
    int failures=0, checks=0;
    auto check=[&](bool okay,const char* label) {
        ++checks; if (!okay) { ++failures; std::cerr << "FAIL " << label << '\n'; }
    };
    auto test=[&](EQ::ItemData item,uint64 expected,const char* label,
                  bool stack=true,int charges=3,bool charged=false) {
        EQ::ItemInstance inst; inst.item=item; inst.stack=stack; inst.charges=charges; inst.charged=charged;
        Client client; client.inv.items[23]=&inst;
        const auto price=SellAllSlot(&client,23);
        check(price==expected && client.money==expected &&
              client.deleted==(expected ? (stack ? charges : 1) : 0) &&
              (client.inv.GetItem(23)!=nullptr)==(expected==0),label);
    };
    EQ::ItemData item;
    test(item,300,"ordinary loot sells full stack");
    item.ItemType=EQ::item::ItemTypeFood; test(item,0,"food kept");
    item.ItemType=EQ::item::ItemTypeDrink; test(item,0,"drink kept"); item.ItemType=0;
    item.ID=13073; test(item,0,"bone chips kept");
    item.ID=200; test(item,0,"last-slot reagent kept");
    item.ID=300; test(item,0,"casting focus kept"); item.ID=100;
    item.bag=true; test(item,0,"bag kept"); item.bag=false;
    item.NoDrop=false; test(item,0,"no-drop kept"); item.NoDrop=true;
    item.NoRent=false; test(item,0,"ordinary temporary kept"); item.NoRent=true;
    item.Price=0; test(item,0,"worthless kept"); item.Price=100;
    item.FixedSellPrice=1000; test(item,3000,"fixed resale full stack");
    item.NoRent=false; test(item,3000,"fixed temporary resale retained");
    item.ID=13073; test(item,0,"fixed temporary reagent kept"); item.ID=100;
    item.ItemType=EQ::item::ItemTypeFood; test(item,0,"fixed food kept");
    item.ItemType=EQ::item::ItemTypeDrink; test(item,0,"fixed drink kept");
    item.ItemType=0; item.NoRent=true;
    test(item,1000,"charged fixed item pays once",false,20,true);
    test(item,0,"empty stack rejected",true,0);
    test(item,0,"negative stack rejected",true,-1);
    item.FixedSellPrice=0; test(item,100,"charged ordinary item pays once",false,20,true);
    spells=nullptr; test(item,0,"missing spell table blocks sales"); spells=records;
    SPDAT_RECORDS=0; test(item,0,"empty spell table blocks sales"); SPDAT_RECORDS=4;
    records[3].component[1]=100; test(item,0,"reload adds protection");
    records[3].component[1]=-1; test(item,300,"reload removes stale protection");
    records[3].no_expend_reagent[0]=1; item.ID=1; test(item,300,"focus slot index is not an item ID");
    records[3].component[2]=0; item.ID=0; test(item,300,"zero component sentinel ignored");
    Client empty; check(SellAllSlot(&empty,23)==0,"empty slot safe");
    for (int food_slot : {23,2300}) {
        EQ::ItemInstance food, reagent, loot, bag, equipped, bank, cursor;
        food.item.ItemType=EQ::item::ItemTypeFood; reagent.item.ID=13073; bag.item.bag=true;
        Client client;
        client.inv.items[food_slot]=&food; client.inv.items[2301]=&reagent;
        client.inv.items[2400]=&loot; client.inv.items[24]=&bag;
        client.inv.items[1]=&equipped; client.inv.items[2000]=&bank; client.inv.items[33]=&cursor;
        command_sell_all(&client,nullptr);
        check(client.money==300 && client.deleted==3 && client.inv.items.size()==6,
              "command sells bag loot and retains supply/equipment/bank/cursor");
        check(client.inv.GetItem(food_slot)==&food && client.inv.GetItem(2301)==&reagent &&
              client.inv.GetItem(24)==&bag,"general/bag supply instances retained");
        command_sell_all(&client,nullptr);
        check(client.money==300 && client.deleted==3 && client.message.find("spell reagents")!=std::string::npos,
              "protected-only repeat changes nothing and explains exclusions");
    }
    EQ::ItemInstance loot; Client masked; masked.inv.lookup.PossessionsBitmask=0;
    masked.inv.items[23]=&loot; command_sell_all(&masked,nullptr);
    check(masked.money==0 && masked.inv.GetItem(23)==&loot,"unavailable client slots untouched");
    std::cout << checks-failures << '/' << checks << " sell-all checks passed\n";
    return failures ? 1 : 0;
}
'''
with tempfile.TemporaryDirectory(prefix='nightcap-sell-all-') as directory:
    cpp = Path(directory)/'test.cpp'
    binary = Path(directory)/('test.exe' if os.name=='nt' else 'test')
    cpp.write_text(harness)
    subprocess.run([os.environ.get('CXX','g++'),'-std=c++17',str(cpp),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)

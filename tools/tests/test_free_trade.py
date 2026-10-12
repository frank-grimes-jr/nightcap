"""Native policy regression controls; run with a local C++17 compiler."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CODE = ROOT / 'server-mods/code'


def body(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth, end = 1, brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


class FreeTradeTests(unittest.TestCase):
    def compile_run(self, source):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            cpp = folder / 'test.cpp'
            cpp.write_text(source)
            if os.name == 'nt':
                binary = folder / 'test.exe'
                script = folder / 'build.cmd'
                script.write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
                                  'cl /nologo /EHsc /W4 /WX /std:c++17 /I"' + str(CODE) + '" test.cpp /Fe:test.exe\n'
                                  'exit /b %errorlevel%\n')
                result = subprocess.run(['cmd', '/d', '/c', str(script)], cwd=folder, capture_output=True, text=True)
            else:
                binary = folder / 'test'
                compiler = os.environ.get('CXX') or shutil.which('c++')
                self.assertIsNotNone(compiler, 'C++ compiler required')
                result = subprocess.run([compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror',
                                         '-I', str(CODE), str(cpp), '-o', str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            subprocess.run([str(binary)], check=True)

    def test_native_policy(self):
        self.compile_run((ROOT / 'tools/tests/fixtures/free_trade.cpp').read_text(encoding='utf-8'))

    def test_actual_recursive_trade_gate_preserves_raw_attunement(self):
        source = (CODE/'common/item_instance.cpp').read_text(encoding='utf-8')
        header = (CODE/'common/item_instance.h').read_text(encoding='utf-8')
        gate = body(source, 'bool EQ::ItemInstance::IsDroppable(')
        effective = body(header, 'bool IsAttunedForTrade() const')
        raw = body(header, 'bool IsAttuned() const')
        self.compile_run('''
#include "common/item_trade_policy.h"
#include <cassert>
#include <map>
int fv = 0;
#define RuleI(category, rule) fv
namespace FVNoDropFlagRule { constexpr int Enabled = 1; }
namespace EQ {
struct Item { bool FreeTrade = false; unsigned NoDrop = 0; unsigned FVNoDrop = 1; };
struct ItemInstance {
 Item *m_item = nullptr;
 bool m_attuned = false;
 std::map<int, ItemInstance*> m_contents;
 bool IsDroppable(bool recurse = true) const;
''' + effective + '\n' + raw + '''
}; }
''' + gate + '''
int main() {
 EQ::Item blocked, free, normal;
 free.FreeTrade = true; free.NoDrop = 255; free.FVNoDrop = 0;
 normal.NoDrop = 255;
 EQ::ItemInstance bag, aug, nested, invalid;
 bag.m_item = &free; bag.m_attuned = true;
 aug.m_item = &free; aug.m_attuned = true;
 nested.m_item = &free; nested.m_attuned = true;
 bag.m_contents[0] = &aug; aug.m_contents[0] = &nested;
 assert(bag.IsDroppable() && bag.IsAttuned() && aug.IsAttuned());
 assert(!bag.IsAttunedForTrade());
 nested.m_item = &blocked; assert(!bag.IsDroppable());
 nested.m_item = nullptr; assert(!bag.IsDroppable());
 assert(!invalid.IsDroppable());
 bag.m_contents.clear(); bag.m_item = &normal;
 assert(!bag.IsDroppable());
 bag.m_attuned = false; assert(bag.IsDroppable());
 bag.m_item = &blocked; assert(!bag.IsDroppable());
}
''')

    def test_live_integration_contracts(self):
        shared = (CODE/'common/shareddb.cpp').read_text(encoding='utf-8')
        self.assertIn('EQ::ItemTradePolicy::Apply(item, RuleB(Items, FreeTrade), e.nodrop == 0);', shared)
        self.assertIn('e.instnodrop          = inst->IsAttuned() ? 1 : 0;', shared)
        for codec in ('titanium', 'sof', 'sod', 'uf', 'rof', 'rof2'):
            self.assertIn('inst->IsAttunedForTrade() ? 1 : 0', (CODE/f'common/patches/{codec}.cpp').read_text(encoding='utf-8'))
        packet = (CODE/'zone/client_packet.cpp').read_text(encoding='utf-8')
        sell = body(packet, 'void Client::Handle_OP_ShopPlayerSell(')
        self.assertLess(sell.index('SaleUnits('), sell.index('AddMoneyToPP(price)'))
        self.assertLess(sell.index('FixedSalePrice('), sell.index('AddMoneyToPP(price)'))
        self.assertNotIn('inst->', sell[sell.index('// Now remove the item'):])
        self.assertIn('const bool is_charged = !is_stackable && inst->IsCharged();', sell)
        self.assertNotIn('|| inst->IsCharged()', sell)
        buy = body(packet, 'void Client::Handle_OP_ShopPlayerBuy(')
        self.assertIn('const bool charged_item = !item->Stackable && item->MaxCharges > 1;', buy)
        self.assertEqual(packet.count('EQ::ItemTradePolicy::PurchasePrice('), 2)
        process = (CODE/'zone/client_process.cpp').read_text(encoding='utf-8')
        self.assertEqual(body(process, 'void Client::BulkSendMerchantInventory(').count('EQ::ItemTradePolicy::PurchasePrice('), 2)
        self.assertIn('(loot.attuned && !item->FreeTrade)', (CODE/'zone/advanced_loot.cpp').read_text(encoding='utf-8'))

    def test_actual_merchant_payout_ignores_modifiers_only_for_former_no_drop(self):
        source = (CODE/'zone/client_packet.cpp').read_text(encoding='utf-8')
        sell = body(source, 'void Client::Handle_OP_ShopPlayerSell(')
        pricing = sell[sell.index('const bool is_stackable'):sell.index('\n\tint charges =')]
        self.compile_run('''
#include "common/item_trade_policy.h"
#include <cassert>
#include <cstdint>
using uint32 = uint32_t;
// Preserve the legacy native rounding in the extracted ordinary-item branch.
#ifdef _MSC_VER
#pragma warning(disable:4244)
#endif
bool UsePriceMod = true, UseClassicPriceMod = false;
double BuyCostMod = 2.5, faction = 1.0;
#define RuleB(category, name) name
#define RuleR(category, name) name
struct Item { uint32 Price = 0, FixedSellPrice = 0; int NoDrop = 255; };
struct Instance {
 bool stack = false, charged = false; int charges = 0;
 bool IsStackable() const { return stack; }
 bool IsCharged() const { return charged; }
 int GetCharges() const { return charges; }
};
struct Request { uint32 quantity = 1; };
struct Client { static double CalcPriceMod(int, bool) { return faction; } };
uint32 paid = 0;
void AddMoneyToPP(uint32 price) { paid += price; }
void sell(Item *item, Instance *inst, Request *mp) {
 uint32 price = 0; int vendor = 0;
''' + pricing + '''
}
int main() {
 Item fixed{7500000,1000,255}, normal{200,0,255};
 Instance item; Request request;
 for (bool use : {false,true}) for (bool classic : {false,true}) {
  UsePriceMod=use; UseClassicPriceMod=classic;
  for (double mod : {0.01,0.95,2.5,10.0}) for (double cha : {0.5,1.0,1.04,2.0}) {
   BuyCostMod=mod; faction=cha; paid=0; request.quantity=1;
   sell(&fixed,&item,&request); assert(paid==1000);
  }
 }
 UsePriceMod=true; UseClassicPriceMod=false; BuyCostMod=2.5; faction=1.0;
 paid=0; request.quantity=1; sell(&normal,&item,&request); assert(paid==500);
 item.stack=true; item.charged=true; item.charges=20;
 paid=0; request.quantity=5; sell(&fixed,&item,&request);
 assert(paid==5000 && request.quantity==5);
 paid=0; request.quantity=21; sell(&fixed,&item,&request); assert(paid==0);
 paid=0; request.quantity=0; sell(&fixed,&item,&request); assert(paid==0);
 item.stack=false; item.charges=10;
 paid=0; request.quantity=10; sell(&fixed,&item,&request);
 assert(paid==1000 && request.quantity==10);
 item.charged=false; item.charges=0;
 paid=0; request.quantity=2; sell(&fixed,&item,&request); assert(paid==0);
}
''')

    def test_actual_sellall_uses_same_fixed_payout(self):
        source = (CODE/'zone/gm_commands/sell_all.cpp').read_text(encoding='utf-8')
        method = body(source, 'static uint64 SellAllSlot(')
        supplies = body(source, 'static bool IsSellAllSupply(')
        self.compile_run('''
#include "common/item_trade_policy.h"
#include <cassert>
#include <cstdint>
using uint64=uint64_t; using uint32=uint32_t; using int16=int16_t;
#define RuleR(category, name) 2.5
namespace EQ {
namespace item { enum { ItemTypeFood=14,ItemTypeDrink=15 }; }
struct ItemData {
 uint32 ID=100,Price=0,FixedSellPrice=0; int ItemType=0; bool NoDrop=true,NoRent=true,bag=false;
 bool IsClassBag() const { return bag; }
};
struct ItemInstance {
 ItemData item; bool stack=false,charged=false; int charges=0;
 const ItemData *GetItem() const { return &item; }
 bool IsStackable() const { return stack; }
 bool IsCharged() const { return charged; }
 int GetCharges() const { return charges; }
}; }
struct Inventory { EQ::ItemInstance *inst; EQ::ItemInstance *GetItem(int16) { return inst; } };
struct Client {
 Inventory inv; uint64 money=0; int deleted=-1;
 Inventory &GetInv() { return inv; }
 void AddMoneyToPP(uint64 price, bool) { money+=price; }
 void DeleteItemInInventory(int16, int quantity, bool) { deleted=quantity; }
};
struct Spell { int component[4]={-1,-1,-1,-1}; int no_expend_reagent[4]={-1,-1,-1,-1}; };
Spell records[1]; const Spell *spells=records; int SPDAT_RECORDS=1;
''' + supplies + '\n' + method + '''
int main() {
 EQ::ItemInstance item; Client c{{&item}};
 item.item.Price=7500000; item.item.FixedSellPrice=1000;
 assert(SellAllSlot(&c,1)==1000 && c.money==1000 && c.deleted==0);
 item.item.NoRent=false; c.money=0;
 assert(SellAllSlot(&c,1)==1000 && c.money==1000);
 item.stack=true; item.charged=true; item.charges=20; c.money=0;
 assert(SellAllSlot(&c,1)==20000 && c.money==20000 && c.deleted==20);
 item.charges=0; c.money=0; c.deleted=-1;
 assert(SellAllSlot(&c,1)==0 && c.money==0 && c.deleted==-1);
 item.charges=5; item.item.bag=true;
 assert(SellAllSlot(&c,1)==0 && c.deleted==-1);
 item.item.bag=false; item.item.FixedSellPrice=0; item.item.Price=200; item.item.NoRent=true;
 assert(SellAllSlot(&c,1)==2500);
 item.item.NoRent=false; assert(SellAllSlot(&c,1)==0);
}
''')

    def test_actual_advanced_loot_consent_respects_free_trade(self):
        source = (CODE/'zone/advanced_loot.cpp').read_text(encoding='utf-8')
        consent = body(source, 'bool Consent(')
        self.compile_run('''
#include <cassert>
#include <map>
struct Item { int NoDrop=255; bool NoTransfer=false,FreeTrade=false; };
struct LootItem { int item_id=1; bool attuned=true; int aug_1=2,aug_2=0,aug_3=0,aug_4=0,aug_5=0,aug_6=0; };
struct Database {
 std::map<int,Item> items;
 const Item* GetItem(int id) const { auto p=items.find(id);return p==items.end()?nullptr:&p->second; }
} database;
''' + consent + '''
int main() {
 LootItem loot; database.items[1]={255,false,true}; database.items[2]={255,false,true};
 assert(!Consent(loot)); assert(loot.attuned);
 database.items[1].FreeTrade=false; assert(Consent(loot));
 database.items[1].FreeTrade=true; database.items.erase(2); assert(Consent(loot));
 database.items[2]={0,false,false}; assert(Consent(loot));
 database.items[2]={255,true,false}; assert(Consent(loot));
 database.items.erase(1); assert(Consent(loot));
}
''')


if __name__ == '__main__':
    unittest.main()

"""Exhaustively execute the deployed loot selection block with proposed rules."""
import pathlib
import os
import re
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class LootQualityRates(unittest.TestCase):
    def test_fresh_install_rates(self):
        sql = (ROOT / 'eq-solo-gm/scripts/tiered_loot_setup.sql').read_text()
        rows = re.findall(r"\(1,'Zone:LootTier(\w+)Chance','(\d+)'", sql)
        self.assertCountEqual(rows, [('Rare', '2000'), ('Epic', '500'), ('Legendary', '700')])

    def test_actual_native_block(self):
        text = (ROOT/'server-mods/code/zone/loot.cpp').read_text()
        block = text[text.index('\tif (item2->ID < 200000'):text.index('\n\tauto item = new LootItem;')]
        source = r'''
#include <cassert>
#include <cstdint>
using uint32 = uint32_t;
namespace EQ {
 namespace item { enum { ItemClassCommon=0, ItemTypeShield=8, ItemTypeArmor=10 }; }
 struct ItemData { uint32 ID; int Slots; int BagSlots; int ItemClass; int ItemType; };
}
struct Random { int value=1; int Int(int,int) { return value; } };
struct Zone { Random random; } actual_zone;
Zone *zone=&actual_zone;
struct DB {
 bool available=true;
 EQ::ItemData item{};
 const EQ::ItemData *GetItem(uint32 id) { item={id,1,0}; return available?&item:nullptr; }
} database;
int LootTierRareChance=2000, LootTierEpicChance=500, LootTierLegendaryChance=700;
#define RuleI(category,name) name
uint32 pick(EQ::ItemData base) {
 const EQ::ItemData *item2=&base;
''' + block + r'''
 return item2->ID;
}
int main() {
 int count[4]={};
 for (int r=1; r<=10000; ++r) {
  zone->random.value=r;
  const uint32 expected=42 + (r<=700 ? 600000 : r<=1200 ? 400000 : r<=3200 ? 200000 : 0);
  const EQ::ItemData eligible[] = {
   {42,1,0,0,0},                             // weapon
   {42,1,0,0,EQ::item::ItemTypeArmor},
   {42,1,0,0,EQ::item::ItemTypeShield},
   {42,1,0,0,29},                            // jewelry
   {42,0,10,1,0}                             // bag
  };
  for (const auto &base : eligible) {
   assert(pick(base)==expected);
   database.available=false;
   assert(pick(base)==base.ID);
   database.available=true;
  }
  ++count[expected/200000];
  assert(pick({42,0,0})==42);
  assert(pick({200042,1,0})==200042);
  assert(pick({940000,1,0})==940000);
  assert(pick({960000,1,0})==960000);
 }
 assert(count[0]==6800 && count[1]==2000 && count[2]==500 && count[3]==700);
 LootTierLegendaryChance=0;
 zone->random.value=1;
 assert(pick({42,1,0,0,EQ::item::ItemTypeArmor})==400042);
 assert(pick({42,1,0,0,0})==400042);
}
'''
        scratch=ROOT/'artifacts/loot-quality-tests'
        scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            cpp=pathlib.Path(directory)/'loot.cpp'
            exe=pathlib.Path(directory)/'loot.exe'
            cpp.write_text(source)
            env=dict(os.environ,TMP=str(scratch),TEMP=str(scratch),TMPDIR=str(scratch))
            result=subprocess.run(['g++','-std=c++11',str(cpp),'-o',str(exe)],capture_output=True,env=env,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            subprocess.run([str(exe)],check=True,capture_output=True)

if __name__=='__main__':
    unittest.main()

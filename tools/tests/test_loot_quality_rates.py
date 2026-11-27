"""Exhaustively execute the deployed loot selection block with proposed rules."""
import pathlib
import os
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]

class LootQualityRates(unittest.TestCase):
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
int LootTierRareChance=2000, LootTierEpicChance=500, LootTierLegendaryChance=100;
#define RuleI(category,name) name
uint32 pick(EQ::ItemData base) {
 const EQ::ItemData *item2=&base;
''' + block + r'''
 return item2->ID;
}
int main() {
 int count[4]={};
 int armor_count[4]={};
 for(int r=1;r<=10000;++r) {
  zone->random.value=r;
  auto id=pick({42,1,0}); ++count[id/200000];
  auto armor=pick({42,1,0,0,EQ::item::ItemTypeArmor});
  ++armor_count[armor/200000];
  assert(pick({42,1,0,0,EQ::item::ItemTypeShield})==armor);
  assert(pick({42,0,0,0,EQ::item::ItemTypeArmor})==42);
  if (r<=2600) assert(armor==id);
  assert(pick({42,0,10})==id);
  assert(pick({42,0,0})==42);
  assert(pick({940000,1,0})==940000);
  assert(pick({960000,1,0})==960000);
  assert(pick({200042,1,0})==200042);
  database.available=false;
  assert(pick({42,1,0})==42 && pick({42,1,0,0,EQ::item::ItemTypeArmor})==42);
  database.available=true;
 }
 assert(count[0]==7400 && count[1]==2000 && count[2]==500 && count[3]==100);
 assert(armor_count[0]==7100 && armor_count[1]==2000 && armor_count[2]==500 && armor_count[3]==400);
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

"""Compile real summon branches and merchant projection without touching a server."""
import unittest
import test_free_trade as native


class DivineSummonedWeaponTests(unittest.TestCase):
    compile_run = native.FreeTradeTests.compile_run

    def test_zero_resale_preserves_combat_and_trade(self):
        self.compile_run(r'''
#include "common/divine_summoned_weapon_policy.h"
#include "common/item_trade_policy.h"
#include "common/item_upgrade_policy.h"
#include <cassert>
struct Item {
 unsigned ID=0, Price=17, FixedSellPrice=0, NoDrop=0, FVNoDrop=1;
 bool FreeTrade=false, Attuneable=true, NoTransfer=true;
 unsigned Damage=8, Delay=32, SpellDmg=20, HealAmt=20, NoRent=0;
};
int main() {
 for (unsigned base : {6307u,6309u,6313u,5800u,15996u,5798u,29365u,77517u,90491u,90492u,90493u}) {
  for (unsigned tier : {0u,200000u,400000u,600000u}) {
   for (bool free_trade : {false,true}) {
    Item item; item.ID=base+tier;
    EQ::ItemTradePolicy::Apply(item,free_trade,true);
    if(free_trade) assert(item.FixedSellPrice==1000);
    NightcapDivineSummons::ApplyMerchantPolicy(item);
    assert(item.Price==0 && item.FixedSellPrice==0);
    assert(item.Damage==8 && item.Delay==32 && item.SpellDmg==20 && item.HealAmt==20 && item.NoRent==0);
    assert(item.FreeTrade==free_trade && item.NoDrop==(free_trade?255u:0u));
    assert(item.Attuneable==!free_trade && item.NoTransfer==!free_trade);
    if(tier==600000) {
     assert(NightcapUpgrade::LegacyTarget(item.ID)==0);
     assert(NightcapUpgrade::ZoneTarget(item.ID)==0);
    }
   }
  }
 }
 for(unsigned id : {0u,6308u,606308u,806307u,1006307u,940024u,6346u,606346u}) {
  Item item;item.ID=id;
  EQ::ItemTradePolicy::Apply(item,true,true);
  NightcapDivineSummons::ApplyMerchantPolicy(item);
  assert(item.Price==1000 && item.FixedSellPrice==1000);
 }
}
''')

    def test_actual_spell_effects_choose_ascended(self):
        source = (native.CODE/'zone/spell_effects.cpp').read_text(encoding='utf-8')
        for effect in ('SummonItem', 'SummonItemIntoBag'):
            start = source.index('case SpellEffect::'+effect+':')
            start = source.index('uint32 summon_item_id', start)
            end = source.index('\n#ifdef SPELL_EFFECT_SPAM', start) if effect == 'SummonItem' else source.index('\n\t\t\t\tif (!item)', start)
            branch = source[start:end]
            self.compile_run(r'''
#include <cassert>
#include <cstdint>
#include <initializer_list>
using uint32=uint32_t;
namespace EQ { struct ItemData { unsigned Slots=8192; }; }
struct Database {
 unsigned base=6307;bool has_base=true,has_tier=true;
 EQ::ItemData normal,ascended;
 const EQ::ItemData *GetItem(unsigned id) {
  if(id==base && has_base)return &normal;
  if(id==base+600000 && has_tier)return &ascended;
  return nullptr;
 }
} database;
struct Spell { unsigned base_value[1]; } spell;
unsigned resolve(unsigned id) {
 spell.base_value[0]=id;int i=0;
''' + branch + r'''
 return summon_item_id;
}
int main() {
 for(unsigned id : {6307u,6309u,6313u,5800u,15996u,5798u,29365u,77517u,90491u,90492u,90493u}) {
  database.base=id; assert(resolve(id)==id+600000);
 }
 database.base=6307;database.has_tier=false;assert(resolve(6307)==6307);
 database.has_tier=true;database.normal.Slots=0;assert(resolve(6307)==6307);
 database.normal.Slots=8192;database.has_base=false;assert(resolve(6307)==6307);
 database.has_base=true;database.base=606307;assert(resolve(606307)==606307);
}
''')

    def test_loader_projects_after_free_trade(self):
        source = (native.CODE/'common/shareddb.cpp').read_text(encoding='utf-8')
        self.assertLess(source.index('EQ::ItemTradePolicy::Apply(item,'),
                        source.index('NightcapDivineSummons::ApplyMerchantPolicy(item);'))
        self.assertLess(source.index('NightcapDivineSummons::ApplyMerchantPolicy(item);'),
                        source.index('hash.insert(item.ID, item);'))


if __name__ == '__main__':
    unittest.main()

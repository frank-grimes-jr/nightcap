"""Compile campaign eligibility and effective item policy, including negative cases."""
import unittest
import test_free_trade as native


class LanternPolicyTests(unittest.TestCase):
    def test_effective_policy_is_applied_after_free_trade(self):
        source = (native.CODE / 'common/shareddb.cpp').read_text(encoding='utf-8')
        projection = source.index('EQ::ItemTradePolicy::Apply(item,')
        override = source.index('NightcapLantern::ApplyEffectivePolicy(item);')
        publication = source.index('hash.insert(item.ID, item);', projection)
        self.assertLess(projection, override)
        self.assertLess(override, publication)

    def test_pet_restore_honors_effective_no_pet(self):
        source = (native.CODE / 'zone/pets.cpp').read_text(encoding='utf-8')
        import re
        condition = re.search(r'if \(([^\n]+)\) \{\s*AddLootDrop\(item2,', source).group(1)
        native.FreeTradeTests.compile_run(self, '''
#include <cassert>
#include <initializer_list>
struct Item { bool NoPet; };
int main() {
 for(bool prohibited : {false,true}) for(bool noDrop : {false,true})
  for(bool petCanHaveNoDrop : {false,true}) {
   Item item{prohibited}; const auto item2=&item;
   const bool accepted=(''' + condition + ''');
   assert(accepted == (!prohibited && (!noDrop || petCanHaveNoDrop)));
  }
}
''')

    def test_native_campaign_policy(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "common/last_lantern_policy.h"
#include "common/item_trade_policy.h"
#include <cstdlib>
#include <cstdio>
#include <set>
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"%s\n",#x); std::exit(1); } } while(false)
struct Item {
 unsigned ID,NoDrop=255,NoTransfer=0,NoPet=0,NoRent=0,Price=100,FixedSellPrice=100;
 bool LoreFlag=true,Attuneable=true,FreeTrade=true;
 unsigned FVNoDrop=0;
};
int main() {
 using namespace NightcapLantern;
 std::set<unsigned> ids;
 for(unsigned fit=0;fit<4;++fit) for(unsigned grade=0;grade<4;++grade) for(unsigned slot=0;slot<8;++slot) {
  auto id=ArmorID(fit,grade,slot); CHECK(IsArmor(id)); CHECK(ids.insert(id).second);
  const auto a=Decode(id); CHECK(a.valid && a.fit==fit && a.grade==grade && a.slot==slot);
 }
 CHECK(ids.size()==128); CHECK(!IsArmor(FirstArmor-1)); CHECK(!IsArmor(FirstArmor+128));
 CHECK(!IsCampaignItem(900620)); // existing live Reforging Box
 CHECK(!Decode(0).valid); CHECK(!ArmorID(4,0,0)); CHECK(!ArmorID(0,4,0)); CHECK(!ArmorID(0,0,8));
 CHECK(CanOffer(9500,20,0)); CHECK(!CanOffer(9500,19,0)); CHECK(!CanOffer(9501,50,0));
 CHECK(CanOffer(9501,25,1)); CHECK(!CanOffer(9503,35,3));
 CHECK(CanOffer(9503,35,7)); CHECK(CanOffer(9507,35,7));
 for(unsigned path=3;path<8;++path) {
  auto done=uint16_t(7|(1u<<path)); CHECK(HasOath(done)); CHECK(CanOffer(9508,38,done));
  CHECK(!CanOffer(9509,50,done)); CHECK(!CanOffer(9515,50,done));
 }
 CHECK(!CanOffer(9508,50,7)); CHECK(!CanOffer(9516,50,65535));
 CHECK(!CanOffer(9500,50,65535)); CHECK(Grade(0)==0);
 CHECK(Grade(1u<<9)==1); CHECK(Grade(1u<<12)==2); CHECK(Grade(1u<<15)==3);
 CHECK(FitAllowed(0,1u<<11)); CHECK(!FitAllowed(3,1u<<11)); CHECK(FitAllowed(3,1u<<0));
 CHECK(!FitAllowed(2,1u<<6)); CHECK(FitAllowed(1,1u<<6)); CHECK(!FitAllowed(4,65535));
 CHECK(!FitAllowed(0,0)); CHECK(!FitAllowed(0,1u<<20));
 for(unsigned slot=0;slot<8;++slot) {
  const auto before=ArmorID(0,0,slot), after=ArmorID(0,3,slot);
  CHECK(!CanRefit(before,after,50,1,0));
  CHECK(CanRefit(before,after,50,1,65535));
  CHECK(!CanRefit(after,before,50,1,65535));
  CHECK(!CanRefit(after,after,50,1,65535));
  CHECK(!CanRefit(before,ArmorID(0,3,(slot+1)%8),50,1,65535));
 }
 CHECK(RequiredLevel(0,0)==20); CHECK(RequiredLevel(0,7)==50);
 CHECK(RequiredLevel(1,0)==40); CHECK(RequiredLevel(2,0)==46); CHECK(RequiredLevel(3,0)==50);
 CHECK(!CanRefit(ArmorID(0,0,0),ArmorID(3,3,0),50,1u<<11,65535));
 CHECK(!CanRefit(ArmorID(0,0,0),ArmorID(0,3,0),49,1,65535));
 Item armor{FirstArmor}; ApplyEffectivePolicy(armor);
 CHECK(armor.NoDrop==0 && armor.NoTransfer && armor.NoPet && armor.NoRent==255);
 CHECK(!armor.Price && !armor.FixedSellPrice && !armor.Attuneable && !armor.LoreFlag);
 CHECK(!armor.FreeTrade && armor.FVNoDrop==1);
 for(bool trade : {false,true}) {
  Item candidate{FirstArmor}; EQ::ItemTradePolicy::Apply(candidate,trade,true);
  ApplyEffectivePolicy(candidate);
  CHECK(!candidate.FreeTrade && candidate.FVNoDrop==1 && candidate.NoDrop==0);
  CHECK(candidate.NoTransfer && candidate.NoPet && !candidate.Price && !candidate.FixedSellPrice);
 }
 Item charm{900501}; ApplyEffectivePolicy(charm); CHECK(charm.NoDrop==0 && charm.NoTransfer && charm.NoPet);
 Item other{1001}; ApplyEffectivePolicy(other); CHECK(other.Price==100 && other.NoDrop==255);
}
''')


if __name__ == '__main__':
    unittest.main()

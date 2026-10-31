"""Execute actual box/zone-forge admission with partial training metadata."""
import unittest
import test_free_trade as native


class ItemXPBoxTests(unittest.TestCase):
    def test_partial_xp_keeps_both_combine_routes(self):
        source=(native.CODE/'zone/advanced_loot_inventory.cpp').read_text(encoding='utf-8')
        methods='\n'.join(native.body(source,signature) for signature in (
            'static bool PlainUpgradeMetadata(', 'bool PlainForgeItem(', 'static bool PlainUpgradeItem('))
        native.FreeTradeTests.compile_run(self,r'''
#include "common/item_xp_eligibility.h"
#include "common/item_xp_metadata.h"
#include <cstdio>
#include <cstdlib>
using uint8=uint8_t;
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"%s\n",#x); std::exit(1); } } while(false)
namespace EQ {
namespace invaug {constexpr unsigned SOCKET_COUNT=6;}
namespace invbag {constexpr unsigned SLOT_COUNT=10;}
struct ItemData {unsigned Color=7;};
struct ItemInstance {
 unsigned id=1001,color=7,ornament=0,augment=0;int charges=1;
 bool common=true,stackable=false,evolving=false,scaling=false,filled=false;
 std::string metadata;ItemData definition;
 bool IsClassCommon()const{return common;}bool IsStackable()const{return stackable;}
 bool IsEvolving()const{return evolving;}unsigned GetEvolveUniqueID()const{return 0;}
 bool IsScaling()const{return scaling;}int GetCharges()const{return charges;}
 unsigned GetColor()const{return color;}unsigned GetID()const{return id;}
 const ItemData* GetItem()const{return &definition;}
 const ItemInstance* GetItem(unsigned)const{return filled?this:nullptr;}
 unsigned GetOrnamentationIcon()const{return ornament;}unsigned GetOrnamentationIDFile()const{return 0;}
 unsigned GetOrnamentHeroModel()const{return 0;}unsigned GetAugmentItemID(unsigned i)const{return i==0?augment:0;}
 std::string GetCustomDataString()const{return metadata;}
};
}
''' + methods + r'''
int main() {
 CHECK(!PlainUpgradeItem(nullptr) && !PlainForgeItem(nullptr));
 for(unsigned id : {1001u,201001u,401001u,940024u,940025u,940026u}) {
  EQ::ItemInstance item;item.id=id;
  CHECK(PlainUpgradeItem(&item));
  item.metadata="nightcap_item_xp^1:"+std::to_string(id)+":123^";
  CHECK(PlainUpgradeItem(&item));
  CHECK(NightcapUpgrade::BoxCopies(id)==(id==1001||id==940024?3u:4u));
  if(id>=940000)CHECK(PlainForgeItem(&item));
  item.augment=42;CHECK(!PlainUpgradeItem(&item));item.augment=0;
  item.ornament=1;CHECK(!PlainUpgradeItem(&item));item.ornament=0;
  item.color=8;CHECK(!PlainUpgradeItem(&item));item.color=7;
  item.evolving=true;CHECK(!PlainUpgradeItem(&item));item.evolving=false;
  item.scaling=true;CHECK(!PlainUpgradeItem(&item));item.scaling=false;
  item.filled=true;CHECK(!PlainUpgradeItem(&item));item.filled=false;
  item.metadata="nightcap_item_xp^1:999:123^";CHECK(!PlainUpgradeItem(&item));
  item.metadata="foreign^data^";CHECK(!PlainUpgradeItem(&item));
 }
}
''')


if __name__ == '__main__':
    unittest.main()

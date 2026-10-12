"""Compile existing native LORE projection and conflict gates for the rule rollout."""
import re
import unittest
import test_free_trade as native


class RemoveItemLoreTests(unittest.TestCase):
    def test_native_projection_and_ownership(self):
        shared = (native.CODE / 'common/shareddb.cpp').read_text()
        assignments = re.findall(r'item\.Lore(?:Group|Flag)\s*=.*?;', shared)
        self.assertEqual(len(assignments), 2)
        gate = native.body((native.CODE / 'zone/inventory.cpp').read_text(),
                           'bool Client::CheckLoreConflict(')
        source = r"""
#include <cassert>
#include <initializer_list>
namespace EQ { struct ItemData { int ID=42, LoreGroup=0; bool LoreFlag=false; }; }
constexpr int invWhereSharedBank=1, INVALID_INDEX=-1;
struct Inventory {
 int HasItem(int, int, int) const { return 23; }
 int HasItemByLoreGroup(int, int) const { return 23; }
};
struct Client {
 Inventory m_inv;
 bool PetArmorLoreConflict(const EQ::ItemData*) const { return true; }
 bool CheckLoreConflict(const EQ::ItemData* item, bool include_pet_armor);
};
""" + gate + r"""
int main() {
 Client client;
 for (int group : {-1, 0, 42, 1000, 2147483647}) {
  for (bool disable_lore : {false, true}) {
   struct { int loregroup; } e{group};
   EQ::ItemData item;
""" + '\n'.join(assignments) + r"""
   assert(item.LoreGroup == (disable_lore ? 0 : group));
   assert(item.LoreFlag == (!disable_lore && group != 0));
   for (bool pets : {false, true})
    assert(client.CheckLoreConflict(&item, pets) == (!disable_lore && group != 0));
   assert(e.loregroup == group);
  }
 }
 assert(!client.CheckLoreConflict(nullptr, true));
}
"""
        native.FreeTradeTests.compile_run(self, source)

    def test_loader_rule_and_client_use_effective_group(self):
        shared = (native.CODE / 'common/shareddb.cpp').read_text()
        self.assertIn('RuleB(Items, DisableLore)', shared)
        codec = (native.CODE / 'common/patches/rof2.cpp').read_text()
        self.assertIn('itbs.loregroup = item->LoreGroup;', codec)


if __name__ == '__main__':
    unittest.main()

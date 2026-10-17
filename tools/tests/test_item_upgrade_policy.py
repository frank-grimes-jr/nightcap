"""Compile the item-upgrade policy independently of live server state."""
import unittest
import test_free_trade as native


class ItemUpgradePolicyTests(unittest.TestCase):
    def test_upgrade_recipe(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "common/item_upgrade_policy.h"
#include <cassert>
int main() {
    using namespace NightcapUpgrade;
    assert(LegacyTarget(1001) == 201001);
    assert(LegacyTarget(201001) == 401001);
    assert(LegacyTarget(401001) == 601001);
    for (unsigned id : {0u, 200000u, 400000u, 600000u, 601001u, 800001u, 940025u})
        assert(LegacyTarget(id) == 0);
    assert(ZoneTarget(940025) == 940026);
    assert(ZoneTarget(940026) == 940027);
    assert(ZoneTarget(940024) == 940025);
    assert(ZoneTarget(940027) == 0);
    assert(ZoneTarget(949998) == 0);
    assert(ZoneCopies(940024) == 3);
    assert(ZoneCopies(940025) == 4);
    assert(ZoneCopies(940026) == 4);
    assert(BoxCopies(1001) == 3);
    assert(BoxCopies(201001) == 4);
    assert(BoxCopies(401001) == 4);
    assert(BoxCopies(940024) == 3);
    assert(BoxCopies(940025) == 4);
    assert(BoxCopies(940026) == 4);
    for (unsigned id : {0u, 200000u, 400000u, 600000u, 601001u, 940027u, 949998u, 960000u})
        assert(BoxCopies(id) == 0);
    assert(NamesMatch("Cloth Cap", "Cloth Cap (Polished)", 1001));
    assert(!NamesMatch("Cloth Cap", "Cloth Gloves (Polished)", 1001));
    assert(!NamesMatch("Cloth Cap", "Cloth Cap (Exalted)", 1001));
    assert(!NamesMatch("", " (Polished)", 1001));
    assert(!NamesMatch("Cloth Cap", "Cloth Cap (Polished)", 601001));
    assert(NamesMatch("Cloth Cap (Polished)", "Cloth Cap (Exalted)", 201001));
    assert(NamesMatch("Cloth Cap (Exalted)", "Cloth Cap (Ascended)", 401001));
    assert(!NamesMatch("Cloth Cap (Polished)", "Cloth Gloves (Exalted)", 201001));
    assert(!NamesMatch("Arbitrary", "Arbitrary", 201001));
}
''')


if __name__ == '__main__':
    unittest.main()

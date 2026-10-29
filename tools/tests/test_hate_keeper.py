"""Cross-zone Keeper routing must retain destination, admission and run identity."""
from pathlib import Path
import unittest
import test_free_trade as native

ROOT=Path(__file__).resolve().parents[2]

class HateKeeper(unittest.TestCase):
    def test_host_and_destination_are_distinct(self):
        native.FreeTradeTests.compile_run(self,r'''
#include "common/dungeon_policy.h"
#include <cassert>
using namespace NightcapDungeon;
int main() {
 const auto hate=FindDungeon(186);
 assert(hate && KeeperDungeon(22,0,998812)==hate);
 assert(!KeeperDungeon(22,1,998812));
 assert(!KeeperDungeon(22,0,998811));
 assert(!KeeperDungeon(21,0,998812));
 assert(!KeeperDungeon(0,0,998812));
 for (const auto &d:Dungeons) {
  assert(KeeperDungeon(d.zone,0,d.keeper)==&d);
  assert(KeeperDungeon(d.zone,12,d.keeper)==&d);
  assert(!KeeperDungeon(d.zone,0,1));
 }
 assert(hate->index==19 && hate->keeper==998812 && hate->zone==186);
}
''')

    def test_entry_uses_target_zone_and_checks_access_before_writes(self):
        source=(ROOT/'server-mods/code/zone/dungeon_service.cpp').read_text()
        keeper=native.body(source,'bool Keeper(')
        self.assertIn('KeeperDungeon(zone->GetZoneID(),zone->GetInstanceID(),keeper->GetNPCTypeID())',keeper)
        self.assertIn('c->CanEnterZone(d->name,0)',keeper)
        self.assertLess(keeper.index('c->CanEnterZone(d->name,0)'),keeper.index('auto legacy='))
        self.assertIn('GetZoneVersionWithFallback(d->zone,0)',keeper)
        self.assertNotIn('zone->GetSafePoint()',keeper)
        self.assertIn('destination->safe_x,destination->safe_y,destination->safe_z,destination->safe_heading',keeper)
        self.assertLess(keeper.index('GetZoneVersionWithFallback(d->zone,0)'),keeper.index('Transaction tx;\n\t\t\t// Serialize'))

if __name__=='__main__':unittest.main()

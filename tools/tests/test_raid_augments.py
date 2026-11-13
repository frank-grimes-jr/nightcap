"""Run the native raid policy and effect handlers with controlled combat and timer inputs."""
from pathlib import Path
import json
import unittest
import test_free_trade

ROOT = Path(__file__).resolve().parents[2]


class RaidAugmentTests(unittest.TestCase):
    def test_native_paths(self):
        fixture = (Path(__file__).with_name('raid_augment_fixture.cpp')).read_text()
        test_free_trade.FreeTradeTests.compile_run(self, fixture)

    def test_actual_corpse_staging(self):
        native = test_free_trade
        source = (native.CODE / 'zone/dungeon_service.cpp').read_text(encoding='utf-8')
        handler = native.body(source, 'bool PrepareRaidAugment(')
        fixture = Path(__file__).with_name('raid_augment_drop_fixture.cpp').read_text()
        native.FreeTradeTests.compile_run(self, fixture.replace('// ACTUAL_DROP', handler))

    def test_all_managed_sources(self):
        items = json.loads((ROOT / 'config/classic-raid-augments.json').read_text())
        sources = {(z, n): p for i in items for z, n, p in i['sources']}
        dungeons = json.loads((ROOT / 'docs/dungeons/catalog.json').read_text())['dungeons']
        for dungeon in dungeons:
            zone = dungeon['zone_id']
            if zone not in (71, 72, 186):
                continue
            for boss in dungeon['bosses']:
                self.assertEqual(sources[(76 if zone == 186 else zone, boss['npc_id'])],
                                 50 if boss['is_final'] else 15)
        self.assertEqual(len(items), 16)
        self.assertEqual(len(sources), 25)


if __name__ == '__main__':
    unittest.main()

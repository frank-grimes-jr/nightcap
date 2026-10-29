"""Compile actual cap functions and the exact integer death/quality policy."""
from pathlib import Path
import unittest
import test_free_trade as native

ROOT=Path(__file__).resolve().parents[2]

class NativeZoneHunt(unittest.TestCase):
    def test_actual_load_with_augment_only_zone(self):
        load=native.body((ROOT/'server-mods/code/zone/zone_hunt.cpp').read_text(),'void Load(')
        fixture=(Path(__file__).parent/'zone_hunt_load_fixture.cpp').read_text()
        native.FreeTradeTests.compile_run(self,fixture.replace('// ACTUAL_LOAD',load))

    def test_actual_death_award(self):
        award=native.body((ROOT/'server-mods/code/zone/zone_hunt.cpp').read_text(),'void Award(')
        fixture=(Path(__file__).parent/'zone_hunt_death_fixture.cpp').read_text()
        native.FreeTradeTests.compile_run(self,fixture.replace('// ACTUAL_AWARD',award))

    def test_native_caps_and_death_policy(self):
        bonus=(ROOT/'server-mods/code/zone/bonuses.cpp').read_text()
        caps=native.body(bonus,'void Mob::ProcessItemCaps()')
        scaling=native.body(bonus,'int Mob::CalcRecommendedLevelBonus(')
        headroom=native.body((ROOT/'server-mods/code/zone/zone_hunt.cpp').read_text(),'int OutputHeadroom(')
        fixture=(Path(__file__).parent/'zone_hunt_caps_fixture.cpp').read_text()
        native.FreeTradeTests.compile_run(self,fixture.replace('// ACTUAL_SCALING',scaling)
            .replace('// ACTUAL_HEADROOM',headroom).replace('// ACTUAL_CAPS',caps))

    def test_death_integration_and_nonplayer_caps(self):
        attack=(ROOT/'server-mods/code/zone/attack.cpp').read_text()
        death=native.body(attack,'bool NPC::Death(')
        self.assertLess(death.index('const bool hunt_owned'),death.index('EVENT_DEATH'))
        # Managed deaths stage the same native corpse before publication so its
        # finalized hunt/native loot can commit with the durable death record.
        self.assertLess(death.index('const bool hunt_owned'),death.index('BuffFadeAll()'))
        self.assertLess(death.index('NightcapDungeon::BeforeDeath'),death.index('entity_list.QueueClients(killer_mob, app'))
        self.assertIn('!prepared_dungeon_death && !prepare_corpse()',death)
        self.assertLess(death.index('NightcapHunt::Award'),death.index('corpse = new Corpse'))
        self.assertEqual(death.count('NightcapHunt::Award'),1)
        bonus=native.body((ROOT/'server-mods/code/zone/bonuses.cpp').read_text(),'void Mob::AddItemBonuses(')
        for stat in ('HealAmt','SpellDmg'):
            line=next(line for line in bonus.splitlines() if f'b->{stat} ' in line and '= IsClient()' in line)
            self.assertIn('CalcCappedItemBonus',line) # preserve mercs without ProcessItemCaps

    def test_no_resale_survives_free_trade(self):
        shared=(ROOT/'server-mods/code/common/shareddb.cpp').read_text()
        start=shared.index('EQ::ItemTradePolicy::Apply(item,')
        custom=shared.index('if (NightcapHunt::IsReward(item.ID) || NightcapDungeon::IsReward(item.ID))',start)
        self.assertIn('item.FixedSellPrice = 0;',shared[custom:custom+360])
        sell=native.body((ROOT/'server-mods/code/zone/client_packet.cpp').read_text(),'void Client::Handle_OP_ShopPlayerSell(')
        self.assertLess(sell.index('NightcapHunt::IsReward(itemid)'),sell.index('const EQ::ItemData* item'))

if __name__=='__main__': unittest.main()

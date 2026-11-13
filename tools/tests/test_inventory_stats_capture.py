"""Execute the real read-only collection, distinguishing similarly named getters."""
from pathlib import Path
import unittest
import test_free_trade as native

ROOT=Path(__file__).resolve().parents[2]


class InventoryStatsCapture(unittest.TestCase):
    def test_exact_combat_getters_caps_heroics_and_signed_sentinel(self):
        text=(ROOT/'server-mods/code/zone/gm_commands/nightcapui.cpp').read_text(encoding='utf-8')
        collection=native.body(text,'static NightcapInventory::Snapshot CaptureInventoryStats(')
        fixture=r'''
#include "common/inventory_stats_protocol.h"
#include <algorithm>
#include <cassert>
struct Client {
 int defense=795;uint32_t attack=1857;
 int GetMitigationAC(){return 916;}int GetTotalDefense(){return defense;}
 uint32_t GetTotalATK(){return attack;}int GetSpellDmg(){return 653;}int GetHealAmt(){return 532;}
 int ACSum(){return 12345;}int GetAvoidance(){return 24;}int GetAC(){return 99;}int compute_defense(){return 80;}
#define STAT(name,cur,cap,hero) int Get##name(){return cur;}int GetMax##name(){return cap;}int GetHeroic##name(){return hero;}
 STAT(STR,434,434,104) STAT(STA,388,388,58) STAT(AGI,356,356,26) STAT(DEX,383,383,53)
 STAT(WIS,508,508,128) STAT(INT,540,540,160) STAT(CHA,356,356,-3)
};
// COLLECTION
int main(){using namespace NightcapInventory;Client c;auto s=CaptureInventoryStats(c);
 assert(s.values[Mitigation]==916&&s.values[Defense]==795&&s.values[Attack]==1857);
 assert(s.values[SpellDamage]==653&&s.values[Heal]==532);
 assert(s.values[Strength]==434&&s.values[StrengthCap]==434&&s.values[HeroicStrength]==104);
 assert(s.values[Stamina]==388&&s.values[Agility]==356&&s.values[Dexterity]==383);
 assert(s.values[Wisdom]==508&&s.values[Intelligence]==540&&s.values[Charisma]==356);
 assert(s.values[StaminaCap]==388&&s.values[AgilityCap]==356&&s.values[DexterityCap]==383);
 assert(s.values[WisdomCap]==508&&s.values[IntelligenceCap]==540&&s.values[CharismaCap]==356);
 assert(s.values[HeroicStamina]==58&&s.values[HeroicAgility]==26&&s.values[HeroicDexterity]==53);
 assert(s.values[HeroicWisdom]==128&&s.values[HeroicIntelligence]==160&&s.values[HeroicCharisma]==-3);
 c.defense=-1;assert(CaptureInventoryStats(c).values[Defense]==-1);
 c.attack=UINT32_MAX;assert(CaptureInventoryStats(c).values[Attack]==INT32_MAX);
}
'''
        native.FreeTradeTests.compile_run(self,fixture.replace('// COLLECTION',collection))

    def test_negotiation_preserves_legacy_and_quiet_permission_boundary(self):
        text=(ROOT/'server-mods/code/zone/gm_commands/nightcapui.cpp').read_text(encoding='utf-8')
        refresh=native.body(text,'void Client::RefreshEquippedStats(')
        self.assertIn('if (include_inventory)',refresh)
        self.assertLess(refresh.index('m_nightcap_ui_refresh_timer.Check(false)'),refresh.index('CaptureInventoryStats'))
        handler=native.body(text,'void command_nightcapui(')
        self.assertIn('!strcmp(sep->arg[1], "inventory")',handler)
        dispatch=native.body((ROOT/'server-mods/code/zone/command.cpp').read_text(encoding='utf-8'),'int command_realdispatch(')
        quiet=dispatch.index('current_command->function == command_nightcapui')
        self.assertLess(dispatch.index('c->Admin()'),quiet)
        self.assertLess(dispatch.index('command_subsettings'),quiet)
        self.assertLess(quiet,dispatch.index('EVENT_GM_COMMAND'))
        self.assertIn('!strcmp(sep.arg[1], "inventory")',dispatch[quiet:quiet+260])

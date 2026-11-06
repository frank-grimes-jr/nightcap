"""Production-capture-backed coverage, budgets, migration and native regression controls."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import augment_audit as audit
import test_free_trade as native


class AugmentAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads((audit.OUT / 'item-preimages.json').read_text())
        cls.summary = json.loads((audit.OUT / 'summary.json').read_text())

    def test_every_family_and_quality_has_a_reviewed_icon_and_specialty(self):
        self.assertEqual(len(self.rows), 232)
        self.assertEqual(len({r['before']['id'] for r in self.rows}), 232)
        self.assertEqual(len(self.summary['families']), 58)
        for f in self.summary['families']:
            rows = [r for r in self.rows if r['zone'] == f['zone']]
            self.assertEqual({r['tier'] for r in rows}, {0, 1, 2, 3})
            self.assertEqual({int(r['after']['icon']) for r in rows}, {f['icon']})
            self.assertIn(f['icon'], audit.ICONS)
            self.assertNotIn(f['icon'], (500, 517))

    def test_no_primary_power_loss_and_small_six_socket_totals(self):
        allowed = {'icon', 'lore', 'accuracy', 'avoidance', 'shielding', 'spellshield', 'spelldmg', 'healamt',
                   'focuseffect', 'focustype', 'focuslevel', 'focuslevel2',
                   'worneffect', 'worntype', 'wornlevel', 'wornlevel2'}
        for r in self.rows:
            for field, value in r['before'].items():
                if field not in allowed:
                    self.assertEqual(r['after'][field], value, (r['zone'], field))
            for field, limit in [('avoidance', 24), ('shielding', 6), ('spellshield', 12),
                                 ('accuracy', 30), ('spelldmg', 48), ('healamt', 48)]:
                self.assertLessEqual(6 * int(r['after'][field]), limit)
            for field in ('spelldmg', 'healamt'):
                self.assertGreaterEqual(int(r['after'][field]), int(r['before'][field]))

    def test_focus_and_worn_effects_are_real_and_correctly_typed(self):
        spells = {s['id']: s for s in json.loads((audit.OUT / 'effect-preimages.json').read_text())}
        for r in self.rows:
            after = r['after']
            if int(after['focuseffect']) > 0:
                spell = spells[after['focuseffect']]
                self.assertIn(spell['effectid1'], ('127', '132'))
                self.assertEqual(after['focustype'], '6')
            if int(after['worneffect']) > 0:
                self.assertIn(after['worneffect'], ('3660', '3889'))
                self.assertEqual(after['worntype'], '2')

    def test_migration_is_exact_and_transactional(self):
        zones = json.loads((audit.OUT / 'zone-preimages.json').read_text())
        effects = json.loads((audit.OUT / 'effect-preimages.json').read_text())
        for reverse, name in [(False, 'forward.sql'), (True, 'rollback.sql')]:
            sql = audit.guarded_sql(self.rows, reverse=reverse, zones=zones, effects=effects)
            self.assertEqual(sql, (audit.OUT / name).read_text())
            self.assertEqual(sql.count(' UPDATE items SET '), 232)
            self.assertEqual(sql.count(' UPDATE nightcap_zone_hunt_zones SET '), 2)
            self.assertIn('ROLLBACK; RESIGNAL;', sql)
            self.assertNotIn('DELETE ', sql)
            self.assertNotIn('ALTER TABLE', sql)

    def test_actual_shield_inventory_scan_and_strongest_only_policy(self):
        source = (ROOT / 'server-mods/code/zone/zone_hunt.cpp').read_text()
        shield = native.body(source, 'int OutputShieldBlock(')
        fixture = r'''
#include "common/zone_hunt_policy.h"
#include <array>
#include <cassert>
#include <map>
#include <memory>
using int16=int16_t;using uint8=uint8_t;
namespace EQ {namespace item {constexpr int ItemTypeShield=8;}namespace invaug {constexpr uint8 SOCKET_COUNT=6;}}
struct Data {int ItemType=0;std::array<int,6> AugSlotType{};bool allowed=true;};
struct Item {Data data;int req=1;uint32_t id=0;std::array<std::shared_ptr<Item>,6> augs;
 bool IsClassCommon()const{return true;}const Data*GetItem()const{return &data;}
 int GetItemRequiredLevel(bool)const{return req;}const Item*GetAugment(uint8 n)const{return augs[n].get();}uint32_t GetID()const{return id;}};
struct Inventory {std::map<int16,Item> items;const Item*GetItem(int16 s)const{auto i=items.find(s);return i==items.end()?nullptr:&i->second;}};
struct Client {Inventory inv;int level=50;int GetLevel(){return level;}Inventory&GetInv(){return inv;}bool CanEquipItem(const Data*d){return d->allowed;}};
namespace NightcapHunt {
// ACTUAL_SHIELD
}
int main(){using namespace NightcapHunt;Client c;assert(!OutputShieldBlock(c));
 c.inv.items[14].data.ItemType=8;
 for(int s:{2,7,12,17,18,19}){auto&p=c.inv.items[static_cast<int16>(s)];p.data.AugSlotType[0]=22;p.augs[0]=std::make_shared<Item>();p.augs[0]->id=940043;}
 assert(OutputShieldBlock(c)==2); // six copies never give 12%
 for(int s:{2,7,12,17,18,19})c.inv.items[static_cast<int16>(s)].augs[0]->id=940041;
 assert(OutputShieldBlock(c)==1);
 c.inv.items[14].data.allowed=false;assert(!OutputShieldBlock(c));c.inv.items[14].data.allowed=true;
 c.inv.items[14].data.ItemType=0;assert(!OutputShieldBlock(c));c.inv.items[14].data.ItemType=8;
 c.inv.items[14].req=51;assert(!OutputShieldBlock(c));c.inv.items[14].req=1;
 for(int s:{2,7,12,17,18,19})c.inv.items[static_cast<int16>(s)].req=51;
 assert(!OutputShieldBlock(c));
 c.inv.items[2].req=1;c.inv.items[2].augs[0]->req=51;assert(!OutputShieldBlock(c));
 c.inv.items[2].augs[0]->req=1;c.inv.items[2].data.AugSlotType[0]=7;assert(!OutputShieldBlock(c));
 for(uint32_t b:{940040u,940280u,940528u}){assert(!AugmentShieldBlock(b));assert(AugmentShieldBlock(b+1)==1);assert(AugmentShieldBlock(b+2)==1);assert(AugmentShieldBlock(b+3)==2);assert(!AugmentShieldBlock(b+4));}
}
'''
        native.FreeTradeTests.compile_run(self, fixture.replace('// ACTUAL_SHIELD', shield))

    def test_load_and_death_order_preserve_layout_and_scripted_guard_drops(self):
        source = (ROOT / 'server-mods/code/zone/zone_hunt.cpp').read_text()
        load = native.body(source, 'void Load(')
        self.assertIn('Revision, z.GetZoneID()', load)
        self.assertIn('gear_chance FROM nightcap_zone_hunt_zones', load)
        self.assertIn('hunt.enabled = true', load)
        self.assertNotIn('hunt.enabled = !hunt.sources.empty()', load)
        death = native.body((ROOT / 'server-mods/code/zone/attack.cpp').read_text(), 'bool NPC::Death(')
        self.assertLess(death.index('NightcapDungeon::PrepareLoot'), death.index('NightcapHunt::Award'))

    def test_expedition_rates_match_default_and_keep_named_reward_gates(self):
        rate = json.loads((ROOT / 'config/zone-hunt-rates.json').read_text())['default']['augment_chance']
        header = (ROOT / 'server-mods/code/common/zone_hunt_policy.h').read_text()
        self.assertIn(f'ExpeditionAugmentChance = {rate}', header)
        source = (ROOT / 'server-mods/code/zone/dungeon_service.cpp').read_text()
        loot = native.body(source, 'bool PrepareLoot(')
        self.assertEqual(loot.count('augment_roll(302)<NightcapHunt::ExpeditionAugmentChance'), 2)
        for ns in ('NightcapVigil', 'NightcapAshen'):
            self.assertIn(f'spawn && {ns}::Combat(npc->GetNPCTypeID()) && mini', loot)
        self.assertEqual(loot.count('GetEntityVariable("nightcap:'), 2)


if __name__ == '__main__':
    unittest.main()

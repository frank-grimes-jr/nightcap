"""Earned title policy and native integration; no player-state writes."""
from pathlib import Path
import unittest
import test_free_trade as native

ROOT = Path(__file__).resolve().parents[2]


class EarnedTitlesTests(unittest.TestCase):
    def test_actual_service_storage_and_failures(self):
        service = (ROOT / 'server-mods/code/zone/earned_titles.inc').read_text(encoding='utf-8')
        service = '\n'.join(line for line in service.splitlines() if not line.startswith('#include'))
        fixture = (ROOT / 'tools/tests/earned_titles_service_fixture.cpp').read_text(encoding='utf-8')
        native.FreeTradeTests.compile_run(self, fixture.replace('// ACTUAL_SERVICE', service))

    def test_native_policy(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "common/earned_title_policy.h"
#include <cassert>
using namespace NightcapTitles;
int main() {
 Snapshot s;
 for (const auto &d : Catalog) { assert(!Earned(d,s)); }
 assert(KillKeys(3,1,1).at(1)==2);
 assert(KillKeys(8,1,1).at(1)==2);
 assert(KillKeys(12,1,1).at(1)==2);
 assert(KillKeys(9,1,1).at(1)==3);
 assert(KillKeys(29,1,1).at(1)==4);
 assert(KillKeys(1,32,32040).back()==100);
 assert(KillKeys(1,22,32040).size()==1);
 assert(!CreditEligible(true,false,false,false,false,0));
 assert(!CreditEligible(true,true,true,true,true,40001));
 assert(CreditEligible(true,true,true,true,true,40000));
 s.counters[1]=99;
 assert(!Earned(Catalog[0],s));
 s.counters[1]=100;
 assert(Earned(Catalog[0],s));
 s.counters[1]=100000;
 assert(Earned(Catalog[2],s));
 unsigned skills=0, classic=0, both=0;
 for (const auto &d : Catalog) {
  if (d.kind==Kind::Skill) {
   ++skills; s.level=49; s.skills[d.key]={200,200};
   assert(!Earned(d,s));
   s.level=50; s.skills[d.key]={0,0}; assert(!Earned(d,s));
   s.skills[d.key]={199,200}; assert(!Earned(d,s));
   s.skills[d.key]={200,200}; assert(Earned(d,s));
  }
  if (d.kind==Kind::Classic) {
   ++classic;
   for (const auto zone : ClassicZones) { s.raid_zones.insert(zone); }
   s.raid_zones.erase(186); s.raid_zones.insert(760); s.raid_zones.insert(113);
   assert(!Earned(d,s));
   s.raid_zones.insert(186); assert(Earned(d,s));
  }
  if (d.kind==Kind::BothDragons) {
   ++both; s.counters[100]=1; assert(!Earned(d,s));
   s.counters[101]=1; assert(Earned(d,s));
  }
  if (d.kind==Kind::AllCrafts) {
   s.level=50;
   for (auto skill : Crafts) { s.skills[skill]={200,200}; }
   s.skills[69]={199,200}; assert(!Earned(d,s));
   s.skills[69]={200,200}; assert(Earned(d,s));
  }
  if (d.kind==Kind::Task) {
   assert(!Earned(d,s)); s.tasks.insert(d.key); assert(Earned(d,s));
  }
 }
 assert(skills>=20 && classic==1 && both==1);
 assert(NormalizeZone(76)==186);
 for (const auto &a : Catalog) {
  assert(a.id>=TitleBegin && a.id<TitleEnd);
  assert(std::string(a.name).size()<32);
  for (const auto &b : Catalog) { if (&a!=&b) { assert(a.id!=b.id); } }
 }
}
''')

    def test_hooks_and_authorization(self):
        zone = ROOT / 'server-mods/code/zone'
        titles = (zone / 'titles.cpp').read_text()
        self.assertIn('NightcapTitles::AppendEligible(c, titles, eligible_titles)', titles)
        self.assertIn('NightcapTitles::Name(title_id, false)', titles)
        self.assertIn('NightcapTitles::Name(title_id, true)', titles)
        attack = (zone / 'attack.cpp').read_text()
        hook = attack.index('NightcapTitles::RecordKill(')
        self.assertGreater(hook, attack.index('m_combat_record.Stop();', attack.index('bool NPC::Death(')))
        self.assertIn('AccountStatus::Player, command_titles)', (zone / 'command.cpp').read_text())

    def test_automatic_completion_hooks(self):
        zone = ROOT / 'server-mods/code/zone'
        for name in ['client_packet.cpp','client_process.cpp','exp.cpp','dungeon_service.cpp','task_manager.cpp','task_client_state.cpp']:
            text=(zone/name).read_text(encoding='utf-8')
            self.assertLess(text.index('#include "zone/earned_titles.h"'),text.index('NightcapTitles::'),name)
        self.assertTrue('NightcapTitles::Pulse(this);' in (zone/'client_process.cpp').read_text(encoding='utf-8'))
        login=(zone/'client_packet.cpp').read_text(encoding='utf-8')
        connect=login[login.index('void Client::CompleteConnect()'):login.index('// connecting opcode handlers')]
        self.assertGreater(connect.index('NightcapTitles::RequestCheck(this);'),connect.index('client_data_loaded = true;'))
        level=(zone/'exp.cpp').read_text(encoding='utf-8').split('void Client::SetLevel(',1)[1].split('uint32 Client::GetEXPForLevel',1)[0]
        self.assertGreater(level.index('NightcapTitles::RequestCheck(this);'),level.rindex('Save();'))
        dungeon=(zone/'dungeon_service.cpp').read_text(encoding='utf-8').split('bool BeforeDeath(',1)[1].split('void JournalForRun(',1)[0]
        self.assertLess(dungeon.index('NightcapTitles::RequestCheck(c);'),dungeon.index('Journal(c);'))
        self.assertGreater(dungeon.index('NightcapTitles::RequestCheck(c);'),dungeon.index('tx.Commit();'))
        self.assertLess(dungeon.index('NightcapTitles::RequestCheck(c);'),dungeon.index('npc->SetEntityVariable("nightcap:dungeon-death-committed"'))
        rescue=(zone/'highkeep_rescue.inc').read_text(encoding='utf-8').split('void Complete(',1)[1].split('bool Action(',1)[0]
        self.assertGreater(rescue.index('NightcapTitles::RequestCheck(c);'),rescue.index('tx.Commit();'))
        self.assertLess(rescue.index('NightcapTitles::RequestCheck(c);'),rescue.index('Journal(c);'))
        task=(zone/'task_manager.cpp').read_text(encoding='utf-8').split('bool TaskManager::SaveClientState(',1)[1].split('int TaskManager::FirstTaskInSet',1)[0]
        self.assertIn('if (task_id==9515) { NightcapTitles::RequestCheck(client); }',task)

    def test_catalog_and_wiki_are_generated_together(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('earned_titles_catalog', ROOT/'tools/earned_titles.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name, expected in module.outputs().items():
            self.assertEqual((ROOT/name).read_text(encoding='utf-8'), expected, name)
        rows, zones = module.catalog()
        self.assertEqual(len(rows), 77)
        self.assertEqual(len({z[0] for z in zones}), 21)


if __name__ == '__main__':
    unittest.main()

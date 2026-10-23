"""Chapterhouse release boundaries: curated level-50 content and no stock loot."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import chapterhouse_content as content
import test_free_trade as native

class Chapterhouse(unittest.TestCase):
    def test_explicit_population_and_reward_budgets(self):
        rows=content.compile_rows()
        combat=[n for n in rows['npc_types'] if n['id'] in content.COMBAT]
        self.assertEqual(len(combat),len(content.COMBAT))
        for n in combat:
            self.assertLessEqual(n['level'],53)
            self.assertGreaterEqual(n['level'],46)
            self.assertEqual(n['skip_global_loot'],1)
            self.assertEqual(n['merchant_id'],0)
            self.assertEqual(n['npc_spells_id'],0)
            self.assertEqual(n['npc_spells_effects_id'],0)
            self.assertEqual(n['loottable_id'],0)
            self.assertEqual(n['hp_regen_per_second'],0)
            self.assertLessEqual(n['maxdmg'],1800)
            self.assertEqual(n['bodytype'],3) # Slay Undead and weapon procs remain effective.
        self.assertEqual(len({s['spawn_id'] for s in rows['nightcap_dungeon_spawns']}),len(rows['nightcap_dungeon_spawns']))
        self.assertTrue(all(s['npc_id'] in content.COMBAT or s['npc_id'] in content.SERVICES for s in rows['nightcap_dungeon_spawns']))
        for r in rows['items']:
            self.assertLess(r['id'],1048576)
            self.assertLessEqual(r['reqlevel'],50)
            for k in ('clickeffect','proceffect','worneffect','focuseffect'):
                self.assertEqual(r[k],-1)
        aug=next(r for r in rows['items'] if r['id']==content.AUGMENT)
        self.assertEqual(aug['augtype'],2097152)
        self.assertEqual(aug['slots'],921732)
        self.assertEqual(aug['reqlevel'],50)

    def test_campaign_order_and_credit_policy(self):
        native.FreeTradeTests.compile_run(self,r'''
#include "common/chapterhouse_policy.h"
#include "common/item_upgrade_policy.h"
#include <cassert>
int main(){
 using namespace NightcapVigil;
 assert(!Eligible(49,8) && Eligible(50,8) && Eligible(50,10) && !Eligible(50,2));
 unsigned mask=0;
 assert(!Advance(mask,Event::Vicar));
 assert(Advance(mask,Event::Enter));
 assert(!Advance(mask,Event::Halvyr));
 assert(Advance(mask,Event::Vicar));
 assert(!Advance(mask,Event::Vicar));
 for(auto e:{Event::Record1,Event::Record2,Event::Record3})assert(Advance(mask,e));
 assert(Advance(mask,Event::Vigil));
 assert(Advance(mask,Event::Halvyr));
 for(auto e:{Event::Knight1,Event::Knight2,Event::Knight3})assert(Advance(mask,e));
 assert(Advance(mask,Event::Vaelen));assert(Advance(mask,Event::Shadow));
 assert(Advance(mask,Event::Chapel));assert(Ready(mask));
 assert(!Advance(mask,Event::Chapel));
 assert(!Credit(true,false,100) && !Credit(false,true,100) && !Credit(true,true,40001));
 assert(Credit(true,true,40000));
 assert(NightcapHunt::IsAugment(961000) && NightcapHunt::IsReward(961003));
 assert(NightcapUpgrade::ZoneCopies(961000)==3 && NightcapUpgrade::ZoneCopies(961001)==4);
 assert(NightcapHunt::NextTier(961002)==961003 && !NightcapHunt::NextTier(961003));
}
''')

    def test_actual_defense_tick_enforces_cadence_and_cleans_failed_attempts(self):
        source=(content.ROOT/'server-mods/code/zone/chapterhouse_vigil.inc').read_text()
        function=native.body(source,'void Tick(')
        native.FreeTradeTests.compile_run(self,r'''
#include <cassert>
#include <cstdint>
#include <exception>
#include <set>
#include <stdexcept>
#include <string>
struct Point{float x=0;};float DistanceSquared(Point a,Point b){return (a.x-b.x)*(a.x-b.x);}
struct NPC{int hp=1;std::string token="attempt";int GetHP(){return hp;}std::string GetEntityVariable(const char*){return token;}Point GetPosition(){return {};}} test_guardian;
struct Client{bool connected=true,dead=false;float x=0;bool Connected(){return connected;}bool IsDead(){return dead;}Point GetPosition(){return {x};}} client;
struct Entities{bool exists=true;NPC*GetNPCByID(unsigned){return exists?&test_guardian:nullptr;}Client*GetClientByCharID(unsigned){return &client;}} entity_list;
struct Defense{std::string run="run",token="attempt";unsigned guardian=1,wave=1;uint64_t expires=300,next_wave=115;std::set<unsigned> enemies,participants{42};} defense;
struct Run{std::string id="run";uint64_t expiry=1000;}current;
bool healthy=true,fail_wave=false;int cleared=0,started=0;uint64_t tick_now=100;
uint64_t Now(){return tick_now;}void ClearDefense(){++cleared;defense.run.clear();}
void NextWave(){if(fail_wave)throw std::runtime_error("injected spawn failure");++started;++defense.wave;defense.enemies.insert(2);}
template<class...T>void LogError(const char*,T...){}
'''+function+r'''
void Reset(){defense=Defense{};current=Run{};test_guardian=NPC{};client=Client{};entity_list.exists=true;healthy=true;tick_now=100;fail_wave=false;}
int main(){
 Tick();assert(started==0&&cleared==0);tick_now=115;Tick();assert(started==1);
 tick_now=130;Tick();assert(started==1); // existing wave must die
 Reset();defense.wave=3;tick_now=200;Tick();assert(started==1); // never fourth wave
 Reset();test_guardian.hp=0;Tick();assert(cleared==1);Tick();assert(cleared==1);
 Reset();test_guardian.token="reused-entity";Tick();assert(cleared==2);
 Reset();client.dead=true;Tick();assert(cleared==3);
 Reset();client.x=201;Tick();assert(cleared==4);
 Reset();current.id="new-generation";Tick();assert(cleared==5);
 Reset();tick_now=301;Tick();assert(cleared==6);
 Reset();tick_now=115;fail_wave=true;Tick();assert(cleared==7);
}
''')

if __name__=='__main__':unittest.main()

"""Ashen progression cannot borrow Camil state or bypass ordered duties."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import test_free_trade as native
import warhelm_content as content

class Warhelm(unittest.TestCase):
    def test_champions_use_kael_storm_giants_and_leave_interrupts_available(self):
        import json
        snapshot=json.loads((content.OUT/'local-content.json').read_text())
        native_giant=next(n for n in snapshot['npc_types'] if n['id']==113001)
        self.assertEqual(native_giant['name'],'#Watchman_Sunderthorn')
        rows={n['id']:n for n in content.compile_rows()['npc_types']}
        for npc in range(998861,998865):
            row=rows[npc]
            self.assertEqual((row['race'],row['bodytype']),(native_giant['race'],4))
            abilities={int(a.split(',')[0]) for a in row['special_abilities'].split('^')}
            self.assertTrue({14,17,21}<=abilities) # Native charm/fear/fleeing immunity.
            self.assertNotIn(15,abilities) # Stun must remain an answer to warnings.
        self.assertIn('5,1,5',rows[998864]['special_abilities']) # Native5-percent flurry.
        self.assertEqual((rows[998876]['race'],rows[998876]['bodytype']),(85,3))
        self.assertNotIn('17,1',rows[998876]['special_abilities'])

    def test_native_order_class_and_isolation(self):
        native.FreeTradeTests.compile_run(self,r'''
#include "common/warhelm_policy.h"
#include "common/chapterhouse_policy.h"
#include <cassert>
int main(){
 using namespace NightcapAshen;
 static_assert(Task!=NightcapVigil::Task && Helmet!=NightcapVigil::Helmet);
 assert(!Eligible(49,32) && Eligible(50,32) && Eligible(50,34));
 assert(!Eligible(50,8) && !Eligible(50,2));
 unsigned mask=0;
 assert(!Advance(mask,Event::Herald));
 assert(Advance(mask,Event::Enter)); assert(Advance(mask,Event::Herald));
 assert(!Advance(mask,Event::Binding));
 for(auto e:{Event::Standard1,Event::Standard2,Event::Standard3})assert(Advance(mask,e));
 assert(Advance(mask,Event::Binding));assert(Advance(mask,Event::Marshal));
 assert(!Advance(mask,Event::General));
 for(auto e:{Event::Knight1,Event::Knight2,Event::Knight3})assert(Advance(mask,e));
 assert(Advance(mask,Event::General));assert(Advance(mask,Event::Echo));
 assert(!Ready(mask));assert(Advance(mask,Event::Altar));assert(Ready(mask));
 assert(!Advance(mask,Event::Altar));
 assert(!Credit(true,false,1)&&!Credit(false,true,1)&&!Credit(true,true,40001));
 assert(Credit(true,true,40000));
 assert(!Combat(998821)&&Combat(998861)&&!Combat(998875));
 assert(Transient(998875)&&Transient(998876)&&!Transient(998861)&&!Transient(998821));
}
''')

    def test_actual_defense_tick_enforces_cadence_and_cleans_failed_attempts(self):
        source=(content.ROOT/'server-mods/code/zone/warhelm_compact.inc').read_text()
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

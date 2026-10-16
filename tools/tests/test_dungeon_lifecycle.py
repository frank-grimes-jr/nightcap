"""Execute actual spawn/credit functions and guard critical integration boundaries."""
from pathlib import Path
import unittest
import test_free_trade as native
ROOT=Path(__file__).resolve().parents[2]

class DungeonLifecycle(unittest.TestCase):
    def test_actual_encounter_credit(self):
        function=native.body((ROOT/'server-mods/code/zone/dungeon_service.cpp').read_text(),'std::vector<Client *> Credit(')
        native.FreeTradeTests.compile_run(self,r'''
#include <vector>
#include <map>
#include <cassert>
struct Pos { float x=0,y=0,z=0; };
float DistanceSquared(Pos a,Pos b) { return (a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y)+(a.z-b.z)*(a.z-b.z); }
struct Client; struct NPC;
struct Mob {
 bool client=false,npc=false; Mob *owner=nullptr; Pos pos;
 bool IsNPC() {return npc;} bool IsClient() {return client;}
 NPC *CastToNPC(); Client *CastToClient();
 Mob *GetUltimateOwner() {return owner?owner->GetUltimateOwner():this;}
 Pos GetPosition() {return pos;}
};
struct Client:Mob {
 bool connected=true,loaded=true; std::vector<Client*> party;
 Client() {client=true;party.push_back(this);}
 bool Connected() {return connected;} bool ClientDataLoaded() {return loaded;}
 std::vector<Client*> GetPartyMembers() {return party;}
};
struct NPC:Mob { unsigned swarm=0; NPC(){npc=true;} unsigned GetSwarmOwner(){return swarm;} };
NPC *Mob::CastToNPC(){return static_cast<NPC*>(this);}
Client *Mob::CastToClient(){return static_cast<Client*>(this);}
struct {std::map<unsigned,Mob*> entities;Mob *GetMobID(unsigned id){return entities[id];}} entity_list;
'''+function+r'''
int main() {
 NPC boss,pet,swarm,wild; Client owner,near,far,unloaded,offline;
 near.pos.z=200;far.pos.z=200.01f;unloaded.loaded=false;offline.connected=false;
 owner.party={&owner,&near,&far,&unloaded,&offline,nullptr};
 auto result=Credit(&boss,&owner); assert(result.size()==2 && result[1]==&near);
 pet.owner=&owner;assert(Credit(&boss,&pet)==result);
 swarm.swarm=7;entity_list.entities[7]=&pet;assert(Credit(&boss,&swarm)==result);
 entity_list.entities.clear();assert(Credit(&boss,&swarm).empty());
 assert(Credit(&boss,&wild).empty() && Credit(&boss,nullptr).empty());
 near.pos={141.43f,141.43f,0};assert(Credit(&boss,&owner).size()==1);
}
''')

    def test_actual_spawn_selection(self):
        source=(ROOT/'server-mods/code/zone/dungeon_service.cpp').read_text()
        function=native.body(source,'bool SelectSpawn(')
        native.FreeTradeTests.compile_run(self,r'''
#include "common/dungeon_policy.h"
#include "common/dungeon_catalog.h"
#include <set>
#include <cassert>
using namespace NightcapDungeon;
struct { Mode mode=Mode::Grind; uint64_t expiry=100; const Dungeon *dungeon=&Dungeons[0]; } current;
bool managed=true,healthy=true;
std::set<uint32_t> deaths,objectives;
uint64_t Now() { return 10; }
uint32_t delay=0;
uint32_t RespawnDelay(uint32_t) { return delay; }
bool Managed() { return managed; }
'''+function+r'''
int main() {
 for (const auto &d : Dungeons) {
  current.dungeon=&d; deaths.clear(); objectives.clear();
  for (unsigned mode=0;mode<2;++mode) {
   current.mode=Mode(mode); objectives.clear();
   for (const auto &b : Bosses) if (b.zone==d.zone) {
    uint32_t id=1;
    assert(SelectSpawn(b.spawn,id)==(!b.final || !mode));
    if (!b.final || !mode) assert(id==b.npc);
    id=b.npc; assert(!SelectSpawn(1,id));
   }
   for (const auto &b : Bosses) if (b.zone==d.zone && !b.final) objectives.insert(b.objective);
   for (const auto &b : Bosses) if (b.zone==d.zone && b.final) {
    uint32_t id=1; assert(SelectSpawn(b.spawn,id) && id==b.npc);
    deaths.insert(b.spawn); assert(SelectSpawn(b.spawn,id)==!mode); deaths.clear();
    delay=1; assert(SelectSpawn(b.spawn,id)==bool(mode)); delay=0;
   }
  }
 }
 uint32_t id=77;healthy=false;assert(!SelectSpawn(999,id));healthy=true;
 current.expiry=10;assert(!SelectSpawn(999,id));
 current.dungeon=FindDungeon(73);healthy=true;current.expiry=100;
 for (const auto &excluded:ExcludedNPCs) {id=excluded.npc;assert(!SelectSpawn(679,id));}
 managed=false;id=73092;assert(SelectSpawn(679,id) && id==73092);
}
''')

    def test_death_and_recovery_publish_only_after_commit(self):
        service=(ROOT/'server-mods/code/zone/dungeon_service.cpp').read_text()
        death=native.body(service,'bool BeforeDeath(')
        self.assertLess(death.index('INSERT INTO nightcap_dungeon_deaths'),death.index('tx.Commit()'))
        self.assertLess(death.index('INSERT INTO nightcap_dungeon_corpses'),death.index('tx.Commit()'))
        self.assertLess(death.index('INSERT INTO nightcap_dungeon_respawns'),death.index('tx.Commit()'))
        self.assertLess(death.index('tx.Commit()'),death.index('Claim(c,true)'))
        self.assertIn('SaveCorpseState(corpse',death)
        self.assertIn('healthy=false',death)
        load=native.body(service,'bool LoadCheckpoint(')
        self.assertIn('death_times.at(s.spawn2_id)',load)
        self.assertIn('deaths.count(s.spawn2_id)',load)
        attack=native.body((ROOT/'server-mods/code/zone/attack.cpp').read_text(),'bool NPC::Death(')
        self.assertLess(attack.index('NightcapDungeon::BeforeDeath'),attack.index('entity_list.QueueClients(killer_mob, app'))
        self.assertLess(attack.index('CheckTrivialMinMaxLevelDrop'),attack.index('NightcapHunt::Award'))
        self.assertLess(attack.index('NightcapHunt::Award'),attack.index('NightcapDungeon::PrepareLoot'))
        self.assertLess(attack.index('NightcapDungeon::PrepareLoot'),attack.index('corpse = new Corpse'))

    def test_keeper_has_no_chat_based_transfer_acknowledgement(self):
        source=(ROOT/'server-mods/code/zone/dungeon_service.cpp').read_text()
        keeper=native.body(source,'bool Keeper(')
        self.assertNotIn('Connected(c)',keeper)
        distance_guard=keeper[keeper.index('if (DistanceSquared'):keeper.index('\n\ttry {')]
        self.assertIn('return true',distance_guard)
        self.assertNotIn('return false',distance_guard)
        self.assertIn('inside_instance<>0',keeper)
        self.assertIn('is_buried=0',keeper)
        self.assertIn('run.owner!=c->CharacterID()',keeper)
        self.assertIn('confirmations.erase(it)',keeper)
        self.assertIn('StorageReady() || !CatalogReady()',keeper)
        self.assertNotIn('GetUnusedInstanceID(',keeper)
        self.assertIn('nc-dungeon:',keeper)
        connected=native.body(source,'void Connected(')
        self.assertLess(connected.index('ReadRun('),connected.index('inside_instance=1'))
        self.assertIn('admitted.expiry<=Now()',connected)
        perl=(ROOT/'server-mods/quests/global/Instance_Keeper.pl').read_text()
        popup=perl[perl.index('sub EVENT_POPUPRESPONSE'):]
        self.assertLess(popup.index("'confirm reset'"),popup.index('quest::DestroyInstance'))

if __name__=='__main__':unittest.main()

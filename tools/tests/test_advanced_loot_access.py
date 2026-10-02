"""Compile actual corpse-access and master-selection functions with dependency fakes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def function(source, signature):
    start = source.index(signature)
    first = source.index('{', start)
    depth = 1
    end = first + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


FIXTURE = r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <map>
#include <string>
#include <vector>
using uint32=uint32_t;
namespace AccountStatus { constexpr int GMAdmin=100; }
enum class LootRequestType { Forbidden, GMAllowed };
struct Client;
struct Mob { virtual ~Mob()=default; virtual bool IsClient(){return false;} Client* CastToClient(){return reinterpret_cast<Client*>(this);} };
struct Party { Mob *leader=nullptr; Mob* GetLeader(){return leader;} };
struct Trade { bool active=false;void* With(){return active?this:nullptr;} };
struct Client : Mob {
 uint32 id=1;bool connected=true,loaded=true,gm=false,dead=false,ai=false,stun=false,mez=false,fear=false,feign=false,trader=false,buyer=false,craft=false;
 int admin=0,hp=100;float position=0;Party *group=nullptr,*raid=nullptr;Trade *trade=nullptr;
 bool IsClient()override{return true;}bool Connected(){return connected;}bool ClientDataLoaded(){return loaded;}uint32 CharacterID(){return id;}
 bool GetGM(){return gm;}int Admin(){return admin;}bool IsDead(){return dead;}int GetHP(){return hp;}bool IsAIControlled(){return ai;}
 bool IsStunned(){return stun;}bool IsMezzed(){return mez;}bool IsFeared(){return fear;}bool GetFeigned(){return feign;}
 bool IsTrader(){return trader;}bool IsBuyer(){return buyer;}void* GetTradeskillObject(){return craft?this:nullptr;}float GetPosition(){return position;}
 Party* GetGroup(){return group;}Party* GetRaid(){return raid;}
};
struct Entities {std::map<uint32,Client*> clients;Client* GetClientByCharID(uint32 id){const auto i=clients.find(id);return i==clients.end()?nullptr:i->second;}} entity_list;
void *zone=reinterpret_cast<void*>(1);
float DistanceSquaredNoZ(float a,float b){return (a-b)*(a-b);}
struct Corpse {
 bool npc=true,become=false,m_player_corpse_depop=false,m_is_locked=false,m_advanced_loot_busy=false,being=false,own=true,has_rights=true,invalid=false;
 uint32 decay=100;float position=0;LootRequestType m_loot_request_type=LootRequestType::Forbidden;
 bool IsNPCCorpse(){return npc;}bool IsBecomeNPCCorpse(){return become;}uint32 GetDecayTime(){return decay;}
 std::string GetEntityVariable(const char*){return invalid?"invalid":"";}bool IsBeingLooted(){return being;}bool IsBeingLootedBy(Client*){return being&&own;}
 std::vector<uint32> allowed;std::vector<uint32> AdvancedLootRights(){return allowed;}
 bool CanPlayerLoot(uint32){return has_rights;}float GetPosition(){return position;}
 bool ClassicLootOverride(Client*);bool AdvancedLootAccessible(Client*,bool=false,bool=false);
};
// ACTUAL_FUNCTIONS
int main(){
 Client a,b,new_leader;a.id=1;b.id=2;new_leader.id=3;entity_list.clients={{1,&a},{2,&b},{3,&new_leader}};
 Party party{&a};a.group=&party;b.group=&party;new_leader.group=&party;
 assert(Master({1,2})==1);a.connected=false;assert(Master({1,2})==2);
 party.leader=&new_leader;assert(Master({1,2,3})==3);assert(Master({1,2})==2);
 b.loaded=false;assert(Master({1,2})==0);a.connected=true;b.loaded=true;
 Corpse c;assert(c.AdvancedLootAccessible(&a));a.position=25;assert(c.AdvancedLootAccessible(&a));a.position=25.01f;assert(!c.AdvancedLootAccessible(&a));a.position=0;
 // Explicit earned corpse rights allow advanced collection anywhere in this
 // zone, while public looting and native corpse clicks keep their old range.
 a.position=1000;c.allowed={a.id};assert(c.AdvancedLootAccessible(&a));
 assert(!c.AdvancedLootAccessible(&a,false,true));
 c.allowed={b.id};assert(!c.AdvancedLootAccessible(&a));
 c.allowed.clear();assert(!c.AdvancedLootAccessible(&a));a.position=0;
 c.m_is_locked=true;assert(!c.AdvancedLootAccessible(&a,false,true));a.admin=100;
 assert(c.AdvancedLootAccessible(&a,false,true)&&!c.AdvancedLootAccessible(&a));
 c.has_rights=false;c.being=true;c.m_loot_request_type=LootRequestType::GMAllowed;
 assert(!c.AdvancedLootAccessible(&a,false,true));a.gm=true;
 assert(c.ClassicLootOverride(&a)&&c.AdvancedLootAccessible(&a,false,true)&&!c.AdvancedLootAccessible(&a));
 c.own=false;assert(!c.ClassicLootOverride(&a)&&!c.AdvancedLootAccessible(&a,false,true));c.own=true;
 c.invalid=true;assert(!c.AdvancedLootAccessible(&a,false,true));c.invalid=false;
 a.admin=99;assert(!c.ClassicLootOverride(&a));a.admin=100;c.m_loot_request_type=LootRequestType::Forbidden;
 assert(!c.AdvancedLootAccessible(&a,false,true));c.m_loot_request_type=LootRequestType::GMAllowed;
 c.m_advanced_loot_busy=true;assert(!c.AdvancedLootAccessible(&a,false,true)&&c.AdvancedLootAccessible(&a,true,true));c.m_advanced_loot_busy=false;
 for(unsigned i=0;i<13;++i){
  Client x;Corpse normal;Trade trade;x.trade=&trade;
  switch(i){case 0:x.connected=false;break;case 1:x.loaded=false;break;case 2:x.dead=true;break;case 3:x.hp=0;break;
   case 4:x.ai=true;break;case 5:x.stun=true;break;case 6:x.mez=true;break;case 7:x.fear=true;break;case 8:x.feign=true;break;
   case 9:x.trader=true;break;case 10:x.buyer=true;break;case 11:x.craft=true;break;case 12:trade.active=true;break;}
  assert(!normal.AdvancedLootAccessible(&x));
 }
 std::cout<<"PASS: actual corpse access, classic GM authority, quarantined/locked/busy/range/state restrictions and connected master selection\n";
}
'''


def run(root, output):
    corpse = root / 'server-mods/code/zone/corpse_advanced_loot.cpp'
    queue = root / 'server-mods/code/zone/advanced_loot.cpp'
    selected = '\n'.join([function(corpse.read_text(), 'bool Corpse::ClassicLootOverride('),
                          function(corpse.read_text(), 'bool Corpse::AdvancedLootAccessible('),
                          function(queue.read_text(), 'uint32 Master(')])
    with tempfile.TemporaryDirectory(prefix='nightcap-advloot-access-') as temporary:
        folder = Path(temporary)
        (folder / 'test.cpp').write_text(FIXTURE.replace('// ACTUAL_FUNCTIONS', selected))
        (folder / 'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
                                        'cl /nologo /EHsc /W4 /WX /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
        result = subprocess.run(['cmd', '/d', '/c', str(folder / 'build.cmd')], cwd=folder)
        if result.returncode:
            raise RuntimeError((folder / 'build.log').read_text())
        result = subprocess.run([str(folder / 'test.exe')], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        output.write_text(json.dumps({'status': 'passed', 'scope': 'production functions with dependency fakes; no native zone execution',
                                     'sources': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (corpse, queue)},
                                     'result': result.stdout.strip()}, indent=2) + '\n')
        print(result.stdout.strip())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.output.resolve())

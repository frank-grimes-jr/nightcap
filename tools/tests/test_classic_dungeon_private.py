"""Run the native private-spawn constructor for fresh and recovered Sky runs."""
import json
from pathlib import Path
import unittest
import test_free_trade as native

ROOT=Path(__file__).resolve().parents[2]

class PrivateSky(unittest.TestCase):
    def test_actual_native_reconstruction_and_fail_closed_population(self):
        rows=json.loads((ROOT/'docs/dungeons/classic-expansion-20261022/install-rows.json').read_text())['nightcap_dungeon_spawns']
        values=',\n'.join('{'+','.join(json.dumps(str(r[k])) for k in
            ('spawn_id','group_id','npc_id','x','y','z','heading','respawn','grid_id'))+'}' for r in rows)
        function=native.body((ROOT/'server-mods/code/zone/dungeon_service.cpp').read_text(),'void PrivateSpawns(')
        code=r'''
#include "common/dungeon_catalog.h"
#include <algorithm>
#include <array>
#include <cassert>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
using namespace NightcapDungeon;
namespace Spawn2Repository {
 struct Spawn2 {uint32_t id=0,spawngroupID=0,respawntime=0,pathgrid=0; int version=0,_condition=0,cond_value=0; float x=0,y=0,z=0,heading=0;std::string zone;};
 Spawn2 NewEntity(){return {};}
}
namespace Strings {uint32_t ToUnsignedInt(const char *s){return std::stoul(s);}}
namespace fmt {std::string format(const char *,uint32_t id){assert(id==71);return "sky";}}
struct Result {
 std::vector<std::array<std::string,9>> rows;
 struct Iterator {
  Result *r;size_t i;
  const char *operator[](size_t n){return r->rows.at(i).at(n).c_str();}
  void operator++(){++i;}bool operator!=(Iterator b){return i!=b.i;}
 };
 Iterator begin(){return {this,0};}Iterator end(){return {this,rows.size()};}
 size_t RowCount(){return rows.size();}
} result;
Result Query(const std::string&){return result;}
struct Groups {std::set<uint32_t> ids;bool GetSpawnGroup(uint32_t id){return ids.count(id);}};
struct Zone {Groups spawn_group_list;} z;
Zone *zone=&z;
struct {void LoadSpawnGroupsByID(uint32_t id,Groups *g){g->ids.insert(id);}} content_db;
struct {const Dungeon *dungeon=FindDungeon(71);} current;
bool managed=true,healthy=true;
bool Managed(){return managed;}
bool RequiredSpawn(uint32_t id){for(const auto &b:Bosses)if(b.zone==71 && b.spawn==id)return true;return false;}
'''+function+'\nint main(){result.rows={'+values+r'''};
 // Checkpoint may have no dynamic Sirran (normal native managed reload).
 // Private canonical points must reconstruct every service on either boot.
 for(unsigned boot=0;boot<2;++boot){
  std::vector<Spawn2Repository::Spawn2> spawns;
  auto public_point=Spawn2Repository::NewEntity();public_point.id=2666;
  public_point.spawngroupID=123;spawns.push_back(public_point);
  PrivateSpawns(spawns);assert(healthy && spawns.size()==13 && spawns[0].id==2666);
  unsigned services=0;std::set<uint32_t> ids;
  for(const auto &s:spawns){assert(ids.insert(s.id).second);if(s.id>=9200005 && s.id<=9200011)++services;}
  assert(services==7);
 }
 managed=false;std::vector<Spawn2Repository::Spawn2> public_spawns;
 PrivateSpawns(public_spawns);assert(public_spawns.empty());
 managed=true;result.rows.pop_back();PrivateSpawns(public_spawns);
 assert(!healthy && public_spawns.empty());
}
'''
        native.FreeTradeTests.compile_run(self,code)

if __name__=='__main__':unittest.main()

"""Hate changes terrain without changing earned identities or encounter strength."""
import unittest
from pathlib import Path
import test_free_trade as native

ROOT=Path(__file__).resolve().parents[2]


class HateLayout(unittest.TestCase):
    def test_native_allocation_and_experience_preserve_scope_and_fail_closed(self):
        source=(ROOT/'server-mods/code/zone/dungeon_service.cpp').read_text()
        native.FreeTradeTests.compile_run(self,r'''
#include "common/dungeon_policy.h"
#include <stdexcept>
#include <string>
#include <vector>
#include <cassert>
using namespace NightcapDungeon;
namespace fmt {
template<class...T>std::string format(std::string pattern,T...values){
 std::vector<std::string> args;((args.push_back(std::to_string(values))),...);
 for(const auto&s:args){auto i=pattern.find("{}");pattern.replace(i,2,s);}return pattern;
}}
uint64_t Now(){return 100;}
std::string sql;unsigned count=0;bool fail=false;
struct Result{unsigned RowCount(){return count;}};
Result Query(const std::string &value){sql=value;if(fail)throw std::runtime_error("DB unavailable");return {};}
struct Zone{unsigned id=186;unsigned GetZoneID(){return id;}} z;
Zone*zone=&z;bool managed=true,present=true;
bool Managed(){return managed;}
struct Entry{float zone_exp_multiplier=1.0f;} classic_row;
Entry *GetZoneVersionWithFallback(unsigned id,unsigned version){assert(id==76&&version==0);return present?&classic_row:nullptr;}
'''+native.body(source,'bool HateAllocation(')+'\n'+native.body(source,'float ExperienceModifier(')+r'''
int main(){
 assert(!HateAllocation(42,76));
 assert(sql.find("p.charid=42 AND i.zone=76 AND i.version=0")!=std::string::npos);
 assert(sql.find("i.never_expires=1 OR i.start_time+i.duration>100")!=std::string::npos);
 count=1;assert(HateAllocation(42,186,true));assert(sql.find(" FOR UPDATE")!=std::string::npos);
 count=2;bool caught=false;try{HateAllocation(42,186);}catch(const std::runtime_error&){caught=true;}assert(caught);
 count=0;fail=true;caught=false;try{HateAllocation(42,76);}catch(const std::runtime_error&){caught=true;}assert(caught);
 fail=false;caught=false;try{HateAllocation(42,99);}catch(const std::runtime_error&){caught=true;}assert(caught);
 assert(ExperienceModifier(1.13f)==1.0f);
 managed=false;assert(ExperienceModifier(1.13f)==1.13f);
 managed=true;z.id=76;assert(ExperienceModifier(0.7f)==0.7f);
 z.id=186;present=false;assert(ExperienceModifier(1.13f)==0.0f);
 assert(ContentZone(186,true)==76);assert(ContentZone(186,false)==186);assert(ContentZone(71,true)==71);
}
''')

    def test_new_destination_retains_legacy_runs_and_reward_identity(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "common/dungeon_policy.h"
#include <cassert>
#undef assert
inline bool Check(bool value) { return value; }
#define assert(value) do { if (!Check(value)) return __LINE__; } while (0)
using namespace NightcapDungeon;
int main() {
 const auto next=FindDungeon(186),old=FindDungeon(76);
 assert(next && old && next!=old);
 assert(next->index==19 && old->index==19);
 assert(next->keeper==998812 && old->keeper==998812);
 assert(next->count==4 && old->count==4);
 assert(KeeperDungeon(22,0,998812)==next);
 assert(KeeperDungeon(76,12,998812)==old);
 assert(KeeperDungeon(186,12,998812)==next);
 assert(!KeeperDungeon(22,12,998812));
 assert(DungeonCount==23 && ItemEnd==960426);
 assert(HateDestination(false,false,false)==186);
 assert(HateDestination(true,false,false)==76);
 assert(HateDestination(false,true,false)==186);
 assert(HateDestination(false,false,true)==76);
 assert(HateDestination(false,true,true)==186);
 assert(HateDestination(true,true,false)==0);
 for(unsigned design=0;design<3;++design)
  for(auto q:{Quality::Polished,Quality::Ascended})
   assert(FinalBossItem(next->index,next->band,design,q)==FinalBossItem(old->index,old->band,design,q));
 unsigned old_count=0,new_count=0;
 for(const auto &b:Bosses) {
  if(b.zone==76)++old_count;
  if(b.zone==186) {
   ++new_count;bool matching=false;
   for(const auto &original:Bosses)
    if(original.zone==76 && original.spawn==b.spawn && original.npc==b.npc && original.objective==b.objective && original.final==b.final)matching=true;
   assert(matching);
  }
 }
 assert(old_count==4 && new_count==4);
}
''')


if __name__ == '__main__':
    unittest.main()

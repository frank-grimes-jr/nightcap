"""Compile phase selection and personal credit rules, without a shadow ledger."""
import unittest
import test_free_trade as native


class LanternScenePolicyTests(unittest.TestCase):
    def test_native_phase_and_credit_policy(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "common/last_lantern_scene_policy.h"
#include <cassert>
#include <set>
using namespace NightcapLantern;
int main() {
 Program p{{Segment{Kind::Records,0,3,1,0,false,false},
            Segment{Kind::Defense,3,1,3,3,true,false},
            Segment{Kind::Battle,4,1,1,0,false,false}},3};
 std::set<unsigned> active{0,1,2};
 auto pick=[&](){return ActiveSegment(p,[&](unsigned i){return active.count(i)!=0;});};
 assert(pick()==0);active={3};assert(pick()==1);active={4};assert(pick()==2);
 active.clear();assert(pick()==-1);
 assert(WaveCredit(p.segments[1],0)==0);
 for(unsigned wave=1;wave<=3;++wave)assert(WaveCredit(p.segments[1],wave)==1);
 assert(WaveCredit(p.segments[1],4)==0);
 Segment rescue{Kind::Defense,2,1,1,3,false,true};
 assert(WaveCredit(rescue,1)==0 && WaveCredit(rescue,2)==0 && WaveCredit(rescue,3)==1);
 Credit c{true,true,true,true,true,true,true,200.0*200.0};
 assert(CanCredit(c));c.distance_squared+=.01;assert(!CanCredit(c));c.distance_squared=0;
 for(unsigned flag=0;flag<7;++flag) {
  Credit invalid=c;
  switch(flag){case 0:invalid.connected=false;break;case 1:invalid.loaded=false;break;
  case 2:invalid.alive=false;break;case 3:invalid.member=false;break;
  case 4:invalid.eligible=false;break;case 5:invalid.task_active=false;break;
  case 6:invalid.activity_active=false;break;}
  assert(!CanCredit(invalid));
 }
}
''')


if __name__ == '__main__':
    unittest.main()

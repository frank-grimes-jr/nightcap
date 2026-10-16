"""Execute native policy boundaries, stable rolls and collision-free identities."""
from pathlib import Path
import unittest
import test_free_trade as native

class DungeonPolicy(unittest.TestCase):
    def test_native_policy(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "common/dungeon_policy.h"
#include <cassert>
#include <set>
int main() {
    using namespace NightcapDungeon;
    assert(Scale(1000,135)==1350 && Scale(100,115)==115);
    assert(Scale(-5,115)==-5 && Scale(0,135)==0);
    assert(Scale(INT64_MAX,135)==INT64_MAX);
    assert(Scale(1,0)==0 && Scale(1000000000000000000LL,135)==1350000000000000000LL);
    assert(SharedItem(0,0,Quality(3))==0 && BossItem(0,0,Quality(3))==0);
    assert(Roll(1,1,1,0)==0);
    for (unsigned r=0;r<10000;++r) {
        assert(RollQuality(Mode::Grind,r)==Quality::Normal);
        assert(RollQuality(Mode::Raid,r)==(r<9000?Quality::Polished:Quality::Ascended));
        assert(BossCount(r)==(r<8000?1u:r<9800?2u:3u));
    }
    std::set<unsigned> ids;
    for(unsigned b=0;b<4;++b) for(unsigned d=0;d<24;++d) for(unsigned q=0;q<3;++q)
        assert(ids.insert(SharedItem(b,d,Quality(q))).second);
    for(unsigned z=0;z<7;++z) for(unsigned d=0;d<3;++d) for(unsigned q=1;q<3;++q)
        assert(ids.insert(BossItem(z,d,Quality(q))).second);
    assert(ids.size()==330 && *ids.rbegin()<1048576);
    for(auto id:ids) assert(IsReward(id));
    assert(!IsReward(ItemBegin-1) && !IsReward(ItemEnd));
    assert(SharedItem(4,0,Quality::Normal)==0);
    assert(BossItem(0,0,Quality::Normal)==0);
    for(uint64_t seed=0;seed<10000;++seed) {
        const auto p=BossOrder(seed);
        assert(std::set<unsigned>(p.begin(),p.end()).size()==3);
        assert(Roll(seed,27,1,24)==Roll(seed,27,1,24));
    }
}
''')

if __name__ == '__main__': unittest.main()

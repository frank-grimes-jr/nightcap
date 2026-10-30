"""Native item training arithmetic and tier-boundary regression coverage."""
import unittest
import test_free_trade as native


class ItemXPPolicyTests(unittest.TestCase):
    def test_progression(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "common/item_xp_policy.h"
#include <cstdio>
#include <cstdlib>
#include <limits>
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"%s\n",#x); std::exit(1); } } while(false)
int main() {
    using namespace NightcapItemXP;
    CHECK(Cost(0)==80000000 && Cost(1)==160000000 && Cost(2)==240000000);
    CHECK(Cost(3)==0 && Cost(255)==0);
    for (unsigned level=1;level<=255;++level) {
        const auto native_level=static_cast<uint8_t>(level);
        const uint64_t denominator=1365ULL*level*level;
        CHECK(Award(denominator,native_level)==8000000);
        CHECK(Award(0,native_level)==0);
        CHECK(Award(UINT64_MAX,native_level)==MaxProgress);
        CHECK(Award(denominator/8,native_level)<=1000000);
    }
    CHECK(Award(100,0)==0);
    CHECK(Award(1,50)>0); // small kills retain micro-unit progress
    auto p=Advance(0,Cost(0)-1,1);
    CHECK(p.valid && p.tier==1 && p.progress==0);
    p=Advance(0,0,MaxProgress);
    CHECK(p.valid && p.tier==3 && p.progress==0);
    p=Advance(1,2,Cost(1)+Cost(2)-3);
    CHECK(p.valid && p.tier==2 && p.progress==Cost(2)-1);
    p=Advance(2,Cost(2)-1,UINT64_MAX);
    CHECK(p.valid && p.tier==3 && p.progress==0);
    CHECK(!Advance(0,Cost(0),1).valid);
    CHECK(!Advance(3,1,1).valid && !Advance(4,0,1).valid);
    CHECK(Advance(3,0,100).valid && Advance(3,0,100).progress==0);
    uint8_t tier=0; uint64_t progress=0;
    for(unsigned kill=0;kill<480;++kill) {
        p=Advance(tier,progress,Unit); CHECK(p.valid);
        tier=p.tier; progress=p.progress;
        if(kill==78) CHECK(tier==0);
        if(kill==79) CHECK(tier==1 && progress==0);
        if(kill==239) CHECK(tier==2 && progress==0);
    }
    CHECK(tier==3 && progress==0);
}
''')


if __name__ == '__main__':
    unittest.main()

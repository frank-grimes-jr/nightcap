"""Native prison-break rules: ordered dialogue, escort gates and legacy isolation."""
import unittest
from pathlib import Path
import test_free_trade as native

class HighkeepRescue(unittest.TestCase):
    def test_native_coordinator(self):
        native.FreeTradeTests.compile_run(self, (Path(__file__).parent/'fixtures/highkeep_runtime.cpp').read_text())

    def test_policy(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "common/highkeep_policy.h"
#include <cassert>
using namespace NightcapHighkeep;
int main() {
 assert(Eligible(6,1,true)); assert(!Eligible(6,0,true));
 assert(!Eligible(6,1,false)); assert(!Eligible(36,1,true));
 Dialogue d;
 assert(!Converse(d,"see osargen",100)); assert(d.step==0);
 assert(!Converse(d,"hail, Gate Sergeant",100)); assert(d.step==1);
 assert(!Converse(d,"see osargen",101)); assert(d.step==1);
 assert(!Converse(d,"relief detail",101)); assert(d.step==2);
 assert(Converse(d,"see osargen",102)); assert(d.step==0);
 Converse(d,"hail",100); Converse(d,"relief detail",101);
 assert(!Converse(d,"see osargen",200)); assert(d.step==0);
 assert(!CanExtract(2,true,true,true)); assert(!CanExtract(3,false,true,true));
 assert(!CanExtract(3,true,false,true)); assert(!CanExtract(3,true,true,false));
 assert(CanExtract(3,true,true,true));
 assert(Guard(6005)); assert(Guard(6181)); assert(Guard(6034));
 assert(!Guard(6051)); assert(!Guard(999229)); assert(!Guard(6049));
 assert(!Guard(6037)); assert(!Guard(999240));
}
''')

if __name__ == '__main__': unittest.main()

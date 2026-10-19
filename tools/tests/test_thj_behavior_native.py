import unittest
from test_pet_equipment import compile_run,ROOT

class Native(unittest.TestCase):
    def test_resource_rounding_focus_endpoints_and_exceptions(self):
        path=(ROOT/'server-mods/code/common/nightcap_thj_behaviors.h').as_posix()
        compile_run('#include "'+path+'"\n'+r'''
#include <cassert>
int main(){using namespace NightcapTHJ;
assert(PercentMana(10001,50)==5000);assert(PercentMana(1,10)==1);
assert(PercentMana(0,40)==0);assert(PercentMana(-100,40)==0);
assert(PercentMana(INT64_MAX,40)==858993458);
assert(ResourcePercent(8450)==10&&ResourcePercent(8451)==20&&ResourcePercent(8452)==30&&ResourcePercent(11068)==40);
assert(!ManaBurn(2775)&&ManaBurn(8450));assert(!ResourcePercent(12));
assert(StrongestEndpoint(1,20)==20);assert(StrongestEndpoint(-5,-20)==-20);assert(StrongestEndpoint(-20,0)==-20);
assert(ScaleFocus(20,true,false,false,false)==200);
assert(ScaleFocus(20,true,true,false,false)==200);
assert(ScaleFocus(20,true,true,true,false)==20);
assert(ScaleFocus(100,true,false,false,true)==100);
assert(ScaleFocus(150,true,false,false,true)==150);
assert(ScaleFocus(20,false,false,false,false)==20);
assert(BroadenDamageTarget(5,8,true));assert(BroadenDamageTarget(-4,8,true));
assert(!BroadenDamageTarget(6,8,true));assert(!BroadenDamageTarget(5,5,true));assert(!BroadenDamageTarget(5,8,false));
assert(BoundDuration(23528,20)==2 && BoundDuration(23528,1)==1 && BoundDuration(23528,-1000)==1);
assert(BoundDuration(8054,999)==600 && BoundDuration(8054,0)==0 && BoundDuration(99,20)==20);
assert(RetiredAA(758));
assert(RetiredAA(25)&&RetiredAA(252)&&RetiredAA(8300)&&RetiredAA(3521)&&!RetiredAA(500));
}
''')

if __name__=='__main__':unittest.main()

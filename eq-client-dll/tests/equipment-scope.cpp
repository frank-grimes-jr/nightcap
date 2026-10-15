#include "../src/equipment_scope.h"
#include <cassert>
#include <thread>
#include <cstdio>
int main() {
    using namespace nightcap;
    int first=0,second=0;
    assert(ActiveEquipItem()==nullptr);
    assert(EquipClassMask(1,&first,true,false,3,69)==1);
    const void* outer=SetActiveEquipItem(&first);
    assert(outer==nullptr);
    for(unsigned primary=1;primary<=16;++primary) {
        const auto base=1u<<(primary-1);
        for(unsigned extra=1;extra<=16;++extra) {
            const auto extra_bit=1u<<(extra-1),held=base|extra_bit;
            for(unsigned c=0;c<16;++c) {
                const auto mask=1u<<c,expected=(mask&held)?mask|base:mask;
                assert(EquipClassMask(mask,&first,true,false,primary,held)==expected);
                assert(EquipClassMask(mask,&second,true,false,primary,held)==mask);
                assert(EquipClassMask(mask,&first,false,false,primary,held)==mask);
                assert(EquipClassMask(mask,&first,true,true,primary,held)==mask);
            }
        }
    }
    assert(EquipClassMask(0,&first,true,false,3,69)==0);
    assert(EquipClassMask(0x10001,&first,true,false,3,69)==0x10005);
    assert(EquipClassMask(1,nullptr,true,false,3,69)==1);
    assert(EquipClassMask(1,&first,true,false,0,69)==1);
    assert(EquipClassMask(1,&first,true,false,17,69)==1);
    assert(EquipClassMask(1,&first,true,false,3,0)==1);
    assert(EquipClassMask(1,&first,true,false,3,1)==1);
    const void* nested=SetActiveEquipItem(&second);
    assert(nested==&first);
    assert(EquipClassMask(1,&first,true,false,3,69)==1);
    assert(EquipClassMask(1,&second,true,false,3,69)==5);
    SetActiveEquipItem(nested);
    std::thread other([&] {
        assert(ActiveEquipItem()==nullptr);
        assert(EquipClassMask(1,&first,true,false,3,69)==1);
        SetActiveEquipItem(&second);
        assert(EquipClassMask(1,&second,true,false,3,69)==5);
    });
    other.join();
    assert(ActiveEquipItem()==&first);
    SetActiveEquipItem(outer);
    assert(ActiveEquipItem()==nullptr);
    std::puts("PASS: 4096 primary/held/item combinations, item/thread/flag scope, zero/high masks and nesting");
}

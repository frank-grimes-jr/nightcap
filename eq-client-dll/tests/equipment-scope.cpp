#include "../src/equipment_scope.h"
#include <cassert>
#include <thread>
#include <cstdio>
int main() {
    using namespace nightcap;
    int first = 0, second = 0;
    assert(ActiveEquipItem() == nullptr);
    assert(EquipClassMask(4, &first, true, false) == 4);
    const void* outer = SetActiveEquipItem(&first);
    assert(outer == nullptr);
    for (unsigned c = 0; c < 16; ++c) {
        const unsigned mask = 1u << c;
        assert(EquipClassMask(mask, &first, true, false) == 0xFFFFu);
        assert(EquipClassMask(mask, &second, true, false) == mask);
        assert(EquipClassMask(mask, &first, false, false) == mask);
        assert(EquipClassMask(mask, &first, true, true) == mask);
    }
    assert(EquipClassMask(0, &first, true, false) == 0);
    assert(EquipClassMask(0x10004, &first, true, false) == 0x1FFFF);
    assert(EquipClassMask(4, nullptr, true, false) == 4);
    const void* nested = SetActiveEquipItem(&second);
    assert(nested == &first);
    assert(EquipClassMask(4, &first, true, false) == 4);
    assert(EquipClassMask(4, &second, true, false) == 0xFFFF);
    SetActiveEquipItem(nested);
    std::thread other([&] {
        assert(ActiveEquipItem() == nullptr);
        assert(EquipClassMask(4, &first, true, false) == 4);
        SetActiveEquipItem(&second);
        assert(EquipClassMask(4, &second, true, false) == 0xFFFF);
    });
    other.join();
    assert(ActiveEquipItem() == &first);
    SetActiveEquipItem(outer);
    assert(ActiveEquipItem() == nullptr);
    assert(EquipClassMask(4, &first, true, false) == 4);
    std::puts("PASS: equipment item/thread/flag scope, 16 class bits, zero masks and nesting");
}

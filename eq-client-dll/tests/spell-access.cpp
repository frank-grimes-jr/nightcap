#include <cassert>
#include "../src/ui_state.h"
#include "../src/spell_access.h"

int main() {
    nightcap::UIState state;
    assert(state.Consume("[NCUI1]S|1|19|22|0|7|2|13|11|Monktest"));
    const auto held = state.ClassMask();
    assert(state.PrimaryClass()==2 && held==((1u<<1)|(1u<<12)|(1u<<10)));
    assert(nightcap::HeldSpellLevel(4,held)==17); // Summon Waterstone MAG17
    assert(nightcap::HeldSpellLevel(4,1u<<1)==255);
    assert(nightcap::HeldSpellLevel(44999,held)==255);
    assert(nightcap::MerchantClassMask(0,2,held,true,4)==0);
    assert(nightcap::MerchantClassMask(65535,2,held,true,4)==((1u<<12)|(1u<<1)));
    assert(nightcap::MerchantClassMask(65535,2,1u<<1,true,4)==(1u<<12));
    assert(nightcap::MerchantClassMask(65535,2,held,true,44999)==0);
    assert(nightcap::MerchantClassMask(1u<<12,2,held,false,0)==((1u<<12)|(1u<<1)));
    assert(nightcap::MerchantClassMask(1u<<14,2,held,false,0)==(1u<<14));
    assert(state.Consume("[NCUI1]S|2|19|22|0|7|2|0|11|Monktest"));
    assert(nightcap::HeldSpellLevel(4,state.ClassMask())==255);
    state.Clear(); assert(state.ClassMask()==0 && state.PrimaryClass()==0);
    for(const auto &spell : NightcapSpellClasses::Catalog) {
        for(unsigned c=1;c<=16;++c)
            assert(nightcap::HeldSpellLevel(spell.id,1u<<(c-1))==spell.levels[c-1]);
    }
}

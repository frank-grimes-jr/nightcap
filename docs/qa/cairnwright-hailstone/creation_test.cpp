// Build against the patched Hailstone source with C++20 and src on the include path.
#include "net/nightcap_creation.h"
#include <cassert>

int main() {
    using namespace hailstone::net;
    assert(nightcap_qa_world("127.0.0.1", "Local Development Server"));
    assert(!nightcap_qa_world("127.0.0.1", "Production"));
    assert(!nightcap_qa_world("example.org", "Local Development Server"));
    CharCreateData data;
    data.combos.push_back({0,8,3,202,14,67});
    add_nightcap_creation_option(data);
    assert(data.combos.size() == 1);
    data.allocations.push_back({14,{100,90,70,95,60,88,55},{0,0,0,20,0,0,0}});
    data.combos.front().race = 1;
    add_nightcap_creation_option(data);
    assert(data.combos.size() == 1);
    data.combos.front().race = 8;
    add_nightcap_creation_option(data);
    add_nightcap_creation_option(data);
    assert(data.combos.size() == 2 && data.combos[0].class_ == 3);
    const auto c = data.combos.back();
    assert(c.class_ == 17 && c.race == 8 && c.deity == 202 && c.zone == 67 &&
           c.allocation_index == 14 && c.expansion_required == 0);
}

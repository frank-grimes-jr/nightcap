#include "../src/tradeskill_repeat.h"
#include <cassert>
#include <initializer_list>

using nightcap::TradeskillRepeat;
using Action = TradeskillRepeat::Action;
int main() {
    struct Reply { const char* text; uint32_t spawn,recipe; bool attempted; };
    const Reply replies[]={{"[NCTS1]|7|20|1",7,20,true},
        {"[NCTS1]|4294967295|4294967295|0",UINT32_MAX,UINT32_MAX,false},
        {"[NCTS1]|0000000007|20|1",7,20,true}};
    for (const auto& reply : replies) {
        uint32_t spawn=0,recipe=0;bool attempted=false;
        assert(nightcap::ParseTradeskillReply(reply.text,spawn,recipe,attempted));
        assert(spawn==reply.spawn && recipe==reply.recipe && attempted==reply.attempted);
    }
    for (const char* text : {static_cast<const char*>(nullptr), "", "[NCTS1]", "[NCTS1]|", "[NCTS1]|7|20", "[NCTS1]|7||1",
             "[NCTS1]|0|20|1", "[NCTS1]|7|0|1", "[NCTS1]|7|20|2", "[NCTS1]|-7|20|1", "[NCTS1]|+7|20|1",
             "[NCTS1]| 7|20|1", "[NCTS1]|7|20|1 ", "[NCTS1]|7|20|1\n", "[NCTS1]|7|20|1|extra",
             "[NCTS1]|4294967303|20|1", "[NCTS1]|7|4294967296|1", "[NCTS1]|00000000007|20|1",
             "[NCTS1]|7|20|-0", "[NCTS1]|7|20|+1", "[NCTS1]|7|20|4294967297", "[NCTS1]|7|2e1|1"}) {
        uint32_t spawn=11,recipe=22;bool attempted=true;
        assert(!nightcap::ParseTradeskillReply(text,spawn,recipe,attempted));
        assert(spawn==11 && recipe==22 && attempted); // reject without partial output changes
    }
    TradeskillRepeat q;
    assert(!q.Start(0, 0, 20));
    assert(q.Start(0, 10, 20));
    assert(!q.Start(1, 10, 20));
    assert(q.Pulse(2199, true, true) == Action::None); // elapsed time is not acknowledgement
    assert(!q.Ack(10, 11, 20, true));
    assert(!q.Ack(10, 10, 21, true));
    assert(q.Ack(10, 10, 20, true));
    assert(!q.Ack(11, 10, 20, true)); // duplicate result
    assert(q.Pulse(2199, true, true) == Action::None);
    assert(q.Pulse(2200, false, true) == Action::Inventory);
    assert(q.Pulse(2400, true, true) == Action::None);
    assert(q.Pulse(2500, true, true) == Action::Craft);
    q.Stop();
    assert(!q.Start(2501, 10, 20)); // Stop does not forget the outstanding attempt
    assert(q.Ack(2502, 10, 20, true));
    assert(q.Pulse(5000, true, true) == Action::None);
    assert(q.Start(5001, 10, 20));
    assert(q.Ack(5002, 10, 20, false)); // missing mats/invalid state ends the run
    assert(!q.Active());
    assert(q.Start(6000, 10, 20));
    assert(q.Pulse(21000, true, true) == Action::Stopped);
    assert(!q.Start(21001, 10, 20)); // timeout never retries uncertain consumption
    assert(q.Uncertain());
    assert(!q.Ack(21002,10,20,true)); // late reply cannot erase uncertainty
    q.Reset();
    assert(q.Start(0,10,20));
    q.NotDispatched();
    assert(!q.Active() && !q.Pending() && !q.Uncertain());
    assert(q.Start(1,10,20)); // known local rejection did not consume anything
    q.Reset();
    assert(q.Start(0, 10, 20));
    assert(q.Ack(1, 10, 20, true));
    assert(q.Pulse(2200, false, true) == Action::Inventory);
    assert(q.Pulse(2500, false, true) == Action::Inventory);
    assert(q.Pulse(7200, false, true) == Action::Stopped); // full bags / uncleared cursor
    q.Reset();
    assert(q.Start(0, 10, 20));
    assert(q.Pulse(100, true, false) == Action::Stopped); // window/recipe/identity changes
    assert(q.Ack(200, 10, 20, true));
    assert(!q.Active());
    q.Reset();
    for (unsigned i=0; i<100; ++i) {
        auto now=uint64_t(i)*3000;
        if (!i) assert(q.Start(now,10,20));
        assert(q.Ack(now+1,10,20,true));
        assert(q.Pulse(now+2200,true,true)==Action::Inventory);
        assert(q.Pulse(now+3000,true,true)==Action::Craft);
    }
    assert(q.Ack(300001,10,20,false));
    assert(!q.Active() && q.Completed()==100);
}

#include "../src/ui_state.h"
#include <cassert>
#include <cstring>
#include <iostream>

int main() {
    nightcap::UIState state;
    assert(!state.Consume("ordinary chat"));
    assert(!state.Consume("[NCUI1]S|1|22|202|0|7|10|1|14|Zozobra|extra"));
    assert(state.Consume("[NCUI1]S|1|22|202|0|7|10|1|14|Zozobra"));
    assert(state.Matches(7,"Zozobra"));
    assert(!state.Matches(8,"Zozobra"));
    assert(!state.Matches(7,"Other"));
    assert(state.Classes() == "SHM/WAR/ENC");
    assert(state.Consume("[NCUI1]A|1|22|202|0|7|123|1024"));
    assert(state.AAClasses(123) == "SHM");
    assert(state.AAClasses(124) == "Unknown");
    assert(!state.Consume("[NCUI1]A|2|22|202|0|7|123|4"));
    assert(!state.Consume("[NCUI1]A|1|23|202|0|7|123|4"));
    assert(!state.Consume("[NCUI1]A|1|22|203|0|7|123|4"));
    assert(!state.Consume("[NCUI1]A|1|22|202|1|7|123|4"));
    assert(!state.Consume("[NCUI1]A|1|22|202|0|8|123|4"));
    assert(!state.Consume("[NCUI1]A|1|22|202|0|7|123|131072"));
    assert(state.AAClasses(123) == "SHM");
    assert(state.Consume("[NCUI1]A|1|22|202|0|7|124|131070"));
    assert(state.AAClasses(124) == "All");
    assert(state.Consume("[NCUI1]A|1|22|202|0|7|125|16386"));
    assert(state.AAClasses(125) == "WAR/ENC");
    assert(!state.Consume("[NCUI1]S|4294967296|22|202|0|7|10|1|14|Zozobra"));
    assert(!state.Consume("[NCUI1]S|-1|22|202|0|7|10|1|14|Zozobra"));
    assert(!state.Consume("[NCUI1]S|2|22|202|0|7|17|1|14|Zozobra"));
    assert(!state.Consume("[NCUI1]S|2|22|202|0|7|10|10|14|Zozobra"));
    assert(!state.Consume("[NCUI1]S|2|22|202|0|7|10|1|1|Zozobra"));
    assert(state.Consume("[NCUI1]S|2|22|202|0|7|10|0|0|Zozobra"));
    assert(state.Classes() == "SHM/---/---");
    assert(state.AAClasses(123) == "Unknown");
    assert(state.Consume("[NCUI1]S|1|23|202|0|7|9|12|6|Pups"));
    assert(state.Classes() == "ROG/WIZ/DRU");
    assert(!state.Matches(7,"Zozobra"));
    assert(!state.Consume((std::string("[NCUI1]S|")+std::string(1024,'9')).c_str()));
    state.Clear();
    assert(!state.Matches(7,"Pups"));
    std::cout << "UI state controls passed\n";
}

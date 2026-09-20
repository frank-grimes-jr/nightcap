#include "../src/pet_state.h"
#include <cassert>
#include <string>
#include <iostream>

int main() {
    nightcap::PetState state;
    assert(!state.Consume("[NCPA1]E|77"));
    assert(state.Consume("[NCPA1]B|77|22|202|0|7|5a6f7a6f627261"));
    assert(!state.Matches(7, "Zozobra")); // incomplete snapshots never become actionable
    assert(state.Consume("[NCPA1]P|77|10|12|506574"));
    assert(!state.Consume("[NCPA1]P|77|10|13|447570"));
    for (int i = 0; i < 8; ++i) {
        const std::string frame = "[NCPA1]I|77|10|" + std::to_string(i) + "|0|456d707479";
        assert(state.Consume(frame.c_str()));
    }
    assert(!state.Consume("[NCPA1]I|77|10|8|4|426164"));
    assert(state.Consume("[NCPA1]E|77"));
    assert(state.Matches(7, "Zozobra"));
    assert(!state.Matches(8, "Zozobra"));
    assert(state.SelectedClass() == 10);
    assert(state.Nonce() == 77);
    assert(state.SlotText(0) == "Head: Empty");
    assert(state.Command("equip", 0) == "#nightcappet equip 10 0 77");
    assert(state.Command("remove", 0).empty());
    assert(state.Command("evil", 0).empty());
    assert(state.Command("equip", 8).empty());
    assert(!state.Consume("[NCPA1]B|4294967296|22|202|0|7|5a"));
    assert(!state.Consume("[NCPA1]B|78|22|202|0|7|GG"));
    assert(state.Consume("[NCPA1]B|78|22|202|0|7|5a6f7a6f627261"));
    assert(state.Command("equip", 0).empty()); // block actions while refreshing
    assert(state.Consume("[NCPA1]P|78|10|0|53746f726564"));
    assert(!state.Consume("[NCPA1]E|78")); // all eight slots must arrive
    for (int i = 0; i < 8; ++i) {
        const std::string frame = "[NCPA1]I|78|10|" + std::to_string(i) + "|100|41726d6f72";
        assert(state.Consume(frame.c_str()));
    }
    assert(state.Consume("[NCPA1]E|78"));
    assert(state.Command("equip", 0).empty());
    assert(state.Command("remove", 0) == "#nightcappet remove 10 0 78");
    assert(state.Command("inspect", 0) == "#nightcappet inspect 10 0 78");
    assert(!state.Consume("[NCPA1]I|77|10|0|400|426164"));
    assert(state.SlotText(0) == "Head: Armor");
    state.Next(1); assert(state.SelectedClass() == 10);
    assert(state.Consume("[NCPA1]B|79|22|202|0|7|5a6f7a6f627261"));
    assert(state.Consume("[NCPA1]E|79"));
    assert(state.SelectedClass() == 0);
    assert(state.Command("remove", 0).empty());
    state.Clear();
    assert(!state.Matches(7, "Zozobra"));
    std::cout << "Pet state controls passed\n";
}

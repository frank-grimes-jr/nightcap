#include <cassert>
#include <iostream>
#include "../src/pet_management.h"

static void AdversarialSnapshots() {
    nightcap::PetManagement state;
    assert(state.OrderCommand(2).empty());
    assert(state.Consume("[NCPM1]|77|10|19|22|0|7|54657374|102|1|11|102|80|426f6e6573"));
    const std::string before = state.RowText(0);
    const std::string order = state.OrderCommand(2);
    assert(order == "#nightcappet order 2 77");
    assert(state.OrderCommand(34).empty());
    assert(state.OrderCommand(UINT32_MAX).empty());
    for (const char* malformed : {
        "[NCPM1]|0|11|19|22|0|7|54657374|0|0",
        "[NCPM1]|77|0|19|22|0|7|54657374|0|0",
        "[NCPM1]|77|11|0|22|0|7|54657374|0|0",
        "[NCPM1]|77|11|19|0|0|7|54657374|0|0",
        "[NCPM1]|77|11|19|22|0|65536|54657374|0|0",
        "[NCPM1]|4294967296|11|19|22|0|7|54657374|0|0",
        "[NCPM1]|-1|11|19|22|0|7|54657374|0|0",
        "[NCPM1]|77|11|19|22|0|7|54657374|0|4",
        "[NCPM1]|77|11|19|22|0|7|54657374|0|1|11|0|80|426f6e6573",
        "[NCPM1]|77|11|19|22|0|7|54657374|0|1|11|65536|80|426f6e6573",
        "[NCPM1]|77|11|19|22|0|7|54657374|0|1|0|102|80|426f6e6573",
        "[NCPM1]|77|11|19|22|0|7|54657374|0|2|11|102|80|426f6e6573|13|102|95|5761746572",
        "[NCPM1]|77|11|19|22|0|7|54657374|0|1|11|102|80|1b",
        "[NCPM1]|77|11|19|22|0|7|54657374|0|1|11|102|80|7f",
        "[NCPM1]|77|11|19|22|0|7|54657374|0|1|11|102|80|zz",
        "[NCPM1]|77|11|19|22|0|7|54657374|0|1|11|102|80|1",
        "[NCPM1]|77|11|19|22|0|7|54657374|0|0|extra"
    }) {
        assert(!state.Consume(malformed));
        assert(state.RowText(0) == before && state.OrderCommand(2) == order);
    }
    assert(!state.Consume(nullptr));
    assert(!state.Consume((std::string("[NCPM1]|") + std::string(768, '1')).c_str()));
    // An unregister rotates the token while the session generation keeps rising.
    assert(state.Consume("[NCPM1]|88|11|19|22|0|7|54657374|103|1|13|103|90|5761746572"));
    assert(!state.Consume("[NCPM1]|77|10|19|22|0|7|54657374|102|1|11|102|80|426f6e6573"));
    assert(state.ScopeText() == "Commands: Water" && state.OrderCommand(2) == "#nightcappet order 2 88");
    // Empty live roster cannot create pet orders; clear allows a fresh login.
    assert(state.Consume("[NCPM1]|88|12|19|22|0|7|54657374|0|0"));
    assert(!state.HasPets() && state.OrderCommand(2).empty());
    state.Clear();
    assert(state.Consume("[NCPM1]|99|1|19|22|0|7|54657374|0|1|11|102|80|426f6e6573"));
    assert(state.Matches(7,"Test") && state.HasPets());
}

int main() {
    AdversarialSnapshots();
    nightcap::PetManagement state;
    const char* trio = "[NCPM1]|77|1|19|22|0|7|54657374|0|3|10|101|95|537069726974|11|102|80|426f6e6573|13|103|100|5761746572";
    assert(state.Consume(trio));
    assert(state.Matches(7, "Test"));
    assert(state.RowText(0) == "SHM  Spirit  95%");
    assert(state.ScopeText() == "Commands: All pets");
    assert(state.SelectCommand(1) == "#nightcappet select 102 77");
    assert(state.SelectCommand(3).empty());
    assert(!state.Consume(trio)); // replay cannot undo a newer selection
    assert(state.Consume("[NCPM1]|77|2|19|22|0|7|54657374|102|1|11|102|80|426f6e6573"));
    assert(state.ScopeText() == "Commands: Bones");
    assert(state.RowText(0) == "> NEC  Bones  80%");
    assert(state.SelectCommand(0) == "#nightcappet select 0 77");
    assert(state.AllCommand() == "#nightcappet select 0 77");
    for (const char* bad : {
        "[NCPM1]|77|3|19|22|0|7|54657374|999|0",
        "[NCPM1]|77|3|19|22|0|7|54657374|0|1|11|102|101|426f6e6573",
        "[NCPM1]|77|3|19|22|0|7|54657374|0|2|11|102|80|426f6e6573|11|103|80|426f6e6573",
        "[NCPM1]|77|3|19|22|0|7|54657374|0|1|17|102|80|426f6e6573",
        "[NCPM1]|77|3|19|22|0|7|54657374|0|1|11|102|80|00"
    }) assert(!state.Consume(bad));
    assert(state.ScopeText() == "Commands: Bones"); // malformed updates are atomic
    assert(state.Consume("[NCPM1]|77|3|19|22|0|7|54657374|0|0"));
    assert(state.RowText(0) == "No pet summoned");
    assert(state.SelectCommand(0).empty());
    assert(!state.Matches(8, "Test") && !state.Matches(7, "Other"));
    state.Clear();
    assert(state.AllCommand().empty() && !state.Matches(7, "Test"));
    std::cout << "pet management state passed\n";
}

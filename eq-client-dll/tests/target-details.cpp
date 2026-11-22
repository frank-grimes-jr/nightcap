#include "../src/target_details.h"
#include <cassert>
#include <cstring>
#include <vector>

int main() {
    using namespace nightcap::target_details;
    std::vector<BYTE> image(0xA67CCC + sizeof(void*));
    alignas(4) BYTE game[0x5CC]{};
    BYTE npc[0xEB9]{};
    BYTE merchant[sizeof npc]{};
    auto& target = *reinterpret_cast<BYTE**>(&image[0x9D2648]);
    auto& state = *reinterpret_cast<int*>(game + 0x5C8);
    char text[48];
    auto expect = [&](const char* expected) {
        Format(Read(reinterpret_cast<uintptr_t>(image.data())), text);
        assert(std::strcmp(expected, text) == 0);
    };
    expect("");
    *reinterpret_cast<BYTE**>(&image[0xA67CCC]) = game;
    state = 5;
    expect("");
    target = npc;
    npc[0x125] = npc[0x160] = 1;
    npc[0x250] = 12;
    npc[0xEB8] = 2;
    expect("Lv 12 Cleric");
    memcpy(merchant, npc, sizeof npc);
    merchant[0xEB8] = 41;
    target = merchant;
    expect("Lv 12 Merchant");
    target = nullptr;
    expect("");
    target = npc;
    npc[0x125] = 0; expect(""); // player
    npc[0x125] = 2; expect(""); // corpse
    npc[0x125] = 1;
    npc[0x160] = 0; expect("");
    npc[0x160] = 1;
    npc[0xEB8] = 17; expect("Lv 12 Cairnwright");
    npc[0xEB8] = 24; expect("Lv 12 Shadow Knight Trainer");
    npc[0xEB8] = 255; expect("Lv 12");
    npc[0x250] = 0; expect("");
    npc[0x250] = 50;
    state = 1; expect("");
    state = 5;
    target = reinterpret_cast<BYTE*>(1); expect("");
    puts("PASS selected NPC details");
}

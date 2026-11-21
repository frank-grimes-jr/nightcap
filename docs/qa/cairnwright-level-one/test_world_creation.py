"""Exercise the world serializer and creation validator with the local PEQ Dwarf rows."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/tests"))
from test_gameplay_policies import function

PRELUDE = r"""
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <vector>
#include "world/sof_char_create_data.h"
using uint8 = uint8_t;
using uint32 = uint32_t;
#define LogInfo(...) ((void)0)
namespace Class { constexpr uint32 Warrior = 1, Berserker = 16; }
enum { OP_CharacterCreateRequest };
struct EQApplicationPacket {
    std::vector<uint8> bytes;
    uint8* pBuffer;
    EQApplicationPacket(int, size_t n) : bytes(n), pBuffer(bytes.data()) {}
};
#define safe_delete(p) delete p
std::vector<RaceClassAllocation> character_create_allocations;
std::vector<RaceClassCombos> character_create_race_class_combos;
struct Client {
    std::vector<uint8> packet;
    void QueuePacket(EQApplicationPacket *app) { packet=app->bytes; }
    bool HandleCharacterCreateRequestPacket(const EQApplicationPacket *);
};
struct CharCreate_Struct {
    uint32 race=8, class_=17, deity=202, start_zone=67;
    uint32 STR=100, DEX=90, AGI=70, STA=115, INT=60, WIS=88, CHA=55;
};
"""
MAIN = r"""
int main() {
    RaceClassAllocation allocation{14, {100,90,70,95,60,88,55}, {0,0,0,20,0,0,0}};
    character_create_allocations.push_back(allocation);
    RaceClassCombos paladin{0,8,3,202,14,67};
    RaceClassCombos berserker{0,8,16,202,14,67};
    RaceClassCombos cairn{0,8,17,202,14,67};
    Client client;
    character_create_race_class_combos={paladin, berserker};
    assert(client.HandleCharacterCreateRequestPacket(nullptr));
    auto stock = client.packet;
    character_create_race_class_combos={paladin, cairn, berserker};
    assert(client.HandleCharacterCreateRequestPacket(nullptr) && stock==client.packet);
    uint32 count=0;
    auto offset=sizeof(uint8)+sizeof(uint32)+sizeof(allocation);
    std::memcpy(&count,stock.data()+offset,sizeof(count));
    assert(count==2 && stock.size()==offset+sizeof(count)+count*sizeof(RaceClassCombos));
    assert(!std::memcmp(stock.data()+offset+sizeof(count), &paladin, sizeof(paladin)));
    assert(!std::memcmp(stock.data()+offset+sizeof(count)+sizeof(paladin), &berserker, sizeof(berserker)));

    CharCreate_Struct c;
    assert(CheckCharCreateInfoSoF(&c));
    c.class_=3; assert(CheckCharCreateInfoSoF(&c));
    c.class_=17; c.race=1; assert(!CheckCharCreateInfoSoF(&c)); c.race=8;
    c.deity=0; assert(!CheckCharCreateInfoSoF(&c)); c.deity=202;
    c.start_zone=394; assert(!CheckCharCreateInfoSoF(&c)); c.start_zone=67;
    c.WIS++; assert(!CheckCharCreateInfoSoF(&c)); c.WIS--;
    character_create_race_class_combos={paladin, berserker};
    assert(!CheckCharCreateInfoSoF(&c));
}
"""
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("eqemu", type=Path, help="EQEmu source with world/sof_char_create_data.h")
    parser.add_argument("--cxx", default="g++", help="Use cl in a Visual Studio developer shell")
    args=parser.parse_args()
    world=(ROOT / "server-mods/code/world/client.cpp").read_text()
    with tempfile.TemporaryDirectory() as tmp:
        src=Path(tmp)/"creation.cpp"
        exe=Path(tmp)/"creation.exe"
        src.write_text("\n".join([PRELUDE,
            function(world,"bool Client::HandleCharacterCreateRequestPacket("),
            function(world,"bool CheckCharCreateInfoSoF(CharCreate_Struct *cc)\n{"),MAIN]))
        if args.cxx == "cl":
            command = ["cl", "/nologo", "/EHsc", "/std:c++17", "/I" + str(args.eqemu.resolve()),
                       str(src), "/Fe:" + str(exe)]
        else:
            command = [args.cxx, "-std=c++11", "-I", str(args.eqemu.resolve()), str(src), "-o", str(exe)]
        subprocess.run(command, cwd=tmp, check=True)
        subprocess.run([str(exe)],check=True)
        print("PASS world creation validation and stock combination packet")

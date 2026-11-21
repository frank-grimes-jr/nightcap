#include "../src/item_name_color.h"
#include <cassert>
#include <iostream>
#include <string>
using namespace nightcap;
int main() {
    assert(ItemNameColor(1234,"Polished Granite Tomahawk") == 0xff00ff00);
    assert(ItemNameColor(1234,"Ascended Guardian Sword") == 0xff00ff00);
    assert(ItemNameColor(900620,"Reforging Box") == 0xff00ff00);
    assert(ItemNameColor(213073,"Sword (Polished)") == 0xff0070dd);
    assert(ItemNameColor(413073,"Sword (Exalted)") == 0xffa335ee);
    assert(ItemNameColor(613073,"Sword (Ascended)") == 0xffff8000);
    assert(ItemNameColor(813073,"Epic (Ascended)") == 0xffff8000);
    assert(ItemNameColor(940025,"Dewstone (Polished)") == 0xff0070dd);
    assert(ItemNameColor(940026,"Dewstone (Exalted)") == 0xffa335ee);
    assert(ItemNameColor(940027,"Dewstone (Ascension)") == 0xffff8000);
    assert(ItemNameColor(961023,"Ember (Ascension)") == 0xffff8000);
    assert(ItemNameColor(960000,"Delver Helm") == 0xff00ff00);
    assert(ItemNameColor(960001,"Polished Delver Helm") == 0xff0070dd);
    assert(ItemNameColor(960002,"Ascended Delver Helm") == 0xffff8000);
    assert(ItemNameColor(960425,"Ascended Dungeon Reward") == 0xffff8000);
    assert(ItemNameColor(960426,"Ascended Other Reward") == 0xff00ff00);
    for(const char* name:{"Sword (Polished) extra","(Polished)","Sword (polished)","Polished",""})
        assert(ItemNameColor(213073,name) == 0xff00ff00);
    assert(ItemNameColor(0,"Sword (Exalted)") == 0xff00ff00);
    assert(ItemNameColor(1048576,"Sword (Exalted)") == 0xff00ff00);
    assert(ItemNameColor(613073,std::string(64,'x')+" (Ascended)") == 0xff00ff00);
    for(uint32_t warning:{0xffff0000u,0xffa020f0u,0xffffffffu})
        assert(InspectionItemNameColor(warning,613073,"Sword (Ascended)") == warning);
    assert(InspectionItemNameColor(0xffff8000,13073,"Sword") == 0xff00ff00);
    assert(InspectionItemNameColor(0xff0070dd,413073,"Sword (Exalted)") == 0xffa335ee);
    std::cout << "PASS: item-name palette, reward conventions, natural names, boundaries and warning preservation\n";
}

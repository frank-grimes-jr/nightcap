"""Verify complete catalog families and exclusions, using the native policy."""
import unittest
import test_free_trade as native


class ItemXPEligibilityTests(unittest.TestCase):
    def test_complete_families(self):
        native.FreeTradeTests.compile_run(self, r'''
#include "common/item_xp_eligibility.h"
#include <map>
#include <cstdio>
#include <cstdlib>
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"%s\n",#x); std::exit(1); } } while(false)
struct Definition {
    uint32_t ID=1001, Slots=4, AugType=0;
    uint8_t ItemClass=0, NoRent=255;
    bool Stackable=false;
    std::string Name="Cloth Cap";
};
int main() {
    using namespace NightcapItemXP;
    std::map<uint32_t,Definition> items;
    const char* names[]={"Cloth Cap","Cloth Cap (Polished)","Cloth Cap (Exalted)","Cloth Cap (Ascended)"};
    for(uint32_t i=0;i<4;++i) { Definition d;d.ID=1001+i*200000;d.Name=names[i];items[d.ID]=d; }
    auto lookup=[&](uint32_t id)->const Definition* { auto it=items.find(id);return it==items.end()?nullptr:&it->second; };
    for(uint32_t i=0;i<4;++i) CHECK(Family(lookup(1001+i*200000),lookup)==static_cast<int>(i));
    items[401001].Name="Wrong item"; CHECK(Family(lookup(1001),lookup)==-1);
    items[401001].Name=names[2]; items[601001].Slots=8; CHECK(Family(lookup(1001),lookup)==-1);
    items[601001].Slots=4; items.erase(201001); CHECK(Family(lookup(1001),lookup)==-1);
    Definition d;
    for(auto id : {0u,200000u,800001u,810099u,960330u,999999u}) {d.ID=id;CHECK(!Candidate(&d));}
    d.ID=1001;d.Slots=PowerSourceMask;CHECK(!Candidate(&d));
    d.Slots=0;CHECK(!Candidate(&d));d.AugType=1;CHECK(Candidate(&d));
    d.Stackable=true;CHECK(!Candidate(&d));d.Stackable=false;
    d.NoRent=0;CHECK(!Candidate(&d));d.NoRent=255;
    d.ItemClass=1;CHECK(!Candidate(&d));
    for(uint32_t base : {940024u,961000u,961020u}) {
        for(uint32_t i=0;i<4;++i) {Definition h;h.ID=base+i;h.Name="Authored Hunt name";h.AugType=1;items[h.ID]=h;}
        for(uint32_t i=0;i<4;++i) CHECK(Family(lookup(base+i),lookup)==static_cast<int>(i));
    }
    CHECK(Family(static_cast<const Definition*>(nullptr),lookup)==-1);
}
''')


if __name__ == '__main__':
    unittest.main()

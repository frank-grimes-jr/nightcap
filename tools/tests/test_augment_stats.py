"""Execute the actual player report against controlled server bonus snapshots."""
from pathlib import Path
import unittest
import test_free_trade as native

ROOT = Path(__file__).resolve().parents[2]


class AugmentStats(unittest.TestCase):
    def test_report_uses_server_totals_and_shield_gate(self):
        body = native.body((ROOT/'server-mods/code/zone/gm_commands/nightcapui.cpp').read_text(), 'void command_augstats(')
        fixture = r'''
#include <cassert>
#include <sstream>
#include <string>
#include <vector>
namespace fmt {
template<class... A> std::string format(std::string text,A... args) {
 std::vector<std::string> values;
 (void)std::initializer_list<int>{(values.push_back(([&]{std::ostringstream s;s<<args;return s.str();})()),0)...};
 for(const auto& value:values){auto pos=text.find("{}");assert(pos!=std::string::npos);text.replace(pos,2,value);}return text;
}
}
struct Bonuses {int ShieldBlock=0,DodgeChance=0;};
struct Client {
 Bonuses item{1,10},spell{2,3},aa{4,5};bool shield=true;std::string text;
 Bonuses GetItemBonuses(){return item;}Bonuses GetSpellBonuses(){return spell;}Bonuses GetAABonuses(){return aa;}
 bool HasShieldEquipped(){return shield;}int GetShielding(){return 6;}int GetSpellShield(){return 12;}
 int GetAvoidance(){return 24;}int GetAccuracy(){return 30;}int GetSpellDmg(){return 29;}int GetHealAmt(){return 92;}
 void SendPopupToClient(const char*,const char* value){text=value;}
};
struct Seperator {};
namespace NightcapHunt {int OutputShieldBlock(Client& c){return c.shield?1:0;}int OutputHeadroom(Client&,bool heal){return heal?30:20;}}
#define RuleI(category,name) name
enum {ItemShieldingCap=35,ItemSpellShieldingCap=35,ItemAvoidanceCap=100,ItemAccuracyCap=150,ItemSpellDmgCap=750,ItemHealAmtCap=750};
// BODY
int main(){Client c;command_augstats(&c,nullptr);
 assert(c.text.find("Shield Block: 7%")!=std::string::npos);
 assert(c.text.find("Hunt augments: +1%")!=std::string::npos);
 assert(c.text.find("Shielding: 6 / 35")!=std::string::npos);
 assert(c.text.find("Spell Damage: 29 / 770")!=std::string::npos);
 assert(c.text.find("Heal Amount: 92 / 780")!=std::string::npos);
 assert(c.text.find("Dodge modifier: +18%")!=std::string::npos);
 c.shield=false;command_augstats(&c,nullptr);
 assert(c.text.find("Shield Block: 0%")!=std::string::npos);
 assert(c.text.find("Hunt augments: +0%")!=std::string::npos);
 assert(c.text.find("Shielding: 6 / 35")!=std::string::npos);
 assert(c.text.find("strongest")!=std::string::npos);
}
'''
        native.FreeTradeTests.compile_run(self, fixture.replace('// BODY',body))

    def test_player_registration(self):
        source = (ROOT/'server-mods/code/zone/command.cpp').read_text()
        self.assertIn('command_add("augstats", "Show equipped combat bonuses and augment stacking.", AccountStatus::Player, command_augstats)',source)


if __name__ == '__main__': unittest.main()

"""Solo self-found (ADR 0074): no passive AA, and every exchange path is gated."""
import re
import test_passive_aa as harness

GATES = {
    'zone/client_packet.cpp': ['Handle_OP_TradeRequest', 'Handle_OP_TradeRequestAck', 'Handle_OP_Trader',
                               'Handle_OP_TraderBuy', 'Handle_OP_Barter', 'Handle_OP_ShopSendParcel',
                               'Handle_OP_GuildBank', 'Handle_OP_GroupFollow2', 'Handle_OP_GroupInvite2',
                               'Handle_OP_RaidCommand'],
    'zone/client_bazaar.cpp': ['BazaarCommand'],
    'zone/inventory.cpp': ['SwapItem'],
    'zone/client_process.cpp': ['OPMoveCoin'],
}


def check_gates():
    for path, names in GATES.items():
        source = (harness.ROOT / 'server-mods/code' / path).read_text(encoding='utf-8')
        for name in names:
            signature = re.search(r'\w+ Client::' + name + r'\(', source).group(0)
            assert 'SSFBlocked(' in harness.function(source, signature), f'{name} is not SSF-gated'


harness.CASES = r"""
void scaled() {
    reset();
    rules["AA:LevelBasedPointsPerLevel"]=20;
    rules["AA:PassiveExpPercent"]=10;
    rules["AA:ExpPerPoint"]=1000000;
    rules["Character:ExpMultiplier"]=1;
    rules["Character:MaxExpLevel"]=50;
}
Client at(int level, bool ssf) {
    Client c; c.level=level; c.ssf=ssf; c.m_pp.exp=c.GetEXPForLevel(level); return c;
}
int main() {
    scaled(); Client c=at(1,true);
    c.AddEXP(Kill,1000,ConsiderColor::White);
    check(c.GetEXP()==1000 && c.GetAAPoints()==0,"SSF at 0% levels normally and earns no AA");

    scaled(); c=at(1,false);
    c.AddEXP(Kill,1000,ConsiderColor::White);
    check(c.GetEXP()==1000 && c.GetAAPoints()==2,"normal character keeps passive AA");

    scaled(); c=at(1,true); c.SetAAExperiencePercent(100);
    c.AddEXP(Kill,1000,ConsiderColor::White);
    check(c.GetEXP()==0 && c.GetAAPoints()==20,"SSF full focus keeps the server AA pace");

    scaled(); c=at(1,true); c.SetAAExperiencePercent(50);
    c.AddEXP(Kill,1000,ConsiderColor::White);
    check(c.GetEXP()==500 && c.GetAAPoints()==10,"SSF half focus has no passive blend");

    reset(); rules["AA:PassiveExpPercent"]=10; c=at(30,true);
    check(c.FinalizeAAExperience(10000,false)==0,"SSF unscaled path has no passive AA");
    std::cout<<checks<<" checks, "<<failures<<" failures\n";
    return failures?1:0;
}
"""

if __name__ == '__main__':
    check_gates()
    harness.main()

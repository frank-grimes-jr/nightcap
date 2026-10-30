"""Actual AddEXP/CalculateExp item award integration, sharing the AA harness."""
import test_passive_aa as harness

harness.CASES = r'''
void training() {
    reset();
    rules["Items:PowerSourceItemXP"]=1;
    rules["AA:LevelBasedPointsPerLevel"]=20;
    rules["AA:PassiveExpPercent"]=10;
    rules["AA:ExpPerPoint"]=1000000;
    rules["Character:MaxExpLevel"]=50;
    NightcapLoot::item_awards=0;
    NightcapLoot::awarded_item_exp=0;
    NightcapLoot::item_result=NightcapLoot::TransferResult::Delivered;
}
int main() {
    NPC npc;
    for(auto level : {1,30,50}) for(auto allocation : {0u,50u,100u}) {
        training(); Client c; c.level=level; c.m_epp.perAA=allocation;
        c.m_pp.exp=c.GetEXPForLevel(level);
        Client baseline=c;
        rules["Items:PowerSourceItemXP"]=0;
        baseline.AddEXP(Kill,10000,ConsiderColor::White,false,&npc);
        rules["Items:PowerSourceItemXP"]=1;
        c.AddEXP(Kill,10000,ConsiderColor::White,false,&npc);
        check(NightcapLoot::item_awards==1 && NightcapLoot::awarded_item_exp==6500,"full pre-allocation basis at every level/allocation");
        check(c.last_exp==baseline.last_exp && c.last_aa==baseline.last_aa,"training does not consume normal or AA XP");
    }
    for(auto source : {Quest,Task,GM,Death,Resurrection,LDoNChest,Sacrifice}) {
        training(); Client c; c.AddEXP(source,10000,ConsiderColor::White,false,&npc);
        check(!NightcapLoot::item_awards,"noncombat source rejected");
    }
    for(auto con : {static_cast<int>(ConsiderColor::Gray),255}) {
        training(); Client c; c.AddEXP(Kill,10000,static_cast<uint8>(con),false,&npc);
        check(!NightcapLoot::item_awards,"gray/unknown con rejected");
    }
    training(); Client c; c.AddEXP(Kill,10000,ConsiderColor::White,true,&npc);
    check(!NightcapLoot::item_awards,"resurrection rejected");
    training(); c=Client{}; c.AddEXP(Kill,10000,ConsiderColor::White);
    check(!NightcapLoot::item_awards,"no NPC identity rejected");
    for(int kind=0;kind<3;++kind) {
        training(); c=Client{}; npc=NPC{};
        npc.owned=kind==0; npc.merc=kind==1; npc.swarm=kind==2;
        c.AddEXP(Kill,10000,ConsiderColor::White,false,&npc);
        check(!NightcapLoot::item_awards,"owned/merc/swarm victims rejected");
    }
    training(); c=Client{}; npc=NPC{}; c.enabled=false;
    c.AddEXP(Kill,10000,ConsiderColor::White,false,&npc);
    check(!NightcapLoot::item_awards,"XP disabled rejects training");
    training(); c=Client{}; NightcapLoot::item_result=NightcapLoot::TransferResult::Uncertain;
    c.AddEXP(Kill,10000,ConsiderColor::White,false,&npc);
    check(c.calls==0,"uncertain inventory commit stops subsequent character saves");
    training(); c=Client{}; rules["Character:FinalExpMultiplier"]=2;
    c.AddEXP(Kill,10000,ConsiderColor::White,false,&npc);
    check(NightcapLoot::awarded_item_exp==13000,"normal XP bonus applied once");
    std::cout<<checks<<" checks, "<<failures<<" failures\n";
    return failures?1:0;
}
'''

if __name__ == '__main__':
    harness.main()

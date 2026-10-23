"""Exercise actual native reward/allocation methods for level-scaled AA."""
import test_passive_aa as harness

harness.CASES = r"""
void scaled() {
    reset();
    rules["AA:LevelBasedPointsPerLevel"]=20;
    rules["AA:PassiveExpPercent"]=10;
    rules["AA:ExpPerPoint"]=1000000;
    rules["Character:ExpMultiplier"]=1;
    rules["Character:MaxExpLevel"]=50;
}
Client at(int level) {
    Client c; c.level=level; c.m_pp.exp=c.GetEXPForLevel(level); return c;
}
int main() {
    scaled(); Client c=at(1);
    c.AddEXP(Kill,500,ConsiderColor::White);
    check(c.GetEXP()==500 && c.GetAAPoints()==1,"level1 half a level earns one passive AA");
    c.AddEXP(Kill,500,ConsiderColor::White);
    check(c.GetEXP()==1000 && c.GetAAPoints()==2,"level1 full level earns two passive AA");

    scaled(); c=at(1); c.SetAAExperiencePercent(100);
    c.AddEXP(Kill,1000,ConsiderColor::White);
    check(c.GetEXP()==0 && c.GetAAPoints()==20,"full focus keeps level1 and tenfold AA rate");

    scaled(); c=at(1); c.SetAAExperiencePercent(50);
    check(c.GetAAPercent()==50,"partial allocation remains selectable");
    c.AddEXP(Kill,1000,ConsiderColor::White);
    check(c.GetEXP()==500 && c.GetAAPoints()==11,"half allocation divides XP and blends passive with focus");

    scaled(); c=at(1); c.SetAAExperiencePercent(100);
    rules["AA:UnusedAAPointCap"]=5; c.m_pp.aapoints=5;
    c.AddEXP(Kill,1000,ConsiderColor::White);
    check(c.GetEXP()==0 && c.GetAAPoints()==5 && c.GetAAPercent()==100,
          "full AA bank never silently resumes leveling");
    for (auto source : {Quest,Task}) {
        scaled(); c=at(1); c.AddLevelBasedExp(source,50);
        check(c.GetEXP()==500 && c.GetAAPoints()==1,"percentage quest/task earns proportional passive AA");
    }
    for (auto source : {GM,Death,Resurrection,Sacrifice,LDoNChest}) {
        scaled(); c=at(1); c.SetAAExperiencePercent(100); c.AddEXP(source,1000);
        check(c.GetAAPoints()==0,"non-progression source grants no level-scaled AA");
    }

    // Verify each native level span, including the actual float32 band jumps.
    for (int level=1;level<=50;++level) {
        for (auto source : {Kill,Quest,Task}) {
            scaled(); c=at(level);
            const auto initial=c.GetEXP(), span=c.GetEXPForLevel(level+1)-initial;
            c.AddEXP(source,span,ConsiderColor::White);
            check(c.GetEXP()==initial+span && c.GetAAPoints()==2,
                  "every native level earns two passive AA");
            scaled(); c=at(level); c.SetAAExperiencePercent(100);
            c.AddEXP(source,span,ConsiderColor::White);
            check(c.GetEXP()==initial && c.GetAAPoints()==20,
                  "every level supports focused AA without normal XP");
        }
    }
    scaled(); c=at(1);
    c.AddEXP(Quest,8000);
    check(c.GetEXP()==8000 && c.GetAAPoints()==4,"single award split over levels1 and2");
    scaled(); c=at(1); c.m_pp.exp=500; c.m_pp.expAA=170000;
    c.AddEXP(Quest,4000);
    check(c.GetEXP()==4500 && c.GetAAPoints()==2 && c.GetAAXP()==170000,
          "partial starting level and preexisting AA fraction preserved");
    scaled(); c=at(1); c.SetAAExperiencePercent(50); c.AddEXP(Quest,16000);
    check(c.GetEXP()==8000 && c.GetAAPoints()==44,"partial allocation split across multiple levels");
    scaled(); c=at(1); c.AddEXP(Quest,c.GetEXPForLevel(50));
    check(c.GetAAPoints()==98 && c.GetAAXP()==0,"continuous level1 through50 produces98 AA");

    // Per-award truncation must not lose passive progress while normal XP moves.
    scaled(); c=at(50);
    const auto capspan=c.GetEXPForLevel(51)-c.GetEXPForLevel(50);
    // Test tiny increments below cap, where endpoint differences accumulate.
    scaled(); c=at(49); const auto tiny_start=c.GetEXP();
    for (int i=0;i<10000;++i) c.AddEXP(Quest,1);
    const auto expected_tiny=uint64(2000000.0L*10000/(c.GetEXPForLevel(50)-tiny_start));
    check(c.GetAAXP()==expected_tiny,"tiny passive rewards accumulate by normal-XP endpoints");
    scaled(); c=at(50); c.m_pp.exp=c.GetEXPForLevel(51); const auto capped=c.GetEXP();
    c.AddEXP(Quest,capspan);
    check(c.GetAAPoints()==2,"passive AA continues after capped XP bar is full");
    scaled(); c=at(50); c.m_pp.exp=c.GetEXPForLevel(51); c.SetAAExperiencePercent(100);
    c.AddEXP(Quest,capspan);
    check(c.GetEXP()==capped && c.GetAAPoints()==20,"capped focused farming retains normal XP");

    scaled(); c=at(1); c.m_pp.expAA=999999; rules["AA:UnusedAAPointCap"]=2;
    c.AddEXP(Quest,100000000);
    check(c.GetAAPoints()==2 && c.GetAAXP()==0,"large scaled award cannot exceed AA wallet cap");
    scaled(); c=at(1); c.m_pp.expAA=123; c.SetAAExperiencePercent(100);
    c.AddEXP(Resurrection,1000,0xff,true);
    check(c.GetEXP()==1000 && c.GetAAXP()==123 && c.GetAAPoints()==0,"resurrection never grants scaled AA");
    scaled(); c=at(1); c.enabled=false; c.AddEXP(Quest,1000); c.AddLevelBasedExp(Task,100);
    check(c.calls==0,"disabled XP rejects both scaled reward APIs");
    scaled(); c=at(1); c.AddEXP(Kill,1000,ConsiderColor::Gray);
    check(c.GetAAPoints()==0 && c.GetAAXP()==0,"gray kill does not create scaled AA");
    scaled(); c=at(1); c.AddEXP(Quest,0);
    check(c.GetAAPoints()==0 && c.GetAAXP()==0,"zero XP creates no AA");

    scaled(); rules["AA:ModernAAScalingEnabled"]=1;
    rules["AA:ModernAAScalingStartPercent"]=10000; rules["AA:ModernAAScalingAALimit"]=4000;
    rules["Character:AAExpMultiplier"]=100; rules["Zone:LevelBasedEXPMods"]=1;
    world.level_exp_mod[1]={1,100}; world.aamod=100;
    rules["Character:EnableCharacterEXPMods"]=1; c=at(1); c.AddEXP(Quest,1000);
    check(c.GetAAPoints()==2,"AA-only modifiers cannot multiply the level-scaled rate again");
    scaled(); rules["Character:FinalExpMultiplier"]=2; c=at(1); c.AddEXP(Quest,250);
    check(c.GetEXP()==500 && c.GetAAPoints()==1,"normal XP boosts increase both bars proportionally");
    scaled(); rules["Character:ExperiencePercentCapPerKill"]=10; c=at(1); c.AddEXP(Kill,1000,ConsiderColor::White);
    check(c.GetEXP()==100 && c.GetAAXP()==200000,"per-kill normal XP cap bounds common AA basis");
    scaled(); rules["AA:MaxAAEXPPerKill"]=100000; c=at(1); c.AddEXP(Quest,1000);
    check(c.GetAAPoints()==0 && c.GetAAXP()==100000,"explicit AA award cap remains enforced");

    for (auto allocation : {0u,1u,5u,10u,25u,50u,95u,99u,100u}) {
        scaled(); c=at(1); c.SetAAExperiencePercent(allocation);
        const auto saved=load_allocation(c.GetAAPercent(),1);
        check(saved==allocation,"level1 allocation survives saved-profile load");
        AA_Action action{aaActionSetEXP,0,0,allocation};
        EQApplicationPacket packet{sizeof(action),&action};c.Handle_OP_AAAction(&packet);
        check(c.GetAAPercent()==allocation,"level1 packet preserves every valid percentage");
        c.AddEXP(Quest,1000);
        check(c.GetEXP()==1000*(100-allocation)/100,"valid percentage diverts exact normal XP fraction");
        const uint64 total=c.GetAAPoints()*1000000ull+c.GetAAXP();
        check(total==2000000+180000*allocation,"all percentages blend passive and focused AA smoothly");
    }
    scaled(); c=at(1); c.m_pp.expAA=123456;
    c.SetAAExperiencePercent(100); c.SetAAExperiencePercent(0);
    check(c.GetAAXP()==123456 && c.GetAAPoints()==0,"changing allocation never reinterprets stored progress");
    c.level=50; c.m_pp.exp=c.GetEXPForLevel(50);
    check(c.GetAAXP()==123456,"level changes retain fractional AA without recalculation");
    c.level=1;c.m_pp.exp=0;
    check(c.GetAAXP()==123456,"delevel does not mint points");

    scaled(); c=at(1);
    const auto huge=c.CalculateLevelBasedAAExp(std::numeric_limits<uint64>::max(),0);
    check(huge==std::numeric_limits<uint32>::max(),"huge focused award saturates before narrowing");
    std::cout<<checks<<" checks, "<<failures<<" failures\n";
    return failures?1:0;
}
"""
if __name__ == '__main__':
    harness.main()

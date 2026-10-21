"""Real native XP methods and SetEXP conversion at 40,000; no server writes."""
import os
import subprocess
import sys
import test_passive_aa as aa

def main():
    source=(aa.ROOT/'server-mods/code/zone/exp.cpp').read_text()
    fake='uint64 GetRequiredAAExperience() { return RuleI(AA,ExpPerPoint); }'
    assert fake in aa.PRELUDE
    aa.PRELUDE=aa.PRELUDE.replace(fake,'uint32 GetRequiredAAExperience();')
    aa.PRELUDE+='\n'+aa.function(source,'uint32 Client::GetRequiredAAExperience')
    conversion=source[source.index('\t\tuint32 last_unspentAA = m_pp.aapoints;'):]
    conversion=conversion[:conversion.index('\n\t\t//Message(')]
    old='m_pp.exp=xp; m_pp.aapoints+=aa/GetRequiredAAExperience();\n    m_pp.expAA=aa%GetRequiredAAExperience();'
    assert old in aa.PRELUDE
    aa.PRELUDE=aa.PRELUDE.replace(old,
        'm_pp.exp=xp; uint64 set_aaxp=aa; auto max_AAXP=GetRequiredAAExperience();\n'
        'if(set_aaxp>=max_AAXP) {\n'+conversion+'\n(void)gained;}\nm_pp.expAA=set_aaxp;')
    extra=r"""
    for(auto level : {1,20,35,50}) for(auto source : {Kill,Quest,Task}) for(auto focus : {0,100}) {
        reset(); rules["AA:PassiveExpPercent"]=10; rules["AA:ExpPerPoint"]=4000;
        c=Client{}; c.level=level; c.m_epp.perAA=focus;
        c.AddEXP(source,1000000,ConsiderColor::White);
        auto xp=c.GetEXP(), award=c.last_aa;
        c=Client{}; c.level=level; c.m_epp.perAA=focus; rules["AA:ExpPerPoint"]=40000;
        c.AddEXP(source,1000000,ConsiderColor::White);
        check(c.GetEXP()==xp && c.last_aa==award,"raw normal/passive/focused awards unchanged");
        check(c.GetAAPoints()==award/40000 && c.GetAAXP()==award%40000,"real SetEXP new denominator");
    }
    for(auto prior : {0u,2000u,3999u,39999u,40000u,79999u}) {
        reset(); rules["AA:PassiveExpPercent"]=10; rules["AA:ExpPerPoint"]=40000;
        c=Client{}; c.m_pp.aapoints=17; c.m_pp.expAA=prior;
        c.AddEXP(Kill,10000,ConsiderColor::White);
        check(c.GetAAPoints()==17+(prior+650)/40000 && c.GetAAXP()==(prior+650)%40000,"points and remainder preserved");
        auto points=c.GetAAPoints(), remainder=c.GetAAXP();
        c.AddEXP(Kill,10000,ConsiderColor::White);
        check(c.GetAAPoints()==points+(remainder+650)/40000 && c.GetAAXP()==(remainder+650)%40000,"no duplicate conversion");
    }
    for(auto source : {Quest,Task}) for(auto focus : {0,100}) {
        reset(); rules["AA:PassiveExpPercent"]=10; rules["AA:ExpPerPoint"]=4000;
        c=Client{}; c.m_epp.perAA=focus; c.AddLevelBasedExp(source,10);
        auto xp=c.GetEXP(), award=c.last_aa;
        c=Client{}; c.m_epp.perAA=focus; rules["AA:ExpPerPoint"]=40000;
        c.AddLevelBasedExp(source,10);
        check(c.GetEXP()==xp && c.last_aa==award && c.GetAAPoints()==award/40000,"percentage quest/task path");
    }
    reset(); rules["AA:PassiveExpPercent"]=10; rules["AA:ExpPerPoint"]=4000;
    c=Client{}; c.m_pp.aapoints=12; c.m_pp.expAA=2000; rules["AA:ExpPerPoint"]=40000;
    check(c.GetAAPoints()==12 && c.GetAAXP()==2000,"rule increase does not rewrite state");
    c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.GetAAPoints()==12 && c.GetAAXP()==2650,"first award preserves raw remainder");
    c.m_pp.expAA=39500; rules["AA:ExpPerPoint"]=4000; c.AddEXP(Kill,10000,ConsiderColor::White);
    check(c.GetAAPoints()==22 && c.GetAAXP()==150,"rollback keeps earned progress");
    reset(); rules["AA:PassiveExpPercent"]=10; rules["AA:ExpPerPoint"]=40000;
    c=Client{}; c.AddEXP(Kill,1,ConsiderColor::White);
    check(c.GetAAPoints()==0 && c.GetAAXP()==0,"tiny awards remain zero");
"""
    marker='    std::cout<<checks'
    assert aa.CASES.count(marker)==1
    aa.CASES=aa.CASES.replace(marker,extra+'\n'+marker)
    if os.name=='nt' and '--compiler' not in sys.argv:
        native_run=subprocess.run
        def run(args,**kwargs):
            if args[0]=='clang++':
                output=args[-1]
                args=['cl.exe','/nologo','/std:c++20','/EHsc','/W3',
                      '/I'+str(aa.ROOT/'server-mods/code'),args[-3],
                      '/Fo'+output+'.obj','/Fe'+output+'.exe']
            return native_run(args,**kwargs)
        aa.subprocess.run=run
    aa.main()

if __name__=='__main__':
    main()

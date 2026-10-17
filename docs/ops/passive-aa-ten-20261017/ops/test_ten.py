"""Existing native XP harness plus focused 10% checks; no production writes."""
import importlib.util
import sys
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('passive',ROOT/'tools/tests/test_passive_aa.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
extra=r'''
    for (int level : {1,10,27,50}) {
        for (auto source : {Kill,Quest,Task}) {
            reset(); rules["AA:PassiveExpPercent"]=10; rules["AA:ExpPerPoint"]=4000;
            c=Client{}; c.level=level; c.AddEXP(source,10000,ConsiderColor::White);
            check(c.last_exp==6500 && c.last_aa==650,"ten percent preserves full normal XP");
            c=Client{}; c.level=level; c.m_epp.perAA=100;
            c.AddEXP(source,10000,ConsiderColor::White);
            check(c.last_exp==0 && c.last_aa==6500,"ten percent leaves focused AA unchanged");
        }
    }
    for (auto source : {Quest,Task}) {
        reset(); rules["AA:PassiveExpPercent"]=10; c=Client{}; c.AddLevelBasedExp(source,10);
        auto award=(c.GetEXPForLevel(31)-c.GetEXPForLevel(30))/10;
        check(c.last_exp==award && c.last_aa==uint64(award*0.65f)*10/100,"ten percent percentage quest reward");
    }
    reset(); rules["AA:PassiveExpPercent"]=10; rules["AA:ExpPerPoint"]=4000;
    c=Client{}; c.m_pp.expAA=3700; c.AddEXP(Quest,10000);
    check(c.m_pp.aapoints==1 && c.m_pp.expAA==350 && c.last_exp==6500,"ten percent keeps prior remainder across point boundary");
    c=Client{}; c.AddEXP(Kill,1,ConsiderColor::White);
    check(c.last_aa==0,"ten percent tiny award rounds down");
'''
needle='    std::cout<<checks'
assert module.CASES.count(needle)==1
module.CASES=module.CASES.replace(needle,extra+'\n'+needle)
sys.argv=['test_passive_aa.py','--compiler','C:/Strawberry/c/bin/g++.exe']
native_run=subprocess.run
def run_with_msvc(args, **kwargs):
    if args[0].endswith('g++.exe'):
        source=args[-3]; output=args[-1]
        args=['C:/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe',
              '/nologo','/std:c++20','/EHsc','/W3','/I'+str(ROOT/'server-mods/code'),
              source,'/Fo'+output+'.obj','/Fe'+output+'.exe']
    return native_run(args,**kwargs)
module.subprocess.run=run_with_msvc
module.main()

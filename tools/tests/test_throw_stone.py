"""Compile actual spell-damage methods with boundary fakes; no server/DB writes.

Run: python tools/tests/test_throw_stone.py --compiler g++
This checks production arithmetic, not a linked server or native gameplay.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile

from test_passive_aa import function

ROOT = Path(__file__).resolve().parents[2]

PRELUDE = r'''
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <map>
#include <string>
using int64 = int64_t; using int32 = int32_t; using uint16 = uint16_t;
std::map<std::string, int> rules;
#define RuleI(c,n) (rules[#c ":" #n])
#define RuleB(c,n) (bool(rules[#c ":" #n]))
namespace Class { constexpr int Wizard = 12; }
namespace Chat { enum { SpellCrit }; }
enum { ST_Self=6, CASTERDPS=1, SPELL_IMP_HARM_TOUCH=2774, SPELL_MANA_BURN=2751,
       aaSpellCastingFury, aaUnholyTouch, FilterSpellCrits, OTHER_CRIT_BLAST, YOU_CRIT_BLAST,
       focusRange, focusImprovedDamage, focusImprovedDamage2, focusFcDamagePctCrit,
       focusFcAmplifyMod, focusFcDamageAmtCrit, focusFcDamageAmt, focusFcDamageAmt2,
       focusFcAmplifyAmt };
bool IsHarmTouchSpell(uint16) { return false; }
const char* itoa(int64) { return "damage"; }
struct Spell {
    int target_type=5, skill=33, override_crit_chance=0, no_heal_damage_item_mod=0;
    int classes[16];
    int cast_time=0, recast_time=10000, recovery_time=0;
    Spell() { std::fill(std::begin(classes), std::end(classes), 1); }
} spells[6000];
struct Zone {
    struct Random {
        bool Roll(int chance) { return chance >= 100; }
        int Int(int low, int) { return low; }
    } random;
} zone_instance, *zone=&zone_instance;
struct EntityList {
    template<class... T> void FilteredMessageCloseString(T...) {}
} entity_list;
struct Bonuses {
    int SpellDmg=0, CriticalSpellChance=0, FrenziedDevastation=0;
    int SpellCritDmgIncrease=0, SpellCritDmgIncNoStack=0;
};
struct Mob {
    Bonuses itembonuses, spellbonuses, aabonuses;
    enum Kind { Client, Bot, Merc, NPC } kind=Client;
    int level=50, cls=1, vulnerability=0, incoming=0;
    std::map<int,int> focuses;
    bool IsNPC() { return kind==NPC; }
    bool IsClient() { return kind==Client; }
    bool IsMerc() { return kind==Merc; }
    bool IsOfClientBot() { return kind==Client || kind==Bot; }
    bool IsOfClientBotMerc() { return kind!=NPC; }
    Mob* CastToNPC() { return this; }
    int GetSpellFocusDMG() { return 0; }
    int GetSpellScale() { return 100; }
    int GetSkillDmgAmt(int) { return 0; }
    int GetClass() { return cls; }
    int GetLevel() { return level; }
    int GetAA(int) { return 0; }
    int GetFocusEffect(int focus, uint16) { return focuses[focus]; }
    int GetVulnerability(Mob*, uint16, int) { return vulnerability; }
    int GetFcDamageAmtIncoming(Mob*, uint16) { return incoming; }
    int GetSpellDmg() { return IsOfClientBotMerc() ? itembonuses.SpellDmg : 0; }
    const char* GetName() { return "Test"; }
    template<class... T> void MessageString(T...) {}
    int64 GetExtraSpellAmt(uint16, int64, int64);
    int64 GetActSpellDamage(uint16, int64, Mob*);
    int64 GetActReflectedSpellDamage(uint16, int64, int);
};
int checks=0, failures=0;
void expect(const char* label, int64 actual, int64 expected) {
    ++checks;
    if (actual!=expected) {
        ++failures;
        std::cerr << label << ": expected " << expected << ", got " << actual << '\n';
    }
}
'''

CASES = r'''
int main() {
    constexpr uint16 stone=5225, other=5224;
    rules["Spells:FlatItemExtraSpellAmt"]=1;
    rules["Spells:ItemExtraSpellAmtCalcAsPercent"]=1;
    rules["Spells:IgnoreSpellDmgLvlRestriction"]=1;
    rules["Spells:BaseCritRatio"]=200;
    Mob caster, target;
    // Capped effective Spell Damage, including representative tier amounts.
    for (int stat : {0, 1, 50, 100, 240, 250, 500}) {
        caster.itembonuses.SpellDmg=stat;
        expect("stone flat bonus", caster.GetActSpellDamage(stone,-1,nullptr), -(1+stat));
        caster.aabonuses.CriticalSpellChance=100;
        expect("stone critical", caster.GetActSpellDamage(stone,-1,nullptr), -(1+stat)*2);
        expect("ordinary critical", caster.GetActSpellDamage(other,-100,nullptr), -(100+stat)*2);
        caster.aabonuses.CriticalSpellChance=0;
        expect("ordinary percentage nuke", caster.GetActSpellDamage(other,-100,nullptr), -(100+stat));
    }
    caster.itembonuses.SpellDmg=250;
    for (int cls=1; cls<=16; ++cls) {
        caster.cls=cls;
        for (int level : {1, 10, 30, 50}) {
            caster.level=level;
            rules["Spells:IgnoreSpellDmgLvlRestriction"]=0;
            expect("stone class and level", caster.GetActSpellDamage(stone,-1,&target), -251);
        }
    }
    caster.cls=1;
    caster.level=50;
    expect("ordinary level restriction", caster.GetActSpellDamage(other,-100,&target), -100);
    rules["Spells:IgnoreSpellDmgLvlRestriction"]=1;
    for (int flat : {0,1}) for (int percent : {0,1}) {
        rules["Spells:FlatItemExtraSpellAmt"]=flat;
        rules["Spells:ItemExtraSpellAmtCalcAsPercent"]=percent;
        expect("stone ignores generic coefficient", caster.GetActSpellDamage(stone,-1,&target), -251);
    }
    rules["Spells:FlatItemExtraSpellAmt"]=1;
    rules["Spells:ItemExtraSpellAmtCalcAsPercent"]=1;
    spells[stone].no_heal_damage_item_mod=1;
    expect("explicit item-mod opt out", caster.GetActSpellDamage(stone,-1,&target), -1);
    caster.aabonuses.CriticalSpellChance=100;
    expect("critical item-mod opt out", caster.GetActSpellDamage(stone,-1,&target), -2);
    caster.aabonuses.CriticalSpellChance=0;
    spells[stone].no_heal_damage_item_mod=0;
    caster.itembonuses.SpellDmg=-50;
    expect("negative stat does not heal", caster.GetActSpellDamage(stone,-1,&target), -1);
    caster.itembonuses.SpellDmg=250;
    for (auto kind : {Mob::Bot, Mob::Merc}) {
        caster.kind=kind;
        expect("player companion", caster.GetActSpellDamage(stone,-1,&target), -251);
    }
    caster.kind=Mob::NPC;
    expect("NPC retains percentage behavior", caster.GetActSpellDamage(stone,-1,&target), -3);
    caster.kind=Mob::Client;
    target.vulnerability=100;
    target.incoming=5;
    caster.focuses[focusImprovedDamage]=100;
    expect("existing focuses and target modifiers", caster.GetActSpellDamage(stone,-1,&target), -258);
    caster.aabonuses.CriticalSpellChance=100;
    expect("critical focuses and target modifiers", caster.GetActSpellDamage(stone,-1,&target), -510);
    caster.aabonuses.CriticalSpellChance=0;
    caster.focuses.clear();
    spells[stone].target_type=ST_Self;
    expect("self-target shortcut", caster.GetActSpellDamage(stone,-1,nullptr), -1);
    spells[stone].target_type=5;
    // Reflection retains the established separate base-spell calculation.
    expect("reflection regression", caster.GetActReflectedSpellDamage(stone,-1,100), -3);
    expect("ordinary reflection regression", caster.GetActReflectedSpellDamage(other,-100,50), -300);
    std::cout << checks << " checks, " << failures << " failures\n";
    return failures ? EXIT_FAILURE : EXIT_SUCCESS;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', default='g++')
    args = parser.parse_args()
    source = (ROOT / 'server-mods/code/zone/effects.cpp').read_text()
    bodies = '\n'.join(function(source, signature) for signature in (
        'int64 Mob::GetActSpellDamage', 'int64 Mob::GetExtraSpellAmt',
        'int64 Mob::GetActReflectedSpellDamage'))
    with tempfile.TemporaryDirectory(prefix='throw-stone-') as temp:
        path = Path(temp)
        test = path / 'test.cpp'
        executable = path / 'test.exe'
        test.write_text(PRELUDE + bodies + CASES)
        if Path(args.compiler).stem.lower() == 'cl':
            command = [args.compiler, '/nologo', '/std:c++17', '/EHsc', '/W3',
                       str(test), '/Fe:' + str(executable)]
        else:
            command = [args.compiler, '-std=c++17', '-Wall', '-Wextra',
                       '-Werror', '-Wno-unused-parameter', str(test),
                       '-o', str(executable)]
        subprocess.run(command, cwd=path, check=True)
        subprocess.run([str(executable)], check=True)


if __name__ == '__main__':
    main()

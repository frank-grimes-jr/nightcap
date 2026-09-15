"""Differential-check spell bases, durations, and ordinary resist distributions."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import subprocess
import uuid

from builds import load_snapshot
from spell_math import effect_value, buff_duration, resist_outcomes
from verify_cpp import extract_function


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    snapshot,manifest = load_snapshot(args.snapshot)
    sources = {name:(args.source/name).read_bytes() for name in ('zone/spell_effects.cpp','zone/spells.cpp')}
    functions = {
        'duration':extract_function(sources['zone/spells.cpp'].decode(),'int CalcBuffDuration_formula('),
        'effect':extract_function(sources['zone/spell_effects.cpp'].decode(),'int64 Mob::CalcSpellEffectValue_formula('),
        'resist':extract_function(sources['zone/spells.cpp'].decode(),'float Mob::ResistSpell('),
    }
    harness = r'''
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
using int64=int64_t; using uint8=uint8_t; using uint16=uint16_t; using uint32=uint32_t; using int16=int16_t;
#define LogSpells(...)
#define LogDebug(...) throw std::runtime_error("Unknown formula")
constexpr int RESIST_NONE=0, RESIST_DISEASE=4, RESIST_PHYSICAL=9, ST_Undead=3;
constexpr int DISC_UNHOLY_AURA=1,focusResistRate=1,focusFcResistIncoming=2;
namespace SpecialAbility { enum { CastingFromRangeImmunity,MagicImmunity,CastingResistDifficulty }; }
struct Rules {
 bool July242002PetResists=false,EnableResistSoftCap=false;
 int ResistFalloff=67,CharismaEffectivenessCap=255,CharismaEffectiveness=10;
 int SpellResistSoftCap=200,CharmBreakCheckChance=25,RootBreakCheckChance=70;
} rules;
#define RuleI(category,name) rules.name
#define RuleB(category,name) rules.name
struct Spell {
 int buff_duration_formula=0,buff_duration=0,pvp_resist_base=0,resist_difficulty=0;
 int target_type=0,max_resist=0,min_resist=0; bool no_resist=false;
} spells[1];
struct Random {
 int forced=0;
 int Int(int low,int high) { return std::clamp(forced,std::min(low,high),std::max(low,high)); }
 bool Roll(int chance) { return false; }
};
struct Zone { Random random; } fixture_zone,*zone=&fixture_zone;
bool partial=false,damage_spell=true;
bool IsValidSpell(uint16) { return true; }
bool IsFearSpell(uint16) { return false; }
bool IsHarmTouchSpell(uint16) { return false; }
bool IsResurrectionSicknessSpell(uint16) { return false; }
bool IsHarmonySpell(uint16) { return false; }
bool IsDamageSpell(uint16) { return damage_spell; }
bool IsPartialResistableSpell(uint16) { return partial; }
struct Mob {
 bool npc=false,immune=false,degenerating_effects=false;
 int level=50,resistance=0;
 int GetSpecialAbility(int ability) { return ability==SpecialAbility::MagicImmunity && immune; }
 int GetSpecialAbilityParam(int,int) { return 0; }
 bool CombatRange(Mob*) { return true; }
 bool IsClient() { return !npc; }
 bool IsNPC() { return npc; }
 bool IsOfClientBot() { return !npc; }
 bool IsPetOwnerOfClientBot() { return false; }
 Mob* GetOwner() { return nullptr; }
 Mob* CastToClient() { return this; }
 bool FindBuff(int) { return false; }
 int64 GetFocusEffect(int,int,Mob* = nullptr) { return 0; }
 int CalcFearResistChance() { return 0; }
 bool TrySpellEffectResist(int) { return false; }
 int CalcResistChanceBonus() { return 0; }
 int GetResist(int) { return resistance; }
 int GetLevel() { return level; }
 int GetCHA() { return 75; }
 int ResistPhysical(int,uint8) { throw std::runtime_error("Physical resist excluded"); }
 float GetHPRatio() { throw std::runtime_error("Dynamic HP formula excluded"); }
 int64 GetHP() { throw std::runtime_error("Dynamic HP formula excluded"); }
 int64 GetMaxHP() { throw std::runtime_error("Dynamic HP formula excluded"); }
 int64 CalcSpellEffectValue_formula(uint32,int64,int64,int,uint16,int);
 float ResistSpell(uint8,uint16,Mob*,bool,int,bool,bool,bool,int);
};
''' + '\n'.join(functions.values()) + r'''
int main() {
 char kind;
 while (std::cin >> kind) {
  if (kind=='V') {
   uint32 formula; int64 base,maximum; int level,remaining,draw;
   std::cin >> formula >> base >> maximum >> level >> spells[0].buff_duration_formula
            >> spells[0].buff_duration >> remaining >> draw;
   zone->random.forced=draw; Mob mob;
   std::cout << "V " << mob.CalcSpellEffectValue_formula(formula,base,maximum,level,0,remaining)
             << ' ' << CalcBuffDuration_formula(level,spells[0].buff_duration_formula,spells[0].buff_duration) << '\n';
  } else {
   Mob target,caster; int modifier;
   std::cin >> target.resistance >> caster.level >> target.level >> modifier >> partial
            >> target.npc >> caster.npc >> damage_spell >> rules.ResistFalloff
            >> spells[0].min_resist >> spells[0].max_resist >> spells[0].no_resist >> target.immune;
   int counts[101]{};
   for (int roll=0;roll<=200;++roll) {
    zone->random.forced=roll;
    int value=target.ResistSpell(1,0,&caster,true,modifier,false,false,false,0);
    if (value<0 || value>100) return 2;
    ++counts[value];
   }
   std::cout << "R";
   for (int count:counts) std::cout << ' ' << count;
   std::cout << '\n';
  }
 }
}
'''
    rng = random.Random(20260912)
    values,expected_values = [],[]
    skipped = Counter()
    for spell in snapshot['tables']['spells_new']:
        for level in (1,25,50,55):
            for slot in range(1,13):
                if spell[f'effectid{slot}']==254:
                    continue
                formula,base,maximum = (spell[f'{key}{slot}'] for key in ('formula','effect_base_value','max'))
                draw = rng.randint(min(abs(base),abs(maximum)),max(abs(base),abs(maximum)))
                row = (formula,base,maximum,level,spell['buffdurationformula'],spell['buffduration'],0,draw)
                try:
                    value=effect_value(formula,base,maximum,level,duration_formula=row[4],duration=row[5],remaining=0,random_value=draw)
                except ValueError:
                    skipped[formula] += 1
                    continue
                values.append(row)
                expected_values.append((value,buff_duration(level,row[4],row[5])))
    resists=[]
    for _ in range(1500):
        resists.append((rng.randint(-100,1200),rng.randint(1,80),rng.randint(1,80),
                        rng.randint(-300,100),rng.randrange(2),rng.randrange(2),rng.randrange(2),
                        rng.randrange(2),67,rng.choice((0,0,20)),rng.choice((0,0,150)),
                        rng.randrange(20)==0,rng.randrange(20)==0))
    rows = ['V '+' '.join(map(str,row)) for row in values]
    rows += ['R '+' '.join(str(int(x)) for x in row) for row in resists]
    binary='/tmp/nightcap-spell-math-'+uuid.uuid4().hex
    container='akk-stack-eqemu-server-1'
    try:
        subprocess.run(['docker','exec','-i',container,'g++','-std=c++17','-O2','-x','c++','-o',binary,'-'],
                       input=harness,text=True,capture_output=True,check=True)
        result=subprocess.run(['docker','exec','-i',container,binary],input='\n'.join(rows)+'\n',
                              text=True,capture_output=True,check=True)
    except subprocess.CalledProcessError as error:
        raise RuntimeError(error.stderr) from error
    finally:
        subprocess.run(['docker','exec',container,'rm','-f',binary],check=True)
    output=result.stdout.splitlines()
    if len(output)!=len(rows):
        raise ValueError('Incomplete spell oracle output')
    mismatches=[]
    for row,expected,line in zip(values,expected_values,output):
        fields=line.split()
        actual=tuple(map(int,fields[1:]))
        if fields[0]!='V' or actual!=expected:
            mismatches.append({'kind':'value','input':row,'cpp':actual,'python':expected})
    for row,line in zip(resists,output[len(values):]):
        resistance,caster,target,modifier,partial,tnpc,cnpc,damage,falloff,minimum,maximum,no_resist,immune=row
        expected=resist_outcomes(resistance,caster,target,modifier=modifier,partial=partial,target_npc=tnpc,
                                 caster_npc=cnpc,damage_spell=damage,falloff=falloff,minimum=minimum,
                                 maximum=maximum,no_resist=no_resist,immune=immune)
        fields=line.split()
        actual=tuple((int(n),pct) for pct,n in enumerate(fields[1:]) if int(n))
        if fields[0]!='R' or len(fields)!=102 or actual!=expected:
            mismatches.append({'kind':'resist','input':row,'cpp':actual,'python':expected})
    report={'snapshot_sha256':manifest['snapshot_sha256'],
            'source_sha256':{k:hashlib.sha256(v).hexdigest() for k,v in sources.items()},
            'function_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in functions.items()},
            'value_duration_cases':len(values),'resist_distributions':len(resists),
            'native_resist_rolls':len(resists)*201,'skipped_formulas':dict(skipped),'mismatches':mismatches,
            'scope':'Stored effect formulas/durations and ordinary resist path with resolved modifier; excludes dynamic HP formulas, focus/AA resistance checks, fear CHA, physical/PvP special handling, softcap, root/charm breaks, and complete spell application'}
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    return int(bool(mismatches))


if __name__=='__main__':
    raise SystemExit(main())

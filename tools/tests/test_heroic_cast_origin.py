"""Measure the checked-out direct damage/heal methods under production cast origin scopes."""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def between(text, start, stop):
    first = text.index(start)
    return text[first:text.index(stop, first)]


def method(text, signature):
    first = text.index(signature)
    end = text.index('{', first) + 1
    depth = 1
    while depth:
        depth += (text[end]=='{') - (text[end]=='}')
        end += 1
    return text[first:end]


def measure(source):
    source = source.resolve()
    paths = ['zone/effects.cpp', 'zone/spells.cpp', 'zone/spell_effects.cpp', 'zone/aa.cpp',
             'zone/special_attacks.cpp', 'zone/raid_augment.h','zone/raid_augment_delivery.h',
             'common/raid_augment.h', 'common/nightcap_spell_scaling.h']
    data = {p:(source/p).read_text(encoding='utf-8') for p in paths}
    casts = data['zone/spells.cpp']
    effects = data['zone/effects.cpp']
    spell_effects = data['zone/spell_effects.cpp']
    prelude = (HERE/'thj_spell_fixture.h').read_text()
    candidate = (source/'zone/nightcap_heroic_cast.h').exists()
    if candidate:
        paths.append('zone/nightcap_heroic_cast.h')
    prelude = prelude.replace('struct Spell{', 'struct Spell{int limit_value[1]{},base_value[1]{};bool is_discipline=false,combat=false,skill_attack=false;')
    prelude = prelude.replace('struct Zone{','''bool IsCombatSkill(int id){return spells[id].combat;}
bool IsEffectInSpell(int id,int){return spells[id].skill_attack;}
struct Rank {int spell=431;} fixture_rank;
struct Zone{const Rank* GetAlternateAdvancementRank(uint32 id){return id==1234?&fixture_rank:nullptr;}
''')
    prelude = prelude.replace('struct Mob{', '''struct Mob{
 int64 observed=0;
 int partial_percent=100;
 bool PassCastRestriction(int){return true;}
 void Damage(Mob*,int64 d,int,int,bool,int,bool){observed=-d;}
 void HealDamage(int64 h,Mob*){observed=h;}
 void ResourceTap(int64,int){}
 Mob* CastToClient(){return this;}
 struct Profile{uint32 mem_spells[12]{431};} pp;
 const Profile& GetPP(){return pp;}
 bool IsFromTriggeredSpell(CastingSlot,uint32);
 void FinishCast(int,CastingSlot,bool,uint32,bool,uint32,const std::function<void()>&);
 int64 Landing(Mob*,int,int,int);
''')
    prelude = prelude.replace('namespace SpellEffect{enum{','namespace SpellEffect{enum{CurrentHP,SkillAttack,')
    prelude = prelude.replace('GetActSpellHealing(uint16,int64,Mob*,bool);','GetActSpellHealing(uint16,int64,Mob*,bool=false);')
    fixture=(HERE/'heroic_cast_origin_fixture.cpp').read_text()
    fixture=fixture.replace('/* SPELL BOUNDARY */',prelude)
    if candidate:
        fixture = '#define HEROIC_ORIGIN 1\n#include "zone/nightcap_heroic_cast.h"\n'+fixture
        fixture = fixture.replace('/* FINISH BARRIER */',between(casts,'const NightcapHeroicCast::Targets nested_targets;', 'Mob *ae_center'))
        fixture = fixture.replace('/* ORIGINAL RECIPIENTS */',between(casts,'NightcapHeroicCast::Targets original_targets','switch(CastAction)'))
        target_gate = between(casts,'const bool original_bolt =','if (!sympathetic)')
        fixture = fixture.replace('/* TARGET ORIGIN */',target_gate.replace('For(this, spell_id)','For(self, spell_id)'))
        fixture = fixture.replace('/* EFFECT ORIGIN */',between(spell_effects,'const bool heroic = NightcapHeroicCast::Cast::Take()', 'auto record_hp'))
        # Retain the exact handoff, with the surrounding validation/network lifecycle controlled.
        bridge = between(casts, 'return NightcapHeroicCast::Cast::Deliver(heroic', '\n\t}))')
        fixture = fixture.replace('/* DELIVER EFFECT */', bridge.replace('SpellEffect(this,','SpellEffect(self,'))
        finish = method(casts,'bool Mob::SpellFinished(')
        assert finish.index('Targets original_targets') < finish.index('switch(CastAction)',finish.index('Targets original_targets')) < finish.index('original_targets.Finish()')
        timed = method(casts,'void Mob::CastedSpellFinished(')
        assert '0xFFFFFFFF, 0, true, casting_spell_aa_id)' in timed
        assert 'timer_duration, false, rank->id)' in data['zone/aa.cpp']
        assert 'timer_duration, nullptr, rank->id)' in data['zone/aa.cpp']
    methods = [method(effects,sig) for sig in
               ('int64 Mob::GetActSpellDamage(','int64 Mob::GetActReflectedSpellDamage(',
                'int64 Mob::GetActDoTDamage(','int64 Mob::GetActSpellHealing(',
                'int64 Mob::GetExtraSpellAmt(','int64 Mob::GetNightcapSpellDamageBonus(',
                'int64 Mob::GetNightcapHeroicSpellValue(')]
    methods.append(method(casts,'bool Mob::IsFromTriggeredSpell('))
    fixture=fixture.replace('/* EFFECT METHODS */','\n'.join(methods))
    fixture=fixture.replace('/* CLASSIFY CAST */',between(casts,'const bool raid_gem =','const bool thj_resource ='))
    fixture=fixture.replace('/* CURRENT HP */',between(spell_effects,'case SpellEffect::CurrentHP:', 'case SpellEffect::CurrentHPOnce:'))
    with tempfile.TemporaryDirectory(prefix='nightcap-heroic-origin-') as temp:
        tmp = Path(temp)
        (tmp/'measure.cpp').write_text(fixture)
        if os.name=='nt':
            (tmp/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars64.bat" >nul || exit /b 1\n'
                                         f'cl /nologo /EHsc /std:c++17 /O2 /I"{source}" measure.cpp /Fe:measure.exe\n')
            command = ['cmd','/d','/c','build.cmd']
            exe = tmp/'measure.exe'
        else:
            command = [os.environ.get('CXX','c++'),'-std=c++17','-O2','-I',str(source),'measure.cpp','-o','measure']
            exe = tmp/'measure'
        built=subprocess.run(command,cwd=tmp,capture_output=True,text=True)
        if built.returncode:
            raise RuntimeError(built.stdout+built.stderr)
        output=subprocess.check_output([str(exe)],text=True)
    rows=list(csv.DictReader(io.StringIO(output)))
    for row in rows:
        for key in ('hint','hwis','sd','ha','damage','healing'):
            row[key]=int(row[key])
    return {'sha256':{p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in paths},
            'fixture_sha256':hashlib.sha256(fixture.encode()).hexdigest(),'samples':rows}


class HeroicCastOrigin(unittest.TestCase):
    def test_native_matrix(self):
        data=measure(ROOT/'server-mods/code')
        verify(data['samples'],True)


def verify(rows, candidate):
    indexed={(r['scenario'],r['hint'],r['hwis']):r for r in rows}
    assert len(indexed)==len(rows)==190
    eligible={'gem','aa','aa_timed','group_gem','ae_aa','parent_after','gem_bolt','aa_bolt','gem_rain','aa_rain','gem_critical','gem_partial'}
    for row in rows:
        name=row['scenario']
        control=indexed[name,0,0]
        old_exception=name in ('pet','npc','dot_hot','rule_disabled','opt_out')
        qualifies=(name in eligible) if candidate else not old_exception
        def expected(v,hero):
            return v + (1 if v>=0 else -1)*(abs(v)*hero//1000) if qualifies else v
        assert row['damage']==expected(control['damage'],row['hint']),row
        assert row['healing']==expected(control['healing'],row['hwis']),row
    assert indexed['gem',0,0]['damage']==-140 and indexed['gem',0,0]['healing']==160
    assert indexed['gem_critical',0,0]['damage']==-280
    assert indexed['gem_partial',0,0]['damage']==-90


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'server-mods/code')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--baseline',action='store_true')
    args=parser.parse_args()
    data=measure(args.source)
    verify(data['samples'],not args.baseline)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2)+'\n')

"""Compile the actual combat packet, Backstab and explicit-damage spell entry points."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def method(source, sig):
    start = source.index(sig)
    end = source.index('{', start)+1
    depth = 1
    while depth:
        depth += (source[end]=='{')-(source[end]=='}')
        end += 1
    return source[start:end]


def run(source):
    source = source.resolve()
    files = {name:(source/'zone'/name).read_text() for name in
             ('special_attacks.cpp','attack.cpp','mob.cpp','spell_effects.cpp')}
    native = files['special_attacks.cpp']
    stubs = (HERE/'backstab_boundary.cpp').read_text()
    methods = []
    item = source/'common/item_instance.cpp'
    for name in ('GetItemWeaponDamage','GetItemBackstabDamage'):
        methods.append(method(item.read_text(), f'int EQ::ItemInstance::{name}('))
    if 'BackstabPiercer(' in native:
        stubs = '#define STRONGER_HAND 1\n' + stubs
        methods.append(native[native.index('namespace {'):native.index('int Mob::GetBaseSkillDamage(')])
        mob = files['mob.cpp']
        methods.append(mob[mob.rindex('namespace {',0,mob.index('int WeaponElementRoll(')):
                           mob.index('int Mob::ResistElementalWeaponDmg(')])
        methods.append(method(mob,'int64 Mob::ExpectedElementalWeaponDamage('))
    methods.extend(method(native,sig) for sig in (
        'int Mob::GetBaseSkillDamage(', 'void Mob::TryBackstab(', 'void Mob::RogueBackstab(',
        'void Mob::DoSpecialAttackDamage(', 'void Mob::DoMeleeSkillAttackDmg(',
        'void Client::OPCombatAbility('))
    if 'void Mob::DoSpecialAttackDamageWithBase(' in native:
        methods.append(method(native,'void Mob::DoSpecialAttackDamageWithBase('))
    methods.extend([method(files['attack.cpp'],'int64 Mob::GetWeaponDamage(Mob *against, const EQ::ItemInstance'),
                    method(files['mob.cpp'],'bool Mob::CanThisClassDualWield('),
                    method(files['mob.cpp'],'int Mob::ResistElementalWeaponDmg('),
                    method(files['mob.cpp'],'int Mob::CheckBaneDamage(')])
    spell = files['spell_effects.cpp']
    dispatch = spell[spell.index('case SpellEffect::SkillAttack:'):spell.index('case SpellEffect::WakeTheDead:',spell.index('case SpellEffect::SkillAttack:'))]
    methods.append('void Mob::SpellSkillAttack(Mob* caster,int spell_id){int i=0;switch(SpellEffect::SkillAttack){'+dispatch+'}}')
    stubs = stubs.replace('// NATIVE METHODS','\n'.join(methods))
    with tempfile.TemporaryDirectory(prefix='nightcap-backstab-') as tmp:
        temp = Path(tmp)
        (temp/'test.cpp').write_text(stubs)
        if os.name=='nt':
            (temp/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars64.bat" >nul || exit /b 1\ncl /nologo /EHsc /O2 /std:c++17 test.cpp /Fe:test.exe\n')
            subprocess.run(['cmd','/d','/c',str(temp/'build.cmd')],cwd=temp,check=True)
            exe=temp/'test.exe'
        else:
            exe=temp/'test'
            subprocess.run(['c++','-std=c++17','-O2',str(temp/'test.cpp'),'-o',str(exe)],check=True)
        data=subprocess.check_output([str(exe)],text=True)
    rows=[json.loads(line) for line in data.splitlines()]
    validate(rows,'BackstabPiercer(' in native)
    inputs=[source/'zone'/name for name in files]+[item]
    return dict(source_sha256={p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                samples=rows)


def validate(rows, candidate):
    by_name={r['case']:r for r in rows}
    assert len(rows)==len(by_name)==57
    # Fixed one-roll damage boundary passes the submitted native base to the damage sink.
    pairs={
        'standard':(42,108),'swapped':(108,108),'tie':(108,108),'only_main':(42,42),
        'only_off':(0,108),'slash_main':(0,108),'slash_off':(42,42),'neither':(0,0),'empty':(0,0),
        'augmented':(114,114),'weapon_fallback':(42,138),'explicit_ignores_weapon_aug':(42,108),
        'required_level':(42,42),'class_lock':(42,42),'race_lock':(42,42),'no_dual_skill':(42,42),
        'offhand_slot_lock':(42,42),'twohanded_main':(0,0),'nonmagical_main':(0,108),
        'nonmagical_off':(42,42),'none_magical':(0,0),'magic_buff':(42,108),'bane_match':(138,138),
        'bane_mismatch':(42,108),'bane_required':(138,138),'bane_missing':(0,0),'bane_ignored':(42,108),
        'immune':(0,0),'invulnerable':(0,0),'element_low_resist':(222,222),'element_high_resist':(42,108),
        'element_immune':(222,108),'element_ignored':(42,108),'element_one_roll':(222,288),
        'element_uprated_low_roll':(42,42),'held_2':(0,108),'held_3':(0,108),'no_rogue':(0,0),
        'front':(0,0),'chaotic':(50,50),'chaotic_double':(92,158),'seized':(42,108),
        'triple_success':(126,324),'triple_lost_double':(42,108),'triple_lost_roll':(84,216),
        'triple_death1':(42,108),'triple_death2':(84,216),'miss':(0,0),'spell_standard':(37,37),
        'spell_swapped':(37,37),'spell_empty':(37,37),'bot_primary':(18,18),'bot_only_off':(0,0),
        'npc_unarmed':(33,33),'resolved_zero':(0,0),'generic_zero':(42,108),'generic_fixed':(31,31),
    }
    assert pairs.keys()==by_name.keys()
    for name,(old,new) in pairs.items():
        r=by_name[name]
        assert r['controlled_damage']==(new if candidate else old),r
        hits=r['hits_submitted']
        if name.startswith('spell_'):
            assert hits==1 and r['animations']==r['attempt_procs']==r['success_procs']==0
        elif name.startswith('generic_'):
            assert hits==r['attempt_procs']==r['success_procs']==1 and r['animations']==0
        else:
            assert r['animations']==r['attempt_procs']==hits,r
            assert r['success_procs']==(0 if name in ('miss','resolved_zero') else hits),r
        assert r['cast_on_skill']==hits
        assert r['front_fallbacks']==int(name=='front')
        assert r['timer_starts']<=1
        if candidate:
            assert r['element_rolls']<=hits,r
    assert by_name['tie']['candidate_weapon']==101
    assert by_name['triple_success']['hits_submitted']==3
    assert by_name['triple_death1']['hits_submitted']==1 and by_name['triple_death2']['hits_submitted']==2
    assert by_name['miss']['hits_submitted']==1 and by_name['chaotic']['last_base']==(108 if candidate else 42)
    if candidate:
        assert by_name['standard']['candidate_weapon']==by_name['swapped']['candidate_weapon']==102
        assert by_name['element_uprated_low_roll']['candidate_weapon']==101
        assert by_name['resolved_zero']['candidate_weapon']==102
        assert by_name['resolved_zero']['hits_submitted']==1
        assert by_name['resolved_zero']['element_rolls']==by_name['resolved_zero']['last_base']==0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'server-mods/code')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.write_text(json.dumps(run(args.source),indent=2)+'\n')

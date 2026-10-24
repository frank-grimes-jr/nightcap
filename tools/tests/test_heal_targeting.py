"""Compile the actual heal classifiers and pre-validation cast paths in isolation.

Run from tools/tests: python test_heal_targeting.py
Requires a C++17 compiler (CXX, or g++ on PATH). No database or server mutation.
The fixture replaces entities/timers, not target-selection or heal logic.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[2]


def function(source, signature):
    assert source.count(signature) == 1, signature
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for end in range(opening, len(source)):
        depth += (source[end] == "{") - (source[end] == "}")
        if depth == 0:
            return source[start:end + 1]
    raise AssertionError(f"Unclosed function: {signature}")


def harness(source, common):
    names = [
        "IsValidSpell", "IsGroupSpell", "IsEffectInSpell", "GetSpellTriggerSpellID",
        "IsPercentalHealSpell", "IsBeneficialSpell", "IsDetrimentalSpell",
        "IsHealOverTimeSpell", "IsCompleteHealSpell", "IsFastHealSpell",
        "IsVeryFastHealSpell", "IsRegularSingleTargetHealSpell", "IsRegularPetHealSpell",
        "IsRegularGroupHealSpell", "IsGroupCompleteHealSpell", "IsGroupHealOverTimeSpell",
        "IsAnyHealSpell",
    ]
    classifiers = []
    for name in names:
        signature = re.search(r"(?:bool|uint16) " + name + r"\([^\n]+", common).group()
        classifiers.append(function(common, signature.split("{")[0].rstrip()))
    native = "\n".join(classifiers)
    declarations = "\n".join(f.split("{")[0].strip() + ";" for f in classifiers)
    effects = sorted(set(re.findall(r"SpellEffect::(\w+)", native)) | {"Blank"})
    targets = sorted(set(re.findall(r"\bST_\w+", native + source)))
    sais = sorted(set(re.findall(r"\bSAI_\w+", native)))
    helper = ""
    if "static Mob* ResolvePlayerHealTarget(" in source:
        helper = function(source, "static Mob* ResolvePlayerHealTarget(")
    cast = function(source, "bool Mob::CastSpell(").split("{", 1)[1]
    cast = cast[:cast.index("\t//It appears that the Sanctuary")]
    finish = function(source, "bool Mob::SpellFinished(").split("{", 1)[1]
    finish = finish[:finish.index("\t//Death Touch")]
    return r'''
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
using uint16=uint16_t; using uint32=uint32_t;
using int32=int32_t;
enum class CastingSlot {AltAbility};
namespace Chat {constexpr int SpellFailure=0;}
namespace NightcapTHJ {
int ResourcePercent(int){return 0;} int PercentMana(int,int){return 0;} bool ManaBurn(int){return false;}
}
constexpr int EFFECT_COUNT=12, SPDAT_RECORDS=3000;
constexpr int SPELL_COMPLETE_HEAL=13, SPELL_MINOR_HEALING=200, SPELL_NATURES_RECOVERY=2520;
constexpr int MAX_FAST_HEAL_CASTING_TIME=2000, MAX_VERY_FAST_HEAL_CASTING_TIME=1000;
constexpr int BENEFICIAL_EFFECT=1, DETRIMENTAL_EFFECT=0, RESIST_MAGIC=1;
namespace EQ { namespace skills { constexpr int SkillDivination=1; } }
''' + "namespace SpellEffect { enum { " + ",".join(effects) + " }; }\n" + \
        "enum { " + ",".join(targets) + " };\n" + \
        "enum { SAI_Unused, " + ",".join(sais) + " };\n" + r'''
struct Spell {
    char player_1[2]={'x',0};
    int target_type=ST_Target, good_effect=1, cast_time=3000, buff_duration=0;
    int resist_type=0, spell_affect_index=0, skill=0;
    int effect_id[EFFECT_COUNT], base_value[EFFECT_COUNT]{}, limit_value[EFFECT_COUNT]{};
    Spell() { std::fill_n(effect_id, EFFECT_COUNT, SpellEffect::Blank); }
} spells[SPDAT_RECORDS];
''' + declarations + "\n" + native + r'''
bool implied=false, reject_npc=false;
#define RuleB(category,name) implied
#define LogSpells(...)
struct Timer { bool Enabled() { return false; } };
struct Mob {
    uint16 id; bool client; Mob* target=nullptr; Mob* owner=nullptr;
    int casting_spell_id=0; bool delaytimer=false, casting_spell_checks=false;
    Timer spellend_timer; Mob* checked=nullptr;
    bool IsClient() { return client; }
    bool IsNPC() { return !client; }
    bool IsOfClientBot() { return client; }
    bool HasOwner() { return owner; }
    Mob* GetOwner() { return owner; }
    Mob* GetNightcapPetOwner() { return !client && owner && owner->client ? owner : nullptr; }
    Mob* GetTarget() { return target; }
    uint16 GetID() { return id; }
    int GetMaxMana(){return 100;} int GetMana(){return 100;} bool FindBuff(int){return false;}
    template<class...T>void Message(int,const char*,T...){}
    void ZeroCastingVars() { casting_spell_id=0; }
    void StopCastSpell(int,bool) {}
    bool DoCastingChecksOnCaster(int,int) { return true; }
    bool DoCastingChecksZoneRestrictions(bool,int) { return true; }
    bool DoCastingChecksOnTarget(bool,int,Mob* mob) {
        checked=mob;
        return mob && !(reject_npc && mob->IsNPC());
    }
    bool CastTarget(uint16 spell_id,uint16& target_id);
    bool FinishTarget(uint16 spell_id,Mob*& spell_target);
};
struct Entities {
    Mob* entries[8]{};
    Mob* GetMobID(uint16 id) { return id<8 ? entries[id] : nullptr; }
} entity_list;
Mob* rescue_target=nullptr;
namespace NightcapDungeon {bool HighkeepHealTarget(Mob* mob){return mob==rescue_target;}}
''' + helper + r'''
bool Mob::CastTarget(uint16 spell_id,uint16& target_id) {
    int slot=0, cast_time=-1, aa_id=0; uint32 item_slot=UINT32_MAX;
''' + cast + "return true;\n}\n" + r'''
bool Mob::FinishTarget(uint16 spell_id,Mob*& spell_target) {
    bool isproc=false; CastingSlot slot=CastingSlot::AltAbility;
''' + finish + "return true;\n}\n" + r'''
int checks=0, failures=0;
void check(bool result,const char* label) {
    ++checks;
    if (!result) { ++failures; std::cerr << "FAIL: " << label << '\n'; }
}
int main() {
    Mob caster{1,true}, npc{2,false}, player{3,true}, pet{4,false}, healer{5,false};
    pet.owner=&caster; npc.target=&player; caster.target=&npc;
    for (auto mob : {&caster,&npc,&player,&pet,&healer}) entity_list.entries[mob->id]=mob;
    auto spell=[](int id,int effect,int base,int type=ST_Target) {
        spells[id]=Spell{};
        spells[id].effect_id[0]=effect; spells[id].base_value[0]=base;
        spells[id].target_type=type;
    };
    spell(200,SpellEffect::CurrentHP,10);
    spell(201,SpellEffect::CurrentHP,100); // normal heal
    spell(202,SpellEffect::CurrentHPOnce,100); spells[202].cast_time=0; // instant AA/item
    spell(203,SpellEffect::HealOverTime,20); spells[203].buff_duration=5;
    spell(13,SpellEffect::CompleteHeal,7500);
    spell(204,SpellEffect::PercentalHeal,50);
    spell(205,SpellEffect::CurrentHP,100,ST_Group);
    spell(206,SpellEffect::SpellTrigger,100); spells[206].limit_value[0]=201;
    spell(207,SpellEffect::CurrentHP,-100); spells[207].good_effect=0; // damage
    spell(208,SpellEffect::Blank,0); // non-healing buff
    spell(209,SpellEffect::CurrentHP,100,ST_Pet);
    spell(210,SpellEffect::CurrentHP,100,ST_SummonedPet);
    spell(211,SpellEffect::CurrentHP,-100,ST_Tap); spells[211].good_effect=0;
    spell(212,SpellEffect::HealOverTime,20,ST_Group); spells[212].buff_duration=5;
    spell(213,SpellEffect::CurrentHPOnce,100); spells[213].cast_time=1500;
    spell(214,SpellEffect::CurrentHP,100,ST_AETarget);
    spell(215,SpellEffect::CurrentHP,100,ST_GroupNoPets);
    spell(216,SpellEffect::CurrentHP,100,ST_GroupClientAndPet);
    spell(217,SpellEffect::Blank,0);
    spells[217].effect_id[11]=SpellEffect::CurrentHPOnce; spells[217].base_value[11]=100;
    spell(218,SpellEffect::CurrentHP,10); spells[218].buff_duration=10; // regeneration
    spell(219,SpellEffect::HealOverTime,20,ST_TargetsTarget);
    spell(220,SpellEffect::HealOverTime,20,ST_Corpse);
    spell(221,SpellEffect::HealOverTime,20,ST_Animal);
    spell(222,SpellEffect::SpellTrigger,100); spells[222].limit_value[0]=202; // triggered HPOnce
    spell(223,SpellEffect::SpellTrigger,100); spells[223].limit_value[0]=204; // triggered percent heal
    for (bool implied_on : {false,true}) {
        implied=implied_on;
        for (int id : {200,201,202,203,13,204,205,206,212,213,214,215,216,217,218,222,223}) {
            uint16 target_id=npc.id;
            check(caster.CastTarget(id,target_id) && target_id==caster.id && caster.checked==&caster,
                  "NPC-targeted heal must validate and cast on caster before implied targeting");
            Mob* target=&npc;
            check(caster.FinishTarget(id,target) && target==&caster,
                  "instant/triggered heal must resolve to caster at spell finish");
        }
    }
    implied=false;
    npc.target=nullptr;
    uint16 idle_target=npc.id;
    check(caster.CastTarget(201,idle_target) && idle_target==caster.id, "idle/friendly NPC defaults to caster");
    npc.target=&player;
    for (auto target : {&caster,&player}) {
        uint16 id=target->id;
        check(caster.CastTarget(201,id) && id==target->id, "player target retained");
        auto finish_target=target;
        check(caster.FinishTarget(201,finish_target) && finish_target==target, "finish player retained");
    }
    uint16 pet_id=pet.id;
    check(caster.CastTarget(201,pet_id) && pet_id==pet.id, "ordinary heal retains owned pet recipient");
    for (int spell_id : {207,208,209,210,211,219,220,221}) {
        uint16 target_id=npc.id;
        check(caster.CastTarget(spell_id,target_id) && target_id==npc.id,
              "damage, buffs, lifetaps and pet-only spells retain native targeting");
        Mob* target=&npc;
        check(caster.FinishTarget(spell_id,target) && target==&npc, "finish preserves non-applicable spells");
    }
    uint16 target_id=npc.id;
    check(healer.CastTarget(201,target_id) && target_id==npc.id, "NPC healer can still heal NPC ally");
    Mob* target=&npc;
    check(healer.FinishTarget(201,target) && target==&npc, "finish preserves NPC AI healing");
    reject_npc=true; target_id=npc.id;
    check(caster.CastTarget(201,target_id) && target_id==caster.id, "redirect before PC-only target validation");
    reject_npc=false;
    target_id=npc.id;
    check(caster.CastTarget(201,target_id), "start timed heal");
    caster.target=&player;
    target=entity_list.GetMobID(target_id);
    check(caster.FinishTarget(201,target) && target==&caster, "retargeting during cast retains chosen recipient");
    caster.target=&npc;
    check(caster.target==&npc, "casting does not change selected combat target");
    target_id=0;
    check(!caster.CastTarget(201,target_id), "no-target behavior unchanged");
    target=&npc;
    check(!caster.FinishTarget(UINT16_MAX,target) && target==&npc, "invalid spell is safe");
    target=nullptr;
    check(caster.FinishTarget(201,target) && !target, "null target is safe");
    rescue_target=&npc;
    for (bool implied_on : {false,true}) {
        implied=implied_on;
        for (int id : {200,201,202,203,13,204,206,213,217,218,222,223}) {
            target_id=npc.id; target=&npc;
            check(caster.CastTarget(id,target_id) && target_id==npc.id && caster.checked==&npc,
                  "rescue escort retains direct healing recipient at cast start");
            check(caster.FinishTarget(id,target) && target==&npc,
                  "rescue escort retains direct healing recipient at cast finish");
        }
    }
    reject_npc=true; target_id=npc.id;
    check(!caster.CastTarget(201,target_id), "rescue exception still runs native target validation");
    reject_npc=false; rescue_target=nullptr; implied=false; target_id=npc.id;
    check(caster.CastTarget(201,target_id) && target_id==caster.id, "public/unmanaged Osargen keeps normal NPC heal redirection");
    std::cout << checks-failures << '/' << checks << " heal-targeting checks passed\n";
    return failures ? 1 : 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "server-mods/code/zone/spells.cpp")
    parser.add_argument("--common", type=Path, default=ROOT / "akk-stack/code/common/spdat.cpp")
    parser.add_argument("--container", help="Compile/run with g++ in this existing Docker container")
    args = parser.parse_args()
    source = args.source.read_text(encoding="utf-8")
    # Verify these are the real pre-validation entry paths, not disconnected helpers.
    finished = function(source, "bool Mob::SpellFinished(")
    assert finished.index("//Death Touch") < finished.index("DetermineSpellTargets(")
    assert finished.index("DetermineSpellTargets(") < finished.index("DoCastingChecksOnTarget(")
    generated = harness(source, args.common.read_text(encoding="utf-8"))
    if args.container:
        binary = "/tmp/nightcap-heal-" + uuid.uuid4().hex
        try:
            subprocess.run(["docker", "exec", "-i", args.container, "g++", "-std=c++17",
                            "-O0", "-x", "c++", "-o", binary, "-"], input=generated, text=True, check=True)
            subprocess.run(["docker", "exec", args.container, binary], check=True)
        finally:
            subprocess.run(["docker", "exec", args.container, "rm", "-f", binary], check=True)
        return
    with tempfile.TemporaryDirectory(prefix="nightcap-heal-") as directory:
        cpp = Path(directory) / "heal.cpp"
        binary = Path(directory) / "heal.exe"
        cpp.write_text(generated, encoding="utf-8")
        subprocess.run([os.environ.get("CXX", "g++"), "-std=c++17", "-O0", str(cpp), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    main()

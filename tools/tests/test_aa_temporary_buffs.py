"""Execute the native AA buff classifier and duration policy in a small fixture.

The real methods are extracted from the tracked overlay. These tests cover policy,
AA graph reloads, and BuffProcess countdown/fade decisions with effect and packet
dependencies stubbed; they do not certify zone networking or in-game acceptance.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ZONE = ROOT / "server-mods/code/zone"


def function(source, signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth, end = 1, brace + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


def policy_helpers(source):
    # The baseline has no classifier. Compile its actual policy so RED comes
    # from the incorrect duration, rather than a missing-symbol compilation.
    return "\n".join(function(source, signature) for signature in (
        "static int AABuffTriggerSpell(",
        "static bool IsAARelatedBuffSpell(",
    ) if signature in source)


AA_FIXTURE = r'''
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <queue>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
using uint16 = uint16_t;
using uint32 = uint32_t;
using int32 = int32_t;
constexpr int PERMANENT_BUFF_DURATION = -1000;
constexpr int DF_Permanent = 50;
constexpr int DF_Aura = 51;
constexpr int SPELL_UNKNOWN = 65535;
constexpr int EFFECT_COUNT = 12;
constexpr int SPDAT_RECORDS = 65536;
constexpr int SPELL_TOUCH_OF_THE_DIVINE = 4789;
namespace SpellEffect {
enum {
 CurrentHP = 0, ArmorClass = 1, WeaponProc = 85, RangedProc = 201, DivineSave = 232,
 SkillAttackProc = 288, CastOnFadeEffect = 289, DefensiveProc = 323,
 CastOnRuneFadeEffect = 333, BardAEDot = 334, PercentXPIncrease = 337, TriggerOnCast = 339,
 SpellTrigger = 340, ProcOnKillShot = 360, SpellOnDeath = 361, ProcOnSpellKillShot = 365,
 CastOnFadeEffectAlways = 373, ApplyEffect = 374, CastOnFadeEffectNPC = 377,
 SympatheticProc = 383, CastOnCurer = 386, CastOnCure = 387,
 CastonNumHitFade = 406, CastonFocusEffect = 407, AddMeleeProc = 419,
 SkillProcAttempt = 427, SkillProcSuccess = 429, TriggerOnReqTarget = 442,
 TriggerOnReqCaster = 443, TriggerMeleeThreshold = 453,
 TriggerSpellThreshold = 454, Chance_Best_in_Spell_Grp = 469,
 Trigger_Best_in_Spell_Grp = 470, Trigger_Spell_Non_Item = 475,
 Weapon_Stance = 476, Fc_Cast_Spell_On_Land = 481
};
}
struct Spell {
 int good_effect = 1, buff_duration_formula = 1, buff_duration = 10;
 int effect_id[EFFECT_COUNT] = {}, base_value[EFFECT_COUNT] = {};
 int limit_value[EFFECT_COUNT] = {}, max_value[EFFECT_COUNT] = {};
 int recourse_link = 0, short_buff_box = 0, spell_group = 0;
 bool discipline = false, suspendable = true;
};
Spell spells[65536];
bool IsValidSpell(uint16 id) { return id > 0 && id < SPELL_UNKNOWN; }
bool IsBeneficialSpell(uint16 id) { return IsValidSpell(id) && spells[id].good_effect; }
bool IsDetrimentalSpell(uint16 id) { return IsValidSpell(id) && !spells[id].good_effect; }
bool IsDisciplineBuff(uint16 id) { return IsValidSpell(id) && spells[id].discipline; }
bool IsSuspendableSpell(uint16 id) { return IsValidSpell(id) && spells[id].suspendable; }
bool IsEffectInSpell(uint16 id, int spa) { return IsValidSpell(id) && std::find(std::begin(spells[id].effect_id), std::end(spells[id].effect_id), spa) != std::end(spells[id].effect_id); }
namespace AA {
struct RankEffect { int effect_id = 0, base_value = 0, limit_value = 0; };
struct Rank { int spell = SPELL_UNKNOWN; std::vector<RankEffect> effects; };
}
struct Zone {
 std::unordered_map<int, std::unique_ptr<AA::Rank>> aa_ranks;
 bool suspended = false;
 bool BuffTimersSuspended() const { return suspended; }
};
Zone fixture_zone;
Zone *zone = &fixture_zone;
AA::Rank& rank(int id, int spell = SPELL_UNKNOWN) {
 auto value = std::make_unique<AA::Rank>();
 value->spell = spell;
 auto *result = value.get();
 fixture_zone.aa_ranks[id] = std::move(value);
 return *result;
}
void effect(int spell, int spa, int base, int limit, int maximum = 0) {
 spells[spell].effect_id[0] = spa;
 spells[spell].base_value[0] = base;
 spells[spell].limit_value[0] = limit;
 spells[spell].max_value[0] = maximum;
}
'''

MOB_FIXTURE = r'''
#define RuleB(group,key) false
#define LogSpells(...) ((void)0)
namespace EQ { namespace versions {
constexpr int maskSoFAndLater = 1;
enum class ClientVersion { UF, RoF2 };
} }
struct Buff {
 uint16 spellid = SPELL_UNKNOWN;
 int ticsremaining = 0, casterid = 0, hit_number = 0;
 bool UpdateClient = false;
};
struct Mob;
struct EntityList { Mob *GetMob(int) { return nullptr; } } entity_list;
struct Mob {
 bool player = true, pet = false;
 Buff buffs[2];
 int fade_count = 0, tick_count = 0;
 bool IsClient() const { return player; }
 bool IsPetOwnerClient() const { return pet; }
 int GetMaxTotalSlots() const { return 2; }
 void DoBuffTic(const Buff &, int, Mob *) { ++tick_count; }
 void BuffFadeBySlot(int slot) { buffs[slot].spellid = SPELL_UNKNOWN; ++fade_count; }
 Mob *CastToClient() { return this; }
 int ClientVersionBit() const { return EQ::versions::maskSoFAndLater; }
 EQ::versions::ClientVersion ClientVersion() const { return EQ::versions::ClientVersion::RoF2; }
 void SendBuffDurationPacket(const Buff &, int) {}
 void SendBuffNumHitPacket(const Buff &, int) {}
 void BuffProcess();
 int32 GetBuffDurationForTarget(uint16 spell_id, int32 duration) const;
};
void expect(int actual, int expected, const char *message) {
 if (actual != expected) throw std::runtime_error(std::string(message) +
  ": expected " + std::to_string(expected) + ", got " + std::to_string(actual));
}
'''

CONTROLS = r'''
int main(int argc, char **argv) {
 try {
  if (argc != 2) throw std::runtime_error("one control group required");
  std::string group = argv[1];
  Mob player, pet, npc; pet.player = false; pet.pet = true; npc.player = false;
  if (group == "xp_boost") {
   rank(999,999);
   for (int slot=0; slot<EFFECT_COUNT; ++slot) {
    spells[21030] = Spell{};
    spells[21030].effect_id[slot] = SpellEffect::PercentXPIncrease;
    for (auto target : {&player,&pet}) {
     for (int old : {-1000,-1}) {
      int ticks=target->GetBuffDurationForTarget(21030,old);
      expect(ticks,1,"stale XP boost retained permanence");
      target->buffs[0]={21030,ticks};
      fixture_zone.suspended=true; target->BuffProcess();
      expect(target->buffs[0].ticsremaining,1,"zone suspension changed");
      fixture_zone.suspended=false; target->BuffProcess();
      expect(target->buffs[0].ticsremaining,0,"minimum countdown did not tick");
      target->BuffProcess();
      expect(target->buffs[0].spellid,SPELL_UNKNOWN,"stale XP boost did not fade");
     }
     for (int ticks : {0,1,20,2400,3600,-4})
      expect(target->GetBuffDurationForTarget(21030,ticks),ticks,"XP remaining duration changed");
    }
    expect(npc.GetBuffDurationForTarget(21030,-1000),-1000,"NPC duration changed");
   }
   for (int formula : {DF_Permanent,DF_Aura}) {
    spells[21030].buff_duration_formula=formula;
    expect(player.GetBuffDurationForTarget(21030,-1),-1,"native permanent formula changed");
   }
   spells[21030]=Spell{};
   expect(player.GetBuffDurationForTarget(21030,2400),PERMANENT_BUFF_DURATION,"ordinary buff lost permanence");
  }
  else if (group == "rabid") {
   rank(153,2750);effect(2750,SpellEffect::ApplyEffect,100,30709);
   for (auto id : {2750,30709}) {
    spells[id].buff_duration_formula=DF_Permanent;
    expect(player.GetBuffDurationForTarget(id,20),PERMANENT_BUFF_DURATION,"Rabid restored timer not normalized");
    expect(player.GetBuffDurationForTarget(id,-1),PERMANENT_BUFF_DURATION,"Rabid client sentinel not normalized");
    expect(player.GetBuffDurationForTarget(id,0),0,"instant spell became buff");
   }
   spells[2750].buff_duration_formula=4;
   expect(player.GetBuffDurationForTarget(2750,20),20,"unpaired old data became permanent");
  } else if (group == "direct") {
   rank(1, 101);
   expect(player.GetBuffDurationForTarget(101, 18), 18, "activated AA lost focused duration");
   expect(pet.GetBuffDurationForTarget(101, 18), 18, "activated pet AA became permanent");
  } else if (group == "passive") {
   rank(1).effects.push_back({SpellEffect::ProcOnKillShot, 100, 102});
   expect(player.GetBuffDurationForTarget(102, 6), 6, "Killing Spree on-kill AA became permanent");
   expect(pet.GetBuffDurationForTarget(102, 6), 6, "passive AA proc on owned pet became permanent");
   expect(player.GetBuffDurationForTarget(100, 6), PERMANENT_BUFF_DURATION, "proc chance interpreted as spell ID");
  } else if (group == "killing_spree_local_client") {
   // Local RoF2 spells_us.txt datum inspected 2026-10-15, not a production DB snapshot.
   // Spell 11023 Killing Spree has duration formula 2, cap 5. AA rank effect is modeled.
   constexpr int killing_spree = 11023;
   spells[killing_spree].buff_duration_formula = 2;
   spells[killing_spree].buff_duration = 5;
   rank(4739).effects.push_back({SpellEffect::ProcOnKillShot, 100, killing_spree});
   const int native = CalcBuffDuration_formula(50, spells[killing_spree].buff_duration_formula,
    spells[killing_spree].buff_duration);
   expect(native, 5, "local-client Killing Spree native duration changed");
   expect(player.GetBuffDurationForTarget(killing_spree, native), native, "Killing Spree lost native five-tick duration");
   expect(pet.GetBuffDurationForTarget(killing_spree, native), native, "pet Killing Spree lost native duration");
  } else if (group.rfind("followon_", 0) == 0) {
   const int spa = std::stoi(group.substr(9));
   rank(1, 182); effect(182, spa, 180, 181);
   spells[180].recourse_link = 183;
   expect(player.GetBuffDurationForTarget(180, 4), 4, "cure/num-hit fade follow-on became permanent");
   expect(player.GetBuffDurationForTarget(183, 4), 4, "cure/num-hit fade recourse became permanent");
   expect(player.GetBuffDurationForTarget(181, 4), PERMANENT_BUFF_DURATION, "cure/num-hit fade limit treated as spell");
  } else if (group == "spell_killshot") {
   rank(1, 182); effect(182, SpellEffect::ProcOnSpellKillShot, 181, 180);
   spells[182].good_effect = 0;
   spells[180].recourse_link = 183;
   expect(player.GetBuffDurationForTarget(180, 4), 4, "spell-kill proc beneficial child became permanent");
   expect(player.GetBuffDurationForTarget(183, 4), 4, "spell-kill proc recourse became permanent");
   expect(player.GetBuffDurationForTarget(181, 4), PERMANENT_BUFF_DURATION, "spell-kill proc chance treated as spell");
   fixture_zone.aa_ranks.clear();
   rank(1).effects.push_back({SpellEffect::ProcOnSpellKillShot, 181, 180});
   expect(player.GetBuffDurationForTarget(180, 4), PERMANENT_BUFF_DURATION, "unimplemented AA-form spell-kill effect classified as spell link");
  } else if (group == "graph") {
   rank(1, 110);
   spells[110].recourse_link = 111;
   effect(111, SpellEffect::SpellTrigger, 100, 112);
   spells[112].recourse_link = 110;
   expect(player.GetBuffDurationForTarget(112, 12), 12, "nested AA recourse/trigger child became permanent");
   expect(player.GetBuffDurationForTarget(120, 12), PERMANENT_BUFF_DURATION, "cyclic AA graph swallowed unrelated blessing");
  } else if (group == "nonlinks") {
   auto &aa = rank(1, 130);
   aa.effects.push_back({SpellEffect::ArmorClass, 131, 132});
   effect(130, SpellEffect::ArmorClass, 133, 134, 135);
   for (int id : {131, 132, 133, 134, 135})
    expect(player.GetBuffDurationForTarget(id, 18), PERMANENT_BUFF_DURATION, "ordinary numeric stat interpreted as spell link");
   aa.effects.push_back({SpellEffect::WeaponProc, 70000, 0});
   expect(player.GetBuffDurationForTarget(4464, 18), PERMANENT_BUFF_DURATION, "out-of-range spell ID wrapped into real blessing");
  } else if (group == "reload") {
   auto &aa = rank(1, 140);
   expect(player.GetBuffDurationForTarget(140, 8), 8, "initial AA catalog not read");
   aa.spell = 141;
   expect(player.GetBuffDurationForTarget(141, 8), 8, "same-size AA catalog reload retained stale classification");
   expect(player.GetBuffDurationForTarget(140, 8), PERMANENT_BUFF_DURATION, "removed AA root retained stale classification");
   aa.effects.push_back({SpellEffect::ProcOnKillShot, 100, 142});
   expect(player.GetBuffDurationForTarget(142, 8), 8, "passive effect reload retained stale classification");
   spells[141].recourse_link = 143;
   expect(player.GetBuffDurationForTarget(143, 8), 8, "spell recourse reload retained stale classification");
  } else if (group == "sentinels") {
   rank(1, 150); spells[151].discipline = true; spells[152].short_buff_box = 1;
   for (int id : {150, 151, 152}) {
    for (int old : {-1000, -1}) {
     expect(player.GetBuffDurationForTarget(id, old), 1, "legacy temporary buff did not receive minimum countdown");
     expect(pet.GetBuffDurationForTarget(id, old), 1, "legacy pet temporary buff did not receive minimum countdown");
    }
    for (int duration : {1, 18, 999999, 1000000, 1000001})
     expect(player.GetBuffDurationForTarget(id, duration), duration, "positive native or focused duration altered");
    for (int formula : {50, 51}) {
     spells[id].buff_duration_formula = formula;
     expect(player.GetBuffDurationForTarget(id, -1), -1, "genuine native permanent formula changed");
     expect(player.GetBuffDurationForTarget(id, -1000), -1000, "genuine native permanent sentinel changed");
    }
   }
  } else if (group == "boundaries") {
   rank(1, 160); spells[161].discipline = true; spells[162].short_buff_box = 1;
   for (int id : {160, 161, 162}) {
    expect(player.GetBuffDurationForTarget(id, 20), 20, "temporary category promoted to permanent");
    expect(player.GetBuffDurationForTarget(id, 0), 0, "instant AA became a buff");
    expect(player.GetBuffDurationForTarget(id, -4), -4, "aura expiry changed");
    expect(npc.GetBuffDurationForTarget(id, -1000), -1000, "NPC lifetime changed");
    spells[id].good_effect = 0;
    expect(player.GetBuffDurationForTarget(id, -1000), -1000, "detrimental lifetime changed");
   }
   for (int old : {20, -1000, -1, 1000000}) {
    expect(player.GetBuffDurationForTarget(163, old), PERMANENT_BUFF_DURATION, "ordinary blessing lost permanence");
    expect(pet.GetBuffDurationForTarget(163, old), PERMANENT_BUFF_DURATION, "ordinary pet blessing lost permanence");
   }
   expect(player.GetBuffDurationForTarget(SPELL_UNKNOWN, 20), 20, "invalid spell changed");
   expect(player.GetBuffDurationForTarget(42801, -1000), 3, "Epic 0.5 guard changed");
   expect(player.GetBuffDurationForTarget(42805, 18), 3, "Epic 0.5 maximum changed");
   expect(player.GetBuffDurationForTarget(42801, 0), 0, "Epic 0.5 instant changed");
  } else if (group == "mapping") {
   const int base_spas[] = {SpellEffect::WeaponProc, SpellEffect::AddMeleeProc,
    SpellEffect::RangedProc, SpellEffect::DefensiveProc, SpellEffect::SkillProcAttempt,
    SpellEffect::SkillProcSuccess, SpellEffect::Weapon_Stance, SpellEffect::CastOnFadeEffect,
    SpellEffect::CastOnFadeEffectNPC, SpellEffect::CastOnFadeEffectAlways,
    SpellEffect::CastOnRuneFadeEffect, SpellEffect::CastOnCurer, SpellEffect::CastOnCure,
    SpellEffect::CastonNumHitFade, SpellEffect::TriggerOnReqTarget,
    SpellEffect::TriggerOnReqCaster, SpellEffect::TriggerMeleeThreshold,
    SpellEffect::TriggerSpellThreshold, SpellEffect::CastonFocusEffect};
   const int limit_spas[] = {SpellEffect::ProcOnKillShot, SpellEffect::TriggerOnCast,
    SpellEffect::SpellTrigger, SpellEffect::ApplyEffect, SpellEffect::Trigger_Spell_Non_Item,
    SpellEffect::ProcOnSpellKillShot,
    SpellEffect::Fc_Cast_Spell_On_Land, SpellEffect::SympatheticProc, SpellEffect::DivineSave};
   const std::unordered_set<int> aa_base_spas = {SpellEffect::WeaponProc, SpellEffect::AddMeleeProc,
    SpellEffect::RangedProc, SpellEffect::DefensiveProc, SpellEffect::SkillProcAttempt,
    SpellEffect::SkillProcSuccess, SpellEffect::Weapon_Stance};
   const std::unordered_set<int> aa_limit_spas = {SpellEffect::ProcOnKillShot,
    SpellEffect::TriggerOnCast, SpellEffect::Fc_Cast_Spell_On_Land,
    SpellEffect::SympatheticProc, SpellEffect::DivineSave};
   for (int spa : base_spas) {
    fixture_zone.aa_ranks.clear();
    rank(1).effects.push_back({spa, 180, 181});
    expect(player.GetBuffDurationForTarget(180, 4), aa_base_spas.count(spa) ? 4 : PERMANENT_BUFF_DURATION,
     "AA base-value mapping disagrees with implemented AA handler");
    expect(player.GetBuffDurationForTarget(181, 4), PERMANENT_BUFF_DURATION, "AA proc limit treated as spell");
    fixture_zone.aa_ranks.clear(); rank(1, 182); effect(182, spa, 180, 181);
    expect(player.GetBuffDurationForTarget(180, 4), 4, "spell base-value proc link omitted");
    expect(player.GetBuffDurationForTarget(181, 4), PERMANENT_BUFF_DURATION, "spell proc limit treated as spell");
   }
   for (int spa : limit_spas) {
    fixture_zone.aa_ranks.clear();
    rank(1).effects.push_back({spa, 181, 180});
    expect(player.GetBuffDurationForTarget(180, 4), aa_limit_spas.count(spa) ? 4 : PERMANENT_BUFF_DURATION,
     "AA limit-value mapping disagrees with implemented AA handler");
    expect(player.GetBuffDurationForTarget(181, 4), PERMANENT_BUFF_DURATION, "AA trigger chance treated as spell");
    fixture_zone.aa_ranks.clear(); rank(1, 182); effect(182, spa, 181, 180);
    expect(player.GetBuffDurationForTarget(180, 4), 4, "spell limit-value trigger link omitted");
    expect(player.GetBuffDurationForTarget(181, 4), PERMANENT_BUFF_DURATION, "spell trigger chance treated as spell");
   }
   fixture_zone.aa_ranks.clear(); rank(1).effects.push_back({SpellEffect::SpellOnDeath, 180, 181});
   expect(player.GetBuffDurationForTarget(180, 4), 4, "AA SpellOnDeath base-value link omitted");
   expect(player.GetBuffDurationForTarget(181, 4), PERMANENT_BUFF_DURATION, "AA SpellOnDeath used spell-form limit value");
   fixture_zone.aa_ranks.clear(); rank(1, 182); effect(182, SpellEffect::SpellOnDeath, 181, 180);
   expect(player.GetBuffDurationForTarget(180, 4), 4, "spell SpellOnDeath limit-value link omitted");
   expect(player.GetBuffDurationForTarget(181, 4), PERMANENT_BUFF_DURATION, "spell SpellOnDeath used AA-form base value");
   effect(182, SpellEffect::SkillAttackProc, 181, 183, 180);
   expect(player.GetBuffDurationForTarget(180, 4), 4, "skill attack proc max-value link omitted");
   expect(player.GetBuffDurationForTarget(181, 4), PERMANENT_BUFF_DURATION, "skill attack proc chance treated as spell");
   expect(player.GetBuffDurationForTarget(183, 4), PERMANENT_BUFF_DURATION, "skill attack proc skill treated as spell");
  } else if (group == "spell_groups") {
   rank(1, 190);
   spells[191].spell_group = 700; spells[192].spell_group = 700;
   for (int spa : {SpellEffect::Chance_Best_in_Spell_Grp, SpellEffect::Trigger_Best_in_Spell_Grp}) {
    effect(190, spa, 100, 700);
    expect(player.GetBuffDurationForTarget(191, 8), 8, "triggered spell-group first rank omitted");
    expect(player.GetBuffDurationForTarget(192, 8), 8, "triggered spell-group later rank omitted");
    expect(player.GetBuffDurationForTarget(700, 8), PERMANENT_BUFF_DURATION, "spell group ID mistaken for spell ID");
   }
   effect(190, SpellEffect::DivineSave, 100, 193);
   expect(player.GetBuffDurationForTarget(193, 8), 8, "Divine Save supplemental trigger omitted");
   expect(player.GetBuffDurationForTarget(SPELL_TOUCH_OF_THE_DIVINE, 8), 8, "Divine Save native fixed trigger omitted");
   fixture_zone.aa_ranks.clear(); rank(1).effects.push_back({SpellEffect::DivineSave, 100, 193});
   expect(player.GetBuffDurationForTarget(SPELL_TOUCH_OF_THE_DIVINE, 8), 8, "passive Divine Save fixed trigger omitted");
  } else if (group == "native_expiry") {
   constexpr int killing_spree = 11023;
   spells[killing_spree].buff_duration_formula = 2;
   spells[killing_spree].buff_duration = 5;
   rank(4739).effects.push_back({SpellEffect::ProcOnKillShot, 100, killing_spree});
   for (Mob *target : {&player, &pet}) {
    target->buffs[0] = {killing_spree, target->GetBuffDurationForTarget(killing_spree, -1000)};
    target->buffs[1] = {201, target->GetBuffDurationForTarget(201, 20)};
    target->BuffProcess();
    expect(target->buffs[0].ticsremaining, 0, "saved AA did not count down to standard zero-tick state");
    expect(target->buffs[0].spellid, killing_spree, "saved AA faded before native zero-tick processing");
    expect(target->fade_count, 0, "saved AA unexpectedly faded on first processing callback");
    target->BuffProcess();
    expect(target->buffs[0].spellid, SPELL_UNKNOWN, "saved AA did not fade on second unsuspended callback");
    expect(target->fade_count, 1, "saved AA expiry did not request exactly one fade");
    expect(target->buffs[1].ticsremaining, PERMANENT_BUFF_DURATION, "ordinary blessing counted down");
    expect(target->buffs[1].spellid, 201, "ordinary blessing faded");

    const int native = CalcBuffDuration_formula(50, 2, 5);
    target->buffs[0] = {killing_spree, target->GetBuffDurationForTarget(killing_spree, native)};
    for (int remaining = native - 1; remaining >= 0; --remaining) {
     target->BuffProcess();
     expect(target->buffs[0].ticsremaining, remaining, "native AA countdown changed");
     expect(target->buffs[0].spellid, killing_spree, "native AA faded before zero-tick processing");
    }
    target->BuffProcess();
    expect(target->buffs[0].spellid, SPELL_UNKNOWN, "native AA did not fade after final tick");
    expect(target->fade_count, 2, "native AA countdown requested wrong fade count");
   }
  } else if (group == "native_suspension") {
   rank(1, 210);
   player.buffs[0] = {210, player.GetBuffDurationForTarget(210, -1000)};
   zone->suspended = true;
   for (int call = 0; call < 3; ++call) player.BuffProcess();
   expect(player.buffs[0].ticsremaining, 1, "native zone suspension consumed temporary timer");
   expect(player.fade_count, 0, "suspended AA faded");
   zone->suspended = false;
   player.BuffProcess(); player.BuffProcess();
   expect(player.buffs[0].spellid, SPELL_UNKNOWN, "resumed AA did not expire");
   player.buffs[0] = {210, 1}; spells[210].suspendable = false; zone->suspended = true;
   player.BuffProcess(); player.BuffProcess();
   expect(player.buffs[0].spellid, SPELL_UNKNOWN, "non-suspendable AA ignored native expiry");
   zone->suspended = false;
   spells[210].buff_duration_formula = DF_Permanent; player.buffs[0] = {210, -1};
   spells[211].buff_duration_formula = DF_Aura; player.buffs[1] = {211, -4};
   for (int call = 0; call < 3; ++call) player.BuffProcess();
   expect(player.buffs[0].ticsremaining, -1, "native permanent formula counted down");
   expect(player.buffs[0].spellid, 210, "native permanent formula faded");
   expect(player.buffs[1].ticsremaining, -4, "native aura formula counted down");
   expect(player.buffs[1].spellid, 211, "native aura formula faded");
  } else if (group == "empty_catalog") {
   expect(player.GetBuffDurationForTarget(200, 18), 18, "empty AA catalog promoted buff to permanent");
   expect(pet.GetBuffDurationForTarget(200, 18), 18, "empty AA catalog promoted pet buff to permanent");
   expect(player.GetBuffDurationForTarget(200, -1000), 1, "empty AA catalog retained stale permanence");
   expect(pet.GetBuffDurationForTarget(200, -1000), 1, "empty AA catalog retained stale pet permanence");
  } else if (group == "missing_catalog") {
   zone = nullptr;
   expect(player.GetBuffDurationForTarget(200, 18), 18, "missing AA catalog promoted buff to permanent");
   expect(pet.GetBuffDurationForTarget(200, 18), 18, "missing AA catalog promoted pet buff to permanent");
   expect(player.GetBuffDurationForTarget(200, 0), 0, "missing AA catalog changed instant spell");
   expect(player.GetBuffDurationForTarget(200, -4), -4, "missing AA catalog changed aura expiry");
   expect(npc.GetBuffDurationForTarget(200, 18), 18, "missing AA catalog changed NPC duration");
  } else if (group == "countdown") {
   rank(1).effects.push_back({SpellEffect::ProcOnKillShot, 100, 170});
   int ticks = player.GetBuffDurationForTarget(170, -1000);
   expect(ticks, 1, "saved permanent AA was not normalized");
   --ticks;
   expect(player.GetBuffDurationForTarget(170, ticks), 0, "expired AA refreshed itself");
   ticks = player.GetBuffDurationForTarget(170, 6);
   for (int remaining = 5; remaining >= 0; --remaining) {
    ticks = player.GetBuffDurationForTarget(170, ticks - 1);
    expect(ticks, remaining, "AA countdown refreshed or became permanent");
   }
  } else throw std::runtime_error("unknown control group");
  std::cout << group << " AA duration controls passed\n";
 } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
'''


def compile_native(out, source):
    (out / "test.cpp").write_text(source, encoding="utf-8")
    if os.name == "nt":
        compiler_env = Path("C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat")
        if not compiler_env.is_file():
            raise AssertionError("MSVC x86 build tools missing")
        (out / "build.cmd").write_text(
            '@echo off\ncall "' + str(compiler_env) + '" >nul || exit /b 1\n'
            'cl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\n'
            'exit /b %errorlevel%\n')
        build = subprocess.run(["cmd", "/d", "/c", str(out / "build.cmd")], cwd=out)
        if build.returncode:
            raise AssertionError((out / "build.log").read_text())
        return out / "test.exe"
    executable = out / "test"
    subprocess.run([shutil.which("c++"), "-std=c++17", str(out / "test.cpp"), "-o", str(executable)], check=True)
    return executable


class AATemporaryBuffs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="nightcap-aa-duration-")
        cls.addClassCleanup(cls.tmp.cleanup)
        source = (ZONE / "spells.cpp").read_text(encoding="utf-8")
        effects_source = (ZONE / "spell_effects.cpp").read_text(encoding="utf-8")
        header = (ROOT / "server-mods/code/common/epic05.h").as_posix()
        cls.exe = compile_native(Path(cls.tmp.name), '#include "' + header + '"\n' +
            '#include "' + (ROOT / 'server-mods/code/common/nightcap_pet_scaling.h').as_posix() + '"\n' +
            '#include "' + (ROOT / 'server-mods/code/common/nightcap_thj_behaviors.h').as_posix() + '"\n' + AA_FIXTURE + MOB_FIXTURE + policy_helpers(source) +
            function(source, "int CalcBuffDuration_formula(") +
            function(source, "int32 Mob::GetBuffDurationForTarget(") +
            function(effects_source, "void Mob::BuffProcess()") + CONTROLS)

    def run_group(self, group):
        run = subprocess.run([str(self.exe), group], text=True, capture_output=True, timeout=15)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_xp_boost_keeps_remaining_timer_and_expires_stale_permanence(self):
        self.run_group("xp_boost")

    def test_rabid_pair_permanent_with_paired_definitions(self):
        self.run_group("rabid")

    def test_activated_aa_preserves_native_and_focused_duration(self):
        self.run_group("direct")

    def test_passive_killing_spree_uses_spell_link_not_chance(self):
        self.run_group("passive")

    def test_nested_recourse_trigger_and_cycle_terminate(self):
        self.run_group("graph")

    def test_non_spell_numeric_effects_do_not_classify_blessings(self):
        self.run_group("nonlinks")

    def test_same_size_catalog_and_spell_reloads_refresh_classification(self):
        self.run_group("reload")

    def test_legacy_permanent_sentinels_expire_but_native_permanent_formulas_remain(self):
        self.run_group("sentinels")

    def test_disciplines_short_buffs_and_preserved_policy_boundaries(self):
        self.run_group("boundaries")

    def test_repeated_duration_policy_does_not_refresh_temporary_buffs(self):
        self.run_group("countdown")

    def test_native_proc_and_trigger_field_mappings(self):
        self.run_group("mapping")

    def test_spell_group_ranks_and_divine_save_fixed_trigger(self):
        self.run_group("spell_groups")

    def test_missing_zone_catalog_does_not_grant_permanence(self):
        self.run_group("missing_catalog")

    def test_empty_zone_catalog_does_not_grant_or_retain_permanence(self):
        self.run_group("empty_catalog")

    def test_local_client_killing_spree_uses_native_formula_and_cap(self):
        self.run_group("killing_spree_local_client")

    def test_cast_on_curer_followon_keeps_native_duration(self):
        self.run_group("followon_386")

    def test_cast_on_cure_followon_keeps_native_duration(self):
        self.run_group("followon_387")

    def test_cast_on_numhit_fade_followon_keeps_native_duration(self):
        self.run_group("followon_406")

    def test_spell_killshot_follows_spell_only_limit_value(self):
        self.run_group("spell_killshot")

    def test_actual_buff_process_expires_player_and_pet_timers_after_zero_tick(self):
        self.run_group("native_expiry")

    def test_actual_buff_process_preserves_native_suspension_and_permanent_formulas(self):
        self.run_group("native_suspension")


if __name__ == "__main__":
    unittest.main()

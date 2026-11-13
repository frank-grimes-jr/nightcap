"""Execute actual native landing branches and the existing instant-DoT policy.

Damage/focus/packet boundaries are fakes. These are not full-zone or player QA.
"""
import gzip
import hashlib
import json
import unittest

from test_gameplay_policies import function
from test_pet_equipment import ROOT, compile_run


PRELUDE = r'''
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
using uint16 = uint16_t; using int32 = int32_t; using int64 = int64_t;
constexpr int EFFECT_COUNT = 12;
constexpr int SPELL_MANA_BURN = 2751, SPELL_LIFE_BURN = 2755;
namespace SpellEffect { enum { CurrentHP = 0, CurrentHPOnce = 79, BardAEDot = 334, TotalHP = 69 }; }
namespace Chat { enum { White }; }
namespace AppearanceType { enum { Die }; }
namespace Animation { enum { Lying }; }
namespace NightcapTHJ { int64 PercentMana(int64 mana, int percent) { return mana * percent / 100; } }
enum { focusFcHealPctIncoming, focusFcHealPctCritIncoming, focusFcHealAmtIncoming };
struct Spell {
 int good_effect = 0, buff_duration_formula = 1, buff_duration = 8, skill = 0;
 int effect_id[12] = {}, base_value[12] = {}, limit_value[12] = {};
} spells[65536];
bool IsValidSpell(uint16 id) { return id > 0 && id < 65535; }
bool IsDetrimentalSpell(uint16 id) { return spells[id].good_effect == 0; }
bool IsEffectInSpell(uint16 id, int effect) {
 for (int i = 0; i < 12; ++i) if (spells[id].effect_id[i] == effect) return true;
 return false;
}
NightcapSympathetic::Cast cast_receipt;
bool thj = false;
#define RuleB(category, rule) (thj)
#define LogSpellsDetail(...) ((void)0)
struct Random { int Int(int, int) { return 150; } };
struct Zone { Random random; } zone_storage, *zone = &zone_storage;
struct Mob {
 bool player = true, restriction = true; int64 damage = 0, healed = 0, taps = 0;
 int dd_calculations = 0, dot_calculations = 0, last_hp = 10, mana = 1000;
 bool IsClient() const { return player; }
 bool IsMoving() const { return false; }
 bool IsInstantCastDot(uint16 spell_id) const;
 bool PassCastRestriction(int) { return restriction; }
 int64 GetMaxMana() { return 1000; } int64 GetMana() { return mana; }
 int64 GetHP() { return 1000; } int GetHealRate() { return 0; }
 int GetFocusEffect(int, uint16, Mob*) { return 0; }
 void SetMana(int64 n) { mana = int(n); } void SetHP(int64) {}
 Mob* CastToClient() { return this; } void SetFeigned(bool) {}
 void SendAppearancePacket(int, int) {} void Message(int, const char*, ...) {}
 int64 GetActSpellDamage(uint16, int64 value, Mob*) { ++dd_calculations; return value - 250; }
 int64 GetActReflectedSpellDamage(uint16, int64 value, int pct) { ++dd_calculations; return (value - 250) * pct / 100; }
 int64 GetActDoTDamage(uint16, int64 value, Mob*, bool) { ++dot_calculations; return value - 125; }
 int64 GetActSpellHealing(uint16, int64 value, Mob*) { return value; }
 void ResourceTap(int64 value, uint16) { taps += value; }
 void Damage(Mob*, int64 value, uint16, int, bool, int, bool) { damage += value; }
 void HealDamage(int64 value, Mob*, uint16 = 0) { healed += value; }
 void Land(Mob* caster, uint16 spell_id, int effect, int effect_value, int buffslot = 0,
           float partial = 100, int reflect_effectiveness = 0, int i = 0);
};
void check(bool ok, const char* message) { if (!ok) { std::cerr << message; throw std::runtime_error(message); } }
'''


CASES = r'''
int main() {
 cast_receipt.effect = NightcapSympathetic::Effect::Strike;
 Mob player, npc, pet, target; npc.player = pet.player = false;
 auto& dot = spells[348]; dot.effect_id[0] = SpellEffect::CurrentHP;
 dot.base_value[0] = -10; dot.effect_id[1] = SpellEffect::CurrentHPOnce; dot.base_value[1] = -6;
 check(player.IsInstantCastDot(348), "DoT casting is no longer instant");
 target.Land(&player, 348, SpellEffect::CurrentHPOnce, -6);
 check(target.damage == 0 && player.dd_calculations == 0 && player.taps == 0,
       "DoT landing still deals amplified direct damage or taps resources");
 check(!cast_receipt.landed, "DoT landing incorrectly qualified for Strike");
 // Repeated instant applications cannot farm the one-time damage.
 for (int n = 0; n < 20; ++n) target.Land(&player, 348, SpellEffect::CurrentHPOnce, -6);
 check(target.damage == 0, "recasting DoT deals direct damage");
 target.Land(&player, 348, SpellEffect::CurrentHP, -10);
 check(target.damage == 0 && player.dot_calculations == 1, "ordinary DoT deals landing damage or loses hit-counter evaluation");
 target.Land(&player, 348, SpellEffect::CurrentHPOnce, -6, 0, 50, 50, 1);
 check(target.damage == 0 && player.dd_calculations == 0, "partial/reflected landing bypasses suppression");
 target.Land(&player, 348, SpellEffect::CurrentHPOnce, 40);
 check(target.healed == 40, "positive one-time heal on a DoT was removed");
 target.Land(&npc, 348, SpellEffect::CurrentHPOnce, -6);
 check(target.damage == 256, "NPC DoT direct damage changed");
 target.Land(&pet, 348, SpellEffect::CurrentHPOnce, -6);
 check(target.damage == 512, "non-client pet direct damage changed");
 target.Land(nullptr, 348, SpellEffect::CurrentHPOnce, -6);
 check(target.damage == 518, "casterless effect changed");
 spells[1].buff_duration_formula = 0;
 target.Land(&player, 1, SpellEffect::CurrentHPOnce, -50, -2);
 check(target.damage == 818, "standalone direct damage removed");
 check(cast_receipt.landed, "eligible standalone damage did not reach the receipt");
 spells[2].effect_id[0] = 3; spells[2].base_value[0] = -20;
 target.Land(&player, 2, SpellEffect::CurrentHPOnce, -50);
 check(target.damage == 1118, "direct damage plus a non-DoT debuff removed");
 // An unrelated DoT on the recipient cannot suppress a standalone nuke.
 target.Land(&player, 1, SpellEffect::CurrentHP, -50, -2);
 check(target.damage == 1418, "ordinary CurrentHP nuke removed");
 dot.good_effect = 1;
 target.Land(&player, 348, SpellEffect::CurrentHPOnce, -6);
 check(target.damage == 1674, "beneficial spell's negative component changed");
 dot.good_effect = 0; dot.buff_duration = 1;
 target.Land(&player, 348, SpellEffect::CurrentHPOnce, -6);
 check(target.damage == 1674, "one-tick DoT direct hit remains");
 dot.buff_duration = 0;
 target.Land(&player, 348, SpellEffect::CurrentHPOnce, -6);
 check(target.damage == 1674, "formula-derived duration DoT direct hit remains");
 dot.effect_id[0] = SpellEffect::BardAEDot;
 target.Land(&player, 348, SpellEffect::CurrentHPOnce, -6);
 target.Land(&player, 348, SpellEffect::BardAEDot, -10);
 check(target.damage == 1674, "Bard DoT deals cast-time damage");
 // Positive immediate buff heals and custom Valor remain intact.
 spells[3].good_effect = 1;
 target.Land(&player, 3, SpellEffect::CurrentHPOnce, 25);
 check(target.healed == 65, "ordinary buff heal removed");
 thj = true;
 target.Land(&player, 2775, SpellEffect::CurrentHPOnce, 1);
 check(target.healed == 1065, "Valor resource healing changed");
}
'''


class DotInitialDamage(unittest.TestCase):
    def test_captured_catalog_distinguishes_initial_hits_from_ticks(self):
        evidence = ROOT / 'docs/balance/dot-initial-damage-20261112'
        raw = gzip.decompress((evidence / 'local-dot-definitions.jsonl.gz').read_bytes())
        audit = json.loads((evidence / 'local-audit.json').read_text())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), audit['source_sha256'])
        rows = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines()]
        initial = [r for r in rows if any(e[0] == 79 and e[1] < 0 for e in r['effects'])]
        self.assertEqual(len(rows), 3626)
        self.assertEqual(len(initial), 980)
        self.assertEqual(sum(e[0] == 79 and e[1] < 0 for r in rows for e in r['effects']), 996)
        # Review alternative direct HP handlers as well as CurrentHPOnce.
        self.assertFalse(any(e[0] in (147, 350) for r in rows for e in r['effects']))
        by_id = {r['id']: r for r in rows}
        for spell_id in (340, 348, 365, 434, 435, 436):
            self.assertTrue(any(e[0] == 79 and e[1] < 0 for e in by_id[spell_id]['effects']))
        for spell_id in (344, 355, 360, 367):
            self.assertFalse(any(e[0] == 79 and e[1] < 0 for e in by_id[spell_id]['effects']))
        self.assertIn([79, 50, 100, 0], by_id[871]['effects'])  # Reckless Health heals once.

    def test_native_landing_and_instant_cast_policy(self):
        source = (ROOT / 'server-mods/code/zone/spell_effects.cpp').read_text(encoding='utf-8')
        spells = (ROOT / 'server-mods/code/zone/spells.cpp').read_text(encoding='utf-8')
        branches = []
        for name, following in [('CurrentHP', 'CurrentHPOnce'),
                                ('CurrentHPOnce', 'PercentalHeal'),
                                ('BardAEDot', 'CurrentEndurance')]:
            start = source.index('case SpellEffect::' + name + ':')
            end = source.index('case SpellEffect::' + following + ':', start)
            branches.append(source[start:end])
        landing = '''void Mob::Land(Mob* caster, uint16 spell_id, int effect, int effect_value,
 int buffslot, float partial, int reflect_effectiveness, int i) {
 auto record_hp = [](NightcapSympathetic::Line line, int64 amount) { cast_receipt.Record(line, amount); };
 const auto& spell = spells[spell_id]; switch(effect) {''' + '\n'.join(branches) + '}}'
        policy = '\n'.join(function(spells, signature) for signature in (
            'int CalcBuffDuration_formula(', 'bool Mob::IsInstantCastDot('))
        header = (ROOT / 'server-mods/code/zone/nightcap_sympathetic.h').as_posix()
        compile_run(f'#include "{header}"\n' + PRELUDE + policy + landing + CASES)


if __name__ == '__main__':
    unittest.main()

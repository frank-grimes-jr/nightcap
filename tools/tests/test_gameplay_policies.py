"""Compile the actual native spell-policy/death methods with a small Mob fixture.

These controls do not certify a full zone, network client, or database round trip.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from test_aa_temporary_buffs import AA_FIXTURE, policy_helpers

ROOT = Path(__file__).resolve().parents[2]
ZONE = ROOT / "server-mods/code/zone"


def function(source, signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


FIXTURE = AA_FIXTURE + r'''
int CalcBuffDuration_formula(int level, int formula, int duration);
bool IsPersistDeathSpell(uint16 id) { return id == 2 || id == 3; }
struct Buff { int spellid = SPELL_UNKNOWN; int ticsremaining = 0; };
struct Mob {
 bool player = true, pet = false; Buff buffs[8]; int recalcs = 0;
 bool IsClient() const { return player; }
 bool IsPetOwnerClient() const { return pet; }
 bool HasPersistDeathIllusion(uint16 id) const { return id == 4; }
 int GetMaxTotalSlots() const { return 8; }
 void BuffFadeBySlot(int i, bool) { buffs[i].spellid = SPELL_UNKNOWN; }
 void CalcBonuses() { ++recalcs; }
 int32 GetBuffDurationForTarget(uint16 spell_id, int32 duration) const;
 bool IsInstantCastDot(uint16 spell_id) const;
 static int32 BuffDurationForClient(int32 duration);
 void BuffFadeNonPersistDeath();
};
void check(bool pass, const char *message) { if (!pass) throw std::runtime_error(message); }
'''

CONTROLS = r'''
int main() {
 try {
  rank(1, 60000); // Loaded catalog, unrelated to the ordinary blessing controls.
  Mob player, pet, npc; pet.player = false; pet.pet = true; npc.player = false;
  for (int id : {1,2,4,5}) {
   check(player.GetBuffDurationForTarget(id, 20) == PERMANENT_BUFF_DURATION, "beneficial player buff timed");
   check(pet.GetBuffDurationForTarget(id, 20) == PERMANENT_BUFF_DURATION, "owned pet buff timed");
   check(npc.GetBuffDurationForTarget(id, 20) == 20, "hostile NPC buff modified");
  }
  check(player.GetBuffDurationForTarget(1, 0) == 0, "instant heal became a buff");
  check(player.GetBuffDurationForTarget(SPELL_UNKNOWN, 20) == 20, "invalid spell changed");
  check(player.GetBuffDurationForTarget(1, -4) == -4, "aura lost range-managed duration");
  spells[3].good_effect = 0; spells[6].good_effect = 0;
  check(player.GetBuffDurationForTarget(3, 20) == 20, "debuff made permanent");
  check(Mob::BuffDurationForClient(PERMANENT_BUFF_DURATION) == -1, "internal sentinel leaked to client");
  check(Mob::BuffDurationForClient(20) == 20, "ordinary wire duration changed");
  check(Mob::BuffDurationForClient(-4) == -4, "aura wire duration changed");
  for (int id : {1,2,3,4,6}) player.buffs[id].spellid = id;
  player.BuffFadeNonPersistDeath();
  for (int id : {1,2,4,6}) check(player.buffs[id].spellid == SPELL_UNKNOWN, "buff survived death");
  check(player.buffs[3].spellid == 3, "unrelated persistent detrimental policy changed");
  check(player.recalcs == 1, "death bonuses not recalculated once");
  npc.buffs[2].spellid = 2; npc.BuffFadeNonPersistDeath();
  check(npc.buffs[2].spellid == 2, "NPC death policy changed");
  spells[3].base_value[0] = -10;
  check(player.IsInstantCastDot(3), "ordinary DoT not instant");
  check(!npc.IsInstantCastDot(3), "hostile NPC DoT instant");
  check(!pet.IsInstantCastDot(3), "pet casting changed outside player scope");
  check(!player.IsInstantCastDot(1), "beneficial spell instant");
  spells[3].buff_duration = 0;
  check(player.IsInstantCastDot(3), "zero-cap DoT not instant");
  spells[3].buff_duration = 1;
  check(player.IsInstantCastDot(3), "one-tick DoT not instant");
  spells[3].buff_duration_formula = 0;
  check(!player.IsInstantCastDot(3), "direct damage instant");
  spells[3].buff_duration_formula = 1; spells[3].effect_id[0] = SpellEffect::BardAEDot;
  check(player.IsInstantCastDot(3), "bard DoT not instant");
  spells[3].effect_id[0] = 99;
  check(!player.IsInstantCastDot(3), "non-damage debuff instant");
  check(!player.IsInstantCastDot(SPELL_UNKNOWN), "invalid spell accepted");
  std::cout << "Native spell-policy and death controls passed\n";
 } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
'''


class GameplayPolicies(unittest.TestCase):
    def test_native_spell_and_death_behavior(self):
        source = (ZONE / "spells.cpp").read_text(encoding="utf-8")
        bodies = [function(source, sig) for sig in (
            "int CalcBuffDuration_formula(",
            "int32 Mob::GetBuffDurationForTarget(",
            "bool Mob::IsInstantCastDot(",
            "int32 Mob::BuffDurationForClient(",
            "void Mob::BuffFadeNonPersistDeath()",
        )]
        with tempfile.TemporaryDirectory(prefix="nightcap-policy-") as tmp:
            out = Path(tmp)
            header = (ROOT / "server-mods/code/common/epic05.h").as_posix()
            thj_header = (ROOT / 'server-mods/code/common/nightcap_thj_behaviors.h').as_posix()
            rules = '#include "' + thj_header + '"\n#define RuleB(category, rule) true\n'
            (out / "test.cpp").write_text(rules + '#include "' + header + '"\n#include "' + (ROOT / 'server-mods/code/common/nightcap_pet_scaling.h').as_posix() + '"\n' + FIXTURE + policy_helpers(source) + "\n".join(bodies) + CONTROLS)
            if os.name == "nt":
                compiler_env = Path("C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat")
                self.assertTrue(compiler_env.is_file(), "MSVC x86 build tools missing")
                (out / "build.cmd").write_text(
                    '@echo off\ncall "' + str(compiler_env) + '" >nul || exit /b 1\n'
                    'cl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\n'
                    'exit /b %errorlevel%\n')
                build = subprocess.run(["cmd", "/d", "/c", str(out / "build.cmd")], cwd=out)
                self.assertEqual(build.returncode, 0, (out / "build.log").read_text())
                exe = out / "test.exe"
            else:
                exe = out / "test"
                subprocess.run([shutil.which("c++"), "-std=c++17", str(out / "test.cpp"), "-o", str(exe)], check=True)
            run = subprocess.run([str(exe)], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_integration_points(self):
        spells = (ZONE / "spells.cpp").read_text(encoding="utf-8")
        add = function(spells, "int Mob::AddBuff(")
        self.assertIn("duration = GetBuffDurationForTarget(spell_id, duration);", add)
        cast = function(spells, "bool Mob::DoCastSpell(")
        self.assertIn("if (IsInstantCastDot(spell_id))", cast)
        self.assertIn("cast_time = orgcasttime = 0;", cast)
        for statement in (
            "sbf->buff.duration = BuffEffectDurationForClient(buff.ticsremaining);",
            "bi->entries[0].tics_remaining = BuffDurationForClient(buff.ticsremaining);",
            "pbs->ticsremaining[buffslot] = BuffDurationForClient(buffs[buffslot].ticsremaining);",
            "buff->entries[index].tics_remaining = BuffDurationForClient(buffs[i].ticsremaining);",
        ):
            self.assertIn(statement, spells)
        attack = (ZONE / "attack.cpp").read_text(encoding="utf-8")
        self.assertIn("(!IsClient() && IsCasting()", function(attack, "bool Mob::Attack("))
        death = function(attack, "bool Client::Death(")
        self.assertLess(death.index("BuffFadeBeneficial();"), death.index("if (!GetGM())"))
        process = (ZONE / "client_process.cpp").read_text(encoding="utf-8")
        attacks = process[process.index("bool may_use_attacks = false;"):process.index("if (AutoFireEnabled())")]
        self.assertNotIn("casting_spell_id", attacks)
        for guard in ("!IsAIControlled()", "!dead", "!IsStunned()", "!IsFeared()", "!IsMezzed()", "!IsMeleeDisabled()", "ranged_timer.Check(false)"):
            self.assertIn(guard, attacks)


if __name__ == "__main__":
    unittest.main()

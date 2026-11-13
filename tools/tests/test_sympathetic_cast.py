"""Compile candidate cast branches and HP handlers against observable combat recipients."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_heal_targeting import function

ROOT = Path(__file__).resolve().parents[2]
ZONE = Path(os.environ.get("SYMPATHETIC_ZONE", ROOT / "server-mods/code/zone"))


def between(source, start, stop):
    return source[source.index(start):source.index(stop, source.index(start))]


class SympatheticCast(unittest.TestCase):
    def test_native_cast_outcomes(self):
        spells = (ZONE / "spells.cpp").read_text()
        effects = (ZONE / "spell_effects.cpp").read_text()
        mob = (ZONE / "mob.cpp").read_text()
        code = (Path(__file__).with_name("sympathetic_cast_fixture.cpp")).read_text()
        code = code.replace("/* ORIGINAL GEM CHECK */", between(spells, "Cast sympathetic;", "auto *const click"))
        code = code.replace("/* RECORD HP */", between(effects, "auto *const sympathetic =", "int caster_level"))
        code = code.replace("/* CURRENT HP */", between(effects, "case SpellEffect::CurrentHP:", "case SpellEffect::CurrentHPOnce:"))
        code = code.replace("/* HEAL EFFECTS */", between(effects, "case SpellEffect::PercentalHeal:", "case SpellEffect::CurrentMana:"))
        sot = function(spells, "bool Mob::SpellOnTarget(")
        code = code.replace("/* TARGET RECEIPT */", between(sot, "auto *sympathetic = Cast::Take();", "auto spellOwner"))
        code = code.replace("/* GROUP WORN RECEIPT */", between(spells, "const NightcapSympathetic::WornGroup worn_targets(", "if (IsBot())"))
        code = code.replace("/* LANDING */", between(spells, "auto *const receipt = spell_effectiveness", "if (!Cast::Deliver(receipt"))
        code = code.replace("/* PROC AND APPLICATION */", function(mob, "void Mob::TrySympatheticProc(") +
                            function(mob, "void Mob::ApplySympatheticClick("))
        with tempfile.TemporaryDirectory(prefix="sympathetic-cast-") as tmp:
            path = Path(tmp)
            (path / "fixture.cpp").write_text(code)
            if os.name == "nt":
                (path / "build.cmd").write_text(
                    '@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars64.bat" >nul || exit /b 1\n'
                    f'cl /nologo /W4 /EHsc /std:c++17 /I"{ZONE}" fixture.cpp /Fe:test.exe\n')
                compile_cmd = ["cmd", "/d", "/c", "build.cmd"]
                binary = path / "test.exe"
            else:
                compile_cmd = [os.environ.get("CXX", "c++"), "-std=c++17", "-I", str(ZONE), "fixture.cpp", "-o", "test"]
                binary = path / "test"
            built = subprocess.run(compile_cmd, cwd=path, capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            run = subprocess.run([str(binary)], cwd=path, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_receipt_only_reaches_original_single_delivery(self):
        spells = (ZONE / "spells.cpp").read_text()
        effects = (ZONE / "spell_effects.cpp").read_text()
        complete = function(spells, "void Mob::CastedSpellFinished(")
        self.assertLess(complete.index("Cast::Deliver(click"), complete.index("TrySympatheticProc"))
        self.assertLess(complete.index("ApplySympatheticClick"), complete.index("TryTwincast"))
        finish = function(spells, "bool Mob::SpellFinished(")
        self.assertEqual(finish.count("CastAction == SingleTarget ? sympathetic : nullptr"), 2)
        group = between(finish, "case GroupSpell:", "case CAHateList:")
        self.assertIn("sympathetic->effect == Effect::WornHeal", group)
        self.assertNotIn("Cast::Deliver", between(finish, "case AECaster:", "// Set and send"))
        sot = function(spells, "bool Mob::SpellOnTarget(")
        for earlier in ("IsBlockedBuff", "IsImmuneToSpell", "spelltar->SpellOnTarget", "ResistSpell"):
            self.assertLess(sot.index(earlier), sot.index("Cast::Deliver(receipt"))
        fx = function(effects, "bool Mob::SpellEffect(")
        self.assertLess(fx.index("EVENT_SPELL_EFFECT_CLIENT"), fx.index("record_hp(NightcapSympathetic::Line"))
        self.assertNotIn("record_hp", effects[effects.index("void Mob::DoBuffTic("):])
        once = between(fx, "case SpellEffect::CurrentHPOnce:", "case SpellEffect::PercentalHeal:")
        self.assertIn("PassCastRestriction", once[:once.index("record_hp(")])
        self.assertEqual(once.count("record_hp(NightcapSympathetic::Line::"), 2)
        focus = function(effects, "uint16 Mob::GetSympatheticFocusEffect(focusType type, uint16 spell_id, bool &worn)")
        self.assertEqual(focus.count("push_back({proc_spellid, true})"), 2)
        self.assertEqual(focus.count("push_back({proc_spellid, false})"), 2)
        self.assertIn("worn = SympatheticProcList[random].worn", focus)
        projectile = (ZONE / "special_attacks.cpp").read_text()
        self.assertIn("ProjectileAtk[i].skill == EQ::skills::SkillConjuration",
                      projectile[projectile.rindex("if (target)", 0, projectile.index("::BoltEffect")):projectile.index("::BoltEffect")])


if __name__ == "__main__":
    unittest.main()

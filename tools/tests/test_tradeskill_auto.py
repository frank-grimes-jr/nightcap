"""Native selected-recipe controls, with actual SQL and consumption planner.

Compile actual HandleAutoCombine, TradeskillAutoReply and TradeskillComponents.
Recipe metadata loading, output/skill execution and native client state are
controlled boundaries; inventory components are real SQL rows in SQLite. These
tests prove native controller guards and response ordering, not RoF2 slot
decoding, UI automation, skill probability, or durable inventory persistence.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import test_tradeskill_stacks as stacks
from test_gameplay_policies import ROOT, function

SOURCE_ROOT = ROOT / "server-mods/code"


def recipe_database(scenario, world=False):
    database = stacks.recipe_database("stacked_pair", world or scenario.startswith("world_"))
    if scenario in {"split", "duplicate_short", "duplicate_enough", "charged", "augmented", "bag_material"}:
        database.execute("DELETE FROM tradeskill_recipe_entries WHERE componentcount > 0")
        requirements = [(100, 2), (100, 2)] if scenario.startswith("duplicate_") else [(100, 2)]
        if scenario == "bag_material":
            requirements = [(999, 1)]
        database.executemany("INSERT INTO tradeskill_recipe_entries(recipe_id,item_id,componentcount) VALUES (1,?,?)", requirements)
    return database


class TradeskillAuto(unittest.TestCase):
    database_factory = staticmethod(recipe_database)
    run_scenario = stacks.TradeskillStacks.run_scenario

    @classmethod
    def setUpClass(cls):
        source = (SOURCE_ROOT / "zone/tradeskills.cpp").read_text(encoding="utf-8")
        code = (stacks.FIXTURES / "native_fixture.cpp").read_text(encoding="utf-8")
        header = (SOURCE_ROOT / "common/tradeskill_policy.h").resolve().as_posix()
        code += '#include "' + header + '"\n'
        code += function(source, "static bool TradeskillComponents(") + "\n"
        code += function(source, "struct TradeskillAutoReply {") + ";\n"
        code += function(source, "void Object::HandleAutoCombine(") + "\n"
        code += (stacks.FIXTURES / "auto_scenarios.cpp").read_text(encoding="utf-8")
        build_root = ROOT / "work"
        build_root.mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix="tradeskill-auto-", dir=build_root)
        cls.addClassCleanup(cls.temp.cleanup)
        path = Path(cls.temp.name)
        (path / "test.cpp").write_text(code, encoding="utf-8")
        cls.binary = path / "test.exe"
        if os.name == "nt":
            (path / "build.cmd").write_text(
                '@echo off\ncall "C:\\BuildTools\\VC\\Auxiliary\\Build\\vcvars32.bat" >nul || exit /b 1\n'
                'cl /nologo /EHsc /W4 /std:c++20 test.cpp /Fe:test.exe\n')
            command = ["cmd", "/d", "/c", str(path / "build.cmd")]
        else:
            command = ["c++", "-std=c++20", "-Wall", "-Wextra", "test.cpp", "-o", "test.exe"]
        result = subprocess.run(command, cwd=path, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def test_material_consumption(self):
        for scenario in ("stacked", "split", "duplicate_short", "duplicate_enough", "charged", "augmented", "bag_material"):
            with self.subTest(scenario=scenario):
                self.run_scenario(scenario)

    def test_actual_container_required(self):
        for scenario in ("wrong_slot", "wrong_id", "wrong_type", "not_bag", "missing_bag"):
            with self.subTest(scenario=scenario):
                self.run_scenario(scenario)

    def test_world_ownership_and_distance(self):
        for scenario in ("world_valid", "world_closed", "world_owner", "world_type", "world_id", "world_range", "world_edge"):
            with self.subTest(scenario=scenario):
                self.run_scenario(scenario)

    def test_client_state_guards(self):
        for scenario in ("disconnected", "unloaded", "zoning", "dead", "engaged", "stunned", "mezzed", "feared", "ai", "trading", "cursor"):
            with self.subTest(scenario=scenario):
                self.run_scenario(scenario)

    def test_recipe_and_character_gates(self):
        for scenario in ("recipe_missing", "unlearned", "skill", "alchemy_class", "alchemy_level", "alchemy_valid",
                         "tinkering_race", "tinkering_valid", "poison_class", "poison_valid", "lore", "quest_denied", "replace_container"):
            with self.subTest(scenario=scenario):
                self.run_scenario(scenario)

    def test_quest_callback_state_rechecked(self):
        for scenario in ("callback_swap", "callback_cursor", "callback_missing", "callback_combat", "world_callback_close"):
            with self.subTest(scenario=scenario):
                self.run_scenario(scenario)

    def test_completion_ack_after_results_and_callbacks(self):
        for scenario in ("success_order", "failure_order", "output_stops", "callback_output_stops"):
            with self.subTest(scenario=scenario):
                self.run_scenario(scenario)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--source-root", type=Path)
    args, remaining = parser.parse_known_args()
    if args.source_root:
        SOURCE_ROOT = args.source_root
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)

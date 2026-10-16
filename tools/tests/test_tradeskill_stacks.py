"""Compile actual experimental-combine methods and execute their SQL in SQLite.

The native fixture supplies inventory/network/quest boundaries; it does not
reimplement recipe matching or component consumption. QueryDatabase relays SQL
to this process, where a real in-memory relational engine executes it. No game
database, running server or client is modified. These controls do not certify
MariaDB, durable inventory transactions or RoF2 rendering/packet handling.

Usage: python tools/tests/test_tradeskill_stacks.py --source-root PATH
PATH contains zone/tradeskills.cpp. Defaults to the tracked server overlay.
"""
import argparse
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from test_gameplay_policies import ROOT, function

SOURCE_ROOT = ROOT / "server-mods/code"
FIXTURES = Path(__file__).parent / "fixtures/tradeskills"


def recipe_database(scenario, world=False):
    connection = sqlite3.connect(":memory:")
    connection.executescript("""
        CREATE TABLE tradeskill_recipe (
            id INTEGER PRIMARY KEY, enabled INTEGER NOT NULL,
            name TEXT DEFAULT 'fixture', tradeskill INTEGER DEFAULT 60,
            skillneeded INTEGER DEFAULT 0, trivial INTEGER DEFAULT 1,
            nofail INTEGER DEFAULT 1, replace_container INTEGER DEFAULT 0,
            must_learn INTEGER DEFAULT 0, quest INTEGER DEFAULT 0);
        CREATE TABLE tradeskill_recipe_entries (
            recipe_id INTEGER, item_id INTEGER, componentcount INTEGER DEFAULT 0,
            iscontainer INTEGER DEFAULT 0, successcount INTEGER DEFAULT 0,
            failcount INTEGER DEFAULT 0, salvagecount INTEGER DEFAULT 0);
    """)

    def recipe(recipe_id, materials):
        connection.execute("INSERT INTO tradeskill_recipe(id,enabled) VALUES (?,1)", (recipe_id,))
        connection.execute("INSERT INTO tradeskill_recipe_entries(recipe_id,item_id,iscontainer) VALUES (?,?,1)",
                           (recipe_id, 10 if world else 999))
        connection.executemany("INSERT INTO tradeskill_recipe_entries(recipe_id,item_id,componentcount) VALUES (?,?,?)",
                               [(recipe_id, item, quantity) for item, quantity in materials])

    if scenario in {"two_from_stack", "split_stacks", "charged_single"}:
        recipe(1, [(100, 2)])
    elif scenario in {"ambiguous_quantity", "exact_quantity"}:
        recipe(1, [(100, 1)])
        recipe(2, [(100, 2)])
    elif scenario == "ambiguous_duplicate":
        recipe(1, [(100, 1)])
        recipe(2, [(100, 1)])
    else:
        recipe(1, [(100, 1), (200, 1)])
    return connection


class TradeskillStacks(unittest.TestCase):
    database_factory = staticmethod(recipe_database)
    @classmethod
    def setUpClass(cls):
        source = (SOURCE_ROOT / "zone/tradeskills.cpp").read_text(encoding="utf-8")
        matching = function(source, "bool ZoneDatabase::GetTradeRecipe(")
        combine = function(source, "void Object::HandleCombine(")
        code = (FIXTURES / "native_fixture.cpp").read_text(encoding="utf-8")
        if "static bool TradeskillContainerStacks(" in source:
            header = (SOURCE_ROOT / "common/tradeskill_policy.h").resolve().as_posix()
            code += '#include "' + header + '"\n'
            code += function(source, "static bool TradeskillContainerStacks(") + "\n"
            code += function(source, "static bool TradeskillComponents(") + "\n"
        code += matching + "\n" + combine + "\n"
        code += (FIXTURES / "scenarios.cpp").read_text(encoding="utf-8")
        build_root = ROOT / "work"
        build_root.mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix="tradeskill-stacks-", dir=build_root)
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

    def run_scenario(self, scenario, world=False):
        database = self.database_factory(scenario, world)
        self.addCleanup(database.close)
        process = subprocess.Popen([self.binary, scenario, "world" if world else "bag"],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, bufsize=1)
        transcript = []
        try:
            for line in process.stdout:
                if line.startswith("QUERY "):
                    query = line[6:].rstrip("\n")
                    try:
                        rows = database.execute(query).fetchall()
                    except sqlite3.Error as error:
                        self.fail(f"Native query failed in fixture: {error}\n{query}")
                    process.stdin.write(str(len(rows)) + "\n")
                    for row in rows:
                        process.stdin.write(str(len(row)) + "\n")
                        for value in row:
                            process.stdin.write(str(value) + "\n")
                    process.stdin.flush()
                else:
                    transcript.append(line)
            process.wait(timeout=10)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
            process.stdin.close()
            process.stdout.close()
        self.assertEqual(process.returncode, 0, "".join(transcript))

    def test_stacked_pair_consumes_one_each(self):
        for world in (False, True):
            with self.subTest(world=world):
                self.run_scenario("stacked_pair", world)

    def test_recipe_can_take_two_from_one_stack(self):
        self.run_scenario("two_from_stack")

    def test_recipe_can_take_components_across_split_stacks(self):
        self.run_scenario("split_stacks")

    def test_missing_material_does_not_consume(self):
        self.run_scenario("missing")

    def test_nonstackable_item_charges_are_not_physical_units(self):
        self.run_scenario("charged_single")

    def test_unrelated_input_rejects_without_consumption(self):
        self.run_scenario("unrelated")

    def test_ambiguous_quantities_do_not_silently_choose_a_recipe(self):
        self.run_scenario("ambiguous_quantity")

    def test_duplicate_recipes_do_not_silently_choose_first(self):
        self.run_scenario("ambiguous_duplicate")

    def test_unstacked_control_still_combines(self):
        self.run_scenario("unstacked")

    def test_augmented_component_is_not_consumed(self):
        self.run_scenario("augmented")

    def test_replaced_container_cannot_destroy_surplus_materials(self):
        self.run_scenario("replace_surplus")

    def test_callback_container_swap_does_not_use_retired_pointer(self):
        for stage in ("combine", "validate"):
            with self.subTest(stage=stage):
                self.run_scenario("callback_" + stage + "_swap")

    def test_callback_material_removal_does_not_consume_remaining_input(self):
        for stage in ("combine", "validate"):
            with self.subTest(stage=stage):
                self.run_scenario("callback_" + stage + "_missing")

    def test_validation_callback_cannot_add_augment_then_combine(self):
        self.run_scenario("callback_validate_augmented")

    def test_validation_callback_closing_world_container_cancels(self):
        self.run_scenario("callback_validate_close", world=True)

    def test_unique_exact_quantity_recipe_is_preferred(self):
        self.run_scenario("exact_quantity")

    def test_replace_container_exact_material_control(self):
        self.run_scenario("replace_exact")

    def test_twenty_repeated_combines_exhaust_twenty_materials(self):
        for world in (False, True):
            with self.subTest(world=world):
                self.run_scenario("repeat_until_empty", world)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--source-root", type=Path)
    args, remaining = parser.parse_known_args()
    if args.source_root:
        SOURCE_ROOT = args.source_root
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)

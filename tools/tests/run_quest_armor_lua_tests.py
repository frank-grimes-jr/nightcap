"""Run actual quest Lua without modifying a development or production runtime.

Local:  python tools/tests/run_quest_armor_lua_tests.py --items-module PATH --lua lua5.1
Docker: python tools/tests/run_quest_armor_lua_tests.py --items-module PATH --docker-container akk-stack-eqemu-server-1

Use --quest-root to reproduce against a captured or installed baseline. All source
is passed through stdin when using Docker; no files or database rows are changed.
The Docker option is for the local development container only, never production.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def lua_literal(text: str) -> str:
    equals = ""
    while f"]{equals}]" in text:
        equals += "="
    return f"[{equals}[{text}]{equals}]"


def main() -> int:
    test_path = Path(__file__).with_name("quest_armor_rewards.lua")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quest-root", type=Path, default=Path(__file__).resolve().parents[2] / "server-mods" / "quests")
    parser.add_argument("--items-module", type=Path, help="Actual installed lua_modules/items.lua helper")
    parser.add_argument("--baseline-capture", type=Path, help="Use captured production source and helper instead of candidate files")
    parser.add_argument("--helpers-capture", type=Path, help="Use a captured production helper with candidate quest source")
    runtime = parser.add_mutually_exclusive_group()
    runtime.add_argument("--lua", default="lua5.1", help="Local Lua interpreter (default: lua5.1)")
    runtime.add_argument("--docker-container", help="Existing local development container with lua5.1")
    args = parser.parse_args()
    quest_root = args.quest_root.resolve()
    items_path = args.items_module.resolve() if args.items_module else quest_root / "lua_modules" / "items.lua"
    source_paths = [
        quest_root / "southkarana" / f"{name}_Meadowgreen.lua" for name in ("Shakrn", "Ulan")
    ] + [quest_root / "soltemple" / "Walthin_Fireweaver.lua"]
    # Long strings preserve source text without shell interpolation, Lua quoting,
    # temporary runtime files, or dependence on host/container mount layout.
    bundle = ["QUEST_TEST_SOURCES = {}"]
    capture = json.loads(args.baseline_capture.read_text(encoding="utf-8-sig")) if args.baseline_capture else None
    sources = {path: capture["scripts"][path.relative_to(quest_root).as_posix()]["source"] if capture else path.read_text(encoding="utf-8-sig") for path in source_paths}
    helper_capture = capture or (json.loads(args.helpers_capture.read_text(encoding="utf-8-sig")) if args.helpers_capture else None)
    sources[items_path] = helper_capture["helpers"]["lua_modules/items.lua"]["source"] if helper_capture else items_path.read_text(encoding="utf-8-sig")
    for source_path, source in sources.items():
        bundle.append(
            f"QUEST_TEST_SOURCES[ {lua_literal(source_path.as_posix())} ] = "
            f"{lua_literal(source)}"
        )
    bundle.append(f"arg = {{{lua_literal(quest_root.as_posix())}, {lua_literal(items_path.as_posix())}}}")
    bundle.append(test_path.read_text(encoding="utf-8"))
    command = ["docker", "exec", "-i", args.docker_container, "lua5.1", "-"] if args.docker_container else [args.lua, "-"]
    result = subprocess.run(command, input="\n".join(bundle).encode("utf-8"), check=False)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

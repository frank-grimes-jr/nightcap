"""Use the local TEST candidate objects with a diagnostic-only main and RAM DB."""
import json
from pathlib import Path
import shlex
import subprocess

from build_test import BUILD, OBJECTS, STAGE, UNITS

FIXTURE = Path("/tmp/nightcap-balance-sympathetic")
MOCK = Path("/tmp/nightcap-balance-stock-worn-atk-20261113")
PROBE = STAGE / "probe"


def main():
    PROBE.mkdir(exist_ok=True)
    for name in ("logs", "shared", "quests", "plugins", "lua_modules"):
        (PROBE / name).mkdir(exist_ok=True)
    if not (PROBE / "maps").exists():
        (PROBE / "maps").symlink_to((FIXTURE / "maps").resolve())
    conf = json.loads((FIXTURE / "eqemu_config.json").read_bytes())
    assert conf["server"]["database"]["host"] == "nightcap-sympathetic-balance"
    assert conf["server"]["database"]["db"] == "nightcap_sympathetic_balance"
    assert conf["server"]["database"]["username"] == "sympathetic_fixture"
    assert "content_database" not in conf["server"] and conf["server"]["auto_database_updates"] == "false"
    config = PROBE / "eqemu_config.json"
    config.write_text(json.dumps(conf)); config.chmod(0o600)
    if not (PROBE / "shared/items").exists():
        with (PROBE / "shared-loader.log").open("wb") as log:
            subprocess.run(["/home/eqemu/server/bin/shared_memory", "items", "spells"], cwd=PROBE,
                           check=True, stdout=log, stderr=subprocess.STDOUT)
    flags = dict(l.split(" = ",1) for l in (OBJECTS/"flags.make").read_text().splitlines() if " = " in l)
    opts = sum((shlex.split(flags[k]) for k in ("CXX_DEFINES", "CXX_INCLUDES", "CXX_FLAGS")), [])
    candidate = STAGE / "candidate"
    subprocess.run(["/usr/bin/clang++", *opts, "-ivfsoverlay", candidate / "vfs.json", "-Xclang",
                    "-include-pch", "-Xclang", candidate / "zone.pch", "-Xclang", "-include", "-Xclang",
                    OBJECTS / "cmake_pch.hxx", "-UNDEBUG", "-c", STAGE / "local_cast_probe.cpp",
                    "-o", PROBE / "probe.o"], cwd=BUILD, check=True)
    link = shlex.split((OBJECTS / "link.txt").read_text())
    for name in UNITS:
        link[link.index("CMakeFiles/zone.dir/" + name + ".cpp.o")] = str(candidate / (name + ".o"))
    link[link.index("CMakeFiles/zone.dir/main.cpp.o")] = str(MOCK / "main.o")
    link[1:1] = ["-fuse-ld=gold", "-Wl,--wrap=_ZNSt13random_device9_M_getvalEv", str(PROBE / "probe.o")]
    link[link.index("-o") + 1] = str(PROBE / "zone")
    subprocess.run(link, cwd=BUILD, check=True)
    (PROBE / "input.json").write_text("{}")


if __name__ == "__main__":
    main()

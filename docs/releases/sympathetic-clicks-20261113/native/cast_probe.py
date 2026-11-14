"""Exercise real clicks in a diagnostic relink of the exact shipping candidate."""
import json
import shutil
import sys
from build import SOURCE, STAGE, UNITS, compile_unit, link, run, sha, write_json

PROBE = STAGE / "probe"
FIXTURE = STAGE.parent / "nightcap-balance-sympathetic"


def replace(s, before, after):
    if s.count(before) != 1:
        raise ValueError("Diagnostic source anchor changed: " + before[:80])
    return s.replace(before, after)


def build():
    PROBE.mkdir(exist_ok=True)
    main = (SOURCE / "zone/main.cpp").read_text()
    for before, after in [
        ("int main(int argc, char **argv)\n{",
         "bool NightcapBalancePreflight(int, char **);\nint NightcapBalanceMain(int, char **);\n"
         "int main(int argc, char **argv)\n{\n\tif (!NightcapBalancePreflight(argc, argv)) return 2;"),
        ("\n\tQServ->CheckForConnectState();", "\n\t// Disabled in isolated native probe."),
        ("\tworldserver.Connect();", "\t// Disabled in isolated native probe."),
        ("\tif (!CheckForCompatibleQuestPlugins()) {", "\tif (false && !CheckForCompatibleQuestPlugins()) {"),
        ("\t\tZoneCLI::CommandHandler(argc, argv);\n\t}\n\n\tTimer InterserverTimer",
         "\t\treturn NightcapBalanceMain(argc, argv);\n\t}\n\n\tTimer InterserverTimer"),
    ]:
        main = replace(main, before, after)
    diagnostic_main = PROBE / "main.cpp"
    diagnostic_main.write_text(main)
    probe = (STAGE / "local_cast_probe.cpp").read_text()
    probe = replace(probe, "/tmp/nightcap-sympathetic-local-test-20261113/probe", str(PROBE))
    # Force active fixture assertions despite the release translation-unit flags.
    probe = replace(probe, "#include <cassert>", "#undef NDEBUG\n#include <cassert>")
    harness = PROBE / "harness.cpp"
    harness.write_text(probe)
    pch, overlay = STAGE / "candidate.pch", STAGE / "vfs.json"
    compile_unit("main", PROBE / "main.o", pch, overlay, diagnostic_main)
    compile_unit("main", PROBE / "harness.o", pch, overlay, harness)
    changes = {n: STAGE / (n + ".o") for n in UNITS}
    changes["main"] = PROBE / "main.o"
    link(PROBE / "check-zone", changes, [str(PROBE / "harness.o"), "-Wl,--wrap=_ZNSt13random_device9_M_getvalEv"])


def execute():
    conf = json.loads((FIXTURE / "eqemu_config.json").read_bytes())
    s = conf["server"]
    db = s["database"]
    assert (db["host"], db["db"], db["username"]) == (
        "nightcap-sympathetic-balance", "nightcap_sympathetic_balance", "sympathetic_fixture")
    assert s["auto_database_updates"] == "false" and "content_database" not in s
    for d in ("logs", "quests", "plugins", "lua_modules", "shared"):
        (PROBE / d).mkdir(exist_ok=True)
    if not (PROBE / "maps").exists():
        (PROBE / "maps").symlink_to((FIXTURE / "maps").resolve())
    shutil.copyfile(FIXTURE / "eqemu_config.json", PROBE / "eqemu_config.json")
    (PROBE / "eqemu_config.json").chmod(0o600)
    from build import PARENT
    run([PARENT / "bin/shared_memory"], "probe-cache.log", PROBE)
    (PROBE / "input.json").write_text("{}")
    run([PROBE / "check-zone", "tests:balance", "input.json", "out.json"], "probe-run.log", PROBE)
    result = json.loads((PROBE / "out.json").read_bytes())
    assert result["real_item_casts"] == 2
    assert result["heal_on"] - result["heal_off"] == min(48, result["heal_off"] // 20) > 0
    assert result["strike_on"] - result["strike_off"] == min(48, result["strike_off"] // 20) == 48
    result["zone"] = sha(STAGE / "zone")
    result["diagnostic"] = sha(PROBE / "check-zone")
    result["shipping_objects"] = {n: sha(STAGE / (n + ".o")) for n in UNITS}
    result["cache_loader"] = sha(PARENT / "bin/shared_memory")
    write_json(STAGE / "cast.json", result)
    print(result)


if __name__ == "__main__":
    {"build": build, "run": execute}[sys.argv[1]]()

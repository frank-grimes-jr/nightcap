"""Link the headless zone driver with the candidate zone objects and Perl archive."""
import importlib.util
import json
from pathlib import Path
import subprocess

work = Path(__file__).resolve().parent
folder = work / "candidate"
spec = importlib.util.spec_from_file_location("equipment", "/tmp/nightcap-classic-equipment-paths-20261121/native.py")
equipment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(equipment)
b, build, objs = equipment.b, equipment.build, equipment.objs
args = list(equipment.m.args)
replacements = dict(equipment.m.rep)
replacements["spell_effects"] = equipment.OLD / "correction/candidate/spell_effects.o"
for name in json.loads((equipment.ORNAMENT / "build.json").read_bytes())["objects"]:
    if name.startswith("zone/"):
        unit = Path(name).stem
        replacements[unit] = equipment.ORNAMENT / "candidate" / (unit + ".o")
for unit in ("aa", "client", "client_mods", "effects", "mob", "spells"):
    replacements[unit] = folder / (unit + ".o")
for unit, path in replacements.items():
    args[args.index(str(objs / (unit + ".cpp.o")))] = str(path)
for index, arg in enumerate(args):
    if arg.endswith("/libcommon.a"):
        args[index] = str(equipment.ORNAMENT / "candidate/zone-libcommon.a")
    if arg.endswith("/libperl_zone.a"):
        args[index] = str(folder / "libperl_zone.a")

# Preserve the normal globals and services. Only the executable entry point changes.
main = objs / "main.cpp.o"
renamed = folder / "zone-main.o"
subprocess.run(["objcopy", "--redefine-sym", "main=nightcap_zone_main",
                str(build / main), str(renamed)], check=True)
args[args.index(str(main))] = str(renamed)
flags = b.ninja(build, str(main))
flags = flags[:flags.index("-MD")]
pch = flags.index("-include-pch")
del flags[pch-1:pch+3]
driver = folder / "zone-probe.o"
b.run([*flags, "-ivfsoverlay", str(folder / "vfs.json"), "-I" + str(equipment.src / "zone"),
       "-c", str(work / "zone_spell_probe.cpp"), "-o", str(driver)], build, folder / "probe-compile.log")
args.insert(args.index(str(renamed)), str(driver))
args[args.index("-o") + 1] = str(folder / "zone-qa")
b.run(args, build, folder / "probe-link.log")
print("Built zone integration test", b.sha(folder / "zone-qa"))

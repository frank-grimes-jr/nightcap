"""Rehearse the zone candidate with the retained November 21 shipping inputs."""
from pathlib import Path
import importlib.util
import json
import shutil
import subprocess
import sys

work = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("equipment", "/tmp/nightcap-classic-equipment-paths-20261121/native.py")
equipment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(equipment)
b, src, build, objs = equipment.b, equipment.src, equipment.build, equipment.objs
assert b.sha(equipment.R / "reproduced/zone") == equipment.EXPECTED
folder = work / "candidate"
folder.mkdir(exist_ok=True)
overlay = {r["name"]: Path(r["external-contents"]) for r in json.loads(
    (equipment.ORNAMENT / "candidate/vfs.json").read_bytes())["roots"]}
diff = (work / "zone.patch").read_bytes()
for line in diff.splitlines():
    if line.startswith(b"--- a/server-mods/code/"):
        rel = line.split(b"a/server-mods/code/", 1)[1].decode()
        key = str(src / rel)
        target = folder / "source" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(overlay.get(key, Path(key)).read_bytes().replace(b"\r\n", b"\n"))
        overlay[key] = target
target = folder / "source/common/cairnwright.h"
shutil.copyfile(work / "cairnwright.h", target)
overlay[str(src / "common/cairnwright.h")] = target
subprocess.run(["patch", "--binary", "--fuzz=0", "-p3"], cwd=folder/"source", input=diff, check=True)
vfs = folder / "vfs.json"
vfs.write_text(json.dumps({"version": 0, "use-external-names": False,
    "roots": [{"type":"file","name":key,"external-contents":str(value)} for key,value in overlay.items()]}))
pch = b.fresh_pch("shipping", build, objs, vfs, folder)
rep = dict(equipment.m.rep)
rep["spell_effects"] = equipment.OLD / "correction/candidate/spell_effects.o"
rep["aa"] = Path("/tmp/nightcap-aa-purchase-latency-20261121/candidate/aa.o")
for name in json.loads((equipment.ORNAMENT/"build.json").read_bytes())["objects"]:
    if name.startswith("zone/"):
        rep[Path(name).stem] = equipment.ORNAMENT/"candidate"/(Path(name).stem+".o")
for unit in ("aa", "client", "client_mods", "spells"):
    output = folder / (unit + ".o")
    b.compile_unit("shipping", unit, build, src, objs, pch, vfs, output)
    rep[unit] = output
    print("Compiled " + unit, flush=True)
args = [str(equipment.ORNAMENT/"candidate/zone-libcommon.a") if x.endswith("/libcommon.a") else x for x in equipment.m.args]
unity, = (p for p in (build/"zone/CMakeFiles/perl_zone.dir/Unity").glob("*.cxx") if "perl_client.cpp" in p.read_text())
unity_flags = b.ninja(build, str(unity.relative_to(build))+".o")
unity_obj = folder / (unity.name+".o")
b.run([*unity_flags[:unity_flags.index("-MD")], "-ivfsoverlay", str(vfs), "-c", str(unity), "-o", str(unity_obj)], build, folder/"perl.log")
archive_input, = (x for x in args if x.endswith("/libperl_zone.a"))
archive = folder/"libperl_zone.a"
shutil.copyfile(build/archive_input, archive)
subprocess.run(["ar","rcs",str(archive),str(unity_obj)],check=True)
args[args.index(archive_input)] = str(archive)
b.linker("shipping", folder, build, objs, args, rep)
print("Local candidate zone SHA-256", b.sha(folder/"zone"), flush=True)

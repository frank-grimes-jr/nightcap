"""Build the LocalDev memorization fix against its retained November 22 zone."""
import importlib.util
import json
from pathlib import Path

work = Path(__file__).resolve().parent
parent = Path("/tmp/cairnwright-lifecycle-final-20261121/candidate")
expected = "771122fc9f8b208eb9338f82df3c614288582a8ae9f5bd19ed7ed4c1b5665989"
spec = importlib.util.spec_from_file_location("equipment", "/tmp/nightcap-classic-equipment-paths-20261121/native.py")
eq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eq)
b, build, src, objs = eq.b, eq.build, eq.src, eq.objs
objects = dict(eq.m.rep)
objects["spell_effects"] = eq.OLD / "correction/candidate/spell_effects.o"
for name in json.loads((eq.ORNAMENT / "build.json").read_bytes())["objects"]:
    if name.startswith("zone/"):
        unit = Path(name).stem
        objects[unit] = eq.ORNAMENT / "candidate" / (unit + ".o")
for unit in ("aa", "client", "client_mods", "effects", "mob", "spells"):
    objects[unit] = parent / (unit + ".o")
args = list(eq.m.args)
for i, arg in enumerate(args):
    if arg.endswith("/libcommon.a"):
        args[i] = str(eq.ORNAMENT / "candidate/zone-libcommon.a")
    if arg.endswith("/libperl_zone.a"):
        args[i] = str(parent / "libperl_zone.a")
assert b.sha(parent / "zone") == expected
baseline = work / "baseline"
baseline.mkdir(exist_ok=True)
b.linker("shipping", baseline, build, objs, args.copy(), objects.copy())
assert b.sha(baseline / "zone") == expected, "parent link inputs changed"

overlay = json.loads((parent / "vfs.json").read_bytes())
entry, = [r for r in overlay["roots"] if r["name"] == str(src / "zone/client_process.cpp")]
old = Path(entry["external-contents"]).read_bytes()
patched = (work / "client_process.cpp").read_bytes().replace(b"\r\n", b"\n")
# The tracked overlay and the retained unit can differ outside this handler.
before = b"!IsPlayerClass(GetClass()) ||"
after = b"(!IsPlayerClass(GetClass()) && GetClass() != Cairnwright::ClassId) ||"
include = b'#include "../common/item_trade_policy.h"'
extra = b'#include "../common/cairnwright.h"'
assert old.count(before) == 1 and old.count(include) == 1 and old.count(after) == 0
assert patched.count(after) == 1 and patched.count(extra) == 1
unit = work / "retained-client_process.cpp"
unit.write_bytes(old.replace(before, after).replace(include, include + b"\n" + extra))
entry["external-contents"] = str(unit)
base_path = str(src / "zone/zone_base_data.cpp")
base_entry = next((r for r in overlay["roots"] if r["name"] == base_path), None)
base_source = Path(base_entry["external-contents"] if base_entry else base_path).read_text()
reviewed = (work / "zone_base_data.cpp").read_text()
stock_filter = "e.level < 1 || !IsPlayerClass(e.class_)"
updated_filter = "e.level < 1 || (!IsPlayerClass(e.class_) && e.class_ != Cairnwright::ClassId)"
assert base_source.count(stock_filter) == 1 and reviewed.count(updated_filter) == 1
assert reviewed == base_source.replace(stock_filter, updated_filter).replace(
    '#include "zone.h"', '#include "zone.h"\n#include "../common/cairnwright.h"'
).replace("l.size(),", "m_base_data.size(),").replace("l.size() != 1", "m_base_data.size() != 1")
if base_entry:
    base_entry["external-contents"] = str(work / "zone_base_data.cpp")
else:
    overlay["roots"].append({"type":"file","name":base_path,"external-contents":str(work / "zone_base_data.cpp")})
mods_entry, = [r for r in overlay["roots"] if r["name"] == str(src / "zone/client_mods.cpp")]
mods_source = Path(mods_entry["external-contents"]).read_text()
before_regen = "\t\t\tif (old)\n\t\t\t\tregen = std::max(regen, static_cast<int64>(2));"
reviewed_mods = (work/"client_mods.cpp").read_text()
start = reviewed_mods.index("\t\t\t// A novice Cairnwright")
end = reviewed_mods.index(before_regen, start)
assert mods_source.count(before_regen) == 1 and end > start
new_mods = work/"retained-client_mods.cpp"
new_mods.write_text(mods_source.replace(before_regen,reviewed_mods[start:end] + before_regen))
mods_entry["external-contents"] = str(new_mods)
vfs = work / "vfs.json"
vfs.write_text(json.dumps(overlay))
out = work / "candidate"
out.mkdir(exist_ok=True)
obj = out / "client_process.o"
b.compile_unit("shipping", "client_process", build, src, objs, parent / "zone.pch", vfs, obj)
objects["client_process"] = obj
base_obj = out / "zone_base_data.o"
b.compile_unit("shipping", "zone_base_data", build, src, objs, parent / "zone.pch", vfs, base_obj)
objects["zone_base_data"] = base_obj
mods_obj = out / "client_mods.o"
b.compile_unit("shipping", "client_mods", build, src, objs, parent / "zone.pch", vfs, mods_obj)
objects["client_mods"] = mods_obj
b.linker("shipping", out, build, objs, args.copy(), objects)
print("Parent", expected, "candidate", b.sha(out / "zone"), flush=True)

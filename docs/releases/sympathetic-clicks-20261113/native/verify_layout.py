"""Compile and run the eight-field probe with retained production libraries."""
import subprocess
from build import BUILD, OBJECTS, STAGE, link, ninja, run, write_json

args = ninja(OBJECTS + "main.cpp.o")
args = args[:args.index("-MD")]
obj = STAGE / "layout.o"
run([*args, "-o", obj, "-c", STAGE / "cache_layout.cpp"], "layout-compile.log")
# The engine's static initializers use its real rule manager. Keep the engine
# globals and paired libraries, giving the probe sole ownership of main().
parent_main = STAGE / "layout-engine-main.o"
run(["objcopy", "--redefine-sym", "main=RetainedEngineMain",
     BUILD / (OBJECTS + "main.cpp.o"), parent_main], "layout-main.log")
link(STAGE / "layout", {"main": parent_main}, [str(obj)])
values = subprocess.check_output([STAGE / "layout"], cwd=STAGE, text=True).strip().split()
fields = ("item_size", "ID", "CastTime_", "MaxCharges", "CastTime", "Click", "ClickName", "spell_size")
receipt = dict(zip(fields, map(int, values), strict=True))
assert receipt["item_size"] == 1332 and receipt["ID"] == 440
write_json(STAGE / "layout.json", receipt)
print(receipt)

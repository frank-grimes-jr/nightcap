"""Relink the LocalDev item cache generator with the Cairnwright world's item layout."""
from pathlib import Path
import hashlib
import sys

shipping = Path("/tmp/nightcap-ornaments-shipping-20261121")
world = Path("/tmp/cairnwright-lifecycle-final-20261121/world-candidate")
out = Path(__file__).resolve().parent
assert hashlib.sha256((world / "world").read_bytes()).hexdigest().startswith("a641bef7")
sys.path.insert(0, str(shipping))
import build_shipping as s

args = s.b.ninja(s.build, "bin/shared_memory")[2:-2]
args[args.index("bin/libcommon.a")] = str(shipping / "candidate/world-libcommon.a")
for unit in ("items", "main", "spells"):
    target = f"shared_memory/CMakeFiles/shared_memory.dir/{unit}.cpp.o"
    flags = s.b.ninja(s.build, target)
    obj = out / (unit + ".o")
    s.b.run([*flags[:flags.index("-MD")], "-ivfsoverlay", str(world / "vfs.json"), "-o", str(obj),
             "-c", str(s.source / "shared_memory" / (unit + ".cpp"))], s.build, out / (unit + ".log"))
    args[args.index(target)] = str(obj)
args[args.index("-o")+1] = str(out / "shared_memory")
s.b.run(args, s.build, out / "link.log")
print("Paired writer SHA-256", s.b.sha(out / "shared_memory"), flush=True)

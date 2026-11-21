"""Build a separate world with the current creation change and retained shipping inputs.

Supply world.patch against main, starter_provisions.h and cairnwright.h in this directory.
"""
import importlib.util
import json
from pathlib import Path
import subprocess

work = Path(__file__).resolve().parent
ornament = Path("/tmp/nightcap-ornaments-shipping-20261121")
spec = importlib.util.spec_from_file_location("ornaments", ornament / "build_shipping.py")
shipping = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shipping)
b, build, source = shipping.b, shipping.build, shipping.source

folder = work / "world-candidate"
folder.mkdir(exist_ok=True)
args = list(shipping.world_args)
args[args.index(str(shipping.rest / "libcommon.a"))] = str(ornament / "candidate/world-libcommon.a")
args[args.index("world/CMakeFiles/world.dir/worlddb.cpp.o")] = str(ornament / "candidate/worlddb.cpp.o")
shipping.link_world(folder, args)
expected = json.loads((ornament / "build.json").read_bytes())["binaries"]["world"]
assert b.sha(folder / "world") == expected, "Retained world inputs differ from the shipping build"

roots = json.loads((ornament / "candidate/vfs.json").read_bytes())["roots"]
mapping = {r["name"]: Path(r["external-contents"]) for r in roots}
key = str(source / "world/client.cpp")
out = folder / "client.cpp"
out.write_bytes(mapping.get(key, Path(key)).read_bytes().replace(b"\r\n", b"\n"))
subprocess.run(["patch", "--fuzz=0", "--binary", str(out)], input=(work / "world.patch").read_bytes(), check=True)
mapping[key] = out
mapping[str(source / "world/starter_provisions.h")] = work / "starter_provisions.h"
mapping[str(source / "common/cairnwright.h")] = work / "cairnwright.h"
vfs = folder / "vfs.json"
shipping.shipping.overlay(mapping, vfs)
target = "world/CMakeFiles/world.dir/client.cpp.o"
flags = b.ninja(build, target)
obj = folder / "client.cpp.o"
b.run([*flags[:flags.index("-MD")], "-ivfsoverlay", str(vfs), "-o", str(obj), "-c", key],
      build, folder / "compile.log")
args[args.index(target)] = str(obj)
shipping.link_world(folder, args)
print("Reproduced shipping world", expected)
print("Candidate world SHA-256", b.sha(folder / "world"))

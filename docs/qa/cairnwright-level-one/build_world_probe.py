"""Link the headless world integration driver against the already built candidate."""
from pathlib import Path
import importlib.util
import subprocess

work = Path(__file__).resolve().parent
ornament = Path("/tmp/nightcap-ornaments-shipping-20261121")
spec = importlib.util.spec_from_file_location("ornaments", ornament / "build_shipping.py")
shipping = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shipping)
b, build = shipping.b, shipping.build
folder = work / "world-candidate"
args = list(shipping.world_args)
def replace(key, value):
    args[args.index(key)] = str(value)
replace(str(shipping.rest / "libcommon.a"), ornament / "candidate/world-libcommon.a")
replace("world/CMakeFiles/world.dir/worlddb.cpp.o", ornament / "candidate/worlddb.cpp.o")
client = "world/CMakeFiles/world.dir/client.cpp.o"
replace(client, folder / "client.cpp.o")
# Keep world's ordinary global services, only rename its executable entry point.
main = "world/CMakeFiles/world.dir/main.cpp.o"
renamed = folder / "world-main.o"
subprocess.run(["objcopy", "--redefine-sym", "main=nightcap_world_main", str(build/main), str(renamed)],check=True)
replace(main,renamed)
flags = b.ninja(build, client)
obj = folder / "world-probe.o"
b.run([*flags[:flags.index("-MD")], "-ivfsoverlay", str(folder/"vfs.json"), "-o", str(obj),
       "-c", str(work/"world_creation_probe.cpp")], build, folder/"probe-compile.log")
args.insert(args.index(str(renamed)), str(obj))
args[args.index("-o")+1] = str(folder/"world-storage-qa")
b.run(args,build,folder/"probe-link.log")
print("Built headless world creation probe", b.sha(folder/"world-storage-qa"))

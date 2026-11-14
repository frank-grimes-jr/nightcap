"""Compare the compiler's Mob, Client and NPC sizes on both sides of the patch."""
import subprocess
from build import BUILD, OBJECTS, STAGE, compile_unit, write_json

s = STAGE / "actor-layout.cpp"
names = ("Mob", "Client", "NPC")
s.write_text('#include "zone/client.h"\n#include "zone/npc.h"\n' +
             "".join("char actor_size_" + n + "[sizeof(" + n + ")];\n" for n in names))
out = {}
for name, pch, overlay in (("parent", BUILD / (OBJECTS + "cmake_pch.hxx.pch"), None),
                           ("candidate", STAGE / "candidate.pch", STAGE / "vfs.json")):
    target = STAGE / ("actor-layout-" + name + ".o")
    compile_unit("main", target, pch, overlay, s)
    symbols = subprocess.check_output(["nm", "-S", "--defined-only", target], text=True)
    out[name] = {w[-1].removeprefix("actor_size_"): int(w[1], 16)
                 for line in symbols.splitlines() if (w := line.split())[-1].startswith("actor_size_")}
assert out["candidate"] == out["parent"] and set(out["parent"]) == set(names)
write_json(STAGE / "actor-layout.json", out)
print(out)

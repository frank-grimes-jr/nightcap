"""Reproduce the OVH zone from its Ninja inputs, then build the reviewed delta.

Run inside the local native build container after stage.py prepares the inputs.
The retained tree, build objects and supervisor are read-only inputs.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess

PARENT = Path("/tmp/nightcap-raid-augments-shipping-20261112-v3")
SOURCE = PARENT / "source"
BUILD = PARENT / "build"
STAGE = Path("/tmp/nightcap-sympathetic-shipping-20261113")
PREVIOUS = "a0506a169cd2481350f02b24468230825c52cd003936042f15d21b8addff7823"
UNITS = ("mob", "spells", "spell_effects", "special_attacks")
INPUTS = sorted(["mob.h", *(n + ".cpp" for n in UNITS)])
HEADERS = ["nightcap_sympathetic.h", "nightcap_sympathetic_eras.h"]
OBJECTS = "zone/CMakeFiles/zone.dir/"


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def ninja(target):
    rows = subprocess.check_output(["ninja", "-t", "commands", target], cwd=BUILD, text=True)
    return shlex.split(rows.splitlines()[-1])


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def run(args, log, cwd=BUILD):
    with (STAGE / log).open("w") as f:
        result = subprocess.run(args, cwd=cwd, stdout=f, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError((STAGE / log).read_text()[-5000:])


def compile_unit(name, out, pch, overlay, source=None, check_asserts=False):
    args = ninja(OBJECTS + name + ".cpp.o")
    args = args[:args.index("-MD")]
    args[1:1] = ["-ivfsoverlay", str(overlay)] if overlay else []
    if check_asserts:
        args.append("-UNDEBUG")
    args[args.index("-include-pch") + 2] = str(pch)
    run([*args, "-o", str(out), "-c", str(source or SOURCE / "zone" / (name + ".cpp"))],
        out.name + ".log")


def link(output, replacements, extra=()):
    args = ninja("bin/zone")
    assert args[:2] == [":", "&&"] and args[-2:] == ["&&", ":"]
    args = args[2:-2]
    for name, obj in replacements.items():
        args[args.index(OBJECTS + name + ".cpp.o")] = str(obj)
    args[args.index("-o") + 1] = str(output)
    args[1:1] = extra
    run(args, output.name + ".link.log")
    return sorted({x for x in args if x.endswith((".o", ".a", ".so", ".so.5.36"))})


def main():
    old = json.loads((STAGE / "production-verified.json").read_bytes())["binaries"]
    manifest = json.loads((PARENT / "inventory-shipping.json").read_bytes())
    assert old["zone"] == PREVIOUS
    for n, pin in manifest["shipping"].items():
        assert pin == old[n] == sha(PARENT / "bin" / n)
    for name, pin in manifest["verified_feature_sources"].items():
        assert sha(SOURCE / name) == pin, name
    proof = {"baseline": PREVIOUS, "paired_native": manifest["shipping"],
             "feature_predecessor": "862eb1ac", "feature_tip": "dceb54bd",
             "patch": sha(STAGE / "feature.patch")}
    inputs = link(STAGE / "relinked-base", {})
    assert sha(STAGE / "relinked-base") == sha(BUILD / "bin/zone")
    run(["objcopy", "--strip-debug", STAGE / "relinked-base", STAGE / "base"], "strip-base.log")
    assert sha(STAGE / "base") == PREVIOUS
    proof["unstripped_reference_relink"] = sha(STAGE / "relinked-base")
    write_json(STAGE / "link-inputs.json", {name: sha(BUILD / name) for name in inputs})
    proof.update(link_input_count=len(inputs), link_manifest_sha256=sha(STAGE / "link-inputs.json"))
    folder = STAGE / "source"
    (folder / "zone").mkdir(parents=True, exist_ok=True)
    for name in INPUTS:
        shutil.copyfile(SOURCE / "zone" / name, folder / "zone" / name)
    for name in HEADERS:
        assert not (SOURCE / "zone" / name).exists()
        (folder / "zone" / name).unlink(missing_ok=True)
    run(["patch", "--batch", "--forward", "--fuzz=0", "-p3", "-i", str(STAGE / "feature.patch")],
        "patch.log", folder)
    assert sorted(p.name for p in (folder / "zone").iterdir() if not p.name.endswith(".orig")) == sorted(INPUTS + HEADERS)
    proof["source_preimages"] = {name: sha(SOURCE / "zone" / name) for name in INPUTS}
    proof["source_postimages"] = {name: sha(folder / "zone" / name) for name in INPUTS + HEADERS}
    overlay = STAGE / "vfs.json"
    # Clang 14's VFS reader expects version first, as in LLVM's JSON writer.
    overlay.write_text(json.dumps({"version": 0, "use-external-names": False, "roots": [
        {"type": "file", "name": str(SOURCE / "zone" / name),
         "external-contents": str(folder / "zone" / name)} for name in INPUTS + HEADERS]}))
    args = ninja(OBJECTS + "cmake_pch.hxx.pch")
    prefix = args[:args.index("-MD")]
    pch = STAGE / "candidate.pch"
    run([*prefix, "-ivfsoverlay", str(overlay), "-o", str(pch), "-c", args[-1]], "pch.log")
    def one(name):
        original = BUILD / (OBJECTS + name + ".cpp.o")
        check = STAGE / ("base-" + name + ".o")
        compile_unit(name, check, BUILD / (OBJECTS + "cmake_pch.hxx.pch"), None)
        assert sha(check) == sha(original), "Predecessor object drift: " + name
        out = STAGE / (name + ".o")
        compile_unit(name, out, pch, overlay)
        return name, {"predecessor_rebuild": sha(check), "candidate": sha(out)}
    with ThreadPoolExecutor(3) as pool:
        proof["units"] = dict(pool.map(one, UNITS))
    link(STAGE / "candidate", {n: STAGE / (n + ".o") for n in UNITS})
    run(["objcopy", "--strip-debug", STAGE / "candidate", STAGE / "zone"], "strip-candidate.log")
    proof["unstripped_candidate"] = sha(STAGE / "candidate")
    proof["zone"] = sha(STAGE / "zone")
    proof["bytes"] = (STAGE / "zone").stat().st_size
    needed = subprocess.check_output(["ldd", STAGE / "zone"], text=True)
    assert "not found" not in needed and "libperl.so" in needed
    proof["linked_libraries"] = sorted(line.split()[0] for line in needed.splitlines() if "=>" in line)
    assert proof["linked_libraries"] == sorted(line.split()[0] for line in
        subprocess.check_output(["ldd", STAGE / "base"], text=True).splitlines() if "=>" in line)
    symbols = subprocess.check_output(["nm", "-C", STAGE / "zone"], text=True)
    assert "Mob::ApplySympatheticClick(" in symbols and "NightcapBalancePreflight" not in symbols
    proof["profile"] = "Clang 14 RelWithDebInfo -O2 -g0 -DNDEBUG; Lua, Perl, ENABLE_SECURITY"
    write_json(STAGE / "build.json", proof)
    print(proof["zone"], flush=True)


if __name__ == "__main__":
    main()

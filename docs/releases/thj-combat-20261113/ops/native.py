"""Relink the retained sympathetic build and compile only the isolated combat overlay.

Run inside the local build container. Production and local TEST use distinct ABIs.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shlex
import subprocess

ROOT = Path("/tmp/nightcap-thj-combat-20261113")
SHIP = Path("/tmp/nightcap-sympathetic-shipping-20261113")
LOCAL = Path("/tmp/nightcap-sympathetic-local-test-20261113")
RAID = Path("/tmp/nightcap-raid-augments-shipping-20261112-v3")
PINS = {
    "shipping": "b462f5fce2f6e2a38e25ec4d3eda81c9efac16b59f39c764fa5a4d1bdd52d7f2",
    "local": "fa821145a3389e9f5f61d24f7699d32b7103c6a0d08f1318e5fd6c2fdfda7f33",
}


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n")


def run(command, build, log):
    with log.open("wb") as stream:
        result = subprocess.run(command, cwd=build, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(log.read_text(errors="replace")[-4000:])


def ninja(build, target):
    output = subprocess.check_output(["ninja", "-t", "commands", target], cwd=build, text=True)
    return shlex.split(output.splitlines()[-1])


def context(profile):
    if profile == "shipping":
        source = RAID / "source"
        build = RAID / "build"
        objects = Path("zone/CMakeFiles/zone.dir")
        previous = SHIP / "zone"
        manifest = load(SHIP / "build.json")
        assert sha(SHIP / "link-inputs.json") == manifest["link_manifest_sha256"]
        for name, pin in load(SHIP / "link-inputs.json").items():
            assert sha(build / name) == pin, name
        replacements = {k: SHIP / (k + ".o") for k in manifest["units"]}
        assert all(sha(f) == manifest["units"][n]["candidate"] for n, f in replacements.items())
        link = ninja(build, "bin/zone")
        assert link[:2] == [":", "&&"] and link[-2:] == ["&&", ":"]
        link = link[2:-2]
        old_overlay = SHIP / "vfs.json"
        pch = SHIP / "candidate.pch"
    else:
        source = Path("/home/eqemu/code")
        build = source / "build/zone"
        objects = Path("CMakeFiles/zone.dir")
        previous = LOCAL / "candidate/zone"
        manifest = load(LOCAL / "candidate/object-hashes.json")
        replacements = {k: LOCAL / "candidate" / (k + ".o") for k in manifest}
        assert all(sha(f) == manifest[n]["built"] for n, f in replacements.items())
        link = shlex.split((build / objects / "link.txt").read_text())
        old_overlay = LOCAL / "candidate/vfs.json"
        pch = LOCAL / "candidate/zone.pch"
    assert sha(previous) == PINS[profile]
    return source, build, objects, previous, replacements, link, old_overlay, pch


def linker(profile, folder, build, objects, args, replacements):
    args = list(args)
    for n, path in replacements.items():
        args[args.index(str(objects / (n + ".cpp.o")))] = str(path)
    binary = folder / ("zone.unstripped" if profile == "shipping" else "zone")
    args[args.index("-o") + 1] = str(binary)
    run(args, build, folder / "link.log")
    if profile == "shipping":
        run(["objcopy", "--strip-debug", binary, folder / "zone"], build, folder / "strip.log")
    return sorted({str(a) for a in args if str(a).endswith((".a", ".o", ".so", ".so.5.36"))})


def compile_unit(profile, name, build, source, objects, pch, overlay, out):
    if profile == "shipping":
        args = ninja(build, str(objects / (name + ".cpp.o")))
        args = args[:args.index("-MD")]
        args[args.index("-include-pch") + 2] = str(pch)
    else:
        flags = dict(line.split(" = ", 1) for line in (build / objects / "flags.make").read_text().splitlines()
                     if line.startswith(("CXX_DEFINES = ", "CXX_FLAGS = ", "CXX_INCLUDES = ")))
        args = ["/usr/bin/clang++"]
        for k in ("CXX_DEFINES", "CXX_INCLUDES", "CXX_FLAGS"):
            args.extend(shlex.split(flags[k]))
        args.extend(["-Xclang", "-include-pch", "-Xclang", str(pch), "-Xclang", "-include", "-Xclang",
                     str(build / objects / "cmake_pch.hxx")])
    args[1:1] = ["-ivfsoverlay", str(overlay)]
    run([*args, "-o", str(out), "-c", str(source / "zone" / (name + ".cpp"))], build, out.with_suffix(".log"))


def fresh_pch(profile, build, objects, overlay, folder):
    pch = folder / "zone.pch"
    if profile == "shipping":
        args = ninja(build, str(objects / "cmake_pch.hxx.pch"))
        prefix = args[:args.index("-MD")]
        command = [*prefix, "-ivfsoverlay", str(overlay), "-o", str(pch), "-c", args[-1]]
    else:
        flags = dict(line.split(" = ",1) for line in (build / objects / "flags.make").read_text().splitlines()
                     if line.startswith(("CXX_DEFINES = ", "CXX_FLAGS = ", "CXX_INCLUDES = ")))
        command = ["/usr/bin/clang++"]
        for k in ("CXX_DEFINES","CXX_INCLUDES","CXX_FLAGS"):
            command.extend(shlex.split(flags[k]))
        command.extend(["-ivfsoverlay", str(overlay), "-Xclang", "-fpch-instantiate-templates",
                        "-x", "c++-header", "-o", str(pch), str(build / objects / "cmake_pch.hxx")])
    run(command, build, folder / "pch.log")
    return pch


def main(profile, phase):
    source, build, objects, previous, replacements, args, old_overlay, pch = context(profile)
    folder = ROOT / profile / phase
    folder.mkdir(parents=True, exist_ok=True)
    proof = {"profile": profile, "baseline": sha(previous), "original_pch": sha(pch)}
    before = load(old_overlay)
    previous_files = {str(Path(r["name"]).relative_to(source)): Path(r["external-contents"]) for r in before["roots"]}
    if phase == "baseline":
        names = linker(profile, folder, build, objects, args, replacements)
        pins = {n: sha(build / n) for n in names}
        save(folder / "link-inputs.json", pins)
        proof.update(link_input_count=len(names), link_manifest_sha256=sha(folder / "link-inputs.json"))
        assert sha(folder / "zone") == PINS[profile], "Retained objects did not reproduce running binary"
    else:
        baseline = ROOT / profile / "baseline"
        assert sha(baseline / "zone") == PINS[profile]
        sources = sorted(p for p in (folder / "source").rglob("*") if p.is_file())
        assert sources and all(p.suffix in (".cpp", ".h", ".inc") for p in sources)
        updated = {str(p.relative_to(folder / "source")): p for p in sources}
        tree = {**previous_files, **updated}
        overlay = folder / "vfs.json"
        overlay.write_text(json.dumps({"version": 0, "use-external-names": False, "roots": [
            {"type":"file","name":str(source / n),"external-contents":str(p)} for n,p in tree.items()]}))
        candidate_pch = fresh_pch(profile,build,objects,overlay,folder)
        proof["source_preimages"] = {}
        proof["source_postimages"] = {p.name: sha(p) for p in sources}
        proof["units"] = {}
        for p in sources:
            key = str(p.relative_to(folder / "source"))
            original = previous_files.get(key, source / key)
            proof["source_preimages"][p.name] = sha(original) if original.exists() else None
            if p.suffix != ".cpp":
                continue
            name = p.stem
            old = replacements.get(name, build / objects / (name + ".cpp.o"))
            check = folder / ("base-" + name + ".o")
            compile_unit(profile, name, build, source, objects, pch, old_overlay, check)
            assert sha(check) == sha(old), "Unchanged object source drift: " + name
            candidate = folder / (name + ".o")
            compile_unit(profile, name, build, source, objects, candidate_pch, overlay, candidate)
            replacements[name] = candidate
            proof["units"][name] = {"predecessor":sha(old), "candidate":sha(candidate)}
        names = linker(profile, folder, build, objects, args, replacements)
        assert proof["units"] and sha(folder / "zone") != PINS[profile]
        ld = subprocess.check_output(["ldd", folder / "zone"], text=True)
        assert "not found" not in ld
        assert sorted(l.split()[0] for l in ld.splitlines() if "=>" in l) == sorted(l.split()[0] for l in
            subprocess.check_output(["ldd", previous], text=True).splitlines() if "=>" in l)
        save(folder / "link-inputs.json", {n:sha(build / n) for n in names})
        proof.update(link_input_count=len(names), link_manifest_sha256=sha(folder / "link-inputs.json"))
    proof["zone"] = sha(folder / "zone")
    save(folder / "build.json", proof)
    print(json.dumps(proof), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("profile", choices=PINS)
    p.add_argument("phase", choices=("baseline","bow","combined"))
    args = p.parse_args()
    main(args.profile, args.phase)

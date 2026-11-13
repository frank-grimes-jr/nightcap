"""Build the narrowly backported local zone against the exact running link inputs.

Runs inside the local akk-stack game container. VFS overlays keep the original
compiler paths (and __FILE__) without modifying the active source or its objects.
"""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys


STAGE = Path("/tmp/nightcap-sympathetic-local-test-20261113")
SRC = Path("/home/eqemu/code")
BUILD = SRC / "build/zone"
OBJECTS = BUILD / "CMakeFiles/zone.dir"
ZONE = SRC / "build/bin/zone"
BASELINE = "b22a5340fa2cc5647975591186b9c381ea796c5850fa9e782372dfe69125775f"
SEPTEMBER_SPELLS = Path("/tmp/nightcap-hosted-build-20260920/source/zone/spells.cpp")
SPELL_SOURCE = "f30c8b53ba3928d2913bc2ced07a2d6d8398124846033eb9fa6c1ce12b13ca0d"
UNITS = ("spells", "spell_effects", "mob", "special_attacks")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main(mode):
    assert digest(ZONE) == BASELINE and digest(STAGE / "zone-baseline") == BASELINE
    assert digest(SEPTEMBER_SPELLS) == SPELL_SOURCE
    folder = STAGE / mode
    folder.mkdir(exist_ok=True)
    flags = dict(line.split(" = ", 1) for line in (OBJECTS / "flags.make").read_text().splitlines()
                 if line.startswith(("CXX_DEFINES = ", "CXX_FLAGS = ", "CXX_INCLUDES = ")))
    command = ["/usr/bin/clang++"]
    for key in ("CXX_DEFINES", "CXX_INCLUDES", "CXX_FLAGS"):
        command.extend(shlex.split(flags[key]))
    replacements = {"spells.cpp": SEPTEMBER_SPELLS}
    if mode == "candidate":
        replacements.update({file.name: file for file in (STAGE / "adapter").iterdir()
                             if file.suffix in (".cpp", ".h")})
    tree = {"version": 0, "use-external-names": False, "roots": [
        {"type": "file", "name": str(SRC / "zone" / name), "external-contents": str(path)}
        for name, path in replacements.items()]}
    overlay = folder / "vfs.json"
    overlay.write_text(json.dumps(tree))
    command += ["-ivfsoverlay", str(overlay)]
    # Create a matching fresh PCH for both builds. It includes mob.h.
    pch = folder / "zone.pch"
    subprocess.run(command + ["-Xclang", "-fpch-instantiate-templates", "-x", "c++-header",
                               "-o", str(pch), str(OBJECTS / "cmake_pch.hxx")], cwd=BUILD, check=True)
    command += ["-Xclang", "-include-pch", "-Xclang", str(pch),
                "-Xclang", "-include", "-Xclang", str(OBJECTS / "cmake_pch.hxx")]
    link = shlex.split((OBJECTS / "link.txt").read_text())
    manifest = {}
    for name in UNITS:
        target = folder / (name + ".o")
        source = SRC / "zone" / (name + ".cpp")
        subprocess.run(command + ["-o", str(target), "-c", str(source)], cwd=BUILD, check=True)
        original = "CMakeFiles/zone.dir/" + name + ".cpp.o"
        manifest[name] = {"built": digest(target), "installed_input": digest(BUILD / original),
                          "source": digest(replacements.get(source.name, source))}
        link[link.index(original)] = str(target)
        print(name, manifest[name], flush=True)
    (folder / "object-hashes.json").write_text(json.dumps(manifest, indent=2) + "\n")
    if mode == "baseline":
        if any(result["built"] != result["installed_input"] for result in manifest.values()):
            raise RuntimeError("Investigate object differences before using this backport")
        return
    baseline = json.loads((STAGE / "baseline/object-hashes.json").read_bytes())
    assert all(result["built"] == result["installed_input"] for result in baseline.values())
    target = folder / "zone"
    # The original binary and reference relink compare byte-for-byte using
    # its original linker. Candidate links use the same toolchain and flags.
    link[link.index("-o") + 1] = str(target)
    subprocess.run(link, cwd=BUILD, check=True)
    print("Complete candidate", digest(target), flush=True)


if __name__ == "__main__":
    if sys.argv[1:] not in (["baseline"], ["candidate"]):
        raise SystemExit("Specify baseline or candidate")
    main(sys.argv[1])

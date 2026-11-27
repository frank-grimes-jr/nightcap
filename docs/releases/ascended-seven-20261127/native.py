"""Rebuild one loot object inside the retained, isolated November 27 compiler."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, "/work")
import build as compiler

STAGE = Path("/work/ascended-seven")
OUTPUT = Path("/tmp/ascended-seven-20261127")
SHIPPING = "d150d164b19f8e0da21b571067b544947b8cebdc119a0053a391136edb06da0b"
CURRENT_VFS = compiler.out / "contract/vfs.json"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(name, value):
    (STAGE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def source_from(overlay, path):
    return next((Path(e["external-contents"]) for e in overlay["roots"] if e["name"] == str(path)), path)


def dependencies(binary):
    output = subprocess.check_output(["ldd", "-r", binary], text=True, stderr=subprocess.STDOUT)
    if "not found" in output or "undefined symbol" in output:
        raise ValueError("Unresolved runtime dependency")
    return sorted(line.split(" => ")[0].strip() for line in output.splitlines() if " => " in line)


def smoke(binary):
    # Exercise real startup in the network-isolated builder with an empty game directory.
    with tempfile.TemporaryDirectory(prefix="ascended-seven-smoke-") as cwd:
        run = subprocess.run([binary], cwd=cwd, capture_output=True, text=True, timeout=25)
    output = run.stdout + run.stderr
    assert run.returncode == 1 and "Loading server configuration failed" in output
    assert "Connecting to MySQL" not in output
    return {"exit_code": run.returncode, "reached": "configuration load", "missing_config_rejected": True}


def run(phase):
    shipping = json.loads((compiler.stage / "contract-link.json").read_bytes())
    assert shipping["zone"] == digest(compiler.out / "contract/zone") == SHIPPING
    objects = {
        "loot": str(compiler.out / "candidate/loot.o"),
        "client_packet": str(compiler.out / "candidate/client_packet.o"),
        "dungeon_service": str(compiler.out / "contract/dungeon_service.o"),
    }
    for path in objects.values():
        assert digest(Path(path)) == shipping["inputs"][path]
    folder = OUTPUT / ("final" if phase == "candidate" else phase)
    folder.mkdir(parents=True, exist_ok=True)
    overlay = json.loads(CURRENT_VFS.read_bytes())
    path = compiler.source / "zone/loot.cpp"
    original = source_from(overlay, path)
    if phase == "smoke":
        receipt_path = STAGE / "native-build.json"
        result = json.loads(receipt_path.read_bytes())
        assert digest(OUTPUT / "final/zone") == result["zone"]
        result["baseline_smoke"] = smoke(OUTPUT / "baseline/zone")
        result["candidate_smoke"] = smoke(OUTPUT / "final/zone")
        save("native-build.json", result)
        print("Both Linux game binaries reached the expected configuration check", flush=True)
        return
    if phase == "baseline":
        # Use the effective objects and source that produced the shipping link.
        pins = compiler.link(objects, folder)
        assert pins == shipping["inputs"] and digest(folder / "zone") == SHIPPING
        fresh = folder / "loot.o"
        compiler.compile("loot", CURRENT_VFS, fresh)
        assert digest(fresh) == shipping["inputs"][objects["loot"]]
        save("baseline.json", {"reproduced_zone": SHIPPING, "verified_link_inputs": len(pins),
                              "reproduced_loot_object": digest(fresh), "loot_source_lf": digest(original)})
        print("Reproduced shipping zone and loot object", SHIPPING, flush=True)
        return
    assert digest(OUTPUT / "baseline/zone") == SHIPPING
    source_dir = folder / "source"
    updated = source_dir / "zone/loot.cpp"
    updated.parent.mkdir(parents=True, exist_ok=True)
    updated.write_bytes(original.read_bytes().replace(b"\r\n", b"\n"))
    patch = STAGE / "loot.patch"
    assert patch.read_bytes().count(b"diff --git ") == 1
    subprocess.run(["patch", "--batch", "--forward", "--fuzz=0", "-p3", "-i", patch],
                   cwd=source_dir, check=True)
    assert updated.read_bytes() == (STAGE / "reviewed-loot.cpp").read_bytes().replace(b"\r\n", b"\n")
    entry = next((r for r in overlay["roots"] if r["name"] == str(path)), None)
    if entry:
        entry["external-contents"] = str(updated)
    else:
        overlay["roots"].append({"type": "file", "name": str(path), "external-contents": str(updated)})
    vfs = folder / "vfs.json"
    vfs.write_text(json.dumps(overlay))
    new_object = folder / "loot.o"
    compiler.compile("loot", vfs, new_object)
    previous = objects["loot"]
    historical = json.loads((compiler.stage / "baseline-link.json").read_bytes())
    historic_loot, = [pin for name, pin in historical["inputs"].items() if name.endswith("/loot.cpp.o")]
    assert digest(new_object) == historic_loot
    assert digest(new_object) != shipping["inputs"][previous]
    objects["loot"] = str(new_object)
    pins = compiler.link(objects, folder)
    same = shipping["inputs"].keys() & pins.keys()
    assert len(pins) == 144 and len(same) == 143
    assert all(pins[p] == shipping["inputs"][p] for p in same)
    binary = folder / "zone"
    assert dependencies(binary) == dependencies(OUTPUT / "baseline/zone")
    sha = digest(binary)
    assert sha != SHIPPING
    shutil.copyfile(binary, STAGE / "zone")
    assert digest(STAGE / "zone") == sha
    save("native-build.json", {"previous_zone": SHIPPING, "reproduced_zone": SHIPPING, "zone": sha,
                              "source_before_lf": digest(original), "source_after_lf": digest(updated),
                              "patch_sha256": digest(patch), "translation_unit": "zone/loot.cpp",
                              "previous_and_reproduced_object": shipping["inputs"][previous],
                              "candidate_object": digest(new_object), "matches_pre_armor_boost_object": True, "retained_link_inputs": len(same),
                              "total_link_inputs": len(pins), "resolved_dynamic_dependencies": dependencies(binary),
                              "runtime_activation": "pending"})
    print("Built and checked zone", sha, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("baseline", "candidate", "smoke"))
    run(parser.parse_args().phase)

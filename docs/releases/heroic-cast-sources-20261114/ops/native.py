"""Rebuild on the actual retained bow/Backstab sources and linker command."""
import argparse
import importlib.util
from pathlib import Path
import subprocess

ROOT = Path("/tmp/nightcap-heroic-cast-sources-20261114")
PREVIOUS = Path("/tmp/nightcap-thj-combat-20261113")
spec = importlib.util.spec_from_file_location("combat_builder", PREVIOUS / "native.py")
combat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(combat)
base_context = combat.context
BASE_BOW = dict(combat.PINS)
PINS = {
    "shipping":"ad119ac221bc6e46e7770827e2777d75a6f0937c9632f88512a169ce20525e00",
    "local":"3bdbedeb535e41c361c1a824fc8af95192046888e0f81768a668298ab20c5bd3",
}
MANIFESTS = {
    "shipping":"d751cb495ee00946414c8ff3d2437b38111cf949e113f2f0a412eb84f213c887",
    "local":"ac85422b11f6931c4d7e95d56de670825334617d68d7a4cb9aa13fd92b7cbe6b",
}


def context(profile):
    combat.PINS = BASE_BOW
    try:
        source, build, objects, _, replacements, args, _, _ = base_context(profile)
    finally:
        combat.PINS = PINS
    parent = PREVIOUS / profile / "combined"
    evidence = combat.load(parent / "build.json")
    assert evidence["zone"] == PINS[profile] == combat.sha(parent / "zone")
    assert combat.sha(parent / "link-inputs.json") == evidence["link_manifest_sha256"] == MANIFESTS[profile]
    for n,pin in combat.load(parent / "link-inputs.json").items():
        assert combat.sha(build/n) == pin, n
    for n,unit in evidence["units"].items():
        obj = parent / (n + ".o")
        assert combat.sha(obj) == unit["candidate"]
        replacements[n] = obj
    return source, build, objects, parent/"zone", replacements, args, parent/"vfs.json", parent/"zone.pch"


def prepare(profile):
    assert profile == "shipping"
    source, _, _, _, _, _, vfs, _ = context(profile)
    patch = ROOT / "feature.patch"
    names = [s.split("+++ b/server-mods/code/", 1)[1] for s in patch.read_text().splitlines()
             if s.startswith("+++ b/server-mods/code/")]
    assert names and len(names) == len(set(names))
    exist = {r["name"]:Path(r["external-contents"]) for r in combat.load(vfs)["roots"]}
    folder = ROOT/profile/"candidate/source"
    folder.mkdir(parents=True)
    for n in names:
        assert n.startswith(("common/","zone/")) and ".." not in n and Path(n).suffix in (".h",".cpp",".inc")
        original = exist.get(str(source/n), source/n)
        target = folder/n
        target.parent.mkdir(exist_ok=True, parents=True)
        if original.exists():
            target.write_bytes(original.read_bytes().replace(b"\r\n",b"\n"))
    result = subprocess.run(["patch","--batch","--forward","--no-backup-if-mismatch","--fuzz=0","-p3"],
                            cwd=folder, input=patch.read_bytes().replace(b"\r\n",b"\n"),
                            stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (folder.parent/"patch.log").write_bytes(result.stdout)
    if result.returncode:
        raise RuntimeError(result.stdout.decode(errors="replace"))
    assert all((folder/n).is_file() for n in names)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("profile",choices=list(PINS))
    parser.add_argument("phase",choices=("baseline","candidate"))
    args = parser.parse_args()
    combat.ROOT,combat.PINS,combat.context = ROOT,PINS,context
    if args.phase == "candidate":
        prepare(args.profile)
    combat.main(args.profile,args.phase)

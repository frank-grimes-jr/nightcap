"""Prepare an isolated source overlay using exact feature hunks and dated native inputs."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess

ROOT = Path("/tmp/nightcap-thj-combat-20261113")
SHIP = Path("/tmp/nightcap-sympathetic-shipping-20261113")
LOCAL = Path("/tmp/nightcap-sympathetic-local-test-20261113")


def replace_one(path, a, b):
    text = path.read_text()
    assert text.count(a) == 1, (path, a)
    path.write_text(text.replace(a, b))


def main(profile, phase):
    shipping = profile == "shipping"
    source = (Path("/tmp/nightcap-raid-augments-shipping-20261112-v3/source") if shipping
              else Path("/home/eqemu/code"))
    vfs = SHIP / "vfs.json" if shipping else LOCAL / "candidate/vfs.json"
    existing = {Path(r["name"]): Path(r["external-contents"]) for r in json.loads(vfs.read_text())["roots"]}
    folder = ROOT / profile / phase / "source"
    folder.mkdir(parents=True,exist_ok=True)
    bow = ROOT / "bow.patch"
    patches = [bow] if phase == "bow" else [bow, ROOT / "backstab.patch"]
    for patch in patches:
        assert patch.is_file()
    all_names = {s.split("+++ b/server-mods/code/",1)[1] for p in patches for s in p.read_text().splitlines()
                 if s.startswith("+++ b/server-mods/code/")}
    for n in all_names:
        assert n.startswith(("common/","zone/")) and ".." not in n
        orig = existing.get(source / n, source / n)
        dest = folder / n
        dest.parent.mkdir(exist_ok=True)
        if orig.exists():
            shutil.copyfile(orig, dest)
        elif not shipping and n == "common/nightcap_melee.h":
            # This September build predates the melee header. Only the new bow
            # function is referenced by its combat adapter.
            shutil.copyfile(Path("/tmp/nightcap-raid-augments-shipping-20261112-v3/source") / n, dest)
    for n in all_names:
        dest = folder / n
        if dest.exists():
            dest.write_bytes(dest.read_bytes().replace(b"\r\n", b"\n"))
        dest.with_suffix(dest.suffix + ".rej").unlink(missing_ok=True)
    for i, p in enumerate(patches):
        cmd = ["patch","--batch","--forward","--no-backup-if-mismatch","--fuzz=0","-p3"]
        patch_text = p.read_text()
        if not shipping and p.name == "backstab.patch":
            # September's immediately preceding skill_to_use guard has no
            # braces. Apply the same one-line hunk against its exact preimage.
            starts = [i for i in range(len(patch_text)) if patch_text.startswith("@@ -", i) and
                      "void Client::DoClassAttacks(" in patch_text[i:patch_text.index("\n",i)]]
            assert len(starts) == 1
            start = starts[0]
            tail = patch_text[start:]
            assert tail.count("@@") == 2 and tail.count("\n-") == 1 and tail.count("\n+") == 3
            old_line, = [s[1:] for s in tail.splitlines() if s.startswith("-")]
            new_lines = "\n".join(s[1:] for s in tail.splitlines() if s.startswith("+"))
            patch_text = patch_text[:start]
            replace_one(folder / "zone/special_attacks.cpp",old_line,new_lines)
        result = subprocess.run(cmd, cwd=folder, input=patch_text, capture_output=True, text=True)
        (folder.parent / ("patch-"+str(i)+".log")).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
    if not shipping:
        header = folder / "common/nightcap_melee.h"
        data = header.read_text()
        header.write_text(data[:data.index("constexpr int HolyShieldAbility")] +
                          data[data.index("inline int64_t ScaleNormalBowHit"):])
        attack = folder / "zone/attack.cpp"
        replace_one(attack, '#include "common/data_verification.h"', '#include "common/nightcap_melee.h"\n#include "common/data_verification.h"')
        replace_one(attack, "normal_bow ? HasCombatClass(Class::Ranger)", "normal_bow ? CastToClient()->IsMulticlassMember(Class::Ranger)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("profile", choices=("shipping","local"))
    p.add_argument("phase", choices=("bow","combined"))
    args = p.parse_args()
    main(args.profile,args.phase)

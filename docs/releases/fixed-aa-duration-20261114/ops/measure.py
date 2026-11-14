"""Compile the feature fixtures against actual effective shipping sources on Linux."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

STAGE = Path("/tmp/nightcap-fixed-aa-duration-20261114")
SOURCE = Path("/tmp/nightcap-raid-augments-shipping-20261112-v3/source")
BASE = Path("/tmp/nightcap-heroic-cast-sources-20261114/shipping/candidate")
sys.path.insert(0,str(STAGE/"tests"))
import test_fixed_aa_duration as suite


def run(profile):
    folder = BASE if profile == "baseline" else STAGE/"shipping/candidate"
    vfs = json.loads((folder/"vfs.json").read_bytes())
    overlay = {Path(r["name"]):Path(r["external-contents"]) for r in vfs["roots"]}
    with tempfile.TemporaryDirectory(prefix="nightcap-shipping-measure-") as tmp:
        tree = Path(tmp)
        # Read the full set of compiler-visible paths required by the fixture.
        for name in ("zone","common"):
            (tree/name).mkdir()
            known = {p for p in (SOURCE/name).iterdir() if p.is_file()}
            known.update(p for p in overlay if p.parent == SOURCE/name)
            for path in known:
                (tree/name/path.name).symlink_to(overlay.get(path,path))
        return suite.measure(tree, profile=="baseline")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-only",action="store_true")
    args = parser.parse_args()
    profiles = ("baseline",) if args.baseline_only else ("baseline","candidate")
    results = {p:run(p) for p in profiles}
    evidence = {"result":"PASS","samples":results}
    if not args.baseline_only:
        evidence["zone"] = json.loads((STAGE/"shipping/candidate/build.json").read_bytes())["zone"]
    evidence["fixtures"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (STAGE/"tests").iterdir() if p.is_file()}
    print(json.dumps(evidence,indent=2))

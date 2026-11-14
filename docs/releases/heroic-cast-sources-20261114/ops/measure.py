"""Compile the feature fixtures against actual effective shipping sources on Linux."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

STAGE = Path("/tmp/nightcap-heroic-cast-sources-20261114")
SOURCE = Path("/tmp/nightcap-raid-augments-shipping-20261112-v3/source")
BASE = Path("/tmp/nightcap-thj-combat-20261113/shipping/combined")
sys.path.insert(0,str(STAGE/"tests"))
import test_heroic_cast_origin as suite


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
        values = suite.measure(tree)
    suite.verify(values["samples"],profile=="candidate")
    return dict(source_sha256=values["sha256"],scenarios=len({r['scenario'] for r in values['samples']}),
                rows=len(values["samples"]), output_sha256=hashlib.sha256(
                    json.dumps(values["samples"],sort_keys=True,separators=(",",":")).encode()).hexdigest())


if __name__ == "__main__":
    receipts = {p:run(p) for p in ("baseline","candidate")}
    assert receipts["baseline"]["output_sha256"] != receipts["candidate"]["output_sha256"]
    fixtures = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (STAGE/"tests").iterdir() if p.is_file()}
    print(json.dumps(dict(result="PASS",samples=receipts,fixtures=fixtures),indent=2))

"""Stage only the authenticated zone, then invoke the predecessor's locked controls."""
import argparse
import importlib.util
import io
import json
import subprocess
import tarfile
import re

from probe import ARTIFACTS, HERE, ROOT, SSH, STAGE, remote, write

PARENT = ROOT / "docs/releases/thj-combat-20261113/ops"
spec = importlib.util.spec_from_file_location("combat_control", PARENT/"control.py")
combat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(combat)


digest = combat.digest


def stage(revision):
    assert re.fullmatch("[0-9a-f]{40}", revision)
    before = json.loads((HERE / "production-before.json").read_bytes())
    build = json.loads((HERE / "shipping-candidate.json").read_bytes())
    assert build["feature_patch_sha256"] == digest((HERE / "feature.patch").read_bytes())
    measured = json.loads((HERE / "shipping-measurement.json").read_bytes())
    assert measured["result"] == "PASS" and all(v["rows"] == 190 for v in measured["samples"].values())
    for name, pin in measured["samples"]["candidate"]["source_sha256"].items():
        n = name.split("/")[-1]
        assert n not in build["source_postimages"] or pin == build["source_postimages"][n]
    files = {"release.py": (HERE / "release.py").read_bytes().replace(b"\r\n", b"\n"),
             "bin/zone": (ARTIFACTS / "zone").read_bytes(), "build.json": (HERE / "shipping-candidate.json").read_bytes()}
    pins = {n:digest(data) for n,data in files.items()}
    assert build["zone"] == pins["bin/zone"] and before["base_hashes"]["bin/zone"] == build["baseline"]
    manifest = dict(stage=STAGE, source_revision=revision, files=pins, client_release=2026111301,
        client_channel_sha256=before["channel"], prior_operator=before["prior_operator"],
        prior_receipt=before["prior_receipt"], base_image_id=before["services"]["game"]["image_id"],
        feature_patch_sha256=build["feature_patch_sha256"], base_hashes=before["base_hashes"], baseline_services=before["services"], binaries={"zone":build["zone"]})
    files["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    archive = ARTIFACTS / (STAGE + ".tar.gz")
    with tarfile.open(archive, "w:gz") as container:
        for name, data in files.items():
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            container.addfile(entry, io.BytesIO(data))
    upload = "/home/ubuntu/" + STAGE + ".tar.gz"
    subprocess.run(SSH[:-1] + ["test ! -e " + upload + " && test ! -e /opt/nightcap/releases/" + STAGE], check=True)
    subprocess.run(["C:/Windows/System32/OpenSSH/scp.exe", *SSH[1:-2], str(archive), SSH[-2] + ":" + upload],
                   check=True, timeout=600)
    code = """
import fcntl, hashlib, os, tarfile
from pathlib import Path
os.umask(0o077)
source = Path(upload)
dest = Path('/opt/nightcap/releases') / stage
with Path('/opt/nightcap/deploy/production/.deployment.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    assert not dest.exists() and hashlib.sha256(source.read_bytes()).hexdigest()==expected
    temp = dest.with_suffix('.staging')
    temp.mkdir(mode=0o700)
    with tarfile.open(source) as tar:
        members = tar.getmembers()
        assert len(members)==len(pins) and set(pins)=={m.name for m in members}
        for m in members:
            file = temp / m.name
            assert m.isfile() and file.resolve().is_relative_to(temp)
            data = tar.extractfile(m).read()
            assert hashlib.sha256(data).hexdigest()==pins[m.name]
            file.parent.mkdir(exist_ok=True)
            with file.open('xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            file.chmod(0o755 if m.name=='bin/zone' else 0o600)
    temp.rename(dest)
    source.unlink()
    print(dest.name)
"""
    print(remote("upload=" + repr(upload) + "\nstage=" + repr(STAGE) + "\nexpected=" +
                 repr(digest(archive.read_bytes())) + "\npins=" +
                 repr({n:digest(b) for n,b in files.items()}) + "\n" + code).strip())
    write("staged.json", manifest)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="action",required=True)
    sub.add_parser("stage").add_argument("revision")
    sub.add_parser("verify")
    sub.add_parser("occupancy")
    for name in ("deploy","recover-closed"):
        sub.add_parser(name).add_argument("--start", action="store_true")
    args = p.parse_args()
    if args.action == "stage":
        stage(args.revision)
    elif args.action == "verify":
        combat.verify()
    elif args.action == "occupancy":
        from probe import LOAD
        print(remote(LOAD + "\nprint(combat.p.a.prior.players())").strip())
    else:
        combat.action(args.action,args.start)

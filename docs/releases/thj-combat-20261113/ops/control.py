"""Stage one merged release, start a durable operation, or fetch its receipts."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

from probe import ARTIFACTS, HERE, SSH, STAGE, remote, write


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stage(revision):
    assert re.fullmatch("[0-9a-f]{40}", revision)
    before = json.loads((HERE / "production-before.json").read_bytes())
    build = json.loads((HERE / "shipping-combined.json").read_bytes())
    files = {"release.py": (HERE / "release.py").read_bytes().replace(b"\r\n", b"\n"),
             "bin/zone": (ARTIFACTS / "zone").read_bytes(), "build.json": (HERE / "shipping-combined.json").read_bytes()}
    pins = {n:digest(data) for n,data in files.items()}
    assert build["zone"] == pins["bin/zone"] and before["base_hashes"]["bin/zone"] == build["baseline"]
    manifest = dict(stage=STAGE, source_revision=revision, files=pins, client_release=2026111301,
        client_channel_sha256=before["channel"], prior_operator=before["prior_operator"],
        prior_receipt=before["prior_receipt"], base_image_id=before["services"]["game"]["image_id"],
        base_hashes=before["base_hashes"], baseline_services=before["services"], binaries={"zone":build["zone"]})
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


def action(name, start, retry_idle=False):
    result = json.loads(remote(f"stage={STAGE!r}\nname={name!r}\nstart={start!r}\nretry_idle={retry_idle!r}\n" + """
from pathlib import Path
import json, subprocess
root=Path('/opt/nightcap/releases')/stage
unit='nightcap-'+stage+'-'+name
log=root/(name+'.log')
if retry_idle:
    assert name=='preflight' and log.is_file()
    if start:
        assert not (root/'evidence').exists()
    assert log.read_text().rstrip().endswith('AssertionError: Players online')
    unit += '-idle'
    log=root/'preflight-idle.log'
if start:
    with log.open('x') as f:
        f.write('')
    subprocess.run(['systemd-run','--unit='+unit,'--property=WorkingDirectory='+str(root),
        '--property=StandardOutput=append:'+str(log),'--property=StandardError=append:'+str(log),
        '/usr/bin/python3','-B',str(root/'release.py'),name], check=True, stdout=subprocess.DEVNULL)
state=subprocess.check_output(['systemctl','show',unit,'--property=LoadState,ActiveState,Result,ExecMainStatus'],text=True)
receipts=sorted(str(p.relative_to(root)) for p in (root/'evidence').rglob('*.json'))
if name=='announced':
    receipts.extend(p.name for p in root.glob('announced-*.json'))
print(json.dumps(dict(state=state.splitlines(),receipts=receipts,log=log.read_text()[-1800:] if log.is_file() else '')))
"""))
    print(json.dumps(result, indent=2))


def verify():
    data = json.loads(remote(f"stage={STAGE!r}\n" + """
from pathlib import Path
import subprocess
root=Path('/opt/nightcap/releases')/stage
print(subprocess.check_output(['/usr/bin/python3','-B',str(root/'release.py'),'verify'],text=True))
""", timeout=1200))
    assert data["result"] == "PASS" and data["gateway_open"] and data["backup_integrity"]
    write("production-verified.json", data)
    print(json.dumps(data, indent=2))


def monitor_idle():
    """Release SSH between checks and only expose the aggregate occupancy."""
    import time
    from probe import LOAD
    last = None
    for _ in range(120):
        count = int(remote(LOAD+"\nprint(prior.a.prior.players())").strip())
        if count != last:
            print("players",count,flush=True)
        if count == 0:
            return
        last = count
        time.sleep(45)
    raise TimeoutError("Nightcap remains occupied")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="op", required=True)
    sub.add_parser("stage").add_argument("revision")
    for phase in ("preflight", "activate", "open","recover-closed"):
        proc=sub.add_parser(phase)
        proc.add_argument("--start", action="store_true")
        if phase == "preflight":
            proc.add_argument("--retry-idle",action="store_true")
    sub.add_parser("occupancy")
    sub.add_parser("wait-idle")
    sub.add_parser("announced")
    sub.add_parser("verify")
    args = parser.parse_args()
    if args.op == "stage":
        stage(args.revision)
    elif args.op == "announced":
        action("announced", False)
    elif args.op == "wait-idle":
        monitor_idle()
    elif args.op == "occupancy":
        from probe import LOAD
        print(remote(LOAD+"\nprint(prior.a.prior.players())").strip())
    elif args.op == "verify":
        verify()
    else:
        action(args.op, args.start, getattr(args,"retry_idle",False))

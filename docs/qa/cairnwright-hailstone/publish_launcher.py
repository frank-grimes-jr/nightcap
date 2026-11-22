"""Install immutable preview files, then advance the checked launcher channel."""
import argparse
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path("/opt/nightcap/deploy/production")
PUBLIC = ROOT / "data/public"
PARENT = "abd6a3bceba70aae02b7ddf178c23832ecdd665bf6a708a47e1e7a4c82172d9b"
RELEASE = 2026112202
VERSION = "0.8.0"

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()

def publish(stage, mode):
    pins = json.loads((stage/"release.json").read_bytes())
    channel = stage/"launcher-channel.json"
    assert digest(channel) == pins["channel"]
    c = json.loads(base64.b64decode(json.loads(channel.read_bytes())["Channel"],validate=True))
    assert c["release"] == RELEASE and c["version"] == VERSION
    assert c["url"] == f"https://play.nightcapgame.org/launcher/{RELEASE}/nightcap-desktop.exe"
    assert (stage/"nightcap-desktop.exe").stat().st_size == c["size"]
    assert pins["desktop"] == c["sha256"]
    folder = PUBLIC/"launcher"/str(RELEASE)
    folder.mkdir(exist_ok=True)
    assert folder.resolve() == folder and (PUBLIC/"launcher-channel.json").resolve() == PUBLIC/"launcher-channel.json"
    live = PUBLIC/"launcher-channel.json"
    assert digest(live) in (PARENT, pins["channel"])
    files = {"nightcap-desktop.exe":pins["desktop"],"nightcap-hailstone-source.zip":pins["source"]}
    for name,pin in files.items():
        src,dst = stage/name,folder/name
        assert digest(src) == pin and not dst.is_symlink()
        if mode == "files" and not dst.exists():
            with tempfile.NamedTemporaryFile(dir=folder,delete=False) as out, src.open("rb") as stream:
                shutil.copyfileobj(stream,out)
                os.fchmod(out.fileno(),0o644)
                out.flush()
                os.fsync(out.fileno())
            temp=Path(out.name)
            try:
                assert digest(temp)==pin
                os.link(temp,dst)
            finally:
                temp.unlink()
        assert digest(dst) == pin
    if mode == "switch" and digest(live) == PARENT:
        backup=stage/"previous-launcher-channel.json"
        if not backup.exists(): shutil.copyfile(live,backup)
        assert digest(backup)==PARENT
        with tempfile.NamedTemporaryFile(dir=PUBLIC,delete=False) as out:
            out.write(channel.read_bytes())
            os.fchmod(out.fileno(),0o644)
            out.flush()
            os.fsync(out.fileno())
        os.replace(out.name,live)
        assert digest(live)==pins["channel"]
    print(json.dumps({"mode":mode,"release":RELEASE,"channel":digest(live),"files":files}))

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("files","switch"))
    args=parser.parse_args()
    with (ROOT/".deployment.lock").open("a") as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        publish(Path(__file__).resolve().parent,args.mode)

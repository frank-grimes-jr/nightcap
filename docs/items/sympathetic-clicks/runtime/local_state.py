"""Inside the local TEST container: retain, install and audit exact native files."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

R = Path("/tmp/nightcap-sympathetic-local-test-20261113")
S = Path("/home/eqemu/server")
BIN = Path("/home/eqemu/code/build/bin/zone")
KNOWN = {
    "zone": "b22a5340fa2cc5647975591186b9c381ea796c5850fa9e782372dfe69125775f",
    "world": "c7a008e95615ff7f74cdca946ef889ad013052227b5593854e56e0091d8c51b3",
    "shared_memory": "337a30c6123df49864e5aadf01c69868ffb782658f413ac27bcf27b1a86371ac",
    "items": "646925c426c9f02f7f840ce7298435e2ee16285db1551ad246ea2d37ae563912",
    "spells": "1ef1b05fc6aca5b69593325a51d7fe482b4dbb7a9877dde96026adab9e16c5eb",
}
CONTROL = "/tmp/nightcap-stock-worn-atk-20261113/local_world.py"


def sha(p):
    with p.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def target(key):
    return S / ("shared" if key in ("items", "spells") else "bin") / key


def processes():
    found = {}
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            name = (path / "comm").read_text().strip()
            if name == "spire" and (path / "cmdline").read_bytes().split(b"\0") == [
                    b"./bin/spire", b"eqemu-server:launcher", b"start", b""]:
                name = "spire-launcher"
            if name not in ("world", "zone", "loginserver", "ucs", "queryserv", "spire-launcher"):
                continue
            if (path / "stat").read_text().split(") ", 1)[1].startswith("Z"):
                continue
            found.setdefault(name, []).append(path)
        except FileNotFoundError:
            pass
    return found


def world(method):
    return json.loads(subprocess.check_output(["python3", CONTROL, method]))


def state(capture=False):
    procs = processes()
    counts = {name: len(paths) for name, paths in procs.items()}
    assert counts == {"world": 1, "zone": 8, "loginserver": 1, "ucs": 1, "queryserv": 1, "spire-launcher": 1}, counts
    hashes = {key: sha(target(key)) for key in KNOWN}
    assert (S / "bin/zone").resolve() == BIN
    for name in ("world", "zone"):
        for proc in procs[name]:
            assert sha(proc / "exe") == hashes[name]
            entries = [line.split() for line in (proc / "maps").read_text().splitlines()]
            for key in (("items", "spells") if name == "zone" else ("items",)):
                p = target(key)
                assert any(len(line) == 6 and line[-1] == str(p) and int(line[4]) == p.stat().st_ino
                           for line in entries), (proc, key)
    data = {"services": counts, "hashes": hashes, "players": world("count"), "locked": world("status")}
    if capture:
        assert hashes == KNOWN and data["players"] == 0 and not data["locked"]
        for key in ("zone", "items", "spells"):
            dest = R / ("before-" + key)
            if not dest.exists():
                shutil.copy2(target(key), dest)
            assert sha(dest) == hashes[key]
    return data


def swap(source, dest, previous):
    assert sha(dest) == previous
    tmp = dest.with_name(dest.name + ".sympathetic-20261113.next")
    assert not tmp.exists()
    shutil.copy2(source, tmp)
    assert sha(tmp) == sha(source)
    os.replace(tmp, dest)


def install():
    assert not processes()
    target_zone = R / "candidate/zone"
    assert (S / "bin/zone").resolve() == BIN and sha(target_zone) != KNOWN["zone"]
    assert all(sha(target(k)) == v for k,v in KNOWN.items())
    with (R / "cache-loader.log").open("wb") as stream:
        subprocess.run([S / "bin/shared_memory", "items", "spells"], cwd=S, stdout=stream,
                       stderr=subprocess.STDOUT, check=True)
    checks = json.loads(subprocess.check_output(["python3", R / "verify_cache.py", S / "shared"]))
    swap(target_zone, BIN, KNOWN["zone"])
    return checks


def disable():
    assert not processes()
    assert sha(BIN) == sha(R / "candidate/zone") and sha(R / "before-zone") == KNOWN["zone"]
    assert all(sha(target(k)) == KNOWN[k] for k in ("world", "shared_memory"))
    checks = json.loads(subprocess.check_output(["python3", R / "verify_cache.py", S / "shared"]))
    spell_hash = checks["spells"]["after"]
    with (R / "disable-item-loader.log").open("wb") as stream:
        subprocess.run([S / "bin/shared_memory", "items"], cwd=S, stdout=stream,
                       stderr=subprocess.STDOUT, check=True)
    assert sha(target("items")) == KNOWN["items"] and sha(target("spells")) == spell_hash
    swap(R / "before-zone", BIN, sha(R / "candidate/zone"))
    return {"zone": sha(BIN), "items": sha(target("items")), "spells": spell_hash}


def verify():
    receipt = state()
    assert not receipt["locked"]
    assert receipt["hashes"]["zone"] == sha(R / "candidate/zone")
    assert all(receipt["hashes"][key] == KNOWN[key] for key in ("world", "shared_memory"))
    receipt["cache_diff"] = json.loads(subprocess.check_output(["python3", R / "verify_cache.py", S / "shared"]))
    return receipt


if __name__ == "__main__":
    mode, = sys.argv[1:]
    print(json.dumps({"capture": lambda: state(True), "state": state, "install": install,
                      "verify": verify, "disable": disable}[mode]()))

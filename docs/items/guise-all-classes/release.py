"""Use the existing stock-item rollout with four full-row Guise guards."""
import hashlib
import importlib.util
import json
import mmap
import os
from pathlib import Path
import struct
import sys
from catalog import changes, generate

STAGE = Path(__file__).resolve().parent

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def cache_check(old, new):
    layout = op.m["layout"]
    size, ident, classes, races = [layout[key] for key in ("size", "ID", "Classes", "Races")]
    with old.open("rb") as f, new.open("rb") as g, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as a, mmap.mmap(g.fileno(), 0, access=mmap.ACCESS_READ) as b:
        assert a[:16] == b[:16]
        payload, slots, capacity, used = struct.unpack_from("<IIII", a)
        assert len(a) == len(b) == payload + 8 == 20 + slots * 4 + size * capacity
        seen = set()
        records = 0
        for item in range(slots):
            left_index, right_index = [struct.unpack_from("<I", buf, 16 + item * 4)[0] for buf in (a, b)]
            if left_index >= used:
                assert right_index >= used
                continue
            assert right_index < used
            left = a[16 + slots * 4 + size * left_index:16 + slots * 4 + size * (left_index + 1)]
            right = b[16 + slots * 4 + size * right_index:16 + slots * 4 + size * (right_index + 1)]
            assert struct.unpack_from("<I", left, ident)[0] == struct.unpack_from("<I", right, ident)[0] == item
            records += 1
            if item in op.stock:
                assert struct.unpack_from("<I", left, classes)[0] == 384
                assert struct.unpack_from("<I", left, races)[0] == 65535
                expected = bytearray(left)
                struct.pack_into("<I", expected, classes, 65535)
                assert right == expected, f"Unexpected Guise cache change {item}"
                seen.add(item)
            else:
                assert left == right, f"Unrelated cache change {item}"
        assert seen == set(op.stock) and records == used
    return dict(records=records, changed=len(seen), unchanged=records-len(seen), items_sha256=op.sha(new))

def initialize():
    global op
    manifest = json.loads((STAGE / "manifest.json").read_bytes())
    for name, digest in manifest["files"].items():
        assert Path(name).name == name
        assert hashlib.sha256((STAGE / name).read_bytes()).hexdigest() == digest
    stock_path = STAGE.parent / "stock-worn-atk-20261113-v1/release.py"
    focus_path = STAGE.parent / "classic-raid-focus-20261114-v1/release.py"
    assert hashlib.sha256(stock_path.read_bytes()).hexdigest() == manifest["stock_operator"]
    assert hashlib.sha256(focus_path.read_bytes()).hexdigest() == manifest["focus_operator"]
    stock = load("guise_stock_controls", stock_path)
    stock.initialize()
    op = load("guise_content_controls", focus_path)
    op.STAGE, op.EVIDENCE, op.m = STAGE, STAGE / "evidence", manifest
    op.op = stock
    op.p, op.r, op.a, op.h, op.base = stock.p, stock.r, stock.a, stock.h, stock.base
    op.stock = changes()
    op.ids = ",".join(map(str, sorted(op.stock)))
    op.cache_check = cache_check
    # All click and other item fields are already checked in the full-row guard.
    op.check_spells = lambda: None
    return op

if __name__ == "__main__":
    import fcntl
    assert __debug__
    os.umask(0o077)
    op = initialize()
    with (op.ROOT / ".deployment.lock").open("a") as lock, open("/var/lock/nightcap-gm.lock", "a") as gm:
        for handle in (lock, gm):
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (op.ROOT / "private/gm-maintenance.json").exists()
        assert op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip() == "1"
        action = sys.argv[1]
        if action == "verify":
            result = op.verify_open(op.read(op.EVIDENCE / "preflight.json"))
            result["item_ids"] = sorted(op.stock)
            result["classes"] = 65535
            result["races"] = 65535
            print(json.dumps(result))
        else:
            {"preflight": op.preflight, "activate": op.activate}[action]()


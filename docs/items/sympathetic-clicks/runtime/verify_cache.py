"""Compare every local native cache record with its preimage and typed afterimage."""
import hashlib
import json
import mmap
from pathlib import Path
import struct
import subprocess
import sys

STAGE = Path("/tmp/nightcap-sympathetic-local-test-20261113")
SERVER = Path("/home/eqemu/server")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def compare(layout, target_dir, targets):
    size, ident, cast1, charges, cast2, click, label, spell_size = layout
    assert size == 1324 and ident == 432
    report = {}
    for name in ("items", "spells"):
        a, b = STAGE / ("before-" + name), target_dir / name
        with a.open("rb") as left, b.open("rb") as right, \
                mmap.mmap(left.fileno(), 0, access=mmap.ACCESS_READ) as old, \
                mmap.mmap(right.fileno(), 0, access=mmap.ACCESS_READ) as new:
            assert len(old) == len(new) and old[:8] == new[:8]
            if name == "items":
                payload, count, capacity, used = struct.unpack_from("<4I", old)
                start = 16 + 4 * count
                assert len(old) == start + size * capacity + 4 == payload + 8
                assert old[:start] == new[:start]
                expected = {}
                for item_id, spell in targets.items():
                    idx, = struct.unpack_from("<I", old, 16 + 4 * item_id)
                    pos = start + idx * size
                    assert idx < used and struct.unpack_from("<I", old, pos+ident)[0] == item_id
                    record = bytearray(old[pos:pos+size])
                    assert struct.unpack_from("<i", record, click)[0] == -1 and not record[label]
                    struct.pack_into("<i", record, cast1, 2000)
                    struct.pack_into("<h", record, charges, -1)
                    struct.pack_into("<I", record, cast2, 2000)
                    struct.pack_into("<i3B", record, click, spell["id"], 4, 1, 1)
                    title = spell["name"].encode("ascii") + b"\0"
                    record[label:label+len(title)] = title
                    expected[pos] = record
                total = used
                chunk = size
            else:
                payload, total = struct.unpack_from("<2I", old)
                assert len(old) == 12 + total * spell_size == payload + 8
                expected = {}
                for spell in targets.values():
                    pos = 8 + spell["id"] * spell_size
                    assert not any(old[pos:pos+spell_size])
                    record = new[pos:pos+spell_size]
                    assert struct.unpack_from("<I", record)[0] == spell["id"]
                    assert record[4:68].split(b"\0")[0].decode("ascii") == spell["name"]
                    expected[pos] = record
                chunk = spell_size
            previous = 0
            for pos, after in sorted(expected.items()):
                for offset in range(previous, pos, 1048576):
                    end = min(offset + 1048576, pos)
                    assert old[offset:end] == new[offset:end], (name, offset)
                assert new[pos:pos+chunk] == after
                previous = pos + chunk
            for offset in range(previous, len(old), 1048576):
                assert old[offset:offset+1048576] == new[offset:offset+1048576], (name, offset)
            report[name] = {"records": total, "changed": len(expected), "before": digest(a), "after": digest(b)}
    return report


if __name__ == "__main__":
    targets = {int(key): value for key, value in json.loads((STAGE / "targets.json").read_text()).items()}
    print(json.dumps(compare(tuple(map(int, subprocess.check_output([STAGE / "cache_layout"]).split())),
                             Path(sys.argv[1]), targets)))

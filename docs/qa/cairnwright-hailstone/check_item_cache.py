"""Read-only check for the November 22 Cairnwright world/zone ItemData format."""
import argparse
import hashlib
import mmap
from pathlib import Path
import struct

def check(path):
    with Path(path).open("rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
        payload, keys, capacity, used = struct.unpack_from("<4I", data)
        if payload + 8 != len(data) or not 0 < used <= capacity or not keys > 998636:
            raise ValueError("unexpected item cache header")
        start = 16 + keys * 4
        stride, rem = divmod(len(data) - start - 4, capacity)
        if rem or stride != 1332:
            raise ValueError(f"world requires 1332 bytes per ItemData, cache has {stride}")
        seen = 0
        for key in range(keys):
            index, = struct.unpack_from("<I", data, 16 + 4*key)
            if index == 0xffffffff:
                continue
            if index >= used or struct.unpack_from("<I", data, start + index*stride + 440)[0] != key:
                raise ValueError(f"invalid cache record for item {key}")
            seen += 1
        if seen != used:
            raise ValueError(f"expected {used} records, verified {seen}")
        for key, name in [(998616,b"Initiate Cairnwright Robe"),(998636,b"Initiate Cairnwright Hammer")]:
            index, = struct.unpack_from("<I", data, 16 + 4*key)
            off = start + index*stride + 265
            if data[off:off+64].split(b"\x00",1)[0] != name:
                raise ValueError(f"incorrect starter equipment at {key}")
        print(f"{path}: {seen} verified records, stride {stride}, SHA-256 {hashlib.sha256(data).hexdigest()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    check(parser.parse_args().cache)

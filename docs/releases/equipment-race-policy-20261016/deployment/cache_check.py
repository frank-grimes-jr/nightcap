"""Verify native loaded masks against SQL and preserve every other cache byte."""
import hashlib
import mmap
import struct


def verify(path, rows, layout, enabled):
    size, offsets = layout['item_size'], layout['offsets']
    assert size == 1332, 'Unreviewed ItemData ABI'
    assert len(rows) == len({row[0] for row in rows})
    normalized = hashlib.sha256()
    changed = excluded_nonplayer = 0
    with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as mem:
        payload, count, maximum, current = struct.unpack_from('<IIII', mem)
        assert payload + 8 == len(mem) and maximum == current == len(rows)
        assert len(mem) == 20 + 4 * count + size * current
        start = 16 + 4 * count
        seen, ranges = set(), []
        for ident, itemclass, classes, races, slots, augtype in rows:
            assert 0 <= ident < count
            index = struct.unpack_from('<I', mem, 16 + ident * 4)[0]
            assert index < current and index not in seen
            seen.add(index)
            begin = start + index * size
            assert struct.unpack_from('<I', mem, begin + offsets['ID'])[0] == ident
            eligible = itemclass == 0 and bool(classes & 65535) and bool(races & 65535) and bool(slots & 8388607 or augtype)
            expected = 65535 if enabled and eligible else races
            actual = struct.unpack_from('<I', mem, begin + offsets['Races'])[0]
            assert actual == expected, (ident, actual, expected)
            if eligible and races != 65535:
                changed += 1
                off = begin + offsets['Races']
                ranges.append((off, off + 4))
            elif itemclass == 0 and bool(slots & 8388607 or augtype) and not (classes & 65535 and races & 65535):
                excluded_nonplayer += 1
        previous = 0
        for begin, end in sorted(ranges) + [(len(mem), len(mem))]:
            assert previous <= begin <= end <= len(mem)
            for chunk in range(previous, begin, 1024 * 1024):
                normalized.update(mem[chunk:min(chunk + 1024 * 1024, begin)])
            previous = end
        full = hashlib.sha256(mem).hexdigest()
    return dict(items_checked=current, projected_definitions=changed, nonplayer_definitions_preserved=excluded_nonplayer,
                race_policy_enabled=enabled, preserved_fields_sha256=normalized.hexdigest(), cache_sha256=full)

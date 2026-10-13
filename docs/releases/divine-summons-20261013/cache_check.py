"""Verify complete native cache preservation outside owned merchant price fields."""
import hashlib
import mmap
import struct

BASE_IDS = (6307,6309,6313,5800,15996,5798,29365,77517,90491,90492,90493)
OWNED = frozenset(base+tier for base in BASE_IDS for tier in (0,200000,400000,600000))


def verify(path, item_ids, layout, enabled):
    size = layout['item_size']
    offsets = layout['offsets']
    assert size == 1332, 'Unreviewed ItemData ABI'
    assert OWNED <= set(item_ids) and len(item_ids) == len(set(item_ids))
    excluded = sorted((offsets['Price'], offsets['FixedSellPrice']))
    assert excluded[0]+4 <= excluded[1] and excluded[1]+4 <= size
    normalized = hashlib.sha256()
    prices = {}
    with path.open('rb') as stream, mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as mem:
        payload,count,maximum,current = struct.unpack_from('<IIII',mem)
        assert payload+8 == len(mem) and maximum == current == len(item_ids)
        assert len(mem) == 20+4*count+size*current
        start = 16+4*count
        seen = set()
        ranges = []
        for ident in sorted(item_ids):
            assert 0 <= ident < count
            index = struct.unpack_from('<I',mem,16+ident*4)[0]
            assert index < current and index not in seen
            seen.add(index)
            record = mem[start+index*size:start+(index+1)*size]
            assert struct.unpack_from('<I',record,offsets['ID'])[0] == ident
            if ident in OWNED:
                values = [struct.unpack_from('<I',record,offsets[n])[0] for n in ('Price','FixedSellPrice')]
                assert values == ([0,0] if enabled else [1000,1000]), (ident, values)
                prices[ident] = values
                for off in excluded:
                    ranges.append((start+index*size+off,start+index*size+off+4))
        # Include header, every lookup slot (including absent IDs), record order
        # and trailing bytes. Only the owned uint32 prices may differ.
        previous = 0
        for begin,end in sorted(ranges)+[(len(mem),len(mem))]:
            assert previous <= begin <= end <= len(mem)
            for chunk in range(previous,begin,1024*1024):
                normalized.update(mem[chunk:min(chunk+1024*1024,begin)])
            previous = end
        full = hashlib.sha256(mem).hexdigest()
    return dict(items_checked=current,weapons_checked=len(prices),zero_resale=enabled,
                preserved_fields_sha256=normalized.hexdigest(),cache_sha256=full)

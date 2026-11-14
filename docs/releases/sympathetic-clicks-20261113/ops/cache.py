"""Verify the production ABI and the exact two keyed item/spell changes."""
import hashlib
import mmap
import struct

TARGETS = {610338: (44379, 'Sympathetic Strike I'), 610150: (44380, 'Sympathetic Healing I')}

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def compare(old_dir, new_dir, layout):
    size, ident, cast1, charges, cast2, click, label, spell_size = layout
    assert size == 1332 and ident == 440
    report = {}
    for name in ('items', 'spells'):
        left, right = old_dir/name, new_dir/name
        with left.open('rb') as lf, right.open('rb') as rf, \
                mmap.mmap(lf.fileno(), 0, access=mmap.ACCESS_READ) as old, \
                mmap.mmap(rf.fileno(), 0, access=mmap.ACCESS_READ) as new:
            assert len(old) == len(new) and old[:8] == new[:8]
            if name == 'items':
                assert old[:16] == new[:16]
                payload, keys, capacity, used = struct.unpack_from('<4I', old)
                start = 16 + 4*keys
                assert len(old) == payload+8 == start+capacity*size+4
                def record(buf, key):
                    index, = struct.unpack_from('<I',buf,16+4*key)
                    if index >= used:
                        return None
                    row = buf[start+size*index:start+size*(index+1)]
                    assert struct.unpack_from('<I',row,ident)[0] == key
                    return row
                seen, changed = 0, set()
                for key in range(keys):
                    before, after = record(old,key), record(new,key)
                    if before is not None:
                        seen += 1
                    if key in TARGETS:
                        sid, title = TARGETS[key]
                        expected = bytearray(before)
                        assert struct.unpack_from('<i',expected,click)[0] == -1 and not expected[label]
                        struct.pack_into('<i',expected,cast1,2000)
                        struct.pack_into('<h',expected,charges,-1)
                        struct.pack_into('<I',expected,cast2,2000)
                        struct.pack_into('<i3B',expected,click,sid,4,1,1)
                        text = title.encode('ascii') + b'\0'
                        expected[label:label+len(text)] = text
                        assert after == expected, key
                        changed.add(key)
                    else:
                        assert before == after, ('Unrelated item change',key)
                assert seen == used and changed == set(TARGETS)
                total = used
            else:
                payload, total = struct.unpack_from('<2I',old)
                assert len(old) == payload+8 == 12+total*spell_size
                pos = 0
                for sid, title in sorted(TARGETS.values()):
                    at = 8+sid*spell_size
                    for i in range(pos,at,1048576):
                        end = min(i+1048576,at)
                        assert old[i:end] == new[i:end], ('Unrelated spell change',i)
                    assert not any(old[at:at+spell_size])
                    assert struct.unpack_from('<I',new,at)[0] == sid
                    assert new[at+4:at+68].split(b'\0')[0] == title.encode('ascii')
                    pos = at+spell_size
                for i in range(pos,len(old),1048576):
                    assert old[i:i+1048576] == new[i:i+1048576], ('Unrelated spell change',i)
            report[name] = dict(records=total, changed=2, unchanged=total-2, before=sha(left), after=sha(right))
    return report

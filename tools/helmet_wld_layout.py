"""Pinned Classic actor layout and typed fragment-reference relocation.

RoF2 EQGraphicsDX9 0x1001e5f8 discovers alternate heads by scanning the
consecutive mesh fragments around the skeleton's first mesh reference.
Names alone do not register an appended head with an existing actor.
"""
import struct

from classic_model_archives import crypt
from classic_model_materials import _Wld


def reference_fields(w, index):
    """All fragment-reference fields for the kinds in the pinned globals.

    Return offsets, including null references. Never treat bone indices,
    animation samples, polygon indices or string offsets as fragment IDs.
    Reject unsupported kinds instead of guessing during relocation.
    """
    data = w.fragments[index - 1]
    kind = w.kind(index)
    def u(offset):
        return struct.unpack_from('<I', data, offset)[0]
    if kind in (3, 0x12):
        return []
    if kind in (4, 5, 0x30, 0x31):
        return [offset for offset, _ in w.references(index)]
    if kind in (0x11, 0x13, 0x2d):
        return [12]
    if kind == 0x36:
        if u(20) or u(24):
            raise ValueError('Unsupported optional mesh reference')
        return [16, 20, 24, 28]
    if kind == 0x2c:
        if u(48) or u(52):
            raise ValueError('Unsupported alternate mesh reference')
        return [44, 48, 52]
    if kind == 0x10:
        flags, count = u(12), u(16)
        if u(20):
            raise ValueError('Unsupported skeleton animation reference')
        fields = [20]
        pos = 24 + 12 * bool(flags & 1) + 4 * bool(flags & 2)
        for _ in range(count):
            fields.extend((pos + 8, pos + 12))
            pos += 20 + 4 * u(pos + 16)
        if flags & 0x200:
            count = u(pos)
            fields.extend(range(pos + 4, pos + 4 + count * 4, 4))
            pos += 4 + count * 8
        if pos != len(data):
            raise ValueError('Unsupported skeleton layout')
        return fields
    if kind == 0x14:
        flags, count, models = u(12), u(20), u(24)
        if u(28):
            raise ValueError('Unsupported optional actor reference')
        fields = [28]
        pos = 32 + 4 * bool(flags & 1) + 28 * bool(flags & 2)
        for _ in range(count):
            pos += 4 + 8 * u(pos)
        fields.extend(range(pos, pos + models * 4, 4))
        pos += models * 4
        end = pos + 4 + u(pos)
        if end > len(data) or len(data) - end > 3:
            raise ValueError('Unsupported actor layout')
        return fields
    raise ValueError(f'Unsupported WLD fragment kind {kind:#x}')


def mesh_block(w, mesh):
    if w.kind(mesh) != 0x36:
        raise ValueError('Expected Classic mesh')
    first = last = mesh
    while first > 1 and w.kind(first - 1) == 0x36:
        first -= 1
    while last < len(w.fragments) and w.kind(last + 1) == 0x36:
        last += 1
    return first, last


def registered_meshes(w, code):
    """Mirror the native skeleton's first-mesh/contiguous-block discovery."""
    index = w.by_name[code + '_HS_DEF'][0]
    data = w.fragments[index - 1]
    flags, count = struct.unpack_from('<II', data, 12)
    if not flags & 0x200:
        raise ValueError('Actor has no alternate mesh list')
    pos = 24 + 12 * bool(flags & 1) + 4 * bool(flags & 2)
    for _ in range(count):
        pos += 20 + 4 * struct.unpack_from('<I', data, pos + 16)[0]
    if not struct.unpack_from('<I', data, pos)[0]:
        raise ValueError('Actor mesh list is empty')
    ref = struct.unpack_from('<I', data, pos + 4)[0]
    if w.kind(ref) != 0x2d:
        raise ValueError('Expected skeleton mesh reference')
    mesh = struct.unpack_from('<I', w.fragments[ref - 1], 12)[0]
    first, last = mesh_block(w, mesh)
    return w.names[first - 1:last]


def reorder(raw, order):
    """Relocate typed references, preserving every other original byte."""
    w = _Wld(raw)
    if sorted(order) != list(range(1, len(w.fragments) + 1)):
        raise ValueError('Fragment order must be an exact permutation')
    mapping = {old: new for new, old in enumerate(order, 1)}
    output = []
    for old in order:
        data = bytearray(w.fragments[old - 1])
        for offset in reference_fields(w, old):
            ref = struct.unpack_from('<i', data, offset)[0]
            if ref > 0:
                if ref not in mapping:
                    raise ValueError('Unresolved fragment reference')
                struct.pack_into('<i', data, offset, mapping[ref])
        output.append(bytes(data))
    result = w.header + crypt(w.strings) + b''.join(output) + w.trailer
    after = _Wld(result)
    # An inverse relocation must recover the exact original fragment bytes.
    inverse = {new: old for old, new in mapping.items()}
    for old, new in mapping.items():
        data = bytearray(after.fragments[new - 1])
        for offset in reference_fields(after, new):
            ref = struct.unpack_from('<i', data, offset)[0]
            if ref > 0:
                struct.pack_into('<i', data, offset, inverse[ref])
        if bytes(data) != w.fragments[old - 1]:
            raise AssertionError('Fragment relocation changed original data')
    return result

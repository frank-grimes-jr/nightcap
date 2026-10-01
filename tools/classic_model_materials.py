"""Make WLD material dependencies loadable through RoF2's actor import filter.

EQGraphicsDX9 filters bitmap names (03), materials (30) and palettes (31)
by the selected actor's first three letters. Zone WLDs can share materials
across actors; an archive round-trip does not prove those imports are safe.
"""
import re
import struct

from classic_model_archives import crypt, wld_parts


class _Wld:
    def __init__(self, raw):
        self.strings, parts = wld_parts(raw)
        self.fragments = [raw[p:p + size + 8] for p, size, _, _ in parts]
        self.names = [self.string(name) for _, _, _, name in parts]
        self.by_name = {}
        for index, name in enumerate(self.names, 1):
            if name:
                self.by_name.setdefault(name.upper(), []).append(index)
        end = parts[-1][0] + parts[-1][1] + 8 if parts else 28 + len(self.strings)
        self.trailer = raw[end:]
        self.header = raw[:28]

    def string(self, ref):
        if ref == 0:
            return ''
        if ref > 0 or not 0 < -ref < len(self.strings):
            raise ValueError('Invalid WLD string reference')
        end = self.strings.find(b'\0', -ref)
        if end < 0:
            raise ValueError('Unterminated WLD string')
        return self.strings[-ref:end].decode('ascii')

    def resolve(self, ref, kind):
        if ref < 0:
            matches = self.by_name.get(self.string(ref).upper(), [])
            matches = [i for i in matches if self.kind(i) == kind]
            if len(matches) != 1:
                raise ValueError('Unresolved or ambiguous material reference')
            ref = matches[0]
        if not 1 <= ref <= len(self.fragments) or self.kind(ref) != kind:
            raise ValueError('Invalid material dependency reference')
        return ref

    def kind(self, index):
        return struct.unpack_from('<I', self.fragments[index - 1], 4)[0]

    def references(self, index):
        """Return (field offset, resolved target) pairs; zero30 is untextured."""
        data, kind = self.fragments[index - 1], self.kind(index)
        def uint(offset):
            if offset + 4 > len(data):
                raise ValueError('Truncated material fragment')
            return struct.unpack_from('<I', data, offset)[0]
        if kind == 0x31:
            count, start, target_kind = uint(16), 20, 0x30
        elif kind == 0x30:
            if uint(32) == 0:
                return []
            count, start, target_kind = 1, 32, 0x05
        elif kind == 0x05:
            count, start, target_kind = 1, 12, 0x04
        elif kind == 0x04:
            flags, count = uint(12), uint(16)
            start = 20 + 4 * bool(flags & 4) + 4 * bool(flags & 8)
            target_kind = 0x03
        elif kind == 0x03:
            return []
        else:
            raise ValueError('Unexpected material fragment type')
        if start + count * 4 > len(data):
            raise ValueError('Truncated material references')
        return [(offset, self.resolve(struct.unpack_from('<i', data, offset)[0], target_kind))
                for offset in range(start, start + count * 4, 4)]

    def palettes(self, prefix):
        return [i for i, name in enumerate(self.names, 1)
                if self.kind(i) == 0x31 and name[:3].upper() == prefix]


def _prefixes(values):
    result = sorted({value.upper() for value in values})
    if any(not re.fullmatch('[A-Z]{3}', value) for value in result):
        raise ValueError('Expected three-letter actor prefixes')
    return result


def validate_materials(raw, prefixes):
    """Reject any palette dependency the native per-actor loader would skip."""
    wld = _Wld(raw)
    for prefix in _prefixes(prefixes):
        seen = set()
        def visit(index):
            if index in seen:
                return
            seen.add(index)
            if wld.kind(index) in (0x03, 0x30) and wld.names[index - 1][:3].upper() != prefix:
                raise ValueError(f'{prefix}: material dependency {index} is outside actor scope')
            for _, target in wld.references(index):
                visit(target)
        for palette in wld.palettes(prefix):
            visit(palette)


def scope_materials(raw, prefixes):
    """Clone shared material chains into each importing actor's namespace.

    Preserve original fragment indices, palette order, rendering values, bitmap
    filenames and all geometry/animation bytes. A material already owned by the
    actor keeps its name (including skin variants); only its child refs may move.
    """
    prefixes = _prefixes(prefixes)
    wld = _Wld(raw)
    output = [bytearray(data) for data in wld.fragments]
    strings = bytearray(wld.strings)
    used_names = set(wld.by_name)
    changed = False
    for prefix in _prefixes(prefixes):
        remapped = {}
        def scoped(index):
            nonlocal changed
            if index in remapped:
                return remapped[index]
            kind = wld.kind(index)
            data = bytearray(wld.fragments[index - 1])
            child_changed = False
            for offset, child in wld.references(index):
                target = scoped(child)
                if target != child:
                    struct.pack_into('<i', data, offset, target)
                    child_changed = True
            owned = wld.names[index - 1][:3].upper() == prefix
            needs_scope = kind in (0x03, 0x30) and not owned
            if not needs_scope and not child_changed:
                remapped[index] = index
                return index
            changed = True
            if kind == 0x31 or owned:
                output[index - 1] = data
                target = index
            else:
                # Short deterministic names fit native model-name buffers.
                name = f'{prefix}_NCM{index:05X}'
                if name in used_names:
                    raise ValueError('Scoped material name collision')
                used_names.add(name)
                struct.pack_into('<i', data, 8, -len(strings))
                strings.extend(name.encode('ascii') + b'\0')
                output.append(data)
                target = len(output)
            remapped[index] = target
            return target
        for palette in wld.palettes(prefix):
            scoped(palette)
    if not changed:
        return raw
    strings.extend(b'\0' * (-len(strings) % 4))
    header = bytearray(wld.header)
    struct.pack_into('<I', header, 8, len(output))
    struct.pack_into('<I', header, 20, len(strings))
    result = bytes(header) + crypt(strings) + b''.join(output) + wld.trailer
    validate_materials(result, prefixes)
    return result


def validate_material_preservation(before, after):
    """Check exact non-material bytes and ordered material graph equivalence."""
    old, new = _Wld(before), _Wld(after)
    if (len(new.fragments) < len(old.fragments) or
            not new.strings.startswith(old.strings) or old.trailer != new.trailer):
        raise ValueError('Original WLD data was removed')
    allowed = {0x03, 0x04, 0x05, 0x30, 0x31}
    def graphs(wld):
        memo = {}
        def graph(index):
            if index not in memo:
                data = bytearray(wld.fragments[index - 1])
                data[8:12] = b'\0' * 4  # Names differ only for scoped clones.
                children = []
                for offset, child in wld.references(index):
                    data[offset:offset + 4] = b'\0' * 4
                    children.append(graph(child))
                memo[index] = (bytes(data), tuple(children))
            return memo[index]
        return graph
    old_graph, new_graph = graphs(old), graphs(new)
    for index, data in enumerate(old.fragments, 1):
        if old.names[index - 1] != new.names[index - 1]:
            raise ValueError('Original fragment name changed')
        if old.kind(index) in allowed:
            if old_graph(index) != new_graph(index):
                raise ValueError('Material rendering data or palette order changed')
        elif data != new.fragments[index - 1]:
            raise ValueError('Geometry, animation or actor data changed')
    if any(new.kind(i) not in allowed - {0x31}
           for i in range(len(old.fragments) + 1, len(new.fragments) + 1)):
        raise ValueError('Unexpected appended non-material fragment')

"""Strict old-format WLD mesh codec for the winged helmet asset pipeline.

Only accepts the pinned Classic format. Never writes to a client directory.
Reference: EQEmu WLD by Windcatcher, fragment 0x36.
"""
import math
import struct


def decode_mesh(raw):
    if len(raw) < 104 or struct.unpack_from('<I', raw, 4)[0] != 0x36:
        raise ValueError('Expected mesh fragment')
    counts = struct.unpack_from('<10H', raw, 84)
    nv, nt, nn, nc, np, nb, npt, nvt, naux, scale = counts
    if nv == 0 or nt != nv or nn != nv or scale > 15 or nc not in (0, nv):
        raise ValueError('Unsupported mesh attribute counts')
    pos = 104
    def take(fmt, count):
        nonlocal pos
        size = struct.calcsize(fmt)
        if pos + size * count > len(raw):
            raise ValueError('Truncated mesh section')
        values = [struct.unpack_from(fmt, raw, pos+i*size) for i in range(count)]
        pos += size * count
        return values
    vertices = [[v / (1 << scale) for v in p] for p in take('<3h', nv)]
    uv = [[u/256, v/256] for u,v in take('<2h', nt)]
    normals = [[v/127 for v in p] for p in take('<3b', nn)]
    colors = take('<I', nc)
    polygons = take('<4H', np)
    bones = take('<2H', nb)
    polygon_materials = take('<2H', npt)
    vertex_materials = take('<2H', nvt)
    # Classic global_chr uses six-byte mesh operations (not the eight-byte
    # layout in the older prose specification), then zero alignment padding.
    aux = take('<6s', naux)
    if any(any(i >= nv for i in p[1:]) for p in polygons):
        raise ValueError('Mesh vertex index out of bounds')
    if sum(n for n,_ in bones) != nv or sum(n for n,_ in polygon_materials) != np:
        raise ValueError('Mesh group counts disagree')
    padding = raw[pos:]
    if len(padding) > 3 or any(padding):
        raise ValueError('Trailing mesh fragment bytes')
    return dict(header=raw[:104], vertices=vertices, uv=uv, normals=normals,
                colors=colors, polygons=polygons, bones=bones,
                polygon_materials=polygon_materials, vertex_materials=vertex_materials,
                aux=aux, scale=scale, padding=padding)


def encode_mesh(mesh, name_ref, palette_ref):
    nv = len(mesh['vertices']); np = len(mesh['polygons'])
    if not 0 < nv < 65536 or not 0 < np < 65536:
        raise ValueError('Mesh exceeds native word-sized counts')
    raw = bytearray(mesh['header'])
    struct.pack_into('<i', raw, 8, name_ref)
    struct.pack_into('<I', raw, 16, palette_ref)
    vertices = mesh['vertices']
    if any(not math.isfinite(v) for p in vertices for v in p):
        raise ValueError('Nonfinite mesh coordinate')
    scale = mesh['scale']
    ints = [tuple(round(v*(1 << scale)) for v in p) for p in vertices]
    if any(not -32768 <= v <= 32767 for p in ints for v in p):
        raise ValueError('Mesh coordinate overflows signed word')
    counts = (nv,len(mesh['uv']),len(mesh['normals']),len(mesh['colors']),np,
              len(mesh['bones']),len(mesh['polygon_materials']),len(mesh['vertex_materials']),len(mesh['aux']),scale)
    struct.pack_into('<10H',raw,84,*counts)
    struct.pack_into('<f',raw,56,max(math.sqrt(sum(v*v for v in p)) for p in vertices))
    struct.pack_into('<6f',raw,60,*[min(p[k] for p in vertices) for k in range(3)],*[max(p[k] for p in vertices) for k in range(3)])
    sections = [('<3h',ints),('<2h',[tuple(round(v*256) for v in p) for p in mesh['uv']]),
                ('<3b',[tuple(max(-127,min(127,round(v*127))) for v in p) for p in mesh['normals']]),
                ('<I',mesh['colors']),('<4H',mesh['polygons']),('<2H',mesh['bones']),
                ('<2H',mesh['polygon_materials']),('<2H',mesh['vertex_materials']),('<6s',mesh['aux'])]
    for fmt, rows in sections:
        for row in rows: raw.extend(struct.pack(fmt,*row))
    raw.extend(bytes((-len(raw)) % 4))
    struct.pack_into('<I',raw,0,len(raw)-8)
    decode_mesh(raw)
    return bytes(raw)

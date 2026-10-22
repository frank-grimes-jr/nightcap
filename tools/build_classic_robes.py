"""Stage Classic robes from the canonical helmet-enabled Nightcap archives.

The protected reference client is read-only. Output must be a new separate
directory. Staging is not publication or evidence of native visual acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from classic_model_archives import crypt, read_pfs, write_pfs
from classic_model_materials import _Wld
from classic_robe_geometry import robe_mesh
from helmet_wld import encode_mesh
from helmet_wld_layout import registered_meshes, mesh_block, reorder
from build_winged_helmet_client import helmet_files

TARGETS = ('BAM', 'BAF', 'ELM', 'ELF', 'HAM', 'HAF', 'DWM', 'DWF',
           'TRM', 'TRF', 'OGM', 'OGF', 'HOM', 'HOF')


def add_robes(raw, donor_raw, codes):
    wld, donor = _Wld(raw), _Wld(donor_raw)
    fragments = list(wld.fragments)
    strings = bytearray(wld.strings)
    names = set(wld.by_name)
    before, after, audit = {}, {}, []
    def name_ref(name, material=False):
        if name in names and not material:
            raise ValueError('Duplicate robe fragment: ' + name)
        names.add(name)
        offset = len(strings)
        strings.extend(name.encode('ascii') + b'\0')
        return -offset
    # Native archives repeat CLK fragment names per actor. Clone explicit
    # positive references before all new consumers; never resolve duplicates
    # by name or borrow a forward material dependency from another mesh block.
    copied = {}
    def import_material(index):
        if index in copied:
            return copied[index]
        name = donor.names[index - 1]
        data = bytearray(donor.fragments[index - 1])
        for offset, child in donor.references(index):
            struct.pack_into('<I', data, offset, import_material(child))
        struct.pack_into('<i', data, 8, name_ref(name, material=True) if name else 0)
        fragments.append(bytes(data))
        copied[index] = len(fragments)
        return len(fragments)
    import_start = len(fragments) + 1
    cloth_refs = {}
    for pattern in range(4, 11):
        for part in range(1, 7):
            name = f'CLK{pattern:02}{part:02}_MDF'
            cloth_refs[pattern, part] = import_material(donor.by_name[name][0])
    imported = list(range(import_start, len(fragments) + 1))
    modified_palettes = {}
    for code in codes:
        target_name = code + '01_DMSPRITEDEF'
        if target_name in names:
            raise ValueError('Actor already has a robe body: ' + code)
        native = wld.by_name[code + '_DMSPRITEDEF'][0]
        first, last = mesh_block(wld, native)
        palette_id = struct.unpack_from('<I', wld.fragments[native - 1], 16)[0]
        if any(struct.unpack_from('<I', wld.fragments[i - 1], 16)[0] != palette_id
               for i in range(first, last + 1)):
            raise ValueError('Actor does not share its first-mesh palette')
        if palette_id in modified_palettes or last in after:
            raise ValueError('Actors share an unsupported palette or mesh block')
        old_refs = [ref for _, ref in wld.references(palette_id)]
        new_refs = [cloth_refs[4, part] for part in range(1, 6)]
        if any(ref in old_refs for ref in new_refs):
            raise ValueError('Unexpected partial robe palette')
        palette = bytearray(wld.fragments[palette_id - 1])
        if len(palette) != 20 + 4 * len(old_refs):
            raise ValueError('Unsupported palette layout')
        palette.extend(struct.pack('<5I', *new_refs))
        struct.pack_into('<I', palette, 0, len(palette) - 8)
        struct.pack_into('<I', palette, 16, len(old_refs) + 5)
        fragments[palette_id - 1] = bytes(palette)
        modified_palettes[palette_id] = bytes(palette)
        model, record = robe_mesh(wld, donor, code,
                                  {part: len(old_refs) + part - 1 for part in range(1, 6)})
        fragments.append(encode_mesh(model, name_ref(target_name), palette_id))
        mesh_id = len(fragments)
        # Register through the same contiguous mesh-block discovery as stock
        # robes and custom HE90. No changes to skeleton or animation fragments.
        after[last] = [mesh_id]
        audit.append(record)
    if imported:
        before[min(modified_palettes)] = imported
    strings.extend(bytes((-len(strings)) % 4))
    header = bytearray(wld.header)
    struct.pack_into('<I', header, 8, len(fragments))
    struct.pack_into('<I', header, 20, len(strings))
    output = bytes(header) + crypt(strings) + b''.join(fragments) + wld.trailer
    order = []
    for index in range(1, len(wld.fragments) + 1):
        order.extend(before.get(index, []))
        order.append(index)
        order.extend(after.get(index, []))
    output = reorder(output, order)
    final = _Wld(output)
    for code in codes:
        if code + '01_DMSPRITEDEF' not in registered_meshes(final, code):
            raise AssertionError('Robe body missing from native registration')
    return output, audit


def robe_files(archives):
    if set(archives) != {'global_chr.s3d', 'global4_chr.s3d'}:
        raise ValueError('Expected the two canonical Classic archives')
    donor = read_pfs(archives['global_chr.s3d'])
    output, reports = {}, {}
    for name, codes in (('global_chr.s3d', TARGETS), ('global4_chr.s3d', ('BAM', 'BAF'))):
        original = read_pfs(archives[name])
        files = dict(original)
        wld_name = name.replace('.s3d', '.wld')
        files[wld_name], models = add_robes(files[wld_name], donor['global_chr.wld'], codes)
        for filename, data in donor.items():
            if filename.startswith('clk') and filename.endswith('.bmp'):
                if filename in files and files[filename] != data:
                    raise ValueError('Conflicting robe texture: ' + filename)
                files[filename] = data
        packed = write_pfs(files)
        if read_pfs(packed) != files:
            raise AssertionError('Archive round-trip failed')
        if any(files[n] != data for n, data in original.items() if n != wld_name):
            raise AssertionError('Existing texture bytes changed')
        output[name] = packed
        reports[name] = dict(input_sha256=hashlib.sha256(archives[name]).hexdigest(),
                             output_sha256=hashlib.sha256(packed).hexdigest(), models=models)
    return output, reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--helmet-mesh', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, output = args.client.resolve(), args.output.resolve()
    if output == source or source in output.parents or output.exists():
        raise ValueError('Output must be a new directory outside the reference client')
    helmet = json.loads(args.helmet_mesh.read_bytes())
    canonical, provenance = helmet_files(source, helmet)
    archives, report = robe_files(canonical)
    output.mkdir(parents=True)
    for name, data in archives.items():
        (output / name).write_bytes(data)
    (output / 'robe-audit.json').write_text(json.dumps(dict(
        status='candidate_not_published_native_visual_QA_pending',
        helmet_provenance=provenance, archives=report), indent=2) + '\n')
    print(json.dumps(dict(output=str(output), actors=sum(len(r['models']) for r in report.values()),
                         status='candidate_not_published_native_visual_QA_pending')))


if __name__ == '__main__':
    main()

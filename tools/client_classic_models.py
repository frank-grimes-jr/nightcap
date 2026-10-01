"""Generate isolated classic actors from pinned, read-only RoF2 archives.

The generated model plan is shared by the proxy, asset builder and packager.
Original archives and user preferences are never overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path

from classic_model_archives import actor_names, read_pfs, rename_wld, write_pfs
from classic_model_materials import scope_materials, validate_material_preservation

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / 'eq-client-dll/config/classic-models.json'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def model_files(client):
    plan = json.loads(PLAN.read_bytes())
    files = {}
    imports = list(plan['stock_imports'])
    for archive in plan['archives']:
        raw = (client / archive['source']).read_bytes()
        if digest(raw) != archive['source_sha256']:
            raise ValueError('Unsupported classic source: ' + archive['source'])
        source = read_pfs(raw)
        aliases = archive['aliases']
        filenames = {n: aliases.get(n[:3].upper(), n[:3]).lower() + n[3:]
                     for n in source if not n.endswith('.wld')}
        output = {}
        for name, data in source.items():
            if name.endswith('.wld'):
                target = archive['output'][:-4] + '.wld' if name == archive['source'][:-4] + '.wld' else name
                if target == name:
                    raise ValueError('Unreviewed companion WLD: ' + name)
                data = rename_wld(data, aliases, filenames)
                expected = {aliases.get(a[:3], a[:3]) + a[3:] for a in actor_names(source[name])}
                if set(actor_names(data)) != expected:
                    raise ValueError('Classic actor rename failed')
                renamed = data
                data = scope_materials(data, [line.split(',')[0] for line in archive['imports']])
                validate_material_preservation(renamed, data)
            else:
                target = filenames[name]
                # Typed modern elementals encode their element in the race ID,
                # often with texture zero. Clone all variants using that same
                # original element palette so texture/head choices stay classic.
                element = archive.get('element_texture')
                if element is not None and name.startswith('ele'):
                    texture = name[:5] + f'{element:02d}' + name[7:]
                    if texture not in source:
                        raise ValueError('Missing original elemental texture: ' + texture)
                    data = source[texture]
            if target in output:
                raise ValueError('Classic archive filename collision')
            output[target] = data
        packed = write_pfs(output)
        if read_pfs(packed) != output:
            raise ValueError('Classic archive failed lossless packing')
        files[archive['output']] = packed
        imports.extend(archive['imports'])
    if len(imports) >= 1000 or len(set(x.split(',')[0] for x in imports)) != len(imports):
        raise ValueError('Duplicate or excessive global model imports')
    files['nightcap_models_chr.txt'] = (str(len(imports)) + '\n' + '\n'.join(imports) + '\n').encode('ascii')
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    client, output = args.client.resolve(), args.output.resolve()
    if output == client or client in output.parents or output in client.parents or output.exists():
        raise ValueError('Output must be a new tree separate from the original client')
    files = model_files(client)
    output.mkdir(parents=True)
    for name, raw in files.items():
        (output / name).write_bytes(raw)
    audit = {'schema': 1, 'status': 'generated_not_installed', 'plan_sha256': digest(PLAN.read_bytes()),
             'files': {n: {'size': len(v), 'sha256': digest(v)} for n, v in files.items()}}
    (output / 'classic-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps({'status': audit['status'], 'files': len(files), 'bytes': sum(map(len, files.values()))}))


if __name__ == '__main__':
    main()

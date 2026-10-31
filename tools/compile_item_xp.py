"""Compile item-XP translation units in a fresh /tmp overlay; never install."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=Path('/home/eqemu/code'))
    args = parser.parse_args()
    stage = args.stage.resolve()
    if stage.parent != Path('/tmp') or not stage.name.startswith('nightcap-item-xp-'):
        raise ValueError('Use an isolated /tmp/nightcap-item-xp-* stage')
    output = stage / 'compile'
    output.mkdir()  # refuse accidental reuse
    overlay = output / 'source'
    overlay.mkdir()

    def mirror(source, target):
        for path in source.iterdir():
            if path.name in {'.git', 'build', 'vcpkg'}:
                continue
            dest = target / path.name
            if path.is_dir():
                dest.mkdir()
                mirror(path, dest)
            else:
                dest.symlink_to(path)

    mirror(args.source, overlay)
    for path in (stage/'candidate').rglob('*'):
        if not path.is_file():
            continue
        target = overlay / path.relative_to(stage/'candidate')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()  # unlink only this newly-created overlay symlink
        shutil.copy2(path, target)
    manifest = {'scope': 'isolated translation units, not linked or installed',
                'candidate_sources': {p.relative_to(stage/'candidate').as_posix():
                    hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (stage/'candidate').rglob('*') if p.is_file()}, 'units': []}
    units = ['common/item_instance.cpp', 'common/patches/rof2.cpp', 'common/rulesys.cpp', 'common/shareddb.cpp',
             'zone/advanced_loot_inventory.cpp', 'zone/exp.cpp', 'zone/inventory.cpp',
             'zone/bonuses.cpp', 'zone/spells.cpp', 'zone/spell_effects.cpp',
             'zone/client_packet.cpp', 'zone/client_mods.cpp', 'zone/command.cpp']
    for relative in units:
        target_name = relative.split('/')[0]
        flags_path = args.source / f'build/{target_name}/CMakeFiles/{target_name}.dir/flags.make'
        flags = dict(line.split(' = ', 1) for line in flags_path.read_text().splitlines() if ' = ' in line)
        options = sum((shlex.split(flags[key]) for key in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')), [])
        options = [value.replace(str(args.source/'zone/..'), str(overlay))
                   .replace(str(args.source/'common/..'), str(overlay)) for value in options]
        source = overlay/relative
        obj = output/(relative.replace('/','_')+'.o')
        dependencies = obj.with_suffix('.d')
        command = ['clang++', '-I'+str(overlay), '-I'+str(overlay/'zone'), *options,
                   '-MD', '-MF', str(dependencies), '-c', str(source), '-o', str(obj)]
        pch = args.source/f'build/{target_name}/CMakeFiles/{target_name}.dir/cmake_pch.hxx'
        if pch.is_file():
            text_pch = output/(target_name+'-pch.hxx')
            text_pch.write_text(pch.read_text().replace(str(args.source),str(overlay)))
            command[1:1] = ['-include',str(text_pch)]
        print('Compiling '+relative, flush=True)
        result = subprocess.run(command)
        manifest['units'].append({'file': relative, 'returncode': result.returncode,
                                  'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                                  'object_sha256': hashlib.sha256(obj.read_bytes()).hexdigest() if result.returncode == 0 else None,
                                  'dependency_sha256': {
                                      name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                                      for name in shlex.split(dependencies.read_text().replace('\\\n', ' ').split(':', 1)[1])
                                  } if result.returncode == 0 else {},
                                  'command': command})
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()

"""Compile changed server units against an isolated source overlay (no install).

Container usage: python3 compile_passive_aa.py --candidate /tmp/nightcap-passive-aa/server-mods/code
Uses the existing configured compiler/dependencies, without old precompiled headers.
This is translation-unit evidence, not a linked world/zone release build.
"""
import argparse
import hashlib
import json
import pathlib
import shlex
import shutil
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=pathlib.Path, required=True)
    parser.add_argument('--source', type=pathlib.Path, default=pathlib.Path('/home/eqemu/code'))
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    output = candidate.parent.parent / 'compile'
    if not str(output).startswith('/tmp/nightcap-passive-aa/') or (output.exists() and not args.resume):
        raise ValueError('Use a fresh isolated /tmp/nightcap-passive-aa directory for compilation')
    overlay = output / 'source'
    overlay.mkdir(parents=True, exist_ok=args.resume)
    # Link source files read-only by convention; copy candidates after unlinking.
    def mirror(source, dest):
        for path in source.iterdir():
            if path.name in {'.git', 'build', 'vcpkg'}:
                continue
            target = dest / path.name
            if path.is_dir():
                target.mkdir()
                mirror(path, target)
            else:
                target.symlink_to(path)
    if not args.resume:
        mirror(args.source, overlay)
    for path in candidate.rglob('*'):
        if path.is_file():
            target = overlay / path.relative_to(candidate)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.unlink(missing_ok=True)
            shutil.copy2(path, target)
    manifest = {'kind': 'translation-unit-compilation', 'files': []}
    for relative, target_name in [
        ('zone/exp.cpp', 'zone'), ('zone/client.cpp', 'zone'),
        ('zone/client_packet.cpp', 'zone'), ('zone/aa.cpp', 'zone'),
        ('zone/zonedb.cpp', 'zone'), ('zone/gm_commands/aa_exp.cpp', 'zone'),
        ('common/rulesys.cpp', 'common'), ('world/main.cpp', 'world'),
    ]:
        flags_file = args.source / f'build/{target_name}/CMakeFiles/{target_name}.dir/flags.make'
        flags = dict(line.split(' = ', 1) for line in flags_file.read_text().splitlines() if ' = ' in line)
        compile_flags = sum((shlex.split(flags[k]) for k in ('CXX_DEFINES', 'CXX_INCLUDES', 'CXX_FLAGS')), [])
        # Rewrite local include paths to the candidate overlay; retain configured libs/build paths.
        compile_flags = [f.replace(str(args.source / 'zone/..'), str(overlay))
                         .replace(str(args.source / 'common/..'), str(overlay))
                         .replace(str(args.source / 'world/..'), str(overlay)) for f in compile_flags]
        source = overlay / relative
        obj = output / (relative.replace('/', '_') + '.o')
        command = ['clang++', '-I' + str(overlay), '-I' + str(overlay/'zone'),
                   *compile_flags, '-c', str(source), '-o', str(obj)]
        # Reproduce CMake's implicit header context as text, never loading a stale PCH.
        pch = args.source / f'build/{target_name}/CMakeFiles/{target_name}.dir/cmake_pch.hxx'
        if pch.is_file():
            text_pch = output / (target_name + '-pch.hxx')
            text_pch.write_text(pch.read_text().replace(str(args.source), str(overlay)))
            command[1:1] = ['-include', str(text_pch)]
        print('Compiling ' + relative, flush=True)
        subprocess.run(command, check=True)
        manifest['files'].append({'file': relative, 'sha256': digest(source),
                                  'object_sha256': digest(obj), 'command': command})
        (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('All eight server translation units compiled.', flush=True)


if __name__ == '__main__':
    main()

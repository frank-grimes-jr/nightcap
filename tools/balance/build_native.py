"""Build a separate diagnostic zone executable without changing engine sources.

Run with container Python after copying this file and native_harness.cpp to an
isolated /tmp/nightcap-balance-* directory. Reuses the existing native object
files; the manifest pins them, but does not claim a fresh full-source rebuild.
"""
import argparse
import hashlib
import json
import shlex
import subprocess
from pathlib import Path


def patched_main(source):
    replacements = {
        'int main(int argc, char **argv)\n{':
            'bool NightcapBalancePreflight(int, char **);\nint NightcapBalanceMain(int, char **);\n'
            'int main(int argc, char **argv)\n{\n\tif (!NightcapBalancePreflight(argc, argv)) return 2;',
        '\n\tQServ->CheckForConnectState();': '\n\t// Isolated harness: QueryServ connection disabled.',
        '\tworldserver.Connect();': '\t// Isolated harness: world connection disabled.',
        '\tif (!CheckForCompatibleQuestPlugins()) {':
            '\t// The stat-only diagnostic has empty quest/plugin directories.\n'
            '\tif (false && !CheckForCompatibleQuestPlugins()) {',
        '\t\tZoneCLI::CommandHandler(argc, argv);\n\t}\n\n\tTimer InterserverTimer':
            '\t\treturn NightcapBalanceMain(argc, argv);\n\t}\n\n\tTimer InterserverTimer',
    }
    for old, new in replacements.items():
        if source.count(old) != 1:
            raise ValueError('Native main changed; review isolation patch before building: ' + old)
        source = source.replace(old, new)
    return source


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/home/eqemu/code'))
    args = parser.parse_args()
    output = Path(__file__).resolve().parent
    if output.parent != Path('/tmp') or not output.name.startswith('nightcap-balance-'):
        raise ValueError('Refusing to build outside isolated temporary harness directory')
    source = args.source.resolve()
    build = source / 'build/zone'
    flags_file = build / 'CMakeFiles/zone.dir/flags.make'
    flags = dict(line.split(' = ', 1) for line in flags_file.read_text().splitlines() if ' = ' in line)
    compile_flags = sum((shlex.split(flags[k]) for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')), [])
    link_file = build / 'CMakeFiles/zone.dir/link.txt'
    link = shlex.split(link_file.read_text())
    main_source = source / 'zone/main.cpp'
    generated = output / 'balance_main.cpp'
    generated.write_text(patched_main(main_source.read_text()))
    # Match the original main's quoted relative includes after moving its copy.
    compile_flags += ['-I' + str(source / 'zone')]
    for cpp in (generated, output / 'native_harness.cpp'):
        subprocess.run([link[0], *compile_flags, '-c', str(cpp), '-o', str(cpp.with_suffix('.o'))],
                       cwd=build, check=True)
    old_main = 'CMakeFiles/zone.dir/main.cpp.o'
    if link.count(old_main) != 1 or link.count('-o') != 1:
        raise ValueError('Unexpected native link command')
    link[link.index(old_main)] = str(generated.with_suffix('.o'))
    link.insert(1, str(output / 'native_harness.o'))
    # GNU libstdc++ random_device seed hook only in this diagnostic link.
    # Native EQ::Random engines/distributions and production objects stay intact.
    link.insert(1, '-Wl,--wrap=_ZNSt13random_device9_M_getvalEv')
    binary = output / 'balance-zone'
    link[link.index('-o') + 1] = str(binary)
    subprocess.run(link, cwd=build, check=True)
    objects = {arg: digest((build / arg).resolve()) for arg in link if arg.endswith(('.o','.a'))}
    manifest = {'binary_sha256':digest(binary), 'original_main_sha256':digest(main_source),
                'patched_main_sha256':digest(generated), 'harness_sha256':digest(output/'native_harness.cpp'),
                'flags_sha256':digest(flags_file), 'link_sha256':digest(link_file), 'objects':objects,
                'diagnostic_link_args':link,
                'random_header_sha256':digest(source/'common/random.h'),
                'rng_seed_hook':'GNU --wrap std::random_device::_M_getval; enabled only by NIGHTCAP_BALANCE_RNG_SEED',
                'scope':'Separate diagnostic binary reusing pinned native objects; no fresh full-source parity claim'}
    (output / 'native-build-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'binary':str(binary), 'sha256':manifest['binary_sha256'], 'objects':len(objects)}))


if __name__ == '__main__':
    main()

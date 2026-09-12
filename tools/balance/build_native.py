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


def patched_client(source):
    """Attach a packet sink only to the existing mock constructor in runtime mode."""
    start = source.index('Client::Client() : Mob(')
    end = source.index('Client::Client(EQStreamInterface *ieqs) : Mob(', start)
    body = source[start:end]
    old = '\tAI_Init();\n\n}\n\n'
    if body.count(old) != 1:
        raise ValueError('Native mock client changed; review runtime attachment')
    body = body.replace(old, '\tAI_Init();\n'
        '\t// Diagnostic-only mock transport; ordinary stat probes stay unchanged.\n'
        '\tif (auto *stream = NightcapBalanceStream(this)) {\n'
        '\t\teqs = stream;\n\t\tclient_state = CLIENT_CONNECTED;\n'
        '\t\tconn_state = ClientConnectFinished;\n'
        '\t\tm_ClientVersion = EQ::versions::ClientVersion::RoF2;\n'
        '\t\tm_ClientVersionBit = EQ::versions::bitRoF2;\n'
        '\t}\n\n}\n\n')
    return source[:start] + 'EQStreamInterface *NightcapBalanceStream(Client *);\n' + body + source[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/home/eqemu/code'))
    parser.add_argument('--spells-source', type=Path,
                        help='Compile a reviewed spells.cpp candidate inside this isolated runtime')
    parser.add_argument('--attack-source', type=Path,
                        help='Compile a reviewed attack.cpp candidate inside this isolated runtime')
    parser.add_argument('--reuse-adapters', action='store_true',
                        help='Reuse manifest-verified main/client adapter objects; still compile harness/runtime')
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
    client_source = source / 'zone/client.cpp'
    client_copy = output / 'balance_client.cpp'
    client_copy.write_text(patched_client(client_source.read_text()))
    # Match the original main's quoted relative includes after moving its copy.
    compile_flags += ['-I' + str(source / 'zone')]
    reused_adapters = []
    if args.reuse_adapters:
        prior = json.loads((output/'native-build-manifest.json').read_text())
        for cpp, original, key in ((generated,main_source,'main'),(client_copy,client_source,'client')):
            obj = str(cpp.with_suffix('.o'))
            if (prior.get('original_'+key+'_sha256') != digest(original)
                    or prior.get('patched_'+key+'_sha256') != digest(cpp)
                    or prior.get('flags_sha256') != digest(flags_file)
                    or prior.get('link_sha256') != digest(link_file)
                    or prior['objects'].get(obj) != digest(Path(obj))):
                raise ValueError('Adapter provenance changed; rebuild without --reuse-adapters')
            reused_adapters.append(cpp)
    for cpp in (generated, client_copy, output / 'native_harness.cpp', output / 'native_runtime.cpp'):
        if cpp in reused_adapters:
            continue
        subprocess.run([link[0], *compile_flags, '-c', str(cpp), '-o', str(cpp.with_suffix('.o'))],
                       cwd=build, check=True)
    spells_candidate = args.spells_source.resolve() if args.spells_source else None
    if spells_candidate:
        if spells_candidate.parent != output or spells_candidate.suffix != '.cpp':
            raise ValueError('The candidate must be a C++ file directly inside the isolated runtime')
        original_object = 'CMakeFiles/zone.dir/spells.cpp.o'
        if link.count(original_object) != 1:
            raise ValueError('Unexpected native spells object link entry')
        subprocess.run([link[0], *compile_flags, '-c', str(spells_candidate),
                        '-o', str(spells_candidate.with_suffix('.o'))], cwd=build, check=True)
        link[link.index(original_object)] = str(spells_candidate.with_suffix('.o'))
    attack_candidate = args.attack_source.resolve() if args.attack_source else None
    if attack_candidate:
        if attack_candidate.parent != output or attack_candidate.suffix != '.cpp':
            raise ValueError('The attack candidate must be a C++ file directly inside the isolated runtime')
        original_object = 'CMakeFiles/zone.dir/attack.cpp.o'
        if link.count(original_object) != 1:
            raise ValueError('Unexpected native attack object link entry')
        subprocess.run([link[0], *compile_flags, '-c', str(attack_candidate),
                        '-o', str(attack_candidate.with_suffix('.o'))], cwd=build, check=True)
        link[link.index(original_object)] = str(attack_candidate.with_suffix('.o'))
    old_main = 'CMakeFiles/zone.dir/main.cpp.o'
    if link.count(old_main) != 1 or link.count('-o') != 1:
        raise ValueError('Unexpected native link command')
    link[link.index(old_main)] = str(generated.with_suffix('.o'))
    old_client = 'CMakeFiles/zone.dir/client.cpp.o'
    if link.count(old_client) != 1:
        raise ValueError('Unexpected native client link entry')
    link[link.index(old_client)] = str(client_copy.with_suffix('.o'))
    link.insert(1, str(output / 'native_harness.o'))
    link.insert(1, str(output / 'native_runtime.o'))
    # GNU libstdc++ random_device seed hook only in this diagnostic link.
    # Native EQ::Random engines/distributions and production objects stay intact.
    link.insert(1, '-Wl,--wrap=_ZNSt13random_device9_M_getvalEv')
    link.insert(1, '-Wl,--wrap=gettimeofday,--wrap=time')
    link.insert(1, '-Wl,--wrap=_ZN11WorldServer10SendPacketEP12ServerPacket')
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
                'original_client_sha256':digest(client_source), 'patched_client_sha256':digest(client_copy),
                'runtime_sha256':digest(output/'native_runtime.cpp'),
                'runtime_header_sha256':digest(output/'native_runtime.h'),
                'reused_adapter_objects':[str(p.with_suffix('.o')) for p in reused_adapters],
                'clock_hook':'GNU --wrap gettimeofday/time; shared virtual clock only in explicit runtime mode',
                'scope':'Separate diagnostic binary reusing pinned native objects; no fresh full-source parity claim'}
    if spells_candidate:
        manifest['spells_candidate'] = {'source': str(spells_candidate),
                                      'sha256': digest(spells_candidate),
                                      'original_source_sha256': digest(source/'zone/spells.cpp')}
    if attack_candidate:
        manifest['attack_candidate'] = {'source': str(attack_candidate),
                                      'sha256': digest(attack_candidate),
                                      'original_source_sha256': digest(source/'zone/attack.cpp')}
    (output / 'native-build-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'binary':str(binary), 'sha256':manifest['binary_sha256'], 'objects':len(objects)}))


if __name__ == '__main__':
    main()

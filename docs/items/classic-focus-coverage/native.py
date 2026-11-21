"""Isolated diagnostic; imports exact retained shipping objects, never installs binaries."""
from pathlib import Path
import importlib.util, json, shutil, subprocess, sys
R = Path('/tmp/nightcap-classic-focus-coverage-20261120')
AA = Path('/tmp/nightcap-aa-availability-20261120')
s = importlib.util.spec_from_file_location('aa_shipping', AA / 'native.py')
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
b, src, build, objs = m.b, m.src, m.build, m.objs
rep = dict(m.rep)
rep['aa'] = AA / 'candidate/aa.o'
args = list(m.h.args)

def build_probe():
    reproduced = R / 'reproduced'
    reproduced.mkdir(exist_ok=True)
    expected = '98d6214630ef36fbd34a54185630543b1fd5266d41f9191078d6ab7e2d44872b'
    b.linker('shipping', reproduced, build, objs, args, rep)
    assert b.sha(reproduced / 'zone') == expected, 'shipping context mismatch'
    # The no-socket Client constructor normally enables login damage immunity.
    # Change ONLY its connection-completion enum in this diagnostic object.
    # Keep socket/client_state behavior untouched; do not patch combat methods.
    vfs_data = b.load(AA / 'candidate/vfs.json')
    tree = {r['name']: Path(r['external-contents']) for r in vfs_data['roots']}
    client_path = str(src / 'zone/client.cpp')
    original = tree.get(client_path, Path(client_path)).read_text()
    boundary = original.index('Client::Client(EQStreamInterface *ieqs)')
    ctor, tail = original[:boundary], original[boundary:]
    old = 'conn_state = NoPacketsReceived;'
    assert ctor.count(old) == 1
    changed = ctor.replace(old, 'conn_state = ClientConnectFinished; // isolated diagnostic login completion') + tail
    (R / 'client-before.cpp').write_text(original)
    client = R / 'client-diagnostic.cpp'
    client.write_text(changed)
    assert changed[changed.index('Client::Client(EQStreamInterface *ieqs)'):] == tail
    tree[client_path] = client
    vfs = R / 'diagnostic-vfs.json'
    vfs.write_text(json.dumps({'version': 0, 'use-external-names': False,
        'roots': [{'type': 'file', 'name': n, 'external-contents': str(p)} for n, p in tree.items()]}))
    b.compile_unit('shipping', 'client', build, src, objs, m.h.STACK / 'zone.pch', vfs, R / 'client-diagnostic.o')
    flags = b.ninja(build, str(objs / 'main.cpp.o'))
    flags = flags[:flags.index('-MD')]
    flags[flags.index('-include-pch') + 2] = str(m.h.STACK / 'zone.pch')
    b.run([*flags, '-ivfsoverlay', str(AA / 'candidate/vfs.json'), '-I' + str(src / 'zone'),
           '-o', str(R / 'probe.o'), '-c', str(R / 'probe.cpp')], build, R / 'probe.log')
    rr = dict(rep)
    rr['client'] = R / 'client-diagnostic.o'
    rr['main'] = Path('/tmp/nightcap-classic-stack-20261114/main.o')
    linkargs = list(args)
    linkargs[1:1] = [str(R / 'probe.o'), '-Wl,--wrap=_ZNSt13random_device9_M_getvalEv',
                     '-Wl,--wrap=gettimeofday', '-Wl,--wrap=time']
    diag = R / 'diagnostic'
    diag.mkdir(exist_ok=True)
    b.linker('shipping', diag, build, objs, linkargs, rr)
    b.save(R / 'build.json', {'shipping_zone': expected, 'diagnostic_zone': b.sha(diag / 'zone'),
                            'probe': b.sha(R / 'probe.cpp'), 'client_before': b.sha(R / 'client-before.cpp'),
                            'client_diagnostic': b.sha(client), 'adapter_scope': 'Default Client constructor conn_state only; all combat/cast methods unchanged'})

def measure():
    for name in ['shared', 'maps', 'plugins', 'quests', 'lua_modules']:
        p = R / name
        if not p.exists():
            p.symlink_to(Path('/tmp/nightcap-classic-stack-20261114') / name)
    pins = {'items': '4c5a40e58677c14834e219f094fa4cebda7c56aa453a7faf797d0480220d1986',
            'spells': '5039b3ab2528dbfcd13830ebd966887c6256e05981f47d70f71ba0c5b432f80c'}
    for name, expected in pins.items():
        assert b.sha(R / 'shared' / name) == expected, 'production cache mismatch: ' + name
    shutil.copyfile('/tmp/nightcap-classic-stack-20261114/eqemu_config.json', R / 'eqemu_config.json')
    (R / 'logs').mkdir(exist_ok=True)
    input_name = sys.argv[2] if len(sys.argv) > 2 else 'input.json'
    output_name = sys.argv[3] if len(sys.argv) > 3 else 'results.json'
    with (R / 'run.log').open('w') as log:
        proc = subprocess.run([R / 'diagnostic/zone', 'tests:balance', input_name, output_name],
                              cwd=R, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    if proc.returncode:
        raise RuntimeError((R / 'run.log').read_text()[-6000:])
    print('PASS controlled native pressure measurement', flush=True)

if __name__ == '__main__':
    build_probe() if sys.argv[1] == 'build' else measure()

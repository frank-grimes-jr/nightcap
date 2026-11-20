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
    flags = b.ninja(build, str(objs / 'main.cpp.o'))
    flags = flags[:flags.index('-MD')]
    flags[flags.index('-include-pch') + 2] = str(m.h.STACK / 'zone.pch')
    b.run([*flags, '-ivfsoverlay', str(AA / 'candidate/vfs.json'), '-I' + str(src / 'zone'),
           '-o', str(R / 'probe.o'), '-c', str(R / 'probe.cpp')], build, R / 'probe.log')
    rr = dict(rep)
    rr['main'] = Path('/tmp/nightcap-classic-stack-20261114/main.o')
    linkargs = list(args)
    linkargs[1:1] = [str(R / 'probe.o'), '-Wl,--wrap=_ZNSt13random_device9_M_getvalEv',
                     '-Wl,--wrap=gettimeofday', '-Wl,--wrap=time']
    diag = R / 'diagnostic'
    diag.mkdir(exist_ok=True)
    b.linker('shipping', diag, build, objs, linkargs, rr)
    b.save(R / 'build.json', {'shipping_zone': expected, 'diagnostic_zone': b.sha(diag / 'zone'),
                            'probe': b.sha(R / 'probe.cpp')})

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

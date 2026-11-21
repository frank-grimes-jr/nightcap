"""Separate corrected shipping and diagnostic builds; never overwrite earlier evidence."""
from pathlib import Path
import importlib.util, json, subprocess, sys, difflib

R = Path('/tmp/nightcap-classic-focus-coverage-20261120')
C = R / 'correction'
s = importlib.util.spec_from_file_location('focus_base', R / 'native.py')
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
b, src, build, objs = m.b, m.src, m.build, m.objs
EXPECTED = '98d6214630ef36fbd34a54185630543b1fd5266d41f9191078d6ab7e2d44872b'
GUARD = ('\t\t\t\t// Keep existing healing strength; only reject healing slots during mana lookup.\n'
         '\t\t\t\tif (type == focusManaCost && focus_spell.effect_id[i] != SpellEffect::ReduceManaCost) {\n'
         '\t\t\t\t\tbreak;\n\t\t\t\t}\n')

def tree():
    return {r['name']: Path(r['external-contents']) for r in b.load(m.AA / 'candidate/vfs.json')['roots']}

def overlay(mapping, path):
    path.write_text(json.dumps({'version': 0, 'use-external-names': False,
        'roots': [{'type': 'file', 'name': n, 'external-contents': str(p)} for n, p in mapping.items()]}))

def shipping():
    C.mkdir(exist_ok=True)
    paths = tree()
    key = str(src / 'zone/spell_effects.cpp')
    original = paths.get(key, Path(key)).read_text()
    candidate = (R / 'focus-candidate.cpp').read_text()
    assert candidate.count(GUARD) == 1
    assert candidate.replace(GUARD, '') == original, 'candidate must differ from retained shipping source only by approved guard'
    evidence = {'baseline_zone': EXPECTED, 'units': {}}
    for stage, content in [('reproduced', original), ('candidate', candidate)]:
        folder = C / stage
        folder.mkdir(exist_ok=True)
        source = folder / 'spell_effects.cpp'
        source.write_text(content)
        mapping = dict(paths)
        mapping[key] = source
        vfs = folder / 'vfs.json'
        overlay(mapping, vfs)
        obj = folder / 'spell_effects.o'
        b.compile_unit('shipping', 'spell_effects', build, src, objs, m.m.h.STACK / 'zone.pch', vfs, obj)
        rep = dict(m.rep)
        rep['spell_effects'] = obj
        b.linker('shipping', folder, build, objs, m.args, rep)
        if stage == 'reproduced':
            assert b.sha(folder / 'zone') == EXPECTED, 'full translation-unit reproduction mismatch'
        evidence['units'][stage] = {'source': b.sha(source), 'object': b.sha(obj), 'zone': b.sha(folder / 'zone')}
    evidence['scope'] = 'Shipping objects plus corrected spell_effects only; no diagnostic main, clock, or Client adapter in candidate zone'
    b.save(C / 'shipping-build.json', evidence)
    receipt()
    print('PASS exact shipping reproduction and corrected shipping zone', flush=True)

def receipt():
    evidence = b.load(C / 'shipping-build.json')
    before, after = C / 'reproduced/spell_effects.cpp', C / 'candidate/spell_effects.cpp'
    patch = C / 'feature.patch'
    patch.write_text(''.join(difflib.unified_diff(before.read_text().splitlines(True), after.read_text().splitlines(True),
        fromfile='a/server-mods/code/zone/spell_effects.cpp', tofile='b/server-mods/code/zone/spell_effects.cpp')))
    evidence.update({'baseline': {'zone': EXPECTED}, 'binaries': {'zone': b.sha(C / 'candidate/zone')},
        'before_source': b.sha(before), 'after_source': b.sha(after), 'patch': b.sha(patch)})
    b.save(C / 'build.json', evidence)

def diagnostics():
    # Reuse the already validated one-line login-completion adapter, not shipping client.o.
    original = tree().get(str(src / 'zone/client.cpp'), src / 'zone/client.cpp').read_text()
    assert (R / 'client-before.cpp').read_text() == original
    expected = original.replace('conn_state = NoPacketsReceived;',
        'conn_state = ClientConnectFinished; // isolated diagnostic login completion', 1)
    assert (R / 'client-diagnostic.cpp').read_text() == expected
    flags = b.ninja(build, str(objs / 'main.cpp.o'))
    flags = flags[:flags.index('-MD')]
    flags[flags.index('-include-pch') + 2] = str(m.m.h.STACK / 'zone.pch')
    b.run([*flags, '-ivfsoverlay', str(m.AA / 'candidate/vfs.json'), '-I' + str(src / 'zone'),
        '-o', str(C / 'probe.o'), '-c', str(R / 'probe.cpp')], build, C / 'probe.log')
    result = {'probe': b.sha(R / 'probe.cpp'), 'client_adapter': b.sha(R / 'client-diagnostic.o')}
    for stage in ('reproduced', 'candidate'):
        rep = dict(m.rep)
        rep['spell_effects'] = C / stage / 'spell_effects.o'
        rep['client'] = R / 'client-diagnostic.o'
        rep['main'] = Path('/tmp/nightcap-classic-stack-20261114/main.o')
        args = list(m.args)
        args[1:1] = [str(C / 'probe.o'), '-Wl,--wrap=_ZNSt13random_device9_M_getvalEv',
                    '-Wl,--wrap=gettimeofday', '-Wl,--wrap=time']
        diag = C / stage / 'diagnostic'
        diag.mkdir(exist_ok=True)
        b.linker('shipping', diag, build, objs, args, rep)
        result[stage] = b.sha(diag / 'zone')
    b.save(C / 'diagnostic-build.json', result)
    print('PASS baseline/corrected diagnostic builds', flush=True)

def measure(stage, input_name, output_name):
    assert stage in ('reproduced', 'candidate') and output_name.startswith('correction-')
    for name, expected in {'items': '4c5a40e58677c14834e219f094fa4cebda7c56aa453a7faf797d0480220d1986',
                          'spells': '5039b3ab2528dbfcd13830ebd966887c6256e05981f47d70f71ba0c5b432f80c'}.items():
        assert b.sha(R / 'shared' / name) == expected
    with (R / (output_name + '.log')).open('w') as log:
        p = subprocess.run([C / stage / 'diagnostic/zone', 'tests:balance', input_name, output_name],
                           cwd=R, stdout=log, stderr=subprocess.STDOUT, timeout=600)
    if p.returncode:
        raise RuntimeError((R / (output_name + '.log')).read_text()[-6000:])
    print('PASS ' + stage + ' ' + output_name, flush=True)

if __name__ == '__main__':
    if sys.argv[1] == 'shipping': shipping()
    elif sys.argv[1] == 'diagnostics': diagnostics()
    elif sys.argv[1] == 'receipt': receipt()
    else: measure(*sys.argv[2:])

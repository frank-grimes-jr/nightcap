"""Build in the local retained shipping workspace; never install or run a server."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys

ROOT = Path('/tmp/nightcap-aa-purchase-latency-20261121')
spec = importlib.util.spec_from_file_location(
    'shipping_focus', '/tmp/nightcap-classic-focus-coverage-20261120/correction_native.py')
shipping = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shipping)
b, source, build, objects = shipping.b, shipping.src, shipping.build, shipping.objs
EXPECTED = '13ad25346d8548b2c2592adafdc7dca2e52be020d836bbf0315a4f0f80ecc6c9'


def main():
    assert b.sha(shipping.C / 'candidate/zone') == EXPECTED
    inherited = {r['name']: Path(r['external-contents'])
                 for r in b.load(shipping.C / 'candidate/vfs.json')['roots']}
    replacements = dict(shipping.m.rep)
    replacements['spell_effects'] = shipping.C / 'candidate/spell_effects.o'
    evidence = {'baseline': {'zone': EXPECTED}, 'stages': {}}
    for stage in ('reproduced', 'candidate'):
        folder = ROOT / stage
        resume = stage == 'reproduced' and sys.argv[1:] == ['--resume-candidate']
        if resume:
            assert b.sha(folder / 'zone') == EXPECTED
        else:
            folder.mkdir(exist_ok=False)
        overlay = dict(inherited)
        for name in ('aa.cpp', 'client.h'):
            key = str(source / 'zone' / name)
            target = folder / 'source/zone' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            original = inherited.get(key, Path(key)).read_bytes()
            if resume:
                assert target.read_bytes() == original
            else:
                target.write_bytes(original)
            overlay[key] = target
        if stage == 'candidate':
            subprocess.run(['patch', '--fuzz=0', '--forward', '-p3'], cwd=folder / 'source',
                           input=(ROOT / 'feature.patch').read_bytes(), check=True)
            before = (ROOT / 'reproduced/source/zone/client.h').read_text()
            after = (folder / 'source/zone/client.h').read_text()
            # Only a nonvirtual method declaration changes: existing member
            # layout, vtable and no-argument symbol remain compatible.
            addition = '\tvoid SendAlternateAdvancementTimers(int purchased_family);\n'
            assert after.count(addition) == 1 and after.replace(addition, '') == before
        vfs = folder / 'vfs.json'
        shipping.overlay(overlay, vfs)
        if not resume:
            pch = b.fresh_pch('shipping', build, objects, vfs, folder)
            b.compile_unit('shipping', 'aa', build, source, objects, pch, vfs, folder / 'aa.o')
        current = dict(replacements)
        current['aa'] = folder / 'aa.o'
        inputs = b.linker('shipping', folder, build, objects, shipping.m.args, current)
        if stage == 'reproduced':
            assert b.sha(folder / 'zone') == EXPECTED, 'shipping source reproduction mismatch'
        evidence['stages'][stage] = {
            'zone': b.sha(folder / 'zone'), 'aa_object': b.sha(folder / 'aa.o'),
            'sources': {name: b.sha(folder / 'source/zone' / name) for name in ('aa.cpp', 'client.h')},
            'link_inputs': {name: b.sha(Path(name) if Path(name).is_absolute() else build / name)
                            for name in inputs},
        }
        print('PASS ' + stage + ' full AA translation unit and link', flush=True)
    evidence.update(binaries={'zone': b.sha(ROOT / 'candidate/zone')},
                    patch=b.sha(ROOT / 'feature.patch'),
                    scope='Local shipping build only; no installation, restart, DB or player writes')
    b.save(ROOT / 'build.json', evidence)


if __name__ == '__main__':
    main()

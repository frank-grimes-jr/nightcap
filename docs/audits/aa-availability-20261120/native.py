"""Reproduce the shipping predecessor and build only the AA translation unit."""
from pathlib import Path
import importlib.util
import json
import subprocess

R = Path('/tmp/nightcap-aa-availability-20261120')
HEAL = Path('/tmp/nightcap-fast-healing-20261120')
s = importlib.util.spec_from_file_location('healing', HEAL/'native.py')
h = importlib.util.module_from_spec(s)
s.loader.exec_module(h)
b, src, build, objs = h.b, h.src, h.build, h.objs
rep = dict(h.rep)
rep['effects'] = HEAL/'candidate/effects.o'
assert b.sha(HEAL/'candidate/zone') == '35330918b99b33b6a0d02fe3da6d3950ab4d97b6a9438c15e64bf2fa65db70d9'
tree = {r['name']:Path(r['external-contents']) for r in b.load(HEAL/'candidate/vfs.json')['roots']}
original = tree.get(str(src/'zone/aa.cpp'), src/'zone/aa.cpp')
assert b.sha(original) == '4b411cc28164148ff4cb054fb167436a578e781480bb46ba87fc58b6a7caca46'

def main():
    for stage in ('reproduced', 'candidate'):
        folder = R/stage
        folder.mkdir(parents=True, exist_ok=True)
        path = folder/'source/zone/aa.cpp'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(original.read_bytes())
        overlay = dict(tree)
        overlay[str(src/'zone/aa.cpp')] = path
        if stage == 'candidate':
            subprocess.run(['patch','--fuzz=0','--forward','-p3'],cwd=folder/'source',
                           input=(R/'feature.patch').read_bytes(),check=True)
            overlay[str(src/'common/aa_availability.h')] = R/'aa_availability.h'
        vfs = folder/'vfs.json'
        vfs.write_text(json.dumps({'version':0,'use-external-names':False,
            'roots':[{'type':'file','name':n,'external-contents':str(p)} for n,p in overlay.items()]}))
        b.compile_unit('shipping','aa',build,src,objs,h.STACK/'zone.pch',vfs,folder/'aa.o')
        replacements = dict(rep)
        replacements['aa'] = folder/'aa.o'
        b.linker('shipping',folder,build,objs,h.args,replacements)
        if stage == 'reproduced':
            assert b.sha(folder/'zone')==b.sha(HEAL/'candidate/zone'), 'shipping source reproduction failed'
    b.save(R/'build.json',dict(baseline={'zone':b.sha(R/'reproduced/zone')},
        binaries={'zone':b.sha(R/'candidate/zone')},patch=b.sha(R/'feature.patch'),
        before_source=b.sha(original),after_source=b.sha(R/'candidate/source/zone/aa.cpp'),
        availability_header=b.sha(R/'aa_availability.h')))
    print('PASS exact shipping reproduction and full AA translation-unit build',flush=True)

if __name__ == '__main__':main()

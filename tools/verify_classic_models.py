"""Read-only structural verification of a generated classic model candidate.

This proves archive/reference/texture integrity, not in-game rendering.
"""
import argparse
import hashlib
import json
from pathlib import Path
from classic_model_archives import actor_names, read_pfs, rename_wld

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--client', required=True, type=Path)
parser.add_argument('--assets', required=True, type=Path)
args = parser.parse_args()
plan_raw = (ROOT/'eq-client-dll/config/classic-models.json').read_bytes()
plan = json.loads(plan_raw)
audit = json.loads((args.assets/'classic-audit.json').read_bytes())
assert audit['plan_sha256'] == hashlib.sha256(plan_raw).hexdigest()
imports = (args.assets/'nightcap_models_chr.txt').read_text().splitlines()
assert int(imports[0]) == len(imports)-1
assert imports[1:1+len(plan['stock_imports'])] == plan['stock_imports']
expected_imports=set(plan['stock_imports'])
actor_catalog=set()
for archive in plan['archives']:
    original_raw=(args.client/archive['source']).read_bytes()
    assert hashlib.sha256(original_raw).hexdigest()==archive['source_sha256']
    original=read_pfs(original_raw)
    output_raw=(args.assets/archive['output']).read_bytes()
    assert audit['files'][archive['output']]=={'size':len(output_raw),'sha256':hashlib.sha256(output_raw).hexdigest()}
    output=read_pfs(output_raw)
    aliases=archive['aliases']
    reverse={v:k for k,v in aliases.items()}
    assert len(reverse)==len(aliases)
    filenames={n:aliases.get(n[:3].upper(),n[:3]).lower()+n[3:] for n in original if not n.endswith('.wld')}
    inverse_files={v:k for k,v in filenames.items()}
    original_wld=original[archive['source'][:-4]+'.wld']
    output_wld=output[archive['output'][:-4]+'.wld']
    assert rename_wld(output_wld,reverse,inverse_files)==original_wld, 'WLD geometry/reference/animation drift'
    assert len(output)==len(original)
    actors=set(actor_names(output_wld))
    for imp in archive['imports']:
        code,stem=imp.split(',')
        assert stem+'.s3d'==archive['output'] and code.upper()+'_ACTORDEF' in actors
        assert code.upper() not in actor_catalog
        actor_catalog.add(code.upper())
        expected_imports.add(imp)
    for name,target in filenames.items():
        expected=name
        if 'element_texture' in archive and name.startswith('ele'):
            expected=name[:5]+f"{archive['element_texture']:02d}"+name[7:]
        assert output[target]==original[expected], 'Texture/palette drift: '+name
assert set(imports[1:])==expected_imports
assert {r['alias'] for r in plan['registrations']}==actor_catalog
for race in (234,349,367,484): assert plan['remakes'][str(race)]==60
assert plan['remakes']['606']==161 and plan['remakes']['604']==122
assert plan['remakes']['485']==85
for race, original in ((566,1),(624,10),(678,3),(481,42)):
    assert plan['remakes'][str(race)]==original, 'Later model with an original counterpart passed through'
assert plan['remake_genders']['481']==1  # WOF: the original scaled-wolf mesh and scales.
for race, original in ((475,210),(476,209),(477,212),(478,211)):
    assert plan['remakes'][str(race)]==original, 'Air/Earth/Fire/Water remake order differs from original IDs'
for race,texture in ((209,0),(210,3),(211,2),(212,1)):
    reg=next(r for r in plan['registrations'] if r['race']==race)
    archive=next(a for a in plan['archives'] if a.get('element_texture')==texture)
    assert archive['aliases']['ELE']==reg['alias']
print('PASS: %d archives; lossless inverse WLDs; preserved textures; elemental palettes; imports; all configured skeletons and remakes' % len(plan['archives']))

"""Matched pet support with a no-slow control and native Feign Death strategy."""
import argparse
import copy
import gzip
import json
from pathlib import Path

from release_pool_controls import verify as verify_pool


def prepare(original, binary_sha256, pilot=False, escape_only=False):
    matrix = copy.deepcopy(original)
    matrix['binary_sha256'] = binary_sha256
    matrix['scope'] = 'Pet threat strategy versus no-slow control; unchanged source-constrained gear, legal AA purchases and preparation.'
    matrix['threat_comparison'] = {'hold_ms': 1000 if escape_only else 4000, 'pilot': pilot,
                                  'policies': ['feign_escape'] if escape_only else ['no_slow_control', 'feign_on_aggro']}
    cases = []
    for source in original['cases']:
        build = source['input']['builds'][0]
        if build['profile'] != 'mag-nec-shm':
            continue
        combat = source['input']['pet_probe']['combat']
        if pilot and (source['seed'] != 1729 or combat['npc_id'] != 32040
                      or build['aa_budget'] not in (0,165,306)):
            continue
        for policy in matrix['threat_comparison']['policies']:
            case = copy.deepcopy(source)
            case['paired_gear_case_id'] = source['id']
            case['id'] += '-'+policy
            case['input']['pet_probe']['combat'].update(threat_policy=policy, feign_hold_ms=matrix['threat_comparison']['hold_ms'])
            cases.append(case)
    if len(cases) != ((3 if pilot else 36) if escape_only else (6 if pilot else 72)):
        raise ValueError('Expected the complete source-constrained pet allocation matrix')
    matrix['cases'] = cases
    return matrix


def verify(matrix, evidence, original, catalog):
    if matrix != prepare(original, matrix['binary_sha256'], matrix['threat_comparison']['pilot'],
                         matrix['threat_comparison']['policies']==['feign_escape']):
        raise ValueError('Threat matrix changed gear, AA purchases or matched combat inputs')
    return verify_pool(matrix, evidence, catalog)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--binary-sha256')
    parser.add_argument('--pilot',action='store_true')
    parser.add_argument('--escape-only',action='store_true')
    parser.add_argument('--inputs',type=Path)
    parser.add_argument('--verify',type=Path)
    parser.add_argument('--catalog',type=Path)
    args = parser.parse_args()
    original = json.loads(args.original.read_text(encoding='utf-8'))
    if args.verify:
        if not args.inputs or not args.catalog:
            parser.error('--verify requires --inputs and --catalog')
        matrix = json.loads(args.inputs.read_text(encoding='utf-8'))
        rows = verify(matrix,json.loads(gzip.decompress(args.verify.read_bytes())),original,
                      json.loads(args.catalog.read_text(encoding='utf-8')))
        output = {'cases':rows}
        print(f'Verified {len(rows)} pet threat comparisons')
    else:
        if not args.binary_sha256:
            parser.error('Input generation requires --binary-sha256')
        output = prepare(original,args.binary_sha256,args.pilot,args.escape_only)
        print(f'Prepared {len(output["cases"])} pet threat comparisons')
    args.output.write_bytes((json.dumps(output,indent=2)+'\n').encode())

"""Respect native belly-casting protection in matched pet-support encounters."""
import argparse
import copy
import gzip
import json
from pathlib import Path

from pet_controls import run
from pet_support_controls import summarize as support_summary


def prepare(source, binary):
    matrix = copy.deepcopy(source)
    matrix['binary_sha256'] = binary
    matrix['scope'] = 'Matched pet support with native ranged-spell immunity respected; open AA sensitivity, not a release pool.'
    for case in matrix['cases']:
        case['id'] = case['id'].replace('pet-support-', 'pet-belly-')
        case['input']['pet_probe']['combat']['approach_policy'] = 'native_spell_range'
    return matrix


def summarize(case, report):
    result = support_summary(case, report)
    combat = report['pet_probe']['combat']
    if (combat['input'].get('approach_policy') != 'native_spell_range'
            or not combat['range_immunity'] or combat['movement']['approach_range'] != 0):
        raise ValueError('Captured dragons require native belly-casting range')
    if combat['trace'][0]['owner_combat_range']:
        raise ValueError('The 80-unit approach must begin outside native melee range')
    if not combat['movement']['events'] or not any(s['owner_combat_range'] for s in combat['trace']):
        raise ValueError('The owner never approached native belly-casting range')
    for action in combat['owner_actions']:
        if action['target'] == combat['boss_id'] and (not action['owner_combat_range'] or not action['owner_los']):
            raise ValueError('Offensive cast requested outside native belly range/LoS')
    return result | {'range_immunity': True, 'approach': 'native_melee_range',
                     'native_range_samples': sum(s['owner_combat_range'] for s in combat['trace']),
                     'control_interrupted_movement_requests': sum(not e['accepted'] for e in combat['movement']['events']),
                     'scope': 'Native belly-casting pet support; fixed candidate gear and explicit AA purchases. '
                              'No optimal-play, full BiS or release-balance certification.'}


def verify(matrix, evidence):
    cases = {c['id']: c for c in matrix['cases']}
    runs = {r['id']: r for r in evidence['runs']}
    if len(cases) != len(matrix['cases']) or len(runs) != len(evidence['runs']) or cases.keys() != runs.keys():
        raise ValueError('Incomplete or duplicate belly-casting evidence')
    for identity, case in cases.items():
        if summarize(case, runs[identity]['report']) != runs[identity]['summary']:
            raise ValueError('Belly-casting summary differs from native evidence')
    return [r['summary'] for r in evidence['runs']]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    matrix = json.loads(args.inputs.read_text(encoding='utf-8'))
    if args.run:
        run(matrix, args.output, summarize)
    else:
        summaries = verify(matrix, json.loads(gzip.decompress(args.verify.read_bytes())))
        args.output.write_bytes((json.dumps({'cases': summaries}, indent=2)+'\n').encode())
        print(f'Verified {len(summaries)} native belly-casting fights')

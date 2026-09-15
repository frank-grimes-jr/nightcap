"""Matched prepared boss controls for expanded zero-spend gear candidates."""
import argparse
import copy
import gzip
import json
from pathlib import Path

from active_aa_controls import run, verify_encounters
from augment_controls import verify_equipment
from verify_native_movement import verify as verify_movement


def prepare(candidates, previous, binary):
    controls = [c for c in previous['cases'] if c['input']['builds'][0]['aa_stage'] == '0']
    if len(controls) != 6:
        raise ValueError('Expected six prepared zero-spend comparison controls')
    cases = copy.deepcopy(controls)
    selected = []
    for build in candidates['builds']:
        policy = build['gear_search']
        # Three weapon layouts under a melee score, plus caster-balanced and
        # durability shields. Keep top available haste at each source ceiling.
        if (build['profile'] != 'war-clr-wiz'
                or policy['objective'] != 'melee' and policy['mode'] != 'shield'
                or policy['forced_haste'] != ('unforced' if policy['scope'] == 'captured_drops' else 'cloak36')):
            continue
        selected.append(build)
        for original in controls:
            case = copy.deepcopy(original)
            replacement = copy.deepcopy(build)
            replacement['gear_control'] = build['tier']
            case['input']['builds'] = [replacement]
            case['input']['export_equipment'] = True
            case['id'] += '/'+build['tier']
            cases.append(case)
    if not selected or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Missing candidates or duplicate cases')
    return {'scope': 'Prepared WAR/CLR/WIZ zero-spend gear sensitivity; unchanged AA allocation and controller, three seeds, not a full BiS certificate.',
            'binary_sha256': binary, 'selected_loadouts': [b['tier'] for b in selected], 'cases': cases}


def prepare_aa(candidates, previous, pools, binary):
    reference = next(b for b in candidates['builds'] if b['profile'] == 'war-clr-wiz'
                     and b['tier'] == 'captured_drops/balanced/shield/unforced')
    selected = copy.deepcopy(previous['cases'])
    for original in pools['cases']:
        identity = original['id']
        if any(marker in identity for marker in ('-early_core-100-', '-early_core-all-',
                                                '-expanded_core-all-', '-without_both-all-')):
            selected.append(copy.deepcopy(original))
    if len(selected) != 54:
        raise ValueError('Expected five open-AA budgets and four curated-pool controls')
    for case in selected:
        build = case['input']['builds'][0]
        build['equipment'] = copy.deepcopy(reference['equipment'])
        build['gear_control'] = 'expanded_balanced_shield'
        build['tier'] += '/expanded_balanced_shield'
        for key in ('total_score', 'raw_item_totals', 'capped_spell_damage', 'capped_heal_amount'):
            build.pop(key, None)
        case['input']['export_equipment'] = True
        case['id'] += '/expanded_balanced_shield'
    return {'scope': 'Identical expanded balanced shield loadout at five open-AA budgets and four proposed AA-pool controls; no deployed curation or full BiS claim.',
            'binary_sha256': binary, 'cases': selected}


def verify(matrix, evidence, previous):
    summaries = verify_encounters(matrix, evidence)
    cases = {c['id']: c for c in matrix['cases']}
    old = {r['id']: r for r in previous['runs']}
    legacy, movement = [], []
    for entry in evidence['runs']:
        case, report = cases[entry['id']], entry['report']
        movement.append({'id': entry['id'], **verify_movement(report)})
        if case['input'].get('export_equipment'):
            verify_equipment(case['input'], report)
        else:
            if entry['native_raw_sha256'] != old[entry['id']]['native_raw_sha256']:
                raise ValueError('Legacy no-augment native report changed')
            legacy.append(entry['id'])
    if len(legacy) != 6:
        raise ValueError('Missing unchanged legacy encounters')
    return {'summaries': summaries, 'movement': movement, 'unchanged_legacy': legacy}


def verify_aa(matrix, evidence, gear_evidence):
    summaries = verify_encounters(matrix, evidence)
    cases = {c['id']: c for c in matrix['cases']}
    reference = {r['id'].split('/captured_drops/')[0]: r['report']['encounter']
                 for r in gear_evidence['runs'] if r['id'].endswith('/captured_drops/balanced/shield/unforced')}
    movement, unchanged = [], []
    equipment = matrix['cases'][0]['input']['builds'][0]['equipment']
    for entry in evidence['runs']:
        case = cases[entry['id']]
        if case['input']['builds'][0]['equipment'] != equipment:
            raise ValueError('AA comparison changed equipment')
        verify_equipment(case['input'], entry['report'])
        movement.append({'id': entry['id'], **verify_movement(entry['report'])})
        if case['input']['builds'][0]['aa_stage'] == '0':
            identity = case['id'].removesuffix('/expanded_balanced_shield')
            if reference[identity] != entry['report']['encounter']:
                raise ValueError('Zero-spend encounter differs from gear comparison')
            unchanged.append(entry['id'])
    if len(unchanged) != 6:
        raise ValueError('Missing matched zero-spend encounters')
    return {'summaries': summaries, 'movement': movement, 'unchanged_zero_spend': unchanged}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--aa', action='store_true', help='Verify fixed-gear AA matrix against earlier gear encounters')
    args = parser.parse_args()
    matrix = json.loads(args.inputs.read_text())
    if args.run:
        run(matrix, args.output)
    else:
        check = verify_aa if args.aa else verify
        result = check(matrix, json.loads(gzip.decompress(args.verify.read_bytes())),
                       json.loads(gzip.decompress(args.previous.read_bytes())))
        args.output.write_bytes((json.dumps(result, indent=2)+'\n').encode())
        print(f'Verified {len(result["summaries"])} encounters and six matched controls')


if __name__ == '__main__':
    main()

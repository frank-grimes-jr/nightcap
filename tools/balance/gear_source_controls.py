"""Matched native AA-pool fights after removing an unproven NPC gear source."""
import argparse
import copy
import gzip
import json
from pathlib import Path

from builds import PROFILES, load_snapshot
from gear_candidates import equipment, socket_augments
from release_pool_controls import verify as verify_pool


OBJECTIVES = {'war-clr-wiz': 'balanced', 'war-clr-mnk': 'melee', 'mag-nec-shm': 'balanced'}


def source_items(snapshot, excluded):
    known = {r['npc_id'] for r in snapshot['tables']['drop_sources']}
    if (not excluded or len(set(excluded)) != len(excluded)
            or any(type(n) is not int or n not in known for n in excluded)):
        raise ValueError('Expected distinct known excluded NPC IDs')
    sources = {}
    for row in snapshot['tables']['drop_sources']:
        if row['npc_id'] not in excluded:
            sources.setdefault(row['item_id'], []).append(row)
    # A second surviving source keeps an item eligible, including its captured tiers.
    items = [i for i in snapshot['tables']['items'] if i['id'] % 200000 in sources]
    return items, sources


def prepare(original, snapshot, snapshot_sha256, excluded=(56182,), monk_cloak36=False, binary_sha256=None):
    items, sources = source_items(snapshot, excluded)
    loadouts = {}
    for profile, objective in OBJECTIVES.items():
        classes, casting_stat, _ = PROFILES[profile]
        forced = {8: 611621} if monk_cloak36 and profile == 'war-clr-mnk' else {}
        gear = equipment(items, classes, 50, casting_stat, objective, 'shield', forced)
        augs = socket_augments(gear, items, classes, 50, casting_stat, objective)
        entries = [{'slot': slot, 'id': item['id'], 'augments': augs[slot]} for slot, item in gear.items()]
        ids = {e['id'] for e in entries} | {a['id'] for e in entries for a in e['augments']}
        loadouts[profile] = {'objective': objective, 'mode': 'shield', 'forced_haste': 'cloak36' if forced else 'unforced',
                             'max_raw_worn_haste': max(i['haste'] for i in gear.values()),
                             'equipment': entries,
                             'sources': {str(i): sources[i % 200000] for i in sorted(ids)}}
    matrix = copy.deepcopy(original)
    if binary_sha256 is not None:
        matrix['binary_sha256'] = binary_sha256
    suffix = 'sources-excluding-'+'-'.join(str(n) for n in sorted(excluded))
    matrix['scope'] = ('Matched source-exclusion sensitivity, fixed legal AA pools and controllers. '
                       'Surviving drop sources are not certified solo acquisition or full BiS.')
    matrix['gear_source_policy'] = {'excluded_npc_ids': sorted(excluded),
                                     'snapshot_sha256': snapshot_sha256, 'loadouts': loadouts}
    if monk_cloak36:
        matrix['gear_source_policy']['monk_cloak36'] = True
        matrix['cases'] = [c for c in matrix['cases'] if c['input']['builds'][0]['profile'] == 'war-clr-mnk']
        suffix += '-cloak36'
    for case in matrix['cases']:
        case['paired_case_id'] = case['id']
        case['id'] += '-'+suffix
        build = case['input']['builds'][0]
        build['equipment'] = copy.deepcopy(loadouts[build['profile']]['equipment'])
        build['tier'] += '/'+suffix
        # Replace a stale generator description where the original pet template has one.
        if 'gear_search' in build:
            build['gear_search'] = {k: v for k, v in loadouts[build['profile']].items()
                                    if k not in ('equipment', 'sources')}
            build['gear_search']['scope'] = suffix
        if 'pet_probe' in case['input']:
            case['input']['pet_probe']['combat']['capture_terminal'] = True
    return matrix


def verify(matrix, evidence, original, snapshot, snapshot_sha256, catalog):
    expected = prepare(original, snapshot, snapshot_sha256,
                       matrix['gear_source_policy']['excluded_npc_ids'],
                       matrix['gear_source_policy'].get('monk_cloak36', False), matrix['binary_sha256'])
    if matrix != expected:
        raise ValueError('Source-exclusion matrix differs from regenerated gear or paired inputs')
    return verify_pool(matrix, evidence, catalog)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--catalog', type=Path)
    parser.add_argument('--monk-cloak36', action='store_true')
    parser.add_argument('--binary-sha256')
    args = parser.parse_args()
    original = json.loads(args.original.read_text(encoding='utf-8'))
    snapshot, manifest = load_snapshot(args.snapshot)
    if args.verify:
        if not args.inputs or not args.catalog:
            parser.error('--verify requires --inputs and --catalog')
        matrix = json.loads(args.inputs.read_text(encoding='utf-8'))
        results = verify(matrix, json.loads(gzip.decompress(args.verify.read_bytes())), original,
                         snapshot, manifest['snapshot_sha256'],
                         json.loads(args.catalog.read_text(encoding='utf-8')))
        output = {'cases': results}
        print(f'Verified {len(results)} matched source-exclusion fights')
    else:
        output = prepare(original, snapshot, manifest['snapshot_sha256'], monk_cloak36=args.monk_cloak36,
                         binary_sha256=args.binary_sha256)
        print(f'Prepared {len(output["cases"])} matched source-exclusion fights')
    args.output.write_bytes((json.dumps(output, indent=2)+'\n').encode())

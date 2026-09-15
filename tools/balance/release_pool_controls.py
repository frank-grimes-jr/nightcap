"""Shared AA whitelist candidates across native caster, melee and pet controllers."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path

from pet_controls import run
from pet_belly_controls import summarize as pet_summary
from melee_controls import verify_case as combat_summary
from augment_controls import verify_equipment
from verify_native_movement import verify as verify_movement


def allocation_plan(catalog, specification):
    from aa_allocations import Purchases, progression, within_budget
    free_caps = {int(k): v for k, v in specification['free_caps'].items()}
    known = {r['ability_id'] for b in catalog['builds'] for r in b['aa_catalog']}
    policies = specification['policies']
    if len({p['id'] for p in policies}) != len(policies):
        raise ValueError('Duplicate release policy')
    allocations = {}
    for b in catalog['builds']:
        profile, ranks = b['profile'], b['aa_catalog']
        for policy in policies:
            caps = {int(k): v for k, v in policy['caps'].items()}
            if free_caps.keys() & caps.keys() or any(a not in known for a in caps | free_caps):
                raise ValueError('Unknown or overlapping AA family')
            caps |= free_caps
            if any(not isinstance(v, int) or isinstance(v, bool) or v < 1 for v in caps.values()):
                raise ValueError('Invalid rank cap')
            allowed = [r for r in ranks if r['rank'] <= caps.get(r['ability_id'], 0)]
            if any(r['cost'] != 0 for r in allowed if r['ability_id'] in free_caps):
                raise ValueError('Free baseline contains a paid rank')
            closure = Purchases(allowed)
            closure.free_closure()
            free_ids = closure.ids.copy()
            unreachable = closure.all_closure()
            reachable = [r for r in allowed if r['rank_id'] in closure.ids]
            path, _ = progression(reachable, profile, 'balanced')
            path.all_closure()
            for requested in policy['budgets']:
                if requested != 'all' and (not isinstance(requested, int) or isinstance(requested, bool) or requested < 0):
                    raise ValueError('Invalid requested AA budget')
                budget = closure.spent if requested == 'all' else requested
                state, next_rank = within_budget(reachable, path.ids, budget)
                digest = hashlib.sha256(json.dumps([profile, state.ids], separators=(',', ':')).encode()).hexdigest()[:16]
                key = profile+'-'+digest
                row = allocations.setdefault(key, {'key': key, 'profile': profile, 'spent': state.spent,
                                                   'rank_ids': state.ids, 'free_rank_ids': free_ids, 'aliases': []})
                alias = {'policy': policy['id'], 'requested': requested, 'spent': state.spent,
                         'unused_points': budget-state.spent, 'pool_cost': closure.spent,
                         'pool_exhausted': set(state.ids) == set(closure.ids),
                         'next_rank_id': next_rank, 'unreachable': unreachable}
                if alias in row['aliases']:
                    raise ValueError('Duplicate requested AA stage')
                row['aliases'].append(alias)
    return list(allocations.values())


def prepare(catalog, specification, caster, melee, pets, binary):
    templates = {
        'war-clr-wiz': [c for c in caster['cases'] if c['input']['builds'][0]['profile'] == 'war-clr-wiz'
                       and c['input']['builds'][0]['aa_stage'] == '0'],
        'war-clr-mnk': [c for c in melee['cases'] if c['input']['builds'][0]['profile'] == 'war-clr-mnk'
                       and c['input']['builds'][0]['tier'] == 'monk/shield/0/specials-True'],
        'mag-nec-shm': [c for c in pets['cases'] if c['input']['builds'][0]['aa_stage'] == '0']}
    for profile, cases in templates.items():
        coordinates = [(c['input'].get('encounter', c['input'].get('pet_probe', {}).get('combat'))['npc_id'], c['seed']) for c in cases]
        if sorted(coordinates) != [(boss, seed) for boss in (32040, 73057) for seed in (1729, 1730, 1731)]:
            raise ValueError('Expected two bosses and three seeds per profile: '+profile)
        if any(c['input']['builds'][0]['equipment'] != cases[0]['input']['builds'][0]['equipment'] for c in cases):
            raise ValueError('Candidate equipment varies within a profile')
    allocations = allocation_plan(catalog, specification)
    cases = []
    for allocation in allocations:
        for original in templates[allocation['profile']]:
            case = copy.deepcopy(original)
            encounter = case['input'].get('encounter', case['input'].get('pet_probe', {}).get('combat'))
            case['id'] = f"{allocation['key']}-{encounter['npc_id']}-{case['seed']}"
            case['allocation_key'] = allocation['key']
            case['aa_pool'] = 'shared curated candidate'
            build = case['input']['builds'][0]
            build.update(aa_rank_ids=allocation['rank_ids'], aa_budget=allocation['spent'],
                         aa_stage=str(allocation['spent']), aa_policy='shared_release_candidate')
            cases.append(case)
    return {'scope': 'Shared global AA caps and explicit free whitelist, fixed gear per profile. '
                     'Identical purchased allocations share native evidence; unused requested budgets are audit metadata, not unspent character wallet points.',
            'binary_sha256': binary, 'specification': specification, 'allocations': allocations, 'cases': cases}


def summarize(case, report):
    if 'pet_probe' in case['input']:
        native = pet_summary(case, report)
        encounter = report['pet_probe']['combat']
        boss, elapsed = encounter['input']['npc_id'], native['elapsed_ms']
        won = encounter['result'] == 'boss_death'
        minimum = native['min_owner_hp_percent']
        final_hp = native['final_boss_hp']
    else:
        native = combat_summary(case, report)
        verify_movement(report)
        verify_equipment(case['input'], report)
        boss, elapsed = native['npc_id'], native['elapsed_ms']
        won = native['result'] == 'npc_death'
        minimum = max(0, native['minimum_sampled_player_hp'])/native['initial_hp']*100
        final_hp = native['final_npc_hp']
    expected, player = case['input']['builds'][0], report['builds'][0]
    if (player['aa_spent'] != expected['aa_budget'] or player['aa_remaining'] != 0
            or player['aa_spent'] != sum(r['cost'] for r in player['aa_purchases'])
            or player['aa_stage'] != expected['aa_stage'] or player['aa_policy'] != expected['aa_policy']):
        raise ValueError('Native shared-pool allocation accounting differs')
    return json.loads(json.dumps({'id': case['id'], 'allocation_key': case['allocation_key'],
                                  'profile': player['profile'], 'aa_spent': player['aa_spent'],
                                  'npc_id': boss, 'seed': case['seed'], 'won': won,
                                  'result': native['result'], 'elapsed_ms': elapsed,
                                  'minimum_hp_percent': minimum, 'final_boss_hp': final_hp, 'native': native}))


def verify(matrix, evidence, catalog):
    if matrix['allocations'] != allocation_plan(catalog, matrix['specification']):
        raise ValueError('Allocation or budget aliases differ from the shared whitelist')
    cases = {c['id']: c for c in matrix['cases']}
    runs = {r['id']: r for r in evidence['runs']}
    if len(cases) != len(matrix['cases']) or len(runs) != len(evidence['runs']) or cases.keys() != runs.keys():
        raise ValueError('Incomplete or duplicate shared-pool evidence')
    allocations = {a['key']: a for a in matrix['allocations']}
    if len(allocations) != len(matrix['allocations']):
        raise ValueError('Duplicate allocation')
    for identity, case in cases.items():
        allocation = allocations[case['allocation_key']]
        build = case['input']['builds'][0]
        if (build['aa_rank_ids'] != allocation['rank_ids'] or build['aa_budget'] != allocation['spent']
                or build['profile'] != allocation['profile']):
            raise ValueError('Case differs from shared allocation')
        if summarize(case, runs[identity]['report']) != runs[identity]['summary']:
            raise ValueError('Shared-pool summary differs from native evidence')
    return [r['summary'] for r in evidence['runs']]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--catalog', type=Path)
    args = parser.parse_args()
    matrix = json.loads(args.inputs.read_text(encoding='utf-8'))
    if args.run:
        run(matrix, args.output, summarize)
    else:
        if not args.catalog:
            parser.error('--verify requires --catalog for independent whitelist validation')
        results = verify(matrix, json.loads(gzip.decompress(args.verify.read_bytes())),
                         json.loads(args.catalog.read_text(encoding='utf-8')))
        args.output.write_bytes((json.dumps({'cases': results}, indent=2)+'\n').encode())
        print(f'Verified {len(results)} shared AA-pool fights')

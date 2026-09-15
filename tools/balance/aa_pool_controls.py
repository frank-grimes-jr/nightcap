"""Compare explicit AA availability candidates without changing server rules."""
import argparse
import copy
import gzip
import json
from pathlib import Path

from active_aa_controls import run, verify_encounters


def prepare(source, catalog, specification):
    from aa_allocations import Purchases, progression, within_budget
    profile = specification['profile']
    ranks = next(b['aa_catalog'] for b in catalog['builds'] if b['profile'] == profile)
    zero = next(c['input']['builds'][0] for c in source['cases'] if c['input']['builds'][0]['aa_stage'] == '0')
    free_ids = zero['aa_rank_ids']
    originals = [c for c in source['cases'] if c['input']['builds'][0]['aa_stage'] == 'all']
    if len(originals) != 6 or any(c['input']['builds'][0]['profile'] != profile for c in originals):
        raise ValueError('Expected six prepared source controls for the requested profile')
    cases, allocations = [], []
    for policy in specification['policies']:
        caps = {int(k): v for k, v in policy.get('caps', {}).items()}
        excluded = set(policy.get('exclude', []))
        if bool(caps) == bool(excluded):
            raise ValueError('Choose rank caps or excluded abilities for each candidate')
        allowed = [r for r in ranks if r['ability_id'] not in excluded and
                   (not caps or r['rank_id'] in free_ids or r['rank'] <= caps.get(r['ability_id'], 0))]
        closure = Purchases(allowed)
        closure.free_closure()
        if closure.ids != free_ids:
            raise ValueError('Candidate changes the common free baseline')
        unreachable = closure.all_closure()
        # Prerequisites stay authoritative: never reintroduce an excluded rank
        # merely to satisfy an otherwise allowed family's purchase requirement.
        purchased = set(closure.ids)
        reachable = [r for r in allowed if r['rank_id'] in purchased]
        if caps:
            ordered, _ = progression(reachable, profile, 'balanced')
            ordered.all_closure()
        else:
            ordered = closure
        for budget in policy['budgets']:
            limit = ordered.spent if budget == 'all' else budget
            state, next_rank = within_budget(reachable, ordered.ids, limit)
            allocation = {'policy': policy['id'], 'budget': budget, 'spent': state.spent,
                          'unused_points': limit-state.spent, 'pool_cost': closure.spent,
                          'pool_exhausted': set(state.ids) == set(closure.ids),
                          'next_rank_id': next_rank, 'rank_ids': state.ids,
                          'unreachable': unreachable}
            if excluded:
                removed = set(originals[0]['input']['builds'][0]['aa_rank_ids']) - set(state.ids)
                grouped = {}
                for rank in sorted(ranks, key=lambda r: r['rank_id']):
                    if rank['rank_id'] not in removed:
                        continue
                    group = grouped.setdefault(rank['ability_id'], {
                        'ability_id': rank['ability_id'], 'name': rank['name'],
                        'removed_ranks': [], 'cost': 0})
                    group['removed_ranks'].append(rank['rank'])
                    group['cost'] += rank['cost']
                allocation['removed_from_unrestricted'] = list(grouped.values())
            allocations.append(allocation)
            for original in originals:
                case = copy.deepcopy(original)
                case['id'] = f"{original['input']['encounter']['npc_id']}-{policy['id']}-{budget}-{case['seed']}"
                build = case['input']['builds'][0]
                build.update(aa_budget=limit, aa_rank_ids=state.ids, aa_stage=str(budget), aa_policy=policy['id'])
                cases.append(case)
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Duplicate AA pool comparison')
    return ({'scope': 'Diagnostic rank-pool candidates and matched burst removals, fixed gear/preparation; no server AA availability change.',
             'binary_sha256': source['binary_sha256'], 'cases': cases},
            {'profile': profile, 'comparison_free_rank_ids': free_ids, 'allocations': allocations})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    matrix = json.loads(args.inputs.read_text())
    if args.run:
        run(matrix, args.output)
    else:
        result = verify_encounters(matrix, json.loads(gzip.decompress(args.verify.read_bytes())))
        args.output.write_bytes((json.dumps({'controls': result}, indent=2)+'\n').encode())
        print(f'Verified {len(result)} native AA-pool encounters')


if __name__ == '__main__':
    main()

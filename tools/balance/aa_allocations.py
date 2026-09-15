"""Deterministic AA purchase candidates from a native eligibility catalogue.

These are explicit progression policies, not proven optimal encounter builds.
Native CanPurchaseAlternateAdvancementRank remains the final authority.
"""
import argparse
import hashlib
import json
from pathlib import Path

from builds import load_snapshot
from prepare_native import native_inputs


class Purchases:
    def __init__(self, ranks):
        self.ranks = {r['rank_id']: r for r in ranks}
        self.by_level = {(r['ability_id'], r['rank']): r for r in ranks}
        if len(self.ranks) != len(ranks) or len(self.by_level) != len(ranks):
            raise ValueError('Duplicate AA rank or ability level')
        if any(r['cost'] < 0 or r['rank'] < 1 for r in ranks):
            raise ValueError('Invalid AA cost or rank')
        self.owned = {}
        self.ids = []
        self.spent = 0

    def reasons(self, r):
        reasons = []
        owned = self.owned.get(r['ability_id'])
        if r['grant_only']:
            reasons.append('grant_only')
        if owned and owned['rank'] >= r['rank']:
            reasons.append('already_owned')
        if r['previous_rank_id'] > 0 and (not owned or owned['rank_id'] != r['previous_rank_id']):
            reasons.append('previous_rank')
        if owned and r['charges'] > 0:
            reasons.append('unspent_charges')
        for p in r['prereqs']:
            # Native purchasing skips prerequisites whose ability does not exist.
            if p['ability_exists'] and self.owned.get(p['ability_id'], {}).get('rank', 0) < p['ranks']:
                reasons.append('prerequisite:' + str(p['ability_id']))
        return reasons

    def buy(self, r):
        if self.reasons(r):
            raise ValueError(f"Illegal purchase {r['rank_id']}: {self.reasons(r)}")
        self.owned[r['ability_id']] = r
        self.ids.append(r['rank_id'])
        self.spent += r['cost']

    def free_closure(self):
        while True:
            available = [r for r in self.ranks.values() if r['cost'] == 0 and not self.reasons(r)]
            if not available:
                return
            for r in sorted(available, key=lambda r: (r['ability_id'], r['rank'])):
                if not self.reasons(r):
                    self.buy(r)

    def require(self, ability, level, visiting=None):
        """Buy a milestone with prerequisites; reject cycles/unavailable ranks."""
        if self.owned.get(ability, {}).get('rank', 0) >= level:
            return
        r = self.by_level.get((ability, level))
        if not r or r['grant_only']:
            raise ValueError(f'Unavailable milestone {ability}:{level}')
        visiting = set() if visiting is None else visiting
        if r['rank_id'] in visiting:
            raise ValueError('Cyclic AA prerequisites')
        visiting = visiting | {r['rank_id']}
        if r['previous_rank_id'] > 0:
            previous = self.ranks.get(r['previous_rank_id'])
            if not previous or previous['ability_id'] != ability:
                raise ValueError('Unavailable previous AA rank')
            self.require(ability, previous['rank'], visiting)
        for p in sorted(r['prereqs'], key=lambda p: p['ability_id']):
            if p['ability_exists']:
                self.require(p['ability_id'], p['ranks'], visiting)
        self.buy(r)

    def all_closure(self):
        while True:
            available = [r for r in self.ranks.values() if not self.reasons(r)]
            if not available:
                break
            for r in sorted(available, key=lambda r: (r['ability_id'], r['rank'])):
                if not self.reasons(r):
                    self.buy(r)
        purchased = set(self.ids)
        return [{'rank_id': r['rank_id'], 'ability_id': r['ability_id'],
                 'reasons': self.reasons(r)} for r in self.ranks.values()
                if r['rank_id'] not in purchased]


DEFENSE = [28, 33, 34]  # Natural Durability, Combat Stability, Combat Agility
SUSTAIN = [20, 224, 18, 19]  # Casting Mastery, Mental Clarity, Healing Adept/Gift
ROLE = {
    'war-clr-wiz': {'offense': [23, 114, 215, 397, 398], 'active': [300, 308, 38, 169, 515]},
    'war-clr-mnk': {'offense': [30, 189, 108, 273, 338, 341, 274, 3511],
                    'active': [300, 38, 169, 109]},
    'mag-nec-shm': {'offense': [3512, 3818, 1205, 1403, 23, 215, 398],
                    'active': [47, 58, 3707, 7703, 515]},
}


def milestones(profile, policy, ranks):
    if policy not in ('balanced', 'durability_first'):
        raise ValueError('Unknown AA allocation policy')
    role = ROLE[profile]
    caps = {}
    for r in ranks:
        if not r['grant_only']:
            caps[r['ability_id']] = max(caps.get(r['ability_id'], 0), r['rank'])
    groups = [DEFENSE, SUSTAIN, role['offense']] if policy == 'durability_first' else [role['offense'], SUSTAIN, DEFENSE]
    # First useful ranks across core families, then early activations, then deepen.
    result = []
    for target in (1, 3, 6, 12, 25, 40):
        for group in groups:
            for ability in group:
                if ability in caps:
                    result.append((ability, min(target, caps[ability])))
        if target == 1:
            result.extend((a, 1) for a in role['active'] if a in caps)
    return result


def progression(ranks, profile, policy):
    state = Purchases(ranks)
    state.free_closure()
    free_ids = state.ids.copy()
    for ability, level in milestones(profile, policy, ranks):
        state.require(ability, level)
    return state, free_ids


def within_budget(ranks, ordered_ids, budget):
    """Use a nested purchase prefix; keep an unaffordable next rank explicit."""
    if budget < 0:
        raise ValueError('Negative AA budget')
    state = Purchases(ranks)
    next_rank = None
    for rank_id in ordered_ids:
        r = state.ranks[rank_id]
        if state.spent + r['cost'] > budget:
            next_rank = rank_id
            break
        state.buy(r)
    return state, next_rank


def matrix(catalog, inputs):
    catalogs = {b['profile']: b['aa_catalog'] for b in catalog['builds']}
    if len(catalogs) != len(catalog['builds']):
        raise ValueError('Duplicate profile catalog')
    result, audit = [], []
    for build in inputs['builds']:
        if build['tier'] != 'Ascended':
            continue
        profile = build['profile']
        ranks = catalogs[profile]
        free = Purchases(ranks)
        free.free_closure()
        common = {'aa_budget': 0, 'aa_rank_ids': free.ids, 'aa_stage': '0', 'aa_policy': 'common_free'}
        result.append(build | common)
        for policy in ('balanced', 'durability_first'):
            path, _ = progression(ranks, profile, policy)
            if path.spent < 500:
                raise ValueError('AA policy does not cover the requested 500-point stage')
            for budget in (100, 200, 500):
                state, next_rank = within_budget(ranks, path.ids, budget)
                result.append(build | {'aa_budget': budget, 'aa_rank_ids': state.ids,
                              'aa_stage': str(budget), 'aa_policy': policy})
                audit.append({'profile': profile, 'stage': str(budget), 'policy': policy,
                              'spent': state.spent, 'unused': budget-state.spent,
                              'next_rank_id': next_rank})
        full = Purchases(ranks)
        full.free_closure()
        unreachable = full.all_closure()
        result.append(build | {'aa_budget': full.spent, 'aa_rank_ids': full.ids,
                               'aa_stage': 'all', 'aa_policy': 'purchase_closure'})
        audit.append({'profile': profile, 'stage': 'all', 'spent': full.spent,
                      'purchased_ranks': len(full.ids), 'owned_abilities': len(full.owned),
                      'common_free_rank_ids': free.ids, 'unreachable': unreachable,
                      'ignored_missing_prerequisites': [
                          {'rank_id': r['rank_id'], 'prerequisite': p}
                          for r in ranks for p in r['prereqs'] if not p['ability_exists']]})
    if not result:
        raise ValueError('No Ascended input builds')
    return {'builds': result}, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--builds', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    args = parser.parse_args()
    snapshot, _ = load_snapshot(args.snapshot)
    inputs = native_inputs(json.loads(args.builds.read_text())['builds'], snapshot['tables'])
    result, audit = matrix(json.loads(args.catalog.read_text()), inputs)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    args.audit.write_text(json.dumps({'catalog_sha256': hashlib.sha256(args.catalog.read_bytes()).hexdigest(),
        'input_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
        'scope': 'Legal purchase candidates; not optimized fights. Zero spent includes common purchasable free ranks; grant-only rewards excluded.',
        'allocations': audit}, indent=2)+'\n')
    print(json.dumps({'builds': len(result['builds']), 'all_spend': {a['profile']: a['spent'] for a in audit if a['stage']=='all'}}))


if __name__ == '__main__':
    main()

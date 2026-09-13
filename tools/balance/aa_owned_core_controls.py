"""Acceptance controls for native earned ownership load/save (not lifecycle QA)."""
import copy

from aa_owned_view_controls import prepare


def cases(matrix):
    partial = prepare(matrix)
    partial['input']['aa_ownership_probe']['inspect_earned'] = True
    partial['expected_active'] = [6, 6, 3, 3, 3, 6, 6]
    partial['expected_valid'] = True
    partial['expected_earned'] = 6

    suspended = copy.deepcopy(partial)
    suspended['id'] = 'all-earned-ranks-temporarily-suspended'
    suspended['input']['aa_ownership_probe']['expansion_mask'] = 0
    suspended['expected_active'] = [6, 6, 0, 0, 0, 6, 6]

    empty = copy.deepcopy(partial)
    empty['id'] = 'empty-ownership-retains-expended-points'
    empty['stored'] = None
    empty['input']['aa_ownership_probe']['initial_spent_points'] = 5
    empty['expected_active'] = [0] * 7
    empty['expected_earned'] = 0

    # Captured full catalog: Glyph of Dragon Scales, one rank costing three
    # points, expansion 12, one charge. This tests preservation, not consumption.
    charged = copy.deepcopy(suspended)
    charged['id'] = 'charged-earned-row-suspension-round-trip'
    charged['stored'].update(aa_id=4702, aa_value=1, charges=1)
    charged['input']['aa_ownership_probe'].update(first_rank_id=4702, initial_spent_points=8)
    charged['expected_active'] = [1, 1, 0, 0, 0, 1, 1]
    charged['expected_earned'] = 1

    invalid = []
    for identity, field, value in [('invalid-earned-count', 'aa_value', 7),
                                   ('noncanonical-earned-rank', 'aa_id', 108)]:
        case = copy.deepcopy(partial)
        case['id'] = identity
        case['stored'][field] = value
        probe = case['input']['aa_ownership_probe']
        probe['operations'] = ['load', 'save']
        probe['allowed_failures'] = ['load', 'save']
        case['expected_active'] = [0, 0]
        case['expected_valid'] = False
        case['expected_earned'] = 0
        invalid.append(case)
    return [partial, suspended, empty, charged, *invalid]


def verify(case, report):
    probe = case['input']['aa_ownership_probe']
    steps = report['aa_ownership_probe']['steps']
    if [s['operation'] for s in steps] != probe['operations']:
        raise ValueError('Incomplete native core operations')
    if [s['effective_rank_count'] for s in steps] != case['expected_active']:
        raise ValueError('Incorrect usable prefix')
    row = case['stored']
    stored = [] if row is None else [{'first_rank_id': row['aa_id'],
                                     'rank_count': row['aa_value'], 'charges': row['charges']}]
    wallet = case['input']['builds'][0]['aa_budget']
    for step in steps:
        active = step['effective_rank_count']
        profile = [] if not active else [{'first_rank_id': probe['first_rank_id'],
                                         'rank_count': active, 'charges': row['charges']}]
        if step['profile'] != profile:
            raise ValueError('Client profile disagrees with native usable ranks')
        if step['stored'] != stored:
            raise ValueError('Earned database row changed')
        if step['spent_points'] != probe['initial_spent_points'] or step['unspent_points'] != wallet:
            raise ValueError('Earned/expended accounting or wallet changed')
        if step['earned_state_valid'] != case['expected_valid'] or step['success'] != case['expected_valid']:
            raise ValueError('Invalid ownership was accepted or valid ownership rejected')
        if step['earned_rank_count'] != case['expected_earned']:
            raise ValueError('Canonical earned count changed')
        if case['expected_earned'] and not step['first_rank_already_earned']:
            raise ValueError('Suspended earned rank was forgotten')
        if (case['expected_earned'] or not case['expected_valid']) and step['first_rank_purchasable']:
            raise ValueError('Earned or unresolved rank could be repurchased')
    return {'id': case['id'], 'operations': len(steps), 'passed': True}

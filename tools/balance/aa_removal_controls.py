"""Native acceptance states for explicit AA reset and charged-AA consumption."""
import copy

from aa_owned_core_controls import cases as core_cases


def cases(matrix):
    core = core_cases(matrix)
    active, suspended, charged = [copy.deepcopy(core[i]) for i in (0, 1, 3)]
    active['id'] = 'reset-earned-active-rank'
    suspended['id'] = 'reset-earned-suspended-rank'
    charged['id'] = 'consume-final-charge-once'
    operations = [
        ['load', 'reset_rank', 'save', 'load'],
        ['load', 'restrict_expansions', 'load', 'reset_rank', 'restore_expansions', 'load', 'save'],
        ['load', 'consume_charge', 'save', 'load', 'consume_charge', 'save', 'load'],
    ]
    result = [active, suspended, charged]
    for case, ops in zip(result, operations):
        case['input']['aa_ownership_probe'].update(operations=ops, inspect_lifecycle=True)
        case['expected'] = []
        removed = False
        for index, op in enumerate(ops):
            removed |= op in ('reset_rank', 'consume_charge')
            count = 0 if removed else case['expected_earned']
            usable = 0 if case is suspended and index == 2 else count
            expended = 8 if case is charged and removed else 5
            spent = expended if removed else case['input']['aa_ownership_probe']['initial_spent_points']
            case['expected'].append(state(case, usable, count, spent, expended, True, True))
    failure = copy.deepcopy(active)
    failure['id'] = 'rollback-reset-when-character-update-fails'
    failure['fail_character_update'] = True
    failure['input']['aa_ownership_probe'].update(operations=['load', 'reset_rank', 'save', 'load'],
                                                allowed_failures=['save'])
    failure['expected'] = [state(failure, 6, 6, 29, 5, valid, success)
                           for valid, success in [(True, True), (False, True), (False, False), (True, True)]]
    result.append(failure)
    for case in result:
        for key in ('expected_active', 'expected_valid', 'expected_earned'):
            del case[key]
    return result


def state(case, active, earned, spent, expended, valid, success):
    row = case['stored']
    stored = [] if not earned else [{'first_rank_id': row['aa_id'], 'rank_count': earned, 'charges': row['charges']}]
    profile = [] if not active else [{'first_rank_id': row['aa_id'], 'rank_count': active, 'charges': row['charges']}]
    return {'effective_rank_count': active, 'earned_rank_count': earned, 'stored': stored,
            'profile': profile, 'spent_points': spent, 'expended_points': expended,
            'unspent_points': 17, 'earned_state_valid': valid, 'success': success,
            'first_rank_already_earned': bool(earned),
            'active_charges': row['charges'] if active else 0,
            'saved_points': {'wallet': 17, 'spent': spent, 'expended': expended}}


def assess(case, report):
    steps = report['aa_ownership_probe']['steps']
    operations = case['input']['aa_ownership_probe']['operations']
    if [s['operation'] for s in steps] != operations:
        raise ValueError('Incomplete native AA removal operations')
    differences = []
    for index, (actual, expected) in enumerate(zip(steps, case['expected'])):
        for key, value in expected.items():
            if actual.get(key) != value:
                differences.append({'step': index, 'operation': operations[index], 'field': key,
                                    'expected': value, 'actual': actual.get(key)})
        if case['id'] == 'consume-final-charge-once' and index and not actual['first_rank_purchasable']:
            differences.append({'step': index, 'field': 'consumed_rank_not_repurchaseable'})
    return {'id': case['id'], 'passed': not differences, 'differences': differences}

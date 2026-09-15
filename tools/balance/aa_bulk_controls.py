"""Acceptance states for bulk earned-AA refunds and guarded profile saves."""
import copy

from aa_owned_view_controls import prepare
from aa_removal_controls import cases as removal_cases


def cases(matrix):
    template = prepare(matrix)
    row = template['stored']
    template['rows'] = [row, {'id': row['id'], 'aa_id': 5006, 'aa_value': 1, 'charges': 0}]
    del template['stored']
    template['input']['profile_save_fixture'] = True
    template['input']['aa_ownership_probe'].update(inspect_earned=True, inspect_lifecycle=True)
    definitions = [
        ('refund-active-and-preserve-grant', ['load', 'refund_all', 'save', 'load', 'refund_all', 'save']),
        ('refund-suspended-and-preserve-grant', ['load', 'restrict_expansions', 'load', 'refund_all', 'restore_expansions', 'load', 'save']),
        ('reset-all-preserves-grant-without-repeat-refund', ['load', 'reset_all', 'save', 'load', 'reset_all', 'save']),
        ('failed-refund-preserves-wallet-and-ownership', ['load', 'refund_all', 'save', 'load']),
        ('untrusted-profile-cannot-overwrite-committed-counters', ['load', 'simulate_committed_reset', 'invalidate_earned', 'load', 'save_character']),
        ('valid-profile-save-remains-available', ['load', 'save_character']),
        ('refund-partial-prefix-at-full-earned-cost', ['load', 'restrict_expansions', 'load', 'refund_all', 'restore_expansions', 'load', 'save']),
    ]
    result = []
    for identity, operations in definitions:
        case = copy.deepcopy(template); case['id'] = identity
        probe = case['input']['aa_ownership_probe']; probe['operations'] = operations
        partial = identity == 'refund-partial-prefix-at-full-earned-cost'
        probe['expansion_mask'] = 4 if partial else 0
        case['expected_before_pass'] = identity == 'valid-profile-save-remains-available'
        failed = identity == 'failed-refund-preserves-wallet-and-ownership'
        uncertain = identity == 'untrusted-profile-cannot-overwrite-committed-counters'
        if failed:
            case['fail_character_update'] = True; probe['allowed_failures'] = ['save', 'load']
        if uncertain:
            probe['allowed_failures'] = ['save_character', 'load']
        grant = {'first_rank_id': 5006, 'rank_count': 1, 'charges': 0}
        paid = {'first_rank_id': 107, 'rank_count': 6, 'charges': 0}
        refunded = False; restricted = False; committed = False; active = 6; valid = True
        expected = []
        for op in operations:
            success = True
            if op == 'restrict_expansions': restricted = True
            if op == 'restore_expansions': restricted = False
            if op == 'load':
                if not valid:
                    success = False
                elif refunded:
                    active = 0
                elif restricted:
                    active = 3 if partial else 0
                else:
                    active = 6
            if op in ('refund_all', 'reset_all'):
                if failed: valid = False
                else: refunded = True; active = 0
            if op == 'simulate_committed_reset': committed = True
            if op == 'invalidate_earned': valid = False
            if op in ('save', 'save_character') and not valid: success = False
            spent = 5 if refunded else 29; wallet = 41 if refunded else 17
            expected.append({'effective_rank_count': active, 'earned_rank_count': 0 if refunded else 6,
                'stored': [grant] if refunded or committed else [paid, grant],
                'profile': [grant] if not active else [{'first_rank_id': 107, 'rank_count': active, 'charges': 0}, grant],
                'spent_points': spent, 'unspent_points': wallet, 'expended_points': 5,
                'saved_points': {'wallet': wallet, 'spent': 5 if committed else spent, 'expended': 5},
                'earned_state_valid': valid, 'success': success,
                'first_rank_already_earned': not refunded})
        case['expected'] = expected
        result.append(case)
    for case in removal_cases(matrix):
        case['rows'] = [case.pop('stored')]
        if case['id'] == 'consume-final-charge-once':
            for step in case['expected'][1:]:
                step['first_rank_purchasable'] = True
        case['id'] = 'regression-' + case['id']
        case['expected_before_pass'] = True
        if case.get('fail_character_update'):
            case['input']['aa_ownership_probe']['allowed_failures'].append('load')
            case['expected'][-1].update(earned_state_valid=False, success=False)
            case['expected_before_pass'] = False
        result.append(case)
    return result


def assess(case, report):
    steps = report['aa_ownership_probe']['steps']
    operations = case['input']['aa_ownership_probe']['operations']
    if [s['operation'] for s in steps] != operations:
        raise ValueError('Incomplete bulk-AA native operations')
    differences = []
    for index, (actual, expected) in enumerate(zip(steps, case['expected'])):
        for field, value in expected.items():
            observed = actual.get(field)
            if field in ('profile', 'stored'):
                observed = sorted(observed, key=lambda r: r['first_rank_id']) if observed is not None else None
            if observed != value:
                differences.append({'step': index, 'operation': operations[index], 'field': field,
                                    'expected': value, 'actual': observed})
    return {'id': case['id'], 'passed': not differences, 'differences': differences}

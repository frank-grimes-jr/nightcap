"""Acceptance states for durable native AA purchases and grants."""
import copy
from aa_owned_view_controls import prepare
from aa_bulk_controls import assess


def cases(matrix):
    template = prepare(matrix)
    template.pop('stored')
    template['input']['profile_save_fixture'] = True
    template['input']['capture_aa_purchase_events'] = True
    result = []

    def add(identity, steps, *, first=107, initial=0, wallet=17, paid=False,
            fail=False, before=False, grant_count=2):
        case = copy.deepcopy(template)
        case['id'] = identity
        case['expected_before_pass'] = before
        case['fail_character_update'] = fail
        case['initial_wallet'] = wallet
        case['input']['builds'][0]['aa_budget'] = wallet
        charges = 1 if first == 4702 else 0
        cost = {107: [0, 2, 6, 12, 14, 18, 24], 4702: [0, 3], 5006: [0, 0]}[first]
        case['rows'] = [] if not initial else [{'id': case['input']['builds'][0]['test_character_id'],
            'aa_id': first, 'aa_value': initial, 'charges': charges}]
        probe = case['input']['aa_ownership_probe']
        probe.update(first_rank_id=first, initial_spent_points=5+cost[initial], initial_expended_points=5,
                     expansion_mask=0, inspect_earned=True, inspect_lifecycle=True, inspect_purchase_events=True,
                     purchase_rank_count=2 if first == 107 else 1, grant_rank_count=grant_count,
                     ignore_cost=not paid, operations=[s[0] for s in steps],
                     allowed_failures=sorted({s[0] for s in steps if not s[5]}))
        case['expected'] = []
        for op, count, balance, expended, valid, success, *active_override in steps:
            active = active_override[0] if active_override else count
            def rows(n):
                return [] if not n else [{'first_rank_id': first, 'rank_count': n, 'charges': charges}]
            spent = expended+cost[count]
            case['expected'].append({'effective_rank_count': active, 'earned_rank_count': count,
                'profile': rows(active), 'stored': rows(count), 'unspent_points': balance,
                'spent_points': spent, 'expended_points': expended, 'earned_state_valid': valid,
                'success': success, 'active_charges': charges if active else 0,
                'saved_points': {'wallet': balance, 'spent': spent, 'expended': expended}})
        result.append(case)

    add('paid-ranks-save-wallet-before-reload', [
        ('load',0,17,5,True,True), ('purchase_first',1,15,5,True,True),
        ('purchase_next',2,11,5,True,True), ('purchase_next',2,11,5,True,True), ('load',2,11,5,True,True)])
    add('silent-grant-is-durable-without-later-save', [
        ('load',0,17,5,True,True), ('grant_silent',2,17,5,True,True), ('load',2,17,5,True,True)])
    for paid in (True,False):
        balance = 11 if paid else 17
        add('multi-rank-'+('paid' if paid else 'free')+'-grant', [
            ('load',0,17,5,True,True), ('grant',2,balance,5,True,True), ('load',2,balance,5,True,True),
            ('grant',2,balance,5,True,False)], paid=paid)
    for op in ('purchase_first','grant','grant_silent'):
        add('rollback-'+op+'-on-character-update-failure', [
            ('load',0,17,5,True,True), (op,0,17,5,False,op!='grant'),
            ('save',0,17,5,False,False), ('load',0,17,5,False,False)], fail=True)
    add('insufficient-wallet-remains-rejected', [
        ('load',0,1,5,True,True), ('purchase_first',0,1,5,True,True)], wallet=1, before=True)
    add('suspended-earned-rank-cannot-be-repurchased', [
        ('load',6,17,5,True,True), ('restrict_expansions',6,17,5,True,True),
        ('load',6,17,5,True,True,0), ('purchase_first',6,17,5,True,True,0),
        ('restore_expansions',6,17,5,True,True,0), ('load',6,17,5,True,True)], initial=6,before=True)
    add('charged-purchase-consume-and-repurchase', [
        ('load',0,17,5,True,True), ('purchase_first',1,14,5,True,True),
        ('purchase_first',1,14,5,True,True), ('consume_charge',0,14,8,True,True),
        ('purchase_first',1,11,8,True,True), ('load',1,11,8,True,True)], first=4702)
    add('grant-only-purchase-rejected-explicit-grant-retained', [
        ('load',0,17,5,True,True), ('purchase_first',0,17,5,True,True),
        ('grant',1,17,5,True,True), ('load',1,17,5,True,True)], first=5006,grant_count=1)
    add('invalid-session-cannot-receive-silent-grant', [
        ('load',0,17,5,True,True), ('invalidate_earned',0,17,5,False,True),
        ('grant_silent',0,17,5,False,True), ('save',0,17,5,False,False)])
    add('paid-rank-cannot-skip-predecessor', [
        ('load',0,17,5,True,True), ('purchase_next',0,17,5,True,True)], before=True)
    def event(rank, cost):
        previous, following = {107: (-1,108), 108: (107,109), 4702: (-1,-1), 5006: (-1,-1)}[rank]
        return {'aa_id': rank, 'aa_cost': cost, 'aa_previous_id': previous, 'aa_next_id': following}
    paid = [event(107,2), event(108,4)]
    free = [event(107,0), event(108,0)]
    glyph = event(4702,3)
    ledgers = {
        'paid-ranks-save-wallet-before-reload': [[],paid[:1],paid,paid,paid],
        'silent-grant-is-durable-without-later-save': [[],[event(108,0)],[event(108,0)]],
        'multi-rank-paid-grant': [[],paid,paid,paid],
        'multi-rank-free-grant': [[],free,free,free],
        'charged-purchase-consume-and-repurchase': [[],[glyph],[glyph],[glyph],[glyph,glyph],[glyph,glyph]],
        'grant-only-purchase-rejected-explicit-grant-retained': [[],[],[event(5006,0)],[event(5006,0)]],
    }
    for case in result:
        expected_events = ledgers.get(case['id'], [[] for _ in case['expected']])
        assert len(expected_events) == len(case['expected'])
        for step, events in zip(case['expected'], expected_events):
            step['purchase_events'] = copy.deepcopy(events)
    return result

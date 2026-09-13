"""Plan effective AA rows while retaining earned ownership across rank caps.

Offline transition model only: no refunds, wallet writes, database installer or
automatic handling of resets, class releases and expendable-AA consumption.
"""
import copy
from collections import defaultdict
import hashlib
import json

from aa_policy_preflight import build_preflight, integer, unique


def keyed(rows):
    for row in rows:
        if set(row) != {'id', 'aa_id', 'aa_value', 'charges'}:
            raise ValueError('Unexpected owned-AA fields')
        for key in ('id', 'aa_id', 'aa_value'):
            integer(row[key], 1)
        integer(row['charges'])
    return unique(rows, lambda r: (r['id'], r['aa_id']), 'owned AA')


def materialize(source, caps, earned):
    data = dict(source, purchases=earned)
    spec = {'free_caps': {}, 'policies': [{'id': 'materialize', 'caps': caps}]}
    policy = build_preflight(data, spec)['policies'][0]
    if not policy['prerequisites_closed']:
        raise ValueError('Ownership policy has prerequisite gaps')
    original = keyed(earned)
    abilities = {a['id']: a for a in source['abilities']}
    ranks = {r['id']: r for r in source['ranks']}
    active, suspended, totals = [], [], defaultdict(lambda: [0, 0])
    for impact in policy['purchase_impact']:
        if impact['status'] == 'unresolved':
            raise ValueError('Unresolved owned AA: ' + impact['reason'])
        key = (impact['character_id'], impact['saved_first_rank_id'])
        row, count = original[key], impact['candidate_rank_count']
        ability = abilities[impact['ability_id']]
        if count != row['aa_value'] and (row['charges'] or ability.get('charges', 0)):
            raise ValueError('Charged AA needs explicit consumption/reconciliation handling')
        full_cost, current = 0, ability['first_rank_id']
        for _ in range(row['aa_value']):
            full_cost += ranks[current]['cost']
            current = ranks[current]['next_id']
        removed = impact['nominal_removed_rank_cost']
        totals[row['id']][0] += full_cost - removed
        totals[row['id']][1] += removed
        if count:
            active.append(dict(row, aa_value=count))
        if count != row['aa_value']:
            suspended.append({'id': row['id'], 'aa_id': row['aa_id'],
                              'earned_rank_count': row['aa_value'], 'active_rank_count': count,
                              'nominal_suspended_cost': removed})
    points = [{'character_id': cid, 'active_nominal_cost': a, 'suspended_nominal_cost': s,
               'earned_nominal_cost': a + s} for cid, (a, s) in sorted(totals.items())]
    return active, suspended, points


def transition(source, specification, policy_id, current_rows, previous=None):
    source_hash = hashlib.sha256(json.dumps(
        {k: source[k] for k in ('abilities', 'ranks', 'prerequisites')},
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    current = keyed(current_rows)
    policies = build_preflight(dict(source, purchases=current_rows), specification)['policies']
    matches = [p for p in policies if p['id'] == policy_id]
    if len(matches) != 1:
        raise ValueError('Unknown ownership policy')
    policy = matches[0]
    if any(r['status'] == 'unresolved' for r in policy['purchase_impact']):
        raise ValueError('Unresolved current owned AA')
    earned = copy.deepcopy(current)
    if previous is not None:
        if previous['ledger_format'] != 1 or previous['source_sha256'] != source_hash:
            raise ValueError('Ownership source changed; explicit ledger rebase required')
        earned = copy.deepcopy(keyed(previous['earned_rows']))
        expected, suspended, points = materialize(source, previous['caps'], previous['earned_rows'])
        if expected != previous['active_rows'] or suspended != previous['suspended'] or points != previous['point_totals']:
            raise ValueError('Previous ledger does not match its earned rows and caps')
        old_active = keyed(expected)
        for key, old in old_active.items():
            if key not in current or current[key]['aa_value'] < old['aa_value']:
                raise ValueError('Active AA decreased or disappeared; explicit refund/reset/class-release handling required')
            if current[key]['charges'] != old['charges']:
                raise ValueError('Charged AA state changed; explicit consumption handling required')
        identities = {r['saved_first_rank_id']: r['ability_id'] for r in policy['purchase_impact']}
        for key, row in current.items():
            if row['aa_value'] > previous['caps'].get(str(identities[row['aa_id']]), 0):
                raise ValueError('New active AA exceeds previous caps')
            if key not in earned:
                earned[key] = copy.deepcopy(row)
            elif row['aa_value'] > earned[key]['aa_value']:
                earned[key] = copy.deepcopy(row)
    earned_rows = [row for key, row in sorted(earned.items())]
    active, suspended, points = materialize(source, policy['caps'], earned_rows)
    return {'ledger_format': 1, 'source_sha256': source_hash, 'policy': policy_id,
            'caps': policy['caps'], 'earned_rows': earned_rows, 'active_rows': active,
            'suspended': suspended, 'point_totals': points,
            'scope': 'Offline ownership transition; preserve earned ranks and nominal spent totals. '
                     'No wallet/refund mutation. Runtime must include suspended cost alongside active '
                     'cost and existing expended-AA accounting. Class changes, resets and charged '
                     'consumption require explicit lifecycle integration before deployment.'}

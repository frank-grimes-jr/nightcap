"""Run native load/save ownership fixtures in the isolated database only."""
import argparse
import copy
import json
from uuid import uuid4

from aa_policy_preflight import read_json
from aa_policy_projection import project, transaction_sql, DATABASE
from run_aa_projection import DOCS, SERVER, RUNTIME, command, digest, dump_tables, native, snapshot, sql, write


def cases(matrix):
    template = next(c['input']['builds'][0] for c in matrix['cases']
                    if c['input']['builds'][0]['profile'] == 'war-clr-wiz')
    build = copy.deepcopy(template)
    build.update(aa_rank_ids=[], aa_budget=17, aa_stage='0', aa_policy='ownership_fixture')
    result = []
    for identity, policy, count, operations in (
            ('valid_saved', None, 2, ['load', 'save', 'load']),
            ('invalid_saved_count', None, 7, ['load', 'save', 'load']),
            ('removed_before_reload', None, 2, ['load', 'erase_saved', 'load']),
            ('above_projected_cap', 'launch_core', 6, ['load', 'save', 'load']),
            ('materialized_cap', 'launch_core', 3, ['load', 'save', 'load'])):
        result.append({'id': identity, 'policy': policy,
                       'stored': {'id': build['test_character_id'], 'aa_id': 107, 'aa_value': count, 'charges': 0},
                       'input': {'builds': [copy.deepcopy(build)], 'aa_ownership_probe': {
                           'first_rank_id': 107, 'operations': operations}}})
    return result


def verify(evidence, expected_cases):
    if not evidence.get('restored_exactly') or len(evidence['cases']) != len(expected_cases):
        raise ValueError('Incomplete ownership evidence or fixture restoration')
    wanted_counts = {'valid_saved': [2, 2, 2], 'invalid_saved_count': [0, 0, 0],
                     'removed_before_reload': [2, 2, 0], 'above_projected_cap': [0, 0, 0],
                     'materialized_cap': [3, 3, 3]}
    for run, case in zip(evidence['cases'], expected_cases):
        if run['id'] != case['id']:
            raise ValueError('Ownership case identity differs')
        steps = run['report']['aa_ownership_probe']['steps']
        operations = case['input']['aa_ownership_probe']['operations']
        if [s['operation'] for s in steps] != operations:
            raise ValueError('Ownership operations differ')
        stored = [{'first_rank_id': 107, 'rank_count': case['stored']['aa_value'], 'charges': 0}]
        for step, count in zip(steps, wanted_counts[case['id']]):
            if step['operation'] == 'erase_saved':
                stored = []
            profile = [{'first_rank_id': 107, 'rank_count': count, 'charges': 0}] if count else []
            if step['effective_rank_count'] != count or step['profile'] != profile:
                raise ValueError('Profile and native ownership disagree: ' + case['id'])
            if step['stored'] != stored or step['unspent_points'] != 17:
                raise ValueError('Stored ownership or wallet changed unexpectedly')
    return {'cases': len(expected_cases), 'profile_consistency': True,
            'invalid_rows_preserved_for_reconciliation': True, 'unspent_wallet_unchanged': True}


def run(stem, manifest_name):
    if stem not in ('aa-ownership-before', 'aa-ownership-after'):
        raise ValueError('Only the two owned-AA evidence destinations are allowed')
    output = DOCS / (stem + '.json.gz')
    if output.exists():
        raise ValueError('Existing evidence must not be overwritten')
    binary = command(['docker', 'exec', SERVER, 'sha256sum', RUNTIME + '/balance-zone'], text=True).split()[0]
    if binary != read_json(DOCS / manifest_name)['binary_sha256']:
        raise ValueError('Ownership binary provenance differs')
    if sql('SELECT (SELECT COUNT(*) FROM account)+(SELECT COUNT(*) FROM character_data)+(SELECT COUNT(*) FROM character_alternate_abilities);').strip() != '0':
        raise ValueError('Ownership fixture is not empty')
    original = snapshot()
    original_dump = dump_tables()
    reference = read_json(DOCS / 'aa-projection-native.json.gz')['before_tables_sha256']
    if digest(original_dump) != reference:
        raise ValueError('Original AA tables changed')
    inputs = cases(read_json(DOCS / 'gear-source-inputs.json'))
    write(DOCS / (stem + '-inputs.json'), inputs)
    evidence = {'binary_sha256': binary, 'cases': [], 'original_tables_sha256': reference}
    for case in inputs:
        plan = project(original, read_json(DOCS / 'aa-release-candidates.json'), case['policy']) if case['policy'] else None
        suffix = uuid4().hex[:12]
        if plan:
            sql(transaction_sql(plan, DATABASE, 'aa_owned_apply_' + suffix))
        row = case['stored']
        try:
            sql(f"INSERT INTO character_alternate_abilities (id,aa_id,aa_value,charges) VALUES ({row['id']},{row['aa_id']},{row['aa_value']},0);")
            result = native(case['input'])
            evidence['cases'].append({'id': case['id'], **result})
            print(case['id'], [(s['operation'], s['effective_rank_count'], len(s['profile']))
                              for s in result['report']['aa_ownership_probe']['steps']], flush=True)
        finally:
            actual = snapshot()['purchases']
            if actual not in ([], [row]):
                raise RuntimeError('Unexpected fixture ownership; refusing unbounded cleanup')
            if actual:
                sql(f"DELETE FROM character_alternate_abilities WHERE id={row['id']} AND aa_id={row['aa_id']} AND aa_value={row['aa_value']} AND charges=0;")
            if plan:
                sql(transaction_sql(plan, DATABASE, 'aa_owned_restore_' + suffix, True))
            if snapshot() != original or dump_tables() != original_dump:
                raise RuntimeError('Owned-AA fixture did not restore exactly')
            write(output, evidence)
    evidence['restored_exactly'] = True
    write(output, evidence)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stem', required=True)
    parser.add_argument('--manifest', required=True)
    args = parser.parse_args()
    run(args.stem, args.manifest)

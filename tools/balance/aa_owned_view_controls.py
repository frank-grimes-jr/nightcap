"""Native earned-AA/usable-prefix control against the unmodified full catalog."""
import copy


def prepare(matrix):
    build = copy.deepcopy(next(c['input']['builds'][0] for c in matrix['cases']
                               if c['input']['builds'][0]['profile'] == 'war-clr-wiz'))
    build.update(aa_rank_ids=[], aa_budget=17, aa_stage='0', aa_policy='earned_view_probe')
    return {
        'id': 'six-earned-ranks-three-usable-ranks-round-trip',
        'stored': {'id': build['test_character_id'], 'aa_id': 107, 'aa_value': 6, 'charges': 0},
        'input': {'builds': [build], 'aa_ownership_probe': {
            'first_rank_id': 107, 'initial_spent_points': 29, 'initial_expended_points': 5,
            'expansion_mask': 1 << (3 - 1),
            'operations': ['load', 'restrict_expansions', 'load', 'save',
                           'restore_expansions', 'load', 'save'],
        }},
    }


def assess(case, report):
    steps = report['aa_ownership_probe']['steps']
    expected_operations = case['input']['aa_ownership_probe']['operations']
    if len(steps) != 7 or [s['operation'] for s in steps] != expected_operations:
        raise ValueError('Incomplete native ownership round trip')
    stored = [{'first_rank_id': 107, 'rank_count': 6, 'charges': 0}]
    return {
        'usable_prefix_preserved': [s['effective_rank_count'] for s in steps] == [6, 6, 3, 3, 3, 6, 6],
        'earned_rows_preserved': all(s['stored'] == stored for s in steps),
        'earned_plus_expended_points_preserved': all(s['spent_points'] == 29 for s in steps),
        'wallet_unchanged': all(s['unspent_points'] == 17 for s in steps),
    }

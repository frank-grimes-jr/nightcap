"""Compare legal owner shielding choices with unchanged pets and combat policy."""
import copy

from release_pool_controls import verify as verify_pool


def prepare(original, binary):
    matrix = copy.deepcopy(original)
    matrix['binary_sha256'] = binary
    selected = {a['key'] for a in original['allocations'] if a['profile'] == 'mag-nec-shm'
                and (a['spent'] == 0 or any(s['requested'] == 'all' for s in a['aliases']))}
    cases = []
    for add_magic in (False, True):
        for original_case in original['cases']:
            if original_case['allocation_key'] not in selected:
                continue
            case = copy.deepcopy(original_case)
            case['paired_gear_case_id'] = case['id']
            case['shield_variant'] = 'arch_magic' if add_magic else 'arch'
            case['id'] += '-' + case['shield_variant']
            actions = case['input']['pet_probe']['actions']
            owners = [a for a in actions if a['spell'] == 168 and not a.get('target_class')]
            if len(owners) != 1 or any(a['spell'] in (67, 64) for a in actions):
                raise ValueError('Unexpected original shielding preparation')
            owners[0]['spell'] = 67
            if add_magic:
                lich = next(i for i, a in enumerate(actions) if a['spell'] == 644)
                actions[lich:lich] = [{'spell': 64}] + [{'spell': 64, 'target_class': c} for c in (13, 11, 10)]
            cases.append(case)
    if len(cases) != 36 or len({c['id'] for c in cases}) != 36:
        raise ValueError('Expected two shielding variants across 18 matched pet cases')
    matrix['cases'] = cases
    matrix['scope'] = 'Arch Shielding replaces owner Talisman; optional Resist Magic on owner and all pets. Fixed source gear, legal AA purchases, pet buffs, caps and combat policy.'
    return matrix


def verify(matrix, evidence, original, catalog):
    if matrix != prepare(original, matrix['binary_sha256']):
        raise ValueError('Shielding comparison changed unrelated inputs')
    rows = verify_pool(matrix, evidence, catalog)
    cases = {c['id']: c for c in matrix['cases']}
    for run in evidence['runs']:
        state = run['report']['pet_probe']['final']
        owner_buffs = {b['spell'] for b in state['player']['buffs']}
        if 67 not in owner_buffs or 168 in owner_buffs:
            raise ValueError('Owner did not retain the chosen shielding buff')
        if cases[run['id']]['shield_variant'] == 'arch_magic':
            if 64 not in owner_buffs or any(64 not in {b['spell'] for b in p['buffs']} for p in state['pets']):
                raise ValueError('Resist Magic missing after preparation')
    return rows

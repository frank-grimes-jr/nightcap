"""Native self-buff preparation before matched candidate boss encounters."""
import argparse
import copy
import gzip
import json
from pathlib import Path

from active_aa_controls import run, verify_encounters


def prepare(source):
    cases = []
    for original in source['cases']:
        build = original['input']['builds'][0]
        if (original['input']['encounter']['active_aa_policy'] != 'burst'
                or build['aa_policy'] == 'durability_first'):
            continue
        case = copy.deepcopy(original)
        case['id'] += '-prepared'
        # Ordinary CLR/WIZ preparation; no borrowed ENC-only clarity assumption.
        resistance = 60 if case['input']['encounter']['npc_id'] == 32040 else 61
        case['input']['encounter']['preparation'] = {
            'spell_ids': [67, 314, 488, 64, resistance],
            'recover': True, 'max_duration_ms': 900000}
        cases.append(case)
    if len(cases) != 30:
        raise ValueError('Expected both bosses, five AA stages and three seeds')
    return {'scope': 'Native CLR/WIZ self-buffs and sitting recovery before candidate WAR/CLR/WIZ fights; same purchased AAs and gear, not certified full BiS.',
            'cases': cases}


def verify_preparation(case, report):
    wanted = case['input']['encounter'].get('preparation')
    observed = report['encounter'].get('preparation')
    if wanted is None or observed is None:
        if wanted != observed:
            raise ValueError('Requested preparation was omitted or unexpectedly added')
        return
    if observed['input'] != wanted:
        raise ValueError('Preparation policy changed')
    build = report['builds'][0]
    trace, actions = observed['trace'], observed['actions']
    final = observed['final_state']
    start = report['encounter']['combat_start_ms']
    if (trace[0]['ms'] != 0 or trace[0]['hp'] != build['hp'] or trace[0]['mana'] != build['mana']
            or trace[0]['buffs'] or start != observed['elapsed_ms'] or trace[-1]['ms'] != start
            or not 0 < start <= wanted['max_duration_ms']
            or any(a['ms'] >= b['ms'] for a, b in zip(trace, trace[1:]))):
        raise ValueError('Invalid preparation origin, resources or continuous clock')
    if {k: v for k, v in trace[-1].items() if k != 'ms'} != final:
        raise ValueError('Preparation final state is not the last observed native state')
    accepted = [a for a in actions if a['accepted']]
    if [a['spell'] for a in accepted] != wanted['spell_ids']:
        raise ValueError('Preparation did not cast every requested spell in order')
    for a in actions:
        if a['spell'] not in wanted['spell_ids'] or not 0 < a['ms'] <= start:
            raise ValueError('Invalid preparation action identity/time')
        if a['accepted'] and (not a['ms'] <= a['completed_ms'] < start
                              or a['completed_state']['casting']):
            raise ValueError('Preparation cast never completed before engagement')
    present = {b['spell'] for b in final['buffs']}
    if not set(wanted['spell_ids']) <= present:
        raise ValueError('A requested preparation buff did not survive native stacking/recovery')
    if actions and not any(s['mana'] < trace[0]['mana'] for s in trace):
        raise ValueError('Preparation mana cost was never observed')
    if wanted['recover'] and actions and not any(s['sitting'] for s in trace):
        raise ValueError('Sitting recovery never reached the native client sitting state')
    if final['casting'] or final['sitting']:
        raise ValueError('Character did not finish preparation standing and ready')
    if wanted['recover'] and (final['hp'] != final['max_hp'] or final['mana'] != final['max_mana']):
        raise ValueError('Full native recovery was requested but not observed')
    first = report['encounter']['trace'][0]
    if first['player_hp'] != final['hp'] or first['player_mana'] != final['mana']:
        raise ValueError('Resources were changed between preparation and engagement')
    if 'aa_state' in first and any(first['aa_state'][k] != final[k]
                                  for k in ('hp', 'max_hp', 'mana', 'casting', 'buffs')):
        raise ValueError('Buff or resource state was changed at engagement')


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
        print(f'Verified {len(result)} prepared native encounters')


if __name__ == '__main__':
    main()

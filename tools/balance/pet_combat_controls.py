"""Reproduce pet command defects and exercise native pet-only boss combat."""
import argparse
import copy
import gzip
import json
from pathlib import Path

from pet_controls import run, summarize as summarize_preparation


def prepare(pets, boss_positions, binary_sha256):
    originals = {c['id']: c for c in pets['cases']}
    cases = []
    for command in (2, 3):
        for distance, extra_only in ((80, False), (500, False), (80, True)):
            case = copy.deepcopy(originals['triple-0'])
            case['id'] = f'command-{command}-{distance}-extraonly-{extra_only}'
            probe = case['input']['pet_probe']
            if extra_only:
                probe['actions'] = [{'spell': 443}, {'spell': 166}]
                case['expected_spells'] = [443, 166]
            probe['combat'] = {'npc_id': 32040, 'npc_position': boss_positions[32040],
                               'starting_distance': distance, 'duration_ms': 500, 'commands_only': True,
                               'commands': [{'ms': ms, 'command': command} for ms in (0, 100, 200, 300)]}
            cases.append(case)
        case = copy.deepcopy(originals['triple-0'])
        case['id'] = f'command-{command}-80-primaryonly'
        case['expected_spells'] = [633]
        probe = case['input']['pet_probe']
        probe['actions'] = [{'spell': 633}, {'spell': 107, 'target_class': 13}]
        probe['combat'] = {'npc_id': 32040, 'npc_position': boss_positions[32040],
                           'starting_distance': 80, 'duration_ms': 500, 'commands_only': True,
                           'commands': [{'ms': ms, 'command': command} for ms in (0, 100, 200, 300)]}
        cases.append(case)
    for stage in ('0', 'all'):
        for boss in (32040, 73057):
            case = copy.deepcopy(originals['triple-'+stage])
            case['id'] = f'pet-only-{stage}-{boss}'
            case['input']['pet_probe']['combat'] = {
                'npc_id': boss, 'npc_position': boss_positions[boss], 'starting_distance': 80,
                'duration_ms': 120000, 'commands_only': False, 'commands': [{'ms': 0, 'command': 2}]}
            cases.append(case)
    return {'scope': 'Native attack-order boundaries and pet-only boss controls; owner combat rotation not implemented.',
            'binary_sha256': binary_sha256, 'cases': cases}


def assess_commands(combat):
    if not combat['input']['commands_only']:
        raise ValueError('Instant command checks require paused NPC AI')
    damage = [c['before']['boss_hp'] - c['after']['boss_hp'] for c in combat['commands']]
    ordered = [[p['id'] for p in c['after']['pets'] if p['present'] and p['hate'] > 0]
               for c in combat['commands']]
    wanted = combat['pet_ids'] if combat['input']['starting_distance'] == 80 else []
    return {'passed': all(d == 0 for d in damage) and all(ids == wanted for ids in ordered),
            'immediate_damage': damage, 'ordered_pet_ids': ordered, 'expected_ordered_pet_ids': wanted}


def summarize(case, report):
    preparation = summarize_preparation(case, report)
    if not preparation['assessment']['ready']:
        raise ValueError('Pet combat requires a correct prepared pet roster')
    combat = report['pet_probe']['combat']
    if combat['input'] != case['input']['pet_probe']['combat']:
        raise ValueError('Pet combat input differs')
    if len(combat['commands']) != len(combat['input']['commands']):
        raise ValueError('Pet command schedule incomplete')
    if [c['input'] for c in combat['commands']] != combat['input']['commands']:
        raise ValueError('Native pet command requests differ from schedule')
    initial_ids = [p['entity_id'] for p in report['pet_probe']['final']['pets']]
    if combat['pet_ids'] != initial_ids or combat['trace'][0]['boss_hp'] != 32000:
        raise ValueError('Pet combat actors or initial target HP differ')
    base = {'id': case['id'], 'aa_spent': preparation['aa_spent'], 'result': combat['result'],
            'final_boss_hp': combat['trace'][-1]['boss_hp']}
    if combat['input']['commands_only']:
        return base | {'command_boundary': assess_commands(combat)}
    events = combat['events']
    pets = set(combat['pet_ids'])
    player = combat['player_id']
    boss = combat['boss_id']
    pet_damage = sum(e['damage'] for e in events if e['type'] == 'damage'
                     and e['source'] in pets and e['target'] == boss and e['damage'] > 0)
    owner_damage = sum(e['damage'] for e in events if e['type'] == 'damage'
                       and e['source'] == player and e['target'] == boss and e['damage'] > 0)
    result = base | {'elapsed_ms': combat['trace'][-1]['ms'], 'pet_damage': pet_damage,
                   'owner_damage': owner_damage,
                   'surviving_pet_ids': [p['id'] for p in combat['trace'][-1]['pets'] if p['present'] and p['hp'] > 0],
                   'scope': 'Pet-only control; no owner spell/heal rotation and no balance certification'}
    if 'damage_ledger' in combat:
        # Root calls already include any nested damage, so count their HP changes once.
        loss = sum(max(0, e['hp_before'])-max(0, e['hp_after']) for e in combat['damage_ledger'] if e['depth'] == 0)
        if loss < 32000-max(0, combat['trace'][-1]['boss_hp']):
            raise ValueError('Native damage ledger does not account for boss HP loss')
        result['native_boss_hp_loss'] = loss
        result['packet_damage_scope'] = 'Observed packets can omit distant actors; native_boss_hp_loss includes all root damage calls.'
    return result


def verify(matrix, evidence):
    cases = {c['id']: c for c in matrix['cases']}
    runs = {r['id']: r for r in evidence['runs']}
    if cases.keys() != runs.keys() or len(runs) != len(evidence['runs']) or len(cases) != len(matrix['cases']):
        raise ValueError('Incomplete or duplicate pet combat evidence')
    for identity, case in cases.items():
        if summarize(case, runs[identity]['report']) != runs[identity]['summary']:
            raise ValueError('Pet combat summary differs from native evidence')
    return [r['summary'] for r in evidence['runs']]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    matrix = json.loads(args.inputs.read_text(encoding='utf-8'))
    if args.run:
        run(matrix, args.output, summarize)
    else:
        results = verify(matrix, json.loads(gzip.decompress(args.verify.read_bytes())))
        args.output.write_bytes((json.dumps({'cases': results}, indent=2)+'\n').encode())
        print(f'Verified {len(results)} pet command/combat records')

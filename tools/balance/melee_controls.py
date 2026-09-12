"""Native WAR/CLR/MNK autoattack, combat-button and self-heal comparisons."""
import argparse
import copy
import gzip
import json
from collections import Counter
from pathlib import Path

from active_aa_controls import run, verify_encounter
from augment_controls import verify_equipment
from verify_native_movement import verify as verify_movement


def prepare(gear, aa, previous, binary):
    legacy = [c for c in previous['cases'] if c['input']['builds'][0]['aa_stage'] == '0']
    if len(legacy) != 6:
        raise ValueError('Expected six zero-spend caster controls')
    cases = copy.deepcopy(legacy)
    templates = {b['aa_stage']: b for b in aa['builds'] if b['profile'] == 'war-clr-mnk'
                 and b['aa_policy'] != 'durability_first'}
    for mode in ('shield', 'dual', 'two_hand'):
        inventory = next(b['equipment'] for b in gear['builds'] if b['profile'] == 'war-clr-mnk'
                         and b['tier'] == f'captured_drops/melee/{mode}/unforced')
        for stage in (('0', '100', '200', '500', 'all') if mode == 'shield' else ('0',)):
            for enabled in ((True, False) if mode == 'shield' and stage in ('0', '500') else (True,)):
                for original in legacy:
                    case = copy.deepcopy(original)
                    build = copy.deepcopy(templates[stage])
                    build['equipment'] = copy.deepcopy(inventory)
                    build['tier'] = f'monk/{mode}/{stage}/specials-{enabled}'
                    build['gear_control'] = 'monk_'+mode
                    for key in ('total_score', 'raw_item_totals', 'capped_spell_damage', 'capped_heal_amount', 'spell_probes'):
                        build.pop(key, None)
                    case['input']['builds'] = [build]
                    case['input']['export_equipment'] = True
                    case['input']['encounter']['combat_policy'] = 'melee_heal'
                    case['input']['encounter']['melee_specials'] = enabled
                    case['id'] = f'{build["tier"]}/{case["input"]["encounter"]["npc_id"]}/{case["seed"]}'
                    cases.append(case)
    if len(cases) != 60 or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Wrong or duplicate melee matrix cases')
    return {'scope': 'WAR/CLR/MNK native autoattack and combat buttons, Superior Healing, prepared candidate drop gear; class/client mastery and full BiS remain unproven.',
            'binary_sha256': binary, 'cases': cases}


def verify_case(case, report):
    summary = verify_encounter(case, report)
    expected = case['input']['encounter']
    if expected.get('combat_policy') != 'melee_heal':
        return summary
    encounter = report['encounter']
    verify_equipment(case['input'], report)
    if encounter['combat_policy'] != 'melee_heal':
        raise ValueError('Wrong native combat policy')
    if encounter['monk_actions']['enabled'] != expected['melee_specials']:
        raise ValueError('Wrong monk button policy')
    if any(a['spell'] != 9 for a in encounter['attempts']):
        raise ValueError('Melee controller cast an offensive or unsupported spell')
    actions = encounter['monk_actions']['requests']
    if not expected['melee_specials'] and actions:
        raise ValueError('Disabled monk skills were requested')
    player, npc = encounter['player_entity_id'], encounter['npc_entity_id']
    if expected['melee_specials'] and {a['skill'] for a in actions} != {26, 52}:
        raise ValueError('Missing Flying Kick or Tiger Claw request')
    last = {}
    for action in actions:
        skill = action['skill']
        if (action['target'] != npc or action['timer_before'] != 0 or action['skill_value'] <= 0
                or action['timer_id'] != {26: 25, 52: 26}[skill]
                or not 0 < action['ms'] <= encounter['elapsed_ms']):
            raise ValueError('Invalid native combat-button request')
        if skill in last:
            before = last[skill]
            if action['ms'] - before['ms'] < 250:
                raise ValueError('Combat button requested faster than declared input policy')
            # Persistent timers use whole seconds. Compare native second buckets.
            start = encounter.get('combat_start_ms', 0)
            if ((start+action['ms'])//1000 < (start+before['ms'])//1000 + before['timer_after']):
                raise ValueError('Combat button requested before native cooldown elapsed')
        last[skill] = action
    damage = Counter()
    for event in encounter['events']:
        if event['type'] == 'damage' and event['source'] == player and event['target'] == npc and event['spell'] == 65535:
            if event['damage'] > 0:
                damage[event['damage_type']] += event['damage']
    # Native wire type30 includes kicks and type23 includes claw/strike skills;
    # Master Wu can add other monk strikes. Do not label every packet an exact skill.
    if expected['melee_specials'] and not damage[30] + damage[23]:
        raise ValueError('Monk requests never produced native kick/claw damage')
    if case['input']['builds'][0]['aa_stage'] == '0' and not sum(damage[t] for t in (0, 1, 4, 36)):
        raise ValueError('Zero-spend melee fight produced no normal weapon damage')
    return summary | {'combat_policy': 'melee_heal', 'specials': expected['melee_specials'],
                      'button_requests': len(actions), 'cooldown_starts': sum(a['timer_after'] > 0 for a in actions),
                      'player_physical_damage_by_wire_type': dict(damage)}


def verify_weapons(report):
    expected = {'war-clr-wiz': {662035: 16, 631822: 42},
                'war-clr-mnk': {662038: 26, 662035: 16, 631822: 42}, 'mag-nec-shm': {}}
    if {b['profile'] for b in report['builds']} != expected.keys() or len(report['builds']) != 3:
        raise ValueError('Missing or duplicate weapon-control profiles')
    checks = []
    for build in report['builds']:
        rows = build['weapon_checks']
        if len(rows) != 5 or {r['id'] for r in rows} != {662038, 662035, 631822, 24587, 5100}:
            raise ValueError('Missing or duplicate weapon controls')
        for row in rows:
            damage = expected[build['profile']].get(row['id'], 0)
            if row['native_weapon_damage'] != damage:
                raise ValueError('Held-class weapon damage or legality restriction differs from expected native result')
            if build['profile'] == 'war-clr-mnk' and row['id'] == 662038 and (
                    row['base_class_equipable'] or not row['held_class_equipable'] or not row['race_equipable']):
                raise ValueError('Monk-only weapon did not exercise the secondary/tertiary class gate')
            checks.append({'profile': build['profile'], 'item': row['id'], 'native_damage': damage})
    return checks


def verify(matrix, evidence, previous):
    cases = {c['id']: c for c in matrix['cases']}
    if len(cases) != len(matrix['cases']) or len(evidence['runs']) != len(cases) or {r['id'] for r in evidence['runs']} != cases.keys():
        raise ValueError('Incomplete or duplicate melee evidence')
    old = {r['id']: r for r in previous['runs']}
    summaries, movement, unchanged = [], [], []
    for row in evidence['runs']:
        case = cases[row['id']]
        summary = verify_case(case, row['report'])
        if json.loads(json.dumps(summary)) != row['summary']:
            raise ValueError('Stored melee summary differs from native report')
        summaries.append(summary)
        movement.append({'id': row['id'], **verify_movement(row['report'])})
        if case['input']['encounter'].get('combat_policy') != 'melee_heal':
            if row['native_raw_sha256'] != old[row['id']]['native_raw_sha256']:
                raise ValueError('Legacy caster report changed')
            unchanged.append(row['id'])
    if len(unchanged) != 6:
        raise ValueError('Missing unchanged caster controls')
    return {'summaries': summaries, 'movement': movement, 'unchanged_caster': unchanged}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--previous', type=Path)
    args = parser.parse_args()
    matrix = json.loads(args.inputs.read_text())
    if args.run:
        run(matrix, args.output, verify_case)
    else:
        result = verify(matrix, json.loads(gzip.decompress(args.verify.read_bytes())),
                        json.loads(gzip.decompress(args.previous.read_bytes())))
        args.output.write_bytes((json.dumps(result, indent=2)+'\n').encode())
        print(f'Verified {len(result["summaries"])} native melee/legacy encounters')


if __name__ == '__main__':
    main()

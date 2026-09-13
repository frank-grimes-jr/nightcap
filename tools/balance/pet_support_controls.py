"""Matched native pet-support fights; unrestricted AA sensitivity, not release certification."""
import argparse
import copy
import gzip
import json
import math
from pathlib import Path

from pet_controls import run
from pet_combat_controls import summarize as summarize_combat

def gems_for(boss):
    return [15, 507, 112, 436, 32 if boss == 32040 else 6,
            510 if boss == 32040 else 120, 754, 447]


def prepare(pets, boss_positions, binary_sha256, seeds=(1729, 1730, 1731)):
    originals = {c['id']: c for c in pets['cases']}
    cases = []
    for stage in ('0', '100', '200', '500', 'all'):
        for boss in (32040, 73057):
            resist = 60 if boss == 32040 else 61
            # Native Talisman replaces Arch Shielding: do not assume both stack.
            actions = [{'spell': s} for s in (168, 145, resist, 633, 443, 166)]
            actions += [{'spell': 107, 'target_class': 13}]
            actions += [{'spell': 170, 'target_class': c} for c in (11, 10)]
            actions += [{'spell': s, 'target_class': c} for s in (145, 168, resist) for c in (13, 11, 10)]
            actions += [{'spell': 644}]
            for seed in seeds:
                case = copy.deepcopy(originals['triple-'+stage])
                case['id'] = f'pet-support-open-{stage}-{boss}-{seed}'
                case['seed'] = seed
                case['aa_pool'] = 'unrestricted stress test' if stage == 'all' else 'open-pool sensitivity'
                case['input']['pet_probe'].update({
                    'actions': copy.deepcopy(actions), 'recover_before_combat': True,
                    'combat': {'npc_id': boss, 'npc_position': boss_positions[boss],
                               'starting_distance': 80, 'duration_ms': 900000,
                               'commands_only': False, 'owner_policy': 'pet_support',
                               'commands': [{'ms': 0, 'command': 13}, {'ms': 50, 'command': 2}]}})
                cases.append(case)
    return {'scope': 'Fixed candidate gear, eight-gem native support, open-pool AA sensitivity. '
                     'All means unrestricted stress only; curated release maximum remains unassigned.',
            'binary_sha256': binary_sha256, 'cases': cases}


def summarize(case, report):
    result = summarize_combat(case, report)
    probe = report['pet_probe']
    combat = probe['combat']
    gems = gems_for(combat['input']['npc_id'])
    if (not probe['input'].get('recover_before_combat')
            or combat['input'].get('owner_policy') != 'pet_support'
            or combat['gems'] != gems or len(set(combat['gems'])) != 8):
        raise ValueError('Support requires recovery and eight fixed combat gems')
    recovery = probe['recovery']
    final = recovery['trace'][-1]
    player = final['player']
    if (final['sitting'] or player['casting'] or player['mana'] != recovery['max_mana']
            or player['hp'] < .95*player['max_hp'] or not final['pets']
            or any(p['hp'] != p['max_hp'] for p in final['pets'])
            or not 0 <= recovery['elapsed_ms'] <= 900000):
        raise ValueError('Native resource recovery incomplete')
    prepared = probe['final']
    if {k: v for k, v in final.items() if k != 'sitting'} != prepared:
        raise ValueError('Preparation differs from final recovery state')
    if combat['trace'][0]['player']['mana'] != player['mana'] or combat['trace'][0]['player']['hp'] != player['hp']:
        raise ValueError('Resources changed between preparation and combat')
    if not all(a['accepted'] for a in probe['actions']):
        raise ValueError('A preparation cast was rejected')
    resist = 60 if combat['input']['npc_id'] == 32040 else 61
    if not {168, 145, resist, 644} <= {b['spell'] for b in player['buffs']}:
        raise ValueError('Required owner buffs absent')
    for pet in prepared['pets']:
        haste = 107 if pet['spell'] == 633 else 170
        if not {145, 168, resist, haste} <= {b['spell'] for b in pet['buffs']}:
            raise ValueError('Required pet buffs absent')
    actions = combat['owner_actions']
    if not actions:
        raise ValueError('No owner support actions')
    owner, boss, pets = combat['player_id'], combat['boss_id'], set(combat['pet_ids'])
    for action in actions:
        gem, spell, target = action['gem'], action['spell'], action['target']
        if not 0 <= gem < len(gems) or gems[gem] != spell:
            raise ValueError('Spell did not use its fixed gem')
        allowed = ({owner} | pets) if spell == 15 else {owner} if spell == 754 else {boss}
        if target not in allowed:
            raise ValueError('Invalid support target')
        if 'ended_ms' in action and action['ended_ms'] < action['ms']:
            raise ValueError('Cast completion precedes request')
    elapsed = combat['trace'][-1]['ms']
    if not 0 < elapsed <= combat['input']['duration_ms']:
        raise ValueError('Invalid fight duration')
    terminal = verify_terminal(combat, elapsed)
    if combat['result'] == 'timeout' and elapsed != combat['input']['duration_ms']:
        raise ValueError('Timeout ended early')
    previous_ms = 0
    for event in combat['movement']['events']:
        if not previous_ms < event['ms'] <= elapsed or event['ms'] % 50:
            raise ValueError('Invalid support movement clock')
        previous_ms = event['ms']
        if event['controlled'] or event['casting'] or event['in_range'] or event['speed'] <= 0:
            raise ValueError('Support moved while inhibited')
        for field in ('from', 'to', 'actual'):
            if len(event[field]) != 3 or not all(math.isfinite(v) for v in event[field]):
                raise ValueError('Invalid support movement coordinates')
        limit = .05*event['speed']*.4*1.45
        if abs(event['limit']-limit) > 1e-5 or math.dist(event['from'], event['to']) > limit+1e-4:
            raise ValueError('Support movement exceeds native speed policy')
        if event['accepted'] != (event['actual'] == event['to']):
            raise ValueError('Support position packet was not applied')
        if not event['accepted'] and not event.get('controlled_after', False):
            raise ValueError('Support position packet was rejected without native control interruption')
    if combat['movement']['events'] and combat['movement']['history_packets'] <= 0:
        raise ValueError('Support movement lacks history packets')
    slow_samples = sum(any(b['spell'] == 507 for b in s['boss_buffs']) for s in combat['trace'])
    dot_damage = sum(max(0, e['hp_before'])-max(0, e['hp_after']) for e in combat['damage_ledger']
                     if e['depth'] == 0 and e['source'] == owner and e['spell'] in (32, 436, 6))
    return result | {
        'aa_pool': case['aa_pool'], 'recovery_ms': recovery['elapsed_ms'],
        'owner_spell_requests': len(actions), 'accepted_requests': sum(a['accepted'] for a in actions),
        'heal_requests': sum(a['spell'] == 15 for a in actions), 'slow_trace_samples': slow_samples,
        'native_owner_dot_hp_loss': dot_damage,
        'min_owner_hp_percent': 0 if any(e['entity_id'] == owner for e in terminal) else
            min(max(0, s['player']['hp'])/s['player']['max_hp']*100 for s in combat['trace']),
        'scope': 'Native active pet support; fixed candidate gear and open-pool AA sensitivity only. '
                 'No continuous kiting/resummoning, no established full BiS or release balance.'}


def verify_terminal(combat, elapsed):
    if not combat['input'].get('capture_terminal', False):
        if combat['result'] == 'boss_death' and combat['trace'][-1]['boss_hp'] > 0:
            raise ValueError('Boss victory lacks terminal HP evidence')
        if combat['result'] == 'player_death' and combat['trace'][-1]['player']['hp'] > 0:
            raise ValueError('Player death lacks terminal HP evidence')
        return []
    events = combat.get('terminal_events')
    if (not isinstance(events, list) or any(not isinstance(e, dict) or
            any(type(e.get(k)) is not int for k in ('entity_id', 'ms', 'hp', 'max_hp')) for e in events)):
        raise ValueError('Invalid native terminal callback evidence')
    ids = [e['entity_id'] for e in events]
    if (len(ids) != len(set(ids)) or set(ids)-{combat['player_id'], combat['boss_id']}
            or any(e['ms'] != elapsed or e['hp'] > 0 or e['max_hp'] <= 0 for e in events)):
        raise ValueError('Invalid native terminal callback evidence')
    expected = ('timeout' if not events else 'player_death'
                if events[0]['entity_id'] == combat['player_id'] else 'boss_death')
    if combat['result'] != expected:
        raise ValueError('Combat result differs from the first native death callback')
    return events


def verify(matrix, evidence):
    cases = {c['id']: c for c in matrix['cases']}
    runs = {r['id']: r for r in evidence['runs']}
    if len(cases) != len(matrix['cases']) or len(runs) != len(evidence['runs']) or cases.keys() != runs.keys():
        raise ValueError('Incomplete or duplicate pet support evidence')
    for identity, case in cases.items():
        if summarize(case, runs[identity]['report']) != runs[identity]['summary']:
            raise ValueError('Support summary differs from native evidence')
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
        summaries = verify(matrix, json.loads(gzip.decompress(args.verify.read_bytes())))
        args.output.write_bytes((json.dumps({'cases': summaries}, indent=2)+'\n').encode())
        print(f'Verified {len(summaries)} native pet support fights')

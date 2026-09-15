"""Broader drop-gear candidates with native recommended scaling and socket rules.

An exact additive assignment is only a candidate generator. Combat, caps, focus,
procs and acquisition difficulty still determine which loadout is preferable.
"""
import argparse
import copy
import json
from pathlib import Path

from builds import PROFILES, load_snapshot
from gear import assign_maximum, legal_item
from gear_haste_controls import recommended_bonus

ONE_HAND = (0, 2, 3, 45)
TWO_HAND = (1, 4, 35)


def lore_key(item):
    group = item['loregroup']
    return ('id', item['id']) if group == -1 else (('group', group) if group else None)


def score_item(item, level, casting_stat, objective, recommended=None):
    rec = item['reclevel'] if recommended is None else recommended
    scaled = lambda key: recommended_bonus(int(item.get(key, 0)), level, rec)
    combined = lambda stat: recommended_bonus(item['a'+stat] + item['heroic_'+stat], level, rec)
    hp_weight, mana_weight, ac_weight = {
        'balanced': (1, 1, 4), 'durability': (3, 1, 12), 'melee': (1, 0, 4)}[objective]
    value = (hp_weight*scaled('hp') + mana_weight*scaled('mana') + ac_weight*scaled('ac')
             + 10*hp_weight*scaled('heroic_sta') + 10*mana_weight*scaled('heroic_'+casting_stat)
             + hp_weight*combined('sta') + 2*mana_weight*combined(casting_stat)
             + 2*scaled('spelldmg') + 2*scaled('healamt'))
    if objective == 'melee' and item['damage'] > 0 and item['delay'] > 0:
        value += item['damage'] * 2000 // item['delay']
    return value


def assign_items(rows, candidates, eligible, score, occupied=(), empty=False):
    """One shared assignment prevents duplicate lore across every requested row."""
    occupied = set(occupied)
    options = {}
    candidates = sorted(candidates, key=lambda i: i['id'])
    for row in rows:
        choices = {}
        for item in candidates:
            key = lore_key(item)
            if key in occupied or not eligible(row, item):
                continue
            key = key or ('free', str(row))
            if key not in choices or score(row, item) > score(row, choices[key]):
                choices[key] = item
        if empty:
            choices[('empty', str(row))] = None
        options[row] = choices
    groups = sorted({k for choice in options.values() for k in choice}, key=str)
    value = lambda row, item: 0 if item is None else score(row, item)
    scores = [[value(row, options[row][k]) if k in options[row] else None for k in groups] for row in rows]
    assignment = assign_maximum(scores)
    return {row: options[row][groups[col]] for row, col in zip(rows, assignment)}


def equipment(items, classes, level, casting_stat, objective, mode, forced=None):
    if mode not in ('shield', 'dual', 'two_hand', 'focus'):
        raise ValueError('Unknown weapon layout')
    if mode == 'dual' and (1 not in classes or level != 50):
        raise ValueError('Dual-wield candidates currently require a level-50 held WAR')
    forced = forced or {}
    slots = tuple(s for s in range(1, 21) if mode != 'two_hand' or s != 14)

    def eligible(slot, item):
        if (item['itemclass'] != 0 or item['augtype'] or not legal_item(item, slot, classes, level)
                or slot in forced and forced[slot] != item['id']):
            return False
        kind = item['itemtype']
        if slot == 13:
            if mode == 'two_hand':
                return kind in TWO_HAND and item['damage'] > 0 and item['delay'] > 0
            if mode != 'focus':
                return kind in ONE_HAND and item['damage'] > 0 and item['delay'] > 0
            return kind not in TWO_HAND
        if slot == 14:
            if mode == 'shield':
                return kind == 8
            if mode == 'dual':
                return kind in ONE_HAND and item['damage'] > 0 and item['delay'] > 0
            return item['damage'] == 0
        return True

    if any(slot not in slots for slot in forced):
        raise ValueError('Forced item conflicts with weapon layout')
    items = [i for i in items if i['itemclass'] == 0 and not i['augtype'] and i['reqlevel'] <= level]
    scores = {i['id']: score_item(i, level, casting_stat, objective) for i in items}
    return assign_items(slots, items, eligible, lambda slot, item: scores[item['id']])


def socket_augments(gear, items, classes, level, casting_stat, objective):
    """Visible sockets, unrestricted augments, no augment-induced parent rescaling.

    Every captured eligible drop augment currently has restriction/recommended=0.
    Future restricted or higher-recommended augments require explicit support.
    """
    augments = [i for i in items if i['itemclass'] == 0 and i['augtype']]
    rows = [(slot, socket) for slot, item in gear.items() for socket in range(6)
            if item[f'augslot{socket+1}type'] > 0 and item[f'augslot{socket+1}visible']]

    def eligible(row, aug):
        slot, socket = row
        parent = gear[slot]
        return (legal_item(aug, slot, classes, level) and aug['augrestrict'] == 0
                and aug['reclevel'] <= max(level, parent['reclevel'])
                and bool(aug['augtype'] & (1 << (parent[f'augslot{socket+1}type']-1))))

    occupied = [lore_key(i) for i in gear.values() if lore_key(i)]
    selected = assign_items(rows, augments, eligible,
                            lambda row, aug: score_item(aug, level, casting_stat, objective,
                                                       max(gear[row[0]]['reclevel'], aug['reclevel'])),
                            occupied, empty=True)
    return {slot: [{'socket': socket, 'id': aug['id']} for (s, socket), aug in selected.items()
                   if s == slot and aug is not None] for slot in gear}


def generate(snapshot, templates):
    sources = {}
    for row in snapshot['tables']['drop_sources']:
        sources.setdefault(row['item_id'], []).append(row)
    result, seen = [], set()
    for scope, max_source_level in (('captured_drops', None), ('sources_at_most_65', 65)):
        items = [i for i in snapshot['tables']['items'] if any(
            max_source_level is None or r['npc_level'] <= max_source_level
            for r in sources.get(i['id'] % 200000, []))]
        for profile, (classes, casting_stat, melee) in PROFILES.items():
            template = next(b for b in templates['builds'] if b['profile'] == profile and b['aa_budget'] == 0)
            modes = ('shield', 'dual', 'two_hand') if 1 in classes else ('shield', 'focus', 'two_hand')
            objectives = ('balanced', 'durability', 'melee') if 1 in classes else ('balanced', 'durability')
            for objective in objectives:
                for mode in modes:
                    # Haste does not stack. Force each relevant top source to expose
                    # that tradeoff; do not add haste from different items together.
                    for haste_name, forced in (('unforced', {}), ('cloak36', {8: 611621}), ('ring41', {15: 609959})):
                        if any(not any(i['id'] == wanted for i in items) for wanted in forced.values()):
                            continue
                        try:
                            gear = equipment(items, classes, 50, casting_stat, objective, mode, forced)
                        except ValueError as error:
                            if str(error) != 'No complete legal assignment exists':
                                raise
                            continue
                        augs = socket_augments(gear, items, classes, 50, casting_stat, objective)
                        entries = [{'slot': slot, 'id': item['id'], 'augments': augs[slot]}
                                   for slot, item in gear.items()]
                        identity = (scope, profile, json.dumps(entries, sort_keys=True))
                        if identity in seen:
                            continue
                        seen.add(identity)
                        build = copy.deepcopy(template)
                        for key in ('total_score', 'raw_item_totals', 'capped_spell_damage', 'capped_heal_amount',
                                    'casting_stat_scored', 'melee_ratio_scored', 'spell_probes'):
                            build.pop(key, None)
                        build['equipment'] = entries
                        build['tier'] = '/'.join((scope, objective, mode, haste_name))
                        build['gear_search'] = {'scope': scope, 'objective': objective, 'mode': mode,
                                                'forced_haste': haste_name,
                                                'max_raw_worn_haste': max(i['haste'] for i in gear.values())}
                        result.append(build)
    return {'status': 'Expanded drop-only candidates; full BiS, solo acquisition and combat optimality unproven.',
            'export_equipment': True, 'builds': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--templates', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    snapshot, manifest = load_snapshot(args.snapshot)
    report = generate(snapshot, json.loads(args.templates.read_text()))
    report['snapshot_sha256'] = manifest['snapshot_sha256']
    args.output.write_bytes((json.dumps(report, indent=2)+'\n').encode())
    print(f'Generated {len(report["builds"])} distinct candidate builds')


if __name__ == '__main__':
    main()

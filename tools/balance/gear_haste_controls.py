"""Generate and verify native recommended-level/haste gear controls, not BiS claims."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from builds import load_snapshot
from formulas import trunc_div
from gear import legal_item


VARIANTS = {
    'original': {},
    'cloak36': {8: 611621},
    'ring41': {15: 609959},
    'ring41_cloak36': {8: 611621, 15: 609959},
}


def recommended_bonus(value, level, recommended):
    """Mob::AddItemBonuses scaling, including signed rounding toward zero."""
    if not 1 <= level <= 255 or not 0 <= recommended <= 255:
        raise ValueError('Invalid item/player level')
    if not recommended or level >= recommended:
        return value
    scaled = (level * 10000 // recommended) * value
    return trunc_div(scaled + (-5000 if scaled < 0 else 5000), 10000)


def build_controls(aa_inputs, tables):
    items = {i['id']: i for i in tables['items']}
    sources = {}
    for source in tables['drop_sources']:
        sources.setdefault(source['item_id'], []).append(source)
    builds = []
    # Hold the purchased ranks and other equipment constant within every comparison.
    for original in aa_inputs['builds']:
        for variant, replacements in VARIANTS.items():
            build = copy.deepcopy(original)
            build['tier'] = original['tier'] + '/' + variant
            build['gear_control'] = variant
            for key in ('total_score', 'raw_item_totals', 'capped_spell_damage', 'capped_heal_amount'):
                build.pop(key, None)
            for slot, item_id in replacements.items():
                item = items[item_id]
                if (not legal_item(item, slot, build['classes'], build['level'])
                        or item['augtype'] or item['itemclass'] != 0
                        or item_id % 200000 not in sources):
                    raise ValueError('Invalid or uncaptured haste replacement')
                replacement = {'slot': slot, 'id': item_id, 'name': item['name'],
                               'base_id': item_id % 200000,
                               'recommended_level': item['reclevel'],
                               'drop_provenance': sources[item_id % 200000]}
                matches = [i for i, entry in enumerate(build['equipment']) if entry['slot'] == slot]
                if len(matches) != 1:
                    raise ValueError('Expected exactly one replacement slot')
                build['equipment'][matches[0]] = replacement
            # Check conflicts with the rest of the worn loadout, including shared lore groups.
            lore = set()
            for entry in build['equipment']:
                item = items[entry['id']]
                group = ('id', item['id']) if item['loregroup'] == -1 else ('group', item['loregroup'])
                if item['loregroup'] and group in lore:
                    raise ValueError('Replacement introduces a lore conflict')
                lore.add(group)
            builds.append(build)
    if not builds:
        raise ValueError('No AA inputs')
    # Isolate the two items to make scaling/non-stacking independently measurable.
    template = next(b for b in aa_inputs['builds'] if b['profile'] == 'war-clr-wiz' and b['aa_budget'] == 0)
    for variant, replacements in VARIANTS.items():
        build = copy.deepcopy(template)
        build['tier'] = 'isolated/' + variant
        build['equipment'] = [{'slot': slot, 'id': item_id} for slot, item_id in replacements.items()]
        for key in ('total_score', 'raw_item_totals', 'capped_spell_damage', 'capped_heal_amount'):
            build.pop(key, None)
        builds.append(build)
    return {'status': 'Controlled gear substitutions; acquisition difficulty, combat optimization, and full BiS remain unproven',
            'builds': builds}


def verify_controls(inputs, native, tables):
    key = lambda b: (b['profile'], b['tier'], b.get('aa_stage'), b.get('aa_policy'))
    expected = {key(b): b for b in inputs['builds']}
    actual = {key(b): b for b in native['builds']}
    if (len(expected) != len(inputs['builds']) or len(actual) != len(native['builds'])
            or expected.keys() != actual.keys()):
        raise ValueError('Missing, duplicate, or unexpected gear-control build')
    items = {i['id']: i for i in tables['items']}
    spells = {s['id']: s for s in tables.get('spells_new', [])}
    mismatches = []
    for identity, build in expected.items():
        result = actual[identity]
        worn = [items[e['id']] for e in build['equipment']]
        # These selected items have no worn spells that alter the flat item HP/mana/haste fields.
        for item in worn:
            if item['worneffect'] > 0:
                spell = spells.get(item['worneffect'])
                # Captured See Invisible / Enduring Breath do not modify these fields.
                if not spell or any(spell[f'effectid{slot}'] not in (13, 14, 254) for slot in range(1, 13)):
                    raise ValueError('Worn-spell item needs a separate native effect control')
        check = {'item_hp': sum(recommended_bonus(i['hp'], build['level'], i['reclevel']) for i in worn),
                 'item_mana': sum(recommended_bonus(i['mana'], build['level'], i['reclevel']) for i in worn),
                 'haste': 100 + max((i['haste'] for i in worn), default=0)}
        for field, value in check.items():
            if result[field] != value:
                mismatches.append({'build': identity, 'field': field, 'expected': value, 'actual': result[field]})
        if [p['rank_id'] for p in result['aa_purchases']] != build['aa_rank_ids']:
            mismatches.append({'build': identity, 'field': 'aa_purchases', 'reason': 'Allocation changed'})
    return mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--aa-inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native', type=Path)
    args = parser.parse_args()
    snapshot, manifest = load_snapshot(args.snapshot)
    source = json.loads(args.aa_inputs.read_text())
    inputs = build_controls(source, snapshot['tables'])
    if args.native:
        native = json.loads(args.native.read_text())
        mismatches = verify_controls(inputs, native, snapshot['tables'])
        output = {'builds': len(inputs['builds']), 'mismatches': mismatches,
                  'native_sha256': hashlib.sha256(args.native.read_bytes()).hexdigest(),
                  'scope': 'Flat item HP/mana recommended-level scaling, non-stacking worn haste, unchanged AA purchases. No combat/BiS conclusion.'}
    else:
        output = inputs
    output.update({'snapshot_sha256': manifest['snapshot_sha256'],
                   'aa_inputs_sha256': hashlib.sha256(args.aa_inputs.read_bytes()).hexdigest()})
    args.output.write_bytes((json.dumps(output, indent=2) + '\n').encode())
    print(json.dumps({k: v for k, v in output.items() if k != 'builds'} | {'build_count': len(inputs['builds'])}, indent=2))
    return int(bool(output.get('mismatches')))


if __name__ == '__main__':
    raise SystemExit(main())

"""Build a reviewable PoK hub proposal from the captured current merchant stock.

This module does not connect to a database or apply changes.
"""
import argparse
import hashlib
import json
from pathlib import Path


CLASSES = ['Warrior', 'Cleric', 'Paladin', 'Ranger', 'Shadow Knight', 'Druid', 'Monk',
           'Bard', 'Rogue', 'Shaman', 'Necromancer', 'Wizard', 'Magician', 'Enchanter',
           'Beastlord', 'Berserker']
SOURCE_SHA256 = 'bae7ba7d897962f67581e3e731b94f4a31898d160c30c2edb74912b21aa11880'


def build_plan(audit):
    if audit['source_sha256'] != SOURCE_SHA256:
        raise ValueError('Original spell catalog source has changed; review before planning')
    stock = audit['stock']
    if not stock or len({i['item_id'] for i in stock}) != len(stock):
        raise ValueError('Expected a nonempty, unique current stock snapshot')
    for item in stock:
        levels = item.get('original_class_levels', [])
        if len(levels) != 16 or any(type(v) is not int or not 0 <= v <= 255 for v in levels):
            raise ValueError('Missing or invalid original class levels')
        if item['price'] < 0 or item['item_type'] != 20:
            raise ValueError('Unexpected current scroll item or price')
    merchants = []
    for side, class_ids in enumerate(([2,6,10,11,12,13,14,15], [1,3,4,5,7,8,9,16])):
        for row, class_id in enumerate(class_ids):
            name = CLASSES[class_id - 1]
            items = [i for i in stock if 1 <= i['original_class_levels'][class_id - 1] <= 50]
            if not items or len(items) > 500:
                raise ValueError('Class stock must fit one nonempty RoF2 merchant window')
            items.sort(key=lambda i: (i['original_class_levels'][class_id - 1], i['item_name'], i['item_id']))
            categories = set('Tomes' if i['item_name'].startswith('Tome') else
                             'Songs' if i['item_name'].startswith('Song:') else 'Spells' for i in items)
            role = 'Discipline_Merchant' if class_id in (1,7,9,16) else 'Song_Merchant' if class_id == 8 else 'Spell_Merchant'
            merchants.append({
                'class_id': class_id, 'class_name': name,
                'npc_id': 997899 + class_id, 'merchant_id': 99299 + class_id,
                'name': name.replace(' ', '_') + '_' + role,
                'lastname': name + ': ' + ' / '.join(sorted(categories)),
                'findable': 1, 'template_npc_id': 999222 if class_id in (2,6,10) else
                    999223 if class_id in (1,4,7,8,9,15,16) else 999224 if class_id in (3,5) else 999221,
                'position': {'x': -325 if side == 0 else -245, 'y': -204 + row * 16,
                             'z': -158.875, 'heading': 128 if side == 0 else 384},
                'items': [{'slot': slot, 'item_id': item['item_id'], 'spell_id': item['spell_id'],
                           'class_level': item['original_class_levels'][class_id - 1], 'price': item['price']}
                          for slot, item in enumerate(items, 1)]})
    actual = {i['item_id'] for m in merchants for i in m['items']}
    if actual != {i['item_id'] for i in stock}:
        raise ValueError('The class plan would lose or introduce current scrolls')
    if any(len(m['name']) > 64 or len(m['lastname']) > 32 for m in merchants):
        raise ValueError('Merchant label exceeds native NPC text fields')
    return {
        'status': 'proposal_not_applied', 'zone': 'poknowledge', 'level_cap': 50,
        'arrival': {'x': -285, 'y': -148, 'z': -159},
        'placement_requires_in_game_qa': True,
        'guide': {'npc_id': 999220, 'name': 'The_Ancient_Chronicler',
                  'lastname': 'Choose / View Classes', 'findable': 1,
                  'position': {'x': -285, 'y': -74, 'z': -158.875, 'heading': 256}},
        'retire_vendor_spawn_npc_ids': [999221,999222,999223,999224,999234,999235,999236],
        'merchants': sorted(merchants, key=lambda m: m['class_id']),
        'invariants': {'current_unique_scrolls': len(stock), 'planned_unique_scrolls': len(actual),
                       'maximum_merchant_slots': max(len(m['items']) for m in merchants),
                       'prices': 'Retain item prices and source merchant faction/pricing settings.'},
        'remaining_gates': ['Verify unused IDs again at apply time.', 'Verify ground, line of sight, and walking paths.',
                            'Build guarded reversible SQL and integrate restocking.',
                            'Consolidate the nearby utility services and verify duplicate Forgemaster records.',
                            'Run in-game merchant and selection QA before promotion.'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.audit.read_bytes()
    plan = build_plan(json.loads(raw))
    plan['audit_sha256'] = hashlib.sha256(raw).hexdigest()
    args.output.write_bytes((json.dumps(plan, separators=(',', ':')) + '\n').encode())
    print(json.dumps(plan['invariants']))


if __name__ == '__main__':
    main()

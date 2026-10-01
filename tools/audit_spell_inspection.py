"""Audit every packaged spell and captured scroll against original eligibility.

Reads files only. The scroll JSON is a read-only items capture containing id,
name, classes and spell_id for every itemtype=20 row.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from client_gameplay_assets import restore_spell_classes
from generate_spell_class_catalog import parse
from generate_pet_spell_catalog import SOURCE_SHA256


def audit(spells, original, scrolls):
    restored, changed = restore_spell_classes(spells, original)
    if changed or restored != spells:
        raise ValueError('Packaged class fields differ from the reviewed original')
    canonical = dict(parse(original))
    packaged = {int(row[0]): row for row in
                (line.split('^') for line in spells.decode('latin1').splitlines())}
    distribution = Counter(int(level) for row in packaged.values() for level in row[104:120])
    affected, unresolved, seen = [], [], set()
    removed, added, special = 0, 0, 0
    for scroll in scrolls:
        item, spell, stock = (int(scroll[key]) for key in ('id', 'spell_id', 'classes'))
        if item in seen or item <= 0 or not 0 <= stock <= 65535:
            raise ValueError('Invalid or duplicate scroll')
        seen.add(item)
        if spell not in packaged:
            unresolved.append({'item_id': item, 'spell_id': spell, 'name': scroll['name']})
            continue
        levels = canonical.get(spell, (255,)*16)
        mask = sum(1 << index for index, level in enumerate(levels) if 0 < level < 255)
        # The display hook respects a native zero. Nonzero masks are projected
        # from the same canonical catalog as actual scroll scribing access.
        displayed = mask if stock else 0
        invalid = stock & ~mask
        missing = displayed & ~stock
        removed += invalid.bit_count()
        added += missing.bit_count()
        special += sum(bool(displayed & (1 << i)) and level in (253, 254)
                       for i, level in enumerate(levels))
        if invalid or missing:
            affected.append({'item_id': item, 'spell_id': spell, 'name': scroll['name'],
                             'before_mask': stock, 'after_mask': displayed,
                             'removed_mask': invalid, 'added_mask': missing})
    return {
        'schema': 1, 'status': 'read_only_audit',
        'source_sha256': SOURCE_SHA256,
        'packaged_sha256': hashlib.sha256(spells).hexdigest(),
        'packaged_spells': len(packaged), 'class_slots': sum(distribution.values()),
        'level_distribution': dict(sorted(distribution.items())),
        'canonical_catalog_spells': len(canonical), 'class_field_drift': len(changed),
        'scroll_items': len(scrolls), 'affected_scroll_items': len(affected),
        'scrolls_with_packaged_spell': len(scrolls)-len(unresolved),
        'unusable_class_entries_removed': removed, 'canonical_class_entries_restored': added,
        'preserved_253_254_scroll_entries': special,
        'scrolls_without_packaged_spell': unresolved, 'affected_scrolls': affected,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spells', required=True, type=Path)
    parser.add_argument('--original', required=True, type=Path)
    parser.add_argument('--scrolls', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.spells.read_bytes(), args.original.read_bytes(),
                   json.loads(args.scrolls.read_bytes()))
    args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('affected_scrolls', 'level_distribution',
                                     'scrolls_without_packaged_spell')}))

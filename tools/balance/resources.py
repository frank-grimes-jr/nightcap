"""RoF2/SoD HP and mana math; callers must supply resolved bonuses and stats.

Mirrors Client resource formulas, not inventory effect/AA/buff resolution.
Missing base data fails closed instead of silently generating a weak character.
"""
import struct

from formulas import trunc_div


INT_CASTERS = frozenset((5, 8, 11, 12, 13, 14))
WIS_CASTERS = frozenset((2, 3, 4, 6, 10, 15))


def validate_classes(classes):
    if not 1 <= len(classes) <= 3 or len(set(classes)) != len(classes) or any(c not in range(1, 17) for c in classes):
        raise ValueError('Expected one to three distinct player classes')


def class_rows(classes, level, rows):
    validate_classes(classes)
    if not 1 <= level <= 255:
        raise ValueError('Invalid player level')
    found = []
    for cls in classes:
        matches = [r for r in rows if r['level'] == level and r['class'] == cls]
        if len(matches) != 1:
            raise ValueError(f'Expected exactly one base-data row for level {level}, class {cls}')
        found.append(matches[0])
    return found


def base_hp(classes, level, stamina, heroic_hp, rows):
    if stamina < 1:
        raise ValueError('Stamina must be a resolved positive stat')
    best = max(class_rows(classes, level, rows), key=lambda row: row['hp'])
    converted = trunc_div(stamina - 255, 2) + 255 if stamina > 255 else stamina
    return int(5 + best['hp'] + best['hp_fac'] * converted) + heroic_hp


def base_mana(classes, level, intelligence, wisdom, heroic_mana, rows):
    if min(intelligence, wisdom) < 1:
        raise ValueError('Casting stats must be resolved positive stats')
    best = 0
    for row in class_rows(classes, level, rows):
        cls = row['class']
        if cls not in INT_CASTERS | WIS_CASTERS:
            continue
        stat = intelligence if cls in INT_CASTERS else wisdom
        converted = stat
        if stat > 100:
            over200 = trunc_div(stat - 200, -2) + stat if stat > 200 else stat
            converted = trunc_div(3 * over200 - 300, 2) + over200
        best = max(best, int(row['mana'] + converted * row['mana_fac'] + heroic_mana))
    return best


def float32(value):
    return struct.unpack('f', struct.pack('f', value))[0]


def max_hp(base, item, *, percent=0, flat=0, leadership=0):
    """Percent is in 1/100 percent units (1500 means +15%)."""
    factor = float32(10000 + percent)
    scaled = float32(float32(float32(base + item) * factor) / 10000)
    return int(scaled) + flat + leadership


def max_mana(classes, base, item, *, spell=0, aa=0, leadership=0):
    validate_classes(classes)
    if not set(classes) & (INT_CASTERS | WIS_CASTERS):
        return 0
    return max(0, base + item + spell + aa + leadership)


def worn_stat(creation, ordinary, heroic, cap, *, spell=0, aa=0, other_cap=0):
    """Unintoxicated, unencumbered stat with fully level-eligible items."""
    return min(cap + heroic + other_cap, max(1, creation + ordinary + heroic + spell + aa))


def heroic_resources(base_class, stamina, intelligence, wisdom, *, sta_multiplier=1.0,
                     int_multiplier=1.0, wis_multiplier=1.0):
    """Default heroic resources, excluding per-character data-bucket overrides.

    These bonuses use base class; Bard gets no heroic mana despite using INT for
    its base mana. Additional held caster classes do not alter these predicates.
    """
    validate_classes((base_class,))
    hp = int(stamina * sta_multiplier * 10)
    mana = 0
    if base_class in INT_CASTERS - {8}:
        mana += int(intelligence * int_multiplier * 10)
    if base_class in WIS_CASTERS:
        mana += int(wisdom * wis_multiplier * 10)
    return hp, mana

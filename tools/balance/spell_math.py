"""Spell base values, durations, and ordinary elemental resist distributions.

Unsupported dynamic formulas fail explicitly. Inputs are resolved values; focus,
effect-specific resistance AAs, physical resists, and resist softcaps are separate.
"""
from collections import Counter

from formulas import trunc_div


def buff_duration(level, formula, duration):
    if level < 1 or duration < 0:
        raise ValueError('Invalid duration inputs')
    values = {1:level//2 if level>3 else 1, 2:level//2+5 if level>3 else 6,
              3:30*level, 4:50, 5:2, 6:level//2+2, 7:level, 8:level+10,
              9:2*level+10, 10:3*level+10, 11:30*(level+3),
              12:level//4 if level>7 else 1, 13:4*level+10,
              14:5*(level+2), 15:10*(level+10)}
    if formula in (50,51):
        return -1 if formula==50 else -4
    temp = values.get(formula, formula if formula>=200 else 0)
    return min(temp,duration) if duration else temp


def effect_value(formula, base, maximum, level, *, duration_formula=0,
                 duration=0, remaining=0, random_value=None):
    if level < 1 or formula < 0:
        raise ValueError('Invalid formula inputs')
    unsigned = abs(base)
    sign = -1 if maximum < base and maximum != 0 else 1
    if formula in (0,100):
        result = unsigned
    elif formula in (60,70):
        result = unsigned//100
    elif formula < 100:
        result = unsigned+level*formula
    elif formula == 101:
        result = sign*(unsigned+level//2)
    elif 102 <= formula <= 105:
        result = sign*(unsigned+level*(formula-101))
    elif formula in (107,108,120,122) or 1000 < formula < 1999:
        elapsed = max(0,buff_duration(level,duration_formula,duration)-max(remaining-1,0))
        scale = {107:1,108:2,120:5,122:12}.get(formula,formula-1000)
        result = sign*(unsigned-scale*elapsed)
    elif formula == 109:
        result = sign*(unsigned+level//4)
    elif formula in (110,119,121):
        result = unsigned+level//{110:6,119:8,121:3}[formula]
    elif 111 <= formula <= 114:
        scale,threshold = {111:(6,16),112:(8,24),113:(10,34),114:(15,44)}[formula]
        result = sign*(unsigned+scale*(level-threshold))
    elif 115 <= formula <= 118:
        scale,threshold = {115:(7,15),116:(10,24),117:(13,34),118:(20,44)}[formula]
        result = unsigned+scale*max(0,level-threshold)
    elif formula == 123:
        if random_value is None or not min(unsigned,abs(maximum)) <= random_value <= max(unsigned,abs(maximum)):
            raise ValueError('Formula 123 requires a resolved uniform integer draw')
        result = random_value
    elif 124 <= formula <= 132:
        scale = (1,2,3,4,5,10,15,20,25)[formula-124]
        result = unsigned+sign*scale*max(0,level-50)
    elif formula in (139,140,141,142):
        extra = max(0,level-30)
        result = unsigned+{139:extra//2,140:extra,141:3*extra//2,142:2*extra}[formula]
    elif formula == 143:
        result = unsigned+3*level//4
    elif formula == 144:
        result = unsigned+level*10+(level-40)*20
    elif formula in (201,203):
        result = maximum
    elif 2000 <= formula <= 2650:
        result = unsigned*(level*(formula-2000)+1)
    else:
        raise ValueError(f'Unsupported state-dependent or unknown spell formula {formula}')
    if maximum:
        result = min(result,maximum) if sign==1 else max(result,maximum)
    return -result if base<0 and result>0 else result


def resist_outcomes(resistance, caster_level, target_level, *, modifier=0, partial=False,
                    target_npc=True, caster_npc=False, damage_spell=True, falloff=67,
                    minimum=0, maximum=0, no_resist=False, immune=False):
    """Exact counts for the 201 equally likely ordinary elemental resist rolls.

    Modifier includes spell resist adjustment and already resolved focus/CHA
    contributions. Excludes physical/PvP/charm/root-break and softcap branches.
    """
    if min(caster_level,target_level,falloff)<1:
        raise ValueError('Invalid resist levels')
    if immune:
        return ((201,0),)
    if no_resist:
        return ((201,100),)
    difference = target_level-caster_level
    if target_npc and target_level>=falloff:
        difference = max(0,falloff-1-caster_level)
    if not target_npc and target_level>=21:
        difference = min(difference,15)
    if target_npc:
        difference = max(difference,-9)
    level_mod = difference*difference//2
    if difference<0:
        level_mod = -level_mod
    if target_npc and target_level-caster_level>20:
        level_mod = 1000
    if target_npc and damage_spell and target_level>=17:
        damage_diff = max(0,falloff-1-caster_level) if target_level>=falloff else target_level-caster_level
        level_mod += 2*damage_diff
    chance = level_mod+modifier+resistance
    if maximum:
        chance = min(chance,maximum)
    if minimum:
        chance = max(chance,minimum)
    outcomes = Counter()
    for roll in range(201):
        if roll>chance:
            landed = 100
        elif not partial:
            landed = 0
        else:
            effective = max(1,chance)
            reduction = trunc_div(150*(effective-roll),effective)
            if target_npc:
                if target_level>caster_level and target_level>=17 and caster_level<=50:
                    reduction += 5
                if target_level>=30 and caster_level<50:
                    reduction += caster_level-25
                if target_level<15:
                    reduction -= 5
            if caster_npc and target_level-caster_level>=20:
                reduction = int(reduction+(target_level-caster_level)*1.5)
            landed = max(0,min(100,100-reduction))
        outcomes[landed] += 1
    return tuple((count,percent) for percent,count in sorted(outcomes.items()))

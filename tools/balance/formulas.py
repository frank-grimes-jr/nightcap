"""Integer spell arithmetic ported from zone/effects.cpp; no focus/crit model yet."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SpellRules:
    flat: bool
    percent: bool


def trunc_div(numerator, denominator):
    """C++ signed integer division (toward zero), without floating-point rounding."""
    if denominator == 0:
        raise ZeroDivisionError
    sign = -1 if (numerator < 0) != (denominator < 0) else 1
    return sign * (abs(numerator) // abs(denominator))


def extra_spell_amount(base, bonus, rules, cast_ms=0, recast_ms=0, recovery_ms=0):
    """Mob::GetExtraSpellAmt, including the nonflat percentage branch."""
    if min(cast_ms, recast_ms, recovery_ms) < 0:
        raise ValueError('Spell timing must be nonnegative')
    if rules.flat:
        return trunc_div(abs(base) * bonus, 100) if rules.percent else bonus
    total = cast_ms + max(recast_ms, recovery_ms)
    if 0 < total <= 2500:
        bonus = trunc_div(bonus * 25, 100)
    elif 2500 < total < 7000:
        bonus = trunc_div(bonus * (167 * trunc_div(total - 1000, 1000)), 1000)
    else:
        bonus = trunc_div(bonus * total, 7000)
    if bonus * 2 > abs(base):
        bonus = trunc_div(abs(base), 2)
    return trunc_div(abs(base) * bonus, 100) if rules.percent else bonus


def spell_amount(base, worn_bonus, cap, rules, *, duration=0, split=False,
                 eligible=True, cast_ms=0, recast_ms=0, recovery_ms=0):
    """Positive base + item contribution only; per tick for periodic spells.

    The caller must resolve spell eligibility, effective base value, focus/crit,
    level restrictions, and target effects separately. Duration splitting here
    follows the item's contribution in GetActDoTDamage/GetActSpellHealing.
    """
    if min(base, worn_bonus, cap, duration, cast_ms, recast_ms, recovery_ms) < 0:
        raise ValueError('Amounts, cap, duration, and timing must be nonnegative')
    if not eligible:
        return base
    bonus = extra_spell_amount(base, min(worn_bonus, cap), rules,
                               cast_ms, recast_ms, recovery_ms)
    if split and duration > 0:
        bonus = trunc_div(bonus, duration)
    return base + bonus

"""Resolved melee arithmetic from attack.cpp; excludes bonus/AC resolution."""
from dataclasses import dataclass

from formulas import trunc_div


def roll0(rng, maximum):
    return rng.randrange(maximum) if maximum > 1 else 0


def hit_succeeds(accuracy, avoidance, attack_roll, defense_roll, tie_wins, *, sitting=False):
    if sitting:
        return True
    if avoidance == -1:
        return False
    if accuracy == -1:
        return True
    return tie_wins if attack_roll == defense_roll else attack_roll > defense_roll


def damage_interval(offense, mitigation, attack_roll, defense_roll, *, sitting=False):
    if min(offense, mitigation) < 0 or not 0 <= attack_roll < offense + 5 or not 0 <= defense_roll < mitigation + 5:
        raise ValueError('Invalid resolved offense/mitigation or Roll0 input')
    if sitting:
        return 2.0
    average = max(1, (offense + mitigation + 10) // 2)
    index = max(0, attack_roll - defense_roll + average // 2)
    return (min(19, index * 20 // average) + 1) / 10


def mitigated_damage(base, interval, *, level_difference=0, level_check=-1, level_bonus=0.0):
    if base < 0 or not 0.1 <= interval <= 2:
        raise ValueError('Invalid base damage or interval')
    if level_check >= 0:
        if level_difference > level_check:
            interval = min(2.0, interval + level_bonus)
        elif level_difference < -level_check:
            interval -= level_bonus
            if interval < 0.10000000149011612:  # native 0.1f promoted to double
                interval = 0.10000000149011612
    # A zero base bypasses MeleeMitigation; the attack starts at damage_done=1.
    return max(1, int(interval * base + 0.5))


def npc_damage(minimum, maximum, interval, *, shielding=0, level_difference=0,
               level_check=-1, level_bonus=0.0, damage_modifier=0):
    """NPC base/DI split, resolved damage SPA modifier, and worn shielding."""
    if not 0 <= minimum <= maximum or not 0 <= shielding <= 100:
        raise ValueError('Invalid NPC damage range or shielding')
    base = int((maximum - minimum) / 1.9 + 0.5)
    additive = minimum - int(base / 10 + 0.5)
    damage = mitigated_damage(base, interval, level_difference=level_difference,
                              level_check=level_check, level_bonus=level_bonus)
    damage += trunc_div(damage * damage_modifier, 100)
    return damage + additive - trunc_div(additive * shielding, 100)


def legacy_round_attacks(level, roll, *, count=1, double=False, triple=False, quad=False):
    """Nonpet main hand with UseLiveCombatRounds=false, no rampage."""
    if not 0 <= roll < 100 or not 1 <= level <= 255:
        raise ValueError('Invalid round roll or level')
    attacks = max(1, count)
    if (double or triple or quad) and roll < level + 20:
        attacks += 1
        if (triple or quad) and roll < level:
            attacks += 1
            if quad and roll < level - 20:
                attacks += 1
    return attacks


@dataclass(frozen=True)
class Melee:
    minimum: int
    maximum: int
    delay_ms: int
    accuracy: int
    offense: int
    level: int
    attacks: int = 1
    double: bool = False
    triple: bool = False
    quad: bool = False
    live_rounds: bool = True
    double_skill: int = 0
    dual_skill: int = 0
    offhand: bool = False

    def __post_init__(self):
        if not 0 <= self.minimum <= self.maximum or self.delay_ms <= 0 or self.offense < 0 or self.accuracy < -1 or not 1 <= self.level <= 255:
            raise ValueError('Invalid resolved melee profile')
        if min(self.double_skill, self.dual_skill) < 0:
            raise ValueError('Skills must be nonnegative')

    def round_attacks(self, rng, *, offhand=False):
        level_bonus = self.level if self.level > 35 else 0
        if offhand:
            if not self.offhand or self.dual_skill <= 0 or rng.randint(1, 375) > self.dual_skill + level_bonus:
                return 0
            return 1 + int(self.double_skill > 0 and self.level > 35 and rng.randint(1, 500) <= self.double_skill + level_bonus)
        if self.live_rounds:
            return 1 + int(self.double_skill > 0 and rng.randint(1, 500) <= self.double_skill + level_bonus)
        return legacy_round_attacks(self.level, rng.randrange(100), count=self.attacks,
                                    double=self.double, triple=self.triple, quad=self.quad)

    def swing(self, rng, *, avoidance, mitigation, shielding=0, sitting=False,
              defender_level=50, level_check=-1, level_bonus=0.0, damage_modifier=0):
        hit = hit_succeeds(self.accuracy, avoidance, roll0(rng, self.accuracy),
                           roll0(rng, avoidance), rng.randrange(100) < 50, sitting=sitting)
        if not hit:
            return 0
        interval = damage_interval(self.offense, mitigation, roll0(rng, self.offense + 5),
                                   roll0(rng, mitigation + 5), sitting=sitting)
        return npc_damage(self.minimum, self.maximum, interval, shielding=shielding,
                          level_difference=self.level-defender_level,
                          level_check=level_check, level_bonus=level_bonus,
                          damage_modifier=damage_modifier)

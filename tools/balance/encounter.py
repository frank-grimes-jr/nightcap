"""Seeded event simulator for explicitly resolved combat profiles.

This schedules actions, not EQEmu zone AI. Actor/Action inputs must declare the
resolved effects, resists, defensive stats, regeneration, and action priorities.
The content adapter is responsible for rejecting unmodeled encounter mechanics.
"""
from dataclasses import dataclass
import heapq
import random

from melee import Melee


@dataclass(frozen=True)
class Action:
    name: str
    effect: str
    amount: int
    mana: int = 0
    cast_ms: int = 0
    recast_ms: int = 0
    recovery_ms: int = 0
    hp_below: int = 1000
    duration_ms: int = 0
    first_ready_ms: int = 0
    outcomes: tuple = ((1, 100),)  # (relative weight, landed percentage)

    def __post_init__(self):
        if self.effect not in ('damage', 'heal', 'dot', 'hot', 'fear'):
            raise ValueError('Unsupported action effect')
        if not self.name or min(self.amount, self.mana, self.cast_ms, self.recast_ms,
                                self.recovery_ms, self.duration_ms, self.first_ready_ms) < 0:
            raise ValueError('Invalid action amount or timing')
        if self.cast_ms + max(self.recast_ms, self.recovery_ms) <= 0:
            raise ValueError('Action must have nonzero repeat time')
        if not 0 <= self.hp_below <= 1000:
            raise ValueError('HP condition must be per mille')
        if self.effect in ('dot', 'hot', 'fear') and self.duration_ms <= 0:
            raise ValueError('Periodic/control actions require duration')
        if not self.outcomes or any(w <= 0 or not 0 <= pct <= 100 for w, pct in self.outcomes):
            raise ValueError('Invalid resolved resist distribution')


@dataclass(frozen=True)
class Actor:
    name: str
    hp: int
    mana: int = 0
    actions: tuple = ()  # highest priority first; HP condition applies to self
    hp_regen: int = 0
    mana_regen: int = 0
    melee: Melee | None = None
    avoidance: int = 1
    mitigation: int = 1
    shielding: int = 0
    avoid_basis_points: int = 0  # explicit resolved combined block/parry/dodge/etc
    level: int = 50
    fear_immune: bool = False
    melee_while_casting: bool = False
    incoming_melee_modifier: int = 0  # SPA modifiers; base WAR includes -5 here

    def __post_init__(self):
        if self.hp <= 0 or min(self.mana, self.hp_regen, self.mana_regen, self.mitigation) < 0:
            raise ValueError('Invalid actor resources or mitigation')
        if self.avoidance < -1 or not 0 <= self.shielding <= 100 or not 0 <= self.avoid_basis_points <= 10000:
            raise ValueError('Invalid resolved defenses')
        if not 1 <= self.level <= 255 or len({a.name for a in self.actions}) != len(self.actions):
            raise ValueError('Invalid level or duplicate action name')
        if self.incoming_melee_modifier < -100:
            raise ValueError('Unsupported melee reduction exceeding 100 percent')


def simulate(player, enemy, *, seed, duration_ms=600000, trace=False,
             think_ms=100, tick_ms=6000, level_check=-1, level_bonus=0.0):
    """Two actors in range; death at HP<=0; fixed global tick phase at t=0.

    Ties resolve ticks, melee, cast completions, decisions; enemy precedes player
    within each event type. This conservative tie policy is not an engine-parity
    claim. Mana is charged at cast completion; interruption cancels the completion.
    No push/fizzle, movement/pathing, adds, pets, procs, or revival is implied.
    Decisions poll at think_ms, so reactions can be delayed by up to one poll.
    """
    if min(duration_ms, think_ms, tick_ms) <= 0:
        raise ValueError('Simulation duration and time steps must be positive')
    rng = random.Random(seed)
    actors = (player, enemy)
    state = [dict(hp=a.hp, mana=a.mana, min_hp=a.hp, damage=0, healing=0, overheal=0,
                  mana_spent=0, mana_regenerated=0, oom_checks=0, casts=0, interrupts=0,
                  resists=0, swings=0, melee_hits=0, busy_until=0, fear_until=0,
                  cast_token=0, casting=False,
                  cooldown={s.name:s.first_ready_ms for s in a.actions}) for a in actors]
    events, log, periodic = [], [], {}
    serial = 0
    now = 0

    def schedule(time, kind, actor, payload=None):
        nonlocal serial
        serial += 1
        priority = {'tick': 0, 'melee': 1, 'finish': 2, 'think': 3}[kind]
        heapq.heappush(events, (time, priority, -actor, serial, kind, actor, payload))

    def record(actor, action, amount):
        if trace:
            log.append({'time_ms': now, 'actor': actors[actor].name, 'action': action,
                        'amount': amount, 'player_hp': state[0]['hp'],
                        'player_mana': state[0]['mana'], 'enemy_hp': state[1]['hp'],
                        'enemy_mana': state[1]['mana']})

    def apply(actor, target, effect, amount, name):
        source, dest = state[actor], state[target]
        if effect in ('damage', 'dot'):
            actual = min(dest['hp'], amount)
            dest['hp'] -= actual
            dest['min_hp'] = min(dest['min_hp'], dest['hp'])
            source['damage'] += actual
        else:
            actual = min(actors[target].hp - dest['hp'], amount)
            dest['hp'] += actual
            source['healing'] += actual
            source['overheal'] += amount - actual
        record(actor, name, actual)

    schedule(tick_ms, 'tick', 1)
    for index, actor in enumerate(actors):
        if actor.actions:
            schedule(0, 'think', index)
        if actor.melee:
            schedule(0, 'melee', index, False)
            if actor.melee.offhand:
                schedule(0, 'melee', index, True)
    while events:
        event_time, _, _, _, kind, index, payload = heapq.heappop(events)
        if event_time > duration_ms:
            now = duration_ms
            break
        now = event_time
        actor, current, other = actors[index], state[index], state[1-index]
        if kind == 'tick':
            # Periodics resolve before regeneration; a lethal tick cannot be rescued.
            for key, (source, target, action, amount, expiry) in list(periodic.items()):
                if now <= expiry:
                    apply(source, target, action.effect, amount, action.name + ':tick')
                    if any(s['hp'] <= 0 for s in state):
                        break
                else:
                    del periodic[key]
            if all(s['hp'] > 0 for s in state):
                for i, a in enumerate(actors):
                    s = state[i]
                    s['hp'] = min(a.hp, s['hp'] + a.hp_regen)
                    gained = min(a.mana - s['mana'], a.mana_regen)
                    s['mana'] += gained
                    s['mana_regenerated'] += gained
                schedule(now + tick_ms, 'tick', index)
        elif kind == 'melee':
            if now >= current['fear_until'] and (not current['casting'] or actor.melee_while_casting):
                m = actor.melee
                attacks = m.round_attacks(rng, offhand=payload)
                defender = actors[1-index]
                for _ in range(attacks):
                    current['swings'] += 1
                    if rng.randrange(10000) < defender.avoid_basis_points:
                        continue
                    amount = m.swing(rng, avoidance=defender.avoidance, mitigation=defender.mitigation,
                                     shielding=defender.shielding, defender_level=defender.level,
                                     level_check=level_check, level_bonus=level_bonus,
                                     damage_modifier=defender.incoming_melee_modifier)
                    if amount > 0:
                        current['melee_hits'] += 1
                        apply(index, 1-index, 'damage', amount, 'melee')
                    if other['hp'] <= 0:
                        break
            schedule(now + actor.melee.delay_ms, 'melee', index, payload)
        elif kind == 'finish':
            token, action = payload
            if token != current['cast_token']:
                continue
            current['casting'] = False
            current['mana'] -= action.mana
            current['mana_spent'] += action.mana
            current['casts'] += 1
            current['cooldown'][action.name] = now + action.recast_ms
            current['busy_until'] = now + action.recovery_ms
            percent = rng.choices([pct for _,pct in action.outcomes],
                                  weights=[w for w,_ in action.outcomes], k=1)[0]
            if percent == 0:
                current['resists'] += 1
                record(index, action.name + ':resist', 0)
            else:
                target = index if action.effect in ('heal', 'hot') else 1-index
                amount = action.amount * percent // 100
                if action.effect in ('damage', 'heal'):
                    apply(index, target, action.effect, amount, action.name)
                elif action.effect in ('dot', 'hot'):
                    periodic[(index, action.name)] = (index, target, action, amount, now + action.duration_ms)
                elif not actors[target].fear_immune:
                    dest = state[target]
                    dest['fear_until'] = max(dest['fear_until'], now + action.duration_ms)
                    if dest['casting']:
                        dest['cast_token'] += 1
                        dest['casting'] = False
                        dest['interrupts'] += 1
                        dest['busy_until'] = now
                    record(index, action.name, action.duration_ms)
        elif kind == 'think':
            if not current['casting'] and now >= max(current['busy_until'], current['fear_until']):
                for action in actor.actions:
                    if current['cooldown'][action.name] > now or current['hp'] * 1000 > actor.hp * action.hp_below:
                        continue
                    if current['mana'] < action.mana:
                        current['oom_checks'] += 1
                        continue
                    current['cast_token'] += 1
                    current['casting'] = True
                    schedule(now + action.cast_ms, 'finish', index, (current['cast_token'], action))
                    record(index, action.name + ':start', action.mana)
                    break
            # A single decision chain continues through interrupts and controls.
            schedule(now + think_ms, 'think', index)
        if any(s['hp'] <= 0 for s in state):
            break
    outcome = 'death' if state[0]['hp'] <= 0 else 'kill' if state[1]['hp'] <= 0 else 'timeout'
    public = ('hp', 'mana', 'min_hp', 'damage', 'healing', 'overheal', 'mana_spent',
              'mana_regenerated', 'oom_checks', 'casts', 'interrupts', 'resists', 'swings', 'melee_hits')
    result = {'seed': seed, 'outcome': outcome, 'elapsed_ms': now,
              'player': {k:state[0][k] for k in public}, 'enemy': {k:state[1][k] for k in public}}
    if trace:
        result['trace'] = log
    return result

"""Reproducible candidate XP curve; estimates are not live timing measurements."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def report():
    policy = ROOT / 'server-mods/code/common/item_xp_policy.h'
    source = policy.read_text(encoding='utf-8')
    costs = [int(n) for n in re.search(r'costs\[\] = \{([^}]+)', source)[1].replace('* Unit', '').split(',')]
    evidence = ROOT / 'docs/releases/aa-level-progression-20261023/production-before.json'
    rules = json.loads(evidence.read_text())['rules']
    multiplier = float(next(row.split('\t')[2] for row in rules if row.startswith('1\tCharacter:ExpMultiplier\t')))
    rows = []
    for level in (10, 30, 50):
        reference = level * level * 75 * 3.5 * multiplier
        rows.append({'character_level': level, 'reference_kill_xp': reference,
                     'raw_xp_per_transition_at_this_level': [int(reference * cost) for cost in costs]})
    scenarios = []
    for zone_modifier in (0.75, 1.0, 1.5):
        for kills_per_hour in (60, 90, 120):
            scenarios.append({'zone_modifier': zone_modifier,
                              'eligible_solo_white_kills_per_hour': kills_per_hour,
                              'hours_per_transition': [round(cost / zone_modifier / kills_per_hour, 3) for cost in costs],
                              'total_hours': round(sum(costs) / zone_modifier / kills_per_hour, 3)})
    return {
        'status': 'candidate; not deployed or player accepted',
        'owner_target_hours': [4, 8],
        'cost_kill_equivalents': costs,
        'normal_xp_multiplier': multiplier,
        'policy_sha256': hashlib.sha256(policy.read_bytes()).hexdigest(),
        'rule_evidence': str(evidence.relative_to(ROOT)),
        'rule_evidence_sha256': hashlib.sha256(evidence.read_bytes()).hexdigest(),
        'assumptions': [
            'Reference uses native level-squared kill formula and dated 0.65 normal XP multiplier.',
            'Solo white-con kills at character level, no additional XP buffs, hotzone or level modifiers.',
            'Kill rates are modeled assumptions, not measured combat throughput.',
            'Group/raid shares, lower-con rewards and downtime can increase completion time.',
            'Actual integer and float rounding can slightly increase counts, especially at low levels.',
            'Required/recommended item-level gates must prevent low-level farming of endgame items.',
        ],
        'level_examples': rows, 'scenarios': scenarios,
    }


if __name__ == '__main__':
    print(json.dumps(report(), indent=2))

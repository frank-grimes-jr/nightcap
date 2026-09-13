"""Validate the Nagafen melee event control against exact discrete expectations."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

from melee import damage_interval, npc_damage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).parent
    scenario_path = root / 'fixtures/nagafen-melee-control.json'
    raw_scenario = scenario_path.read_bytes()
    scenario = json.loads(raw_scenario)
    results = json.loads(args.results.read_text(encoding='utf-8'))
    if results['scenario_sha256'] != hashlib.sha256(raw_scenario).hexdigest():
        raise ValueError('Results were generated for a different control')
    for name, expected in results['model_sha256'].items():
        if name not in ('encounter.py','melee.py') or hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Model changed since control results were generated')
    if results['runs'] < 1000 or len(results['results']) != results['runs']:
        raise ValueError('At least 1000 complete control trials are required')
    defender, m = scenario['player'], scenario['enemy']['melee']
    # Exact enumeration of independent hit and DI outcomes; scheduling and double
    # attack count are calculated independently of the event runner.
    accuracy, avoidance = m['accuracy'], defender['avoidance']
    hit_probability = sum(min(a, avoidance) + .5*(a < avoidance)
                          for a in range(accuracy)) / (accuracy*avoidance)
    offense, mitigation = m['offense'], defender['mitigation']
    damage_sum = 0
    for atk in range(offense+5):
        for defense in range(mitigation+5):
            interval = damage_interval(offense, mitigation, atk, defense)
            damage_sum += npc_damage(m['minimum'], m['maximum'], interval,
                                     shielding=defender['shielding'],
                                     damage_modifier=defender['incoming_melee_modifier'])
    mean_hit_damage = damage_sum / ((offense+5)*(mitigation+5))
    rounds = scenario['duration_ms']//m['delay_ms'] + 1
    expected_swings = rounds*(1+(m['double_skill']+m['level'])/500)
    expected_damage = expected_swings*hit_probability*mean_hit_damage
    values = [row['enemy']['damage'] for row in results['results']]
    mean_damage = statistics.mean(values)
    standard_error = statistics.stdev(values)/(len(values)**.5)
    z_score = (mean_damage-expected_damage)/standard_error if standard_error else float('inf')
    checks = {
        'all_runs_reach_control_duration':all(r['elapsed_ms']==scenario['duration_ms'] and r['outcome']=='timeout' for r in results['results']),
        'damage_matches_defender_hp_loss':all(defender['hp']-r['player']['hp']==r['enemy']['damage'] for r in results['results']),
        'mean_within_four_standard_errors':abs(z_score) <= 4,
    }
    report = {'status':'pass' if all(checks.values()) else 'fail', 'runs':len(values),
              'checks':checks, 'rounds_per_run':rounds, 'expected_swings':expected_swings,
              'exact_hit_probability':hit_probability, 'exact_mean_damage_per_hit':mean_hit_damage,
              'expected_total_damage':expected_damage, 'observed_mean_total_damage':mean_damage,
              'observed_mean_swings':statistics.mean(r['enemy']['swings'] for r in results['results']),
              'sample_standard_error':standard_error, 'z_score':z_score,
              'results_sha256':hashlib.sha256(args.results.read_bytes()).hexdigest(),
              'scope':'Event integration of the isolated melee control; not complete combat or a BiS encounter'}
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return int(not all(checks.values()))


if __name__ == '__main__':
    raise SystemExit(main())

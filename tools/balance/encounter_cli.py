"""Run repeatable diagnostic encounter scenarios and report conditional outcomes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics

from encounter import Action, Actor, simulate
from melee import Melee


def parse_actor(data):
    data = dict(data)
    data['actions'] = tuple(Action(**a) for a in data.get('actions', ()))
    if data.get('melee') is not None:
        data['melee'] = Melee(**data['melee'])
    return Actor(**data)


def distribution(values):
    if not values:
        return None
    ordered = sorted(values)
    def percentile(fraction):
        index = (len(ordered)-1) * fraction
        left = int(index)
        return ordered[left] + (ordered[min(left+1, len(ordered)-1)]-ordered[left]) * (index-left)
    return {'count':len(values), 'min':min(values), 'p10':percentile(.1),
            'median':statistics.median(values), 'mean':statistics.mean(values),
            'p90':percentile(.9), 'max':max(values)}


def run_trials(scenario, runs, first_seed, *, keep_trace=False):
    if scenario.get('schema_version') != 1 or scenario.get('status') != 'diagnostic':
        raise ValueError('Expected version 1 diagnostic scenario')
    if not scenario.get('assumptions') or not isinstance(scenario['assumptions'], list):
        raise ValueError('Scenario must explicitly declare its assumptions and omissions')
    if runs <= 0:
        raise ValueError('At least one trial is required')
    player, enemy = parse_actor(scenario['player']), parse_actor(scenario['enemy'])
    results = [simulate(player, enemy, seed=first_seed+i,
                        duration_ms=scenario.get('duration_ms', 600000),
                        think_ms=scenario.get('think_ms', 100),
                        tick_ms=scenario.get('tick_ms', 6000),
                        level_check=scenario.get('level_check', -1),
                        level_bonus=scenario.get('level_bonus', 0.0),
                        trace=keep_trace and i == 0) for i in range(runs)]
    counts = Counter(r['outcome'] for r in results)
    return {'status':'Diagnostic model results; not certified live encounter predictions',
            'assumptions':scenario['assumptions'], 'first_seed':first_seed, 'runs':runs,
            'outcomes':{k:counts[k] for k in ('kill','death','timeout')},
            'kill_time_ms':distribution([r['elapsed_ms'] for r in results if r['outcome']=='kill']),
            'death_time_ms':distribution([r['elapsed_ms'] for r in results if r['outcome']=='death']),
            'remaining_player_mana':distribution([r['player']['mana'] for r in results]),
            'results':results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runs', type=int, default=100)
    parser.add_argument('--seed', type=int, default=20260912)
    parser.add_argument('--trace', action='store_true', help='Keep the first trial event trace')
    args = parser.parse_args()
    raw = args.scenario.read_bytes()
    report = run_trials(json.loads(raw), args.runs, args.seed, keep_trace=args.trace)
    report['scenario_sha256'] = hashlib.sha256(raw).hexdigest()
    report['model_sha256'] = {name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                              for name in ('encounter.py','melee.py')}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='results'}, indent=2))


if __name__ == '__main__':
    main()

"""Verify native AA timer restoration without changing ordinary preparation buffs."""
import argparse
import gzip
import json
from pathlib import Path

from active_aa_controls import run, verify_case as verify_aa_case


# Native raw duration and the already captured focus modifiers. effects.cpp
# GetActSpellDuration truncates 11 * 1.8 to odd 19, while 20 * 1.8 is exactly 36.
EXPECTED_TICKS = {4925: 11, 23617: 19, 27436: 20, 31534: 21, 5245: 20, 5247: 36}


def verify_case(case, report):
    probe = report['aa_probe']
    if '-preparation-' not in case['id']:
        summary = verify_aa_case(case, report)
        for action in probe['actions']:
            if not action['started'] or action['spell'] not in EXPECTED_TICKS:
                continue
            buff = next(b for b in action['after']['buffs'] if b['spell'] == action['spell'])
            if buff['ticks'] != EXPECTED_TICKS[action['spell']]:
                raise ValueError('Activated AA did not retain native duration/focus rounding')
            if action['spell'] in (4925, 27436, 31534) and any(
                    b['spell'] == action['spell'] for b in probe['trace'][-1]['buffs']):
                raise ValueError('Expected temporary AA expiry was not observed')
        return summary
    wanted = case['input']['aa_probe']
    build = report['builds'][0]
    if ([p['rank_id'] for p in build['aa_purchases']] != case['input']['builds'][0]['aa_rank_ids']
            or report['native_rng_seed'] != case['seed'] or len(probe['actions']) != 1
            or probe['result'] != 'duration' or probe['trace'][-1]['ms'] != wanted['duration_ms']):
        raise ValueError('Preparation control identity or lifecycle changed')
    action = probe['actions'][0]
    spell = wanted['actions'][0]['spell_id']
    if action['spell'] != spell or action['ms'] != 50 or not action['started']:
        raise ValueError('Preparation cast was not accepted')
    buffs = [b for s in probe['trace'] for b in s['buffs'] if b['spell'] == spell]
    # Trace samples are 500 ms apart. A six-second buff tick can run between
    # native cast completion and the first sample that observes the new buff.
    if not buffs or max(b['ticks'] for b in buffs) < 999999:
        raise ValueError('Ordinary self-buff lost its long duration')
    if not any(b['spell'] == spell for b in probe['trace'][-1]['buffs']):
        raise ValueError('Ordinary preparation buff unexpectedly expired')
    if not any(s['mana'] < probe['trace'][0]['mana'] for s in probe['trace']):
        raise ValueError('Preparation cast did not consume mana')
    return {'id': case['id'], 'spell': spell, 'maximum_observed_ticks': max(b['ticks'] for b in buffs),
            'final_hp': probe['trace'][-1]['hp'], 'final_max_hp': probe['trace'][-1]['max_hp']}


def verify(matrix, evidence, baseline):
    cases = {c['id']: c for c in matrix['cases']}
    runs = {r['id']: r for r in evidence['runs']}
    old = {r['id']: r for r in baseline['runs']}
    if (len(cases) != 18 or len(runs) != len(evidence['runs']) or cases.keys() != runs.keys()):
        raise ValueError('Incomplete or duplicate duration controls')
    summaries = []
    unchanged = []
    for name, case in cases.items():
        report = runs[name]['report']
        summaries.append(verify_case(case, report))
        if name in old:
            if report['builds'] != old[name]['report']['builds']:
                raise ValueError('AA duration comparison changed gear, purchases or skills')
            if name.endswith(('-idle', '-frenzied', '-arbitration')):
                if report != old[name]['report']:
                    raise ValueError('Unrelated lifecycle changed')
                unchanged.append(name)
    return {'controls': summaries, 'unchanged_native_controls': unchanged}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    matrix = json.loads(args.inputs.read_text())
    if args.run:
        run(matrix, args.output, verify_case)
    else:
        result = verify(matrix, json.loads(gzip.decompress(args.verify.read_bytes())),
                        json.loads(gzip.decompress(args.baseline.read_bytes())))
        args.output.write_bytes((json.dumps(result, indent=2)+'\n').encode())
        print('Verified 18 native duration controls and unchanged gear/AA allocations')


if __name__ == '__main__':
    main()

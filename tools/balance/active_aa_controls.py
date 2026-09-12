"""Native activated-AA lifecycle controls, separate from boss balance estimates."""
import argparse
import copy
import gzip
import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path('/tmp/nightcap-balance-20260912')


def prepare_encounters(encounters):
    cases = []
    for source in encounters['cases']:
        if source['input']['builds'][0]['gear_control'] != 'ring41':
            continue
        for policy in ('burst', 'burst_regeneration', 'burst_tenacity'):
            case = copy.deepcopy(source)
            case['id'] += '-' + policy
            case['input']['encounter']['active_aa_policy'] = policy
            cases.append(case)
    return {'scope': 'Native candidate encounters with explicit once-per-fight activated AA policies; no preparation buffs or certified full BiS.',
            'cases': cases}


def verify_encounter(case, report):
    from encounter_matrix import summarize
    summary = summarize(case, report)
    encounter = report['encounter']
    policy = case['input']['encounter']['active_aa_policy']
    active = encounter['activated_aa']
    if active['policy'] != policy:
        raise ValueError('Wrong active-AA policy')
    owned = {}
    for p in report['builds'][0]['aa_purchases']:
        owned[p['ability_id']] = p['rank_id']
    allowed = [515, 308] + ({'burst': [], 'burst_regeneration': [38], 'burst_tenacity': [300]}[policy])
    actions = active['actions']
    ids = [a['ability_id'] for a in actions]
    if len(set(ids)) != len(ids) or ids != [i for i in allowed if i in ids]:
        raise ValueError('Repeated or out-of-order active AA')
    for ability in (515, 308):
        if ability in owned and ability not in ids:
            raise ValueError('Missing owned opening AA')
    for a in actions:
        if owned.get(a['ability_id']) != a['rank_id'] or not 0 < a['ms'] <= encounter['elapsed_ms']:
            raise ValueError('Unowned rank or invalid activation time')
        if a['ability_id'] in (38, 300) and a['before']['hp'] * 100 >= a['before']['max_hp'] * 80:
            raise ValueError('Sustain requested above its health threshold')
        if a['before']['casting'] or a['timer_before']:
            raise ValueError('AA requested while already casting or cooling down')
        if a['ability_id'] == 38:
            if a['started'] or a['after'] != a['before'] or not any(
                    e['type'] == 'message' and e['ms'] == a['ms'] and e['string_id'] == 197
                    for e in encounter['events']):
                raise ValueError('Regeneration rejection differs from lifecycle controls')
        elif not a['started'] or a['timer_after'] != a['effective_recast_seconds']:
            raise ValueError('Opening/sustain AA did not activate')
    twins = [a for a in actions if a['ability_id'] == 515]
    observed_decrements = 0
    if twins:
        twin = twins[0]
        buff = next(b for b in twin['after']['buffs'] if b['spell'] == twin['spell'])
        after = [s['aa_state'] for s in encounter['trace'] if s['ms'] > twin['ms']]
        remaining = [next((b['hits'] for b in s['buffs'] if b['spell'] == twin['spell']), None) for s in after]
        present = [buff['hits']] + [hits for hits in remaining if hits is not None]
        if len(present) < 2 or buff['hits'] <= 0 or any(a < b for a, b in zip(present, present[1:])):
            raise ValueError('Invalid Twincast charge lifecycle')
        # A disappearing buff could be dispelled. Only count directly observed
        # decrements while present, rather than assuming every missing charge was used.
        observed_decrements = buff['hits'] - min(present)
    return summary | {'active_policy': policy, 'aa_requested': len(actions),
                      'aa_started': sum(a['started'] for a in actions),
                      'twincast_observed_charge_decrements': observed_decrements}


def verify_encounters(matrix, evidence):
    cases = {c['id']: c for c in matrix['cases']}
    runs = {r['id']: r for r in evidence['runs']}
    if (len(cases) != len(matrix['cases']) or len(runs) != len(evidence['runs'])
            or cases.keys() != runs.keys()):
        raise ValueError('Incomplete, duplicate or unexpected encounters')
    summaries = []
    for key, case in cases.items():
        summary = verify_encounter(case, runs[key]['report'])
        if json.loads(json.dumps(summary)) != runs[key]['summary']:
            raise ValueError('Stored active-AA summary differs from native report')
        summaries.append(summary)
    return summaries


def prepare(encounters, catalog):
    ranks = {r['rank_id']: r for b in catalog['builds'] if b['profile'] == 'war-clr-wiz'
             for r in b['aa_catalog']}
    cases = []
    for stage, policy in [('200', 'balanced'), ('all', 'purchase_closure')]:
        source = next(c for c in encounters['cases']
                      if c['id'] == f'73057-ring41-{stage}-{policy}-1729')
        build = copy.deepcopy(source['input']['builds'][0])
        owned = {}
        for rank_id in build['aa_rank_ids']:
            rank = ranks[rank_id]
            owned[rank['ability_id']] = rank
        for name, abilities in [('idle', []), ('tenacity', [300, 38, 300]),
                                ('regeneration', [38, 300, 38]),
                                ('frenzied', [308, 308]), ('twincast', [515, 515]),
                                ('arbitration', [169, 169]), ('burst', [515, 308])]:
            actions = [{'ms': ms, 'rank_id': owned[a]['rank_id']}
                       for ms, a in zip([50, 2500, 5000], abilities)]
            cases.append({'id': f'{stage}-{name}', 'seed': 1729,
                          'input': {'builds': [build], 'aa_probe': {
                              'duration_ms': 150000, 'initial_hp_percent': 40, 'actions': actions}}})
    return {'scope': 'Same gear and purchased AAs; isolated solo AA lifecycle controls.',
            'cases': cases}


def verify_case(case, report):
    probe = report['aa_probe']
    build = report['builds'][0]
    expected = case['input']['aa_probe']
    if report['native_rng_seed'] != case['seed']:
        raise ValueError('Wrong native seed')
    if [p['rank_id'] for p in build['aa_purchases']] != case['input']['builds'][0]['aa_rank_ids']:
        raise ValueError('AA purchases changed')
    trace, actions = probe['trace'], probe['actions']
    finished = probe['result'] == 'duration' and trace[-1]['ms'] == expected['duration_ms']
    tenacity_death = (any(a['ability_id'] == 300 and a['started'] for a in actions)
                     and probe['result'] == 'player_death'
                     and 0 < trace[-1]['ms'] < expected['duration_ms'] and trace[-1]['hp'] <= 0)
    if trace[0]['ms'] != 0 or not (finished or tenacity_death):
        raise ValueError('Incomplete AA lifecycle')
    if any(a['ms'] >= b['ms'] for a, b in zip(trace, trace[1:])):
        raise ValueError('Non-monotonic probe clock')
    if (trace[0]['hp'] != build['hp'] * expected['initial_hp_percent'] // 100
            or trace[0]['mana'] != build['mana'] or trace[0]['buffs']):
        raise ValueError('Invalid initial resources or buffs')
    if len(actions) != len(expected['actions']):
        raise ValueError('Missing AA action')
    groups = {}
    for wanted, action in zip(expected['actions'], actions):
        if any(wanted[k] != action[k] for k in ('ms', 'rank_id')):
            raise ValueError('Wrong activation identity/time')
        group = action['cooldown_group']
        blocked = group in groups
        if not blocked and action['ability_id'] == 38:
            # Captured AA spell levels are 254. The enabled native target buff
            # gate rejects this group spell at level 50 even though its AA is owned.
            messages = [e['string_id'] for e in probe['events']
                        if e['type'] == 'message' and e['ms'] == action['ms']]
            if (action['started'] or action['timer_before'] or action['timer_after']
                    or action['before'] != action['after'] or 197 not in messages
                    or action['spell_minimum_level'] != 254
                    or not action['buff_level_restrictions'] or action['target_type'] != 3):
                raise ValueError('Regeneration target-level rejection not established')
            continue
        if action['started'] == blocked:
            raise ValueError('Native acceptance disagrees with shared cooldown control')
        if blocked:
            if action['timer_before'] <= 0 or action['timer_after'] != action['timer_before']:
                raise ValueError('Blocked activation changed its native cooldown')
            if action['before'] != action['after']:
                raise ValueError('Blocked activation changed resources, casting or buffs')
        else:
            if action['timer_before'] or action['effective_recast_seconds'] <= 0:
                raise ValueError('Fresh activation was not ready')
            if not action['after']['casting'] and action['timer_after'] != action['effective_recast_seconds']:
                raise ValueError('Instant activation did not start the native cooldown')
            groups[group] = action
    return {'id': case['id'], 'requested': len(actions),
            'started': sum(a['started'] for a in actions),
            'initial_hp': trace[0]['hp'], 'final_hp': trace[-1]['hp'],
            'maximum_hp_cap': max(s['max_hp'] for s in trace),
            'minimum_hp': min(s['hp'] for s in trace),
            'final_buffs': trace[-1]['buffs']}


def verify(matrix, evidence):
    cases = {c['id']: c for c in matrix['cases']}
    runs = {r['id']: r for r in evidence['runs']}
    if (len(cases) != len(matrix['cases']) or len(runs) != len(evidence['runs'])
            or cases.keys() != runs.keys()):
        raise ValueError('Incomplete, duplicate or unexpected controls')
    summaries = [verify_case(cases[key], runs[key]['report']) for key in cases]
    # Divine Arbitration needs a group. With this solo fixture it must have no
    # resource effect relative to the identical no-action control, despite cooldown use.
    for stage in ('200', 'all'):
        idle = runs[f'{stage}-idle']['report']['aa_probe']['trace']
        arbitration = runs[f'{stage}-arbitration']['report']['aa_probe']['trace']
        sampled = {s['ms']: s for s in arbitration}
        for state in idle:
            other = sampled[state['ms']]
            if any(state[k] != other[k] for k in ('hp', 'max_hp', 'mana', 'buffs')):
                raise ValueError('Solo arbitration unexpectedly changes resources')
    return summaries


def run(matrix, output):
    if Path.cwd().resolve() != ROOT or output.resolve().parent != ROOT or output.exists():
        raise ValueError('Run in the isolated runtime with a new output path')
    binary = ROOT / 'balance-zone'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != matrix['binary_sha256']:
        raise ValueError('Diagnostic binary changed')
    runs = []
    for case in matrix['cases']:
        source, target = ROOT/'active-aa-case-input.json', ROOT/'active-aa-case-output.json'
        source.write_text(json.dumps(case['input']))
        result = subprocess.run([str(binary), 'tests:balance', str(source), str(target)],
                                env=os.environ | {'NIGHTCAP_BALANCE_RNG_SEED': str(case['seed'])},
                                capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise RuntimeError(f'{case["id"]}: {result.stderr[-2000:]}')
        raw = target.read_bytes()
        report = json.loads(raw)
        summary = (verify_case if 'aa_probe' in case['input'] else verify_encounter)(case, report)
        runs.append({'id': case['id'], 'native_raw_sha256': hashlib.sha256(raw).hexdigest(),
                     'summary': summary, 'report': report})
        output.write_bytes(gzip.compress(json.dumps({'scope': matrix['scope'], 'runs': runs}, separators=(',', ':')).encode(), mtime=0))
        print(json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    matrix = json.loads(args.inputs.read_text())
    if args.run:
        run(matrix, args.output)
    elif args.verify:
        checker = verify if 'aa_probe' in matrix['cases'][0]['input'] else verify_encounters
        result = checker(matrix, json.loads(gzip.decompress(args.verify.read_bytes())))
        args.output.write_bytes((json.dumps({'controls': result}, indent=2)+'\n').encode())
        print(f'Verified {len(result)} native activated-AA controls')
    else:
        parser.error('Choose --run or --verify')


if __name__ == '__main__':
    main()

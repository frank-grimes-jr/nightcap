"""Run reproducible candidate gear/AA encounters in the existing isolated native runtime."""
import argparse
import copy
import gzip
import hashlib
import json
import os
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path('/tmp/nightcap-balance-20260912')
BINARY_SHA256 = '84af2efdaffb601c9e2634b3791a5354b2a05dd0f9ef003ea2eb252d1e6783e1'
SCOPE = ('Candidate WAR/CLR/WIZ weapon/haste matrix with native purchased AA bonuses. '
         'Fixed nuke/self-heal controller; no preparation buffs or activated AAs. '
         'Three seeds per AA scenario are exploratory, not a win-rate estimate or full BiS certification.')


def prepare(gear_inputs, tables, encounters):
    items = {i['id']: i for i in tables['items']}
    weapon = items[608079]
    sources = [s for s in tables['drop_sources'] if s['item_id'] == 8079]
    if not sources or weapon['damage'] != 22 or weapon['delay'] != 29:
        raise ValueError('Expected captured Sabertooth weapon control')
    cases = []
    for source in gear_inputs['builds']:
        if source['profile'] != 'war-clr-wiz' or source['tier'].startswith('isolated/'):
            continue
        variant = source['gear_control']
        if variant == 'ring41_cloak36':
            continue
        if variant != 'ring41' and source['aa_stage'] != '0':
            continue
        build = copy.deepcopy(source)
        primary = next(e for e in build['equipment'] if e['slot'] == 13)
        primary.clear()
        primary.update({'slot': 13, 'id': weapon['id'], 'name': weapon['name'], 'base_id': 8079,
                        'drop_provenance': sources})
        for npc_id, encounter in encounters.items():
            for seed in ((1729, 1730, 1731) if variant == 'ring41' else (1729,)):
                identity = f'{npc_id}-{variant}-{build["aa_stage"]}-{build["aa_policy"]}-{seed}'
                cases.append({'id': identity, 'seed': seed,
                              'input': {'builds': [build], 'encounter': encounter | {'duration_ms': 900000}}})
    if not cases or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Empty or duplicate encounter matrix')
    return {'scope': SCOPE, 'binary_sha256': BINARY_SHA256, 'cases': cases}


def summarize(case, report):
    """Validate encounter/accounting structure without requiring a random boss spell to fire."""
    build = case['input']['builds'][0]
    if len(report['builds']) != 1:
        raise ValueError('Expected one resolved player')
    player = report['builds'][0]
    if [p['rank_id'] for p in player['aa_purchases']] != build['aa_rank_ids']:
        raise ValueError('Native purchases differ from requested allocation')
    if (player['profile'], player['tier'], player['aa_stage'], player['aa_policy']) != (
            build['profile'], build['tier'], build['aa_stage'], build['aa_policy']):
        raise ValueError('Native build identity mismatch')
    encounter = report['encounter']
    if encounter['npc_id'] != case['input']['encounter']['npc_id'] or report['native_rng_seed'] != case['seed']:
        raise ValueError('Native target or seed mismatch')
    state, trace = encounter['initial_state'], encounter['trace']
    player_id, boss_id = encounter['player_entity_id'], encounter['npc_entity_id']
    if not player_id or not boss_id or player_id == boss_id or state['npc_hate_target'] != player_id:
        raise ValueError('Invalid actor/engagement identity')
    if not all(state[k] for k in ('zone_loaded', 'npc_ai', 'npc_engaged', 'npc_has_spells',
                                  'can_combat', 'npc_can_attack', 'player_can_attack')):
        raise ValueError('Invalid native initial combat state')
    if any(state[k] for k in ('player_dead', 'player_zoning', 'player_destroying')):
        raise ValueError('Player cannot begin the encounter')
    if (trace[0]['ms'] != 0 or trace[0]['npc_hp'] != 32000
            or trace[0]['player_hp'] != player['hp'] or trace[0]['player_mana'] != player['mana']):
        raise ValueError('Unexpected initial resources')
    elapsed = encounter['elapsed_ms']
    if (trace[-1]['ms'] != elapsed or not 0 < elapsed <= case['input']['encounter']['duration_ms']
            or any(a['ms'] >= b['ms'] for a, b in zip(trace, trace[1:]))):
        raise ValueError('Incomplete or non-monotonic encounter clock')
    result = encounter['result']
    last = trace[-1]
    if result == 'npc_death':
        valid_end = last['npc_hp'] <= 0 and last['player_hp'] > 0
    elif result == 'player_death':
        valid_end = last['player_hp'] <= 0
    elif result == 'timeout':
        valid_end = elapsed == case['input']['encounter']['duration_ms'] and min(last['npc_hp'], last['player_hp']) > 0
    else:
        valid_end = False
    if not valid_end:
        raise ValueError('Invalid terminal state')
    events = encounter['events']
    melee = lambda source: sum(e['type'] == 'damage' and e['source'] == source
                               and e['spell'] == 65535 and e['damage'] > 0 for e in events)
    boss_melee, player_melee = melee(boss_id), melee(player_id)
    if not boss_melee or not player_melee:
        raise ValueError('Missing native melee activity for weapon-equipped encounter')
    spells = Counter(e['spell'] for e in events if e['source'] == boss_id and e['type'] == 'begin_cast')
    return {'id': case['id'], 'npc_id': encounter['npc_id'], 'seed': case['seed'],
            'gear': build['gear_control'], 'aa_stage': build['aa_stage'], 'aa_policy': build['aa_policy'],
            'aa_spent': player['aa_spent'], 'initial_hp': player['hp'], 'initial_mana': player['mana'],
            'haste': player['haste'], 'result': result, 'elapsed_ms': elapsed,
            'final_player_hp': last['player_hp'], 'final_player_mana': last['player_mana'],
            'final_npc_hp': last['npc_hp'], 'minimum_sampled_player_hp': min(s['player_hp'] for s in trace),
            'boss_positive_melee_events': boss_melee, 'player_positive_melee_events': player_melee,
            'boss_casts': dict(spells), 'sampled_fear_states': sum(s['feared'] for s in trace)}


def run(matrix, output):
    if Path.cwd().resolve() != ROOT or output.resolve().parent != ROOT or output.exists():
        raise ValueError('Use the isolated runtime and a new output path directly within it')
    binary = ROOT / 'balance-zone'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != matrix['binary_sha256']:
        raise ValueError('Native binary differs from reviewed build')
    runs = []
    for case in matrix['cases']:
        input_path = ROOT / 'matrix-case-input.json'
        result_path = ROOT / 'matrix-case-output.json'
        input_path.write_text(json.dumps(case['input']))
        # A fresh process per case resets native RNG, clocks, mobs, AA and spell state.
        completed = subprocess.run([str(binary), 'tests:balance', str(input_path), str(result_path)],
                                   env=os.environ | {'NIGHTCAP_BALANCE_RNG_SEED': str(case['seed'])},
                                   capture_output=True, text=True, timeout=120)
        if completed.returncode:
            raise RuntimeError(f'Native case {case["id"]} failed: {completed.stderr[-2000:]}')
        raw = result_path.read_bytes()
        report = json.loads(raw)
        summary = summarize(case, report)
        runs.append({'id': case['id'], 'native_raw_sha256': hashlib.sha256(raw).hexdigest(),
                     'summary': summary, 'report': report})
        # Persist completed evidence after each case; no resumptions/restarts are inferred.
        output.write_bytes(gzip.compress(json.dumps({'scope': SCOPE, 'runs': runs}, separators=(',', ':')).encode(), mtime=0))
        print(json.dumps(summary), flush=True)


def verify_matrix(matrix, evidence):
    cases = {c['id']: c for c in matrix['cases']}
    runs = {r['id']: r for r in evidence['runs']}
    if (len(cases) != len(matrix['cases']) or len(runs) != len(evidence['runs'])
            or cases.keys() != runs.keys()):
        raise ValueError('Incomplete, duplicate, or unexpected encounter cases')
    summaries = []
    for identity, case in cases.items():
        run = runs[identity]
        summary = summarize(case, run['report'])
        # JSON object keys (spell IDs) become strings on disk.
        if json.loads(json.dumps(summary)) != run['summary']:
            raise ValueError('Stored summary does not match native trace')
        summaries.append(summary)
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--boss-inputs', type=Path, nargs=2)
    args = parser.parse_args()
    data = json.loads(args.inputs.read_text())
    if args.run:
        run(data, args.output)
    elif args.verify:
        raw = args.verify.read_bytes()
        summaries = verify_matrix(data, json.loads(gzip.decompress(raw)))
        output = {'scope': SCOPE, 'case_count': len(summaries), 'cases': summaries,
                  'matrix_inputs_sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest(),
                  'evidence_sha256': hashlib.sha256(raw).hexdigest(), 'binary_sha256': data['binary_sha256']}
        args.output.write_bytes((json.dumps(output, indent=2) + '\n').encode())
        print(f'Verified {len(summaries)} complete native encounter records')
    else:
        from builds import load_snapshot
        snapshot, manifest = load_snapshot(args.snapshot)
        encounters = {}
        for path in args.boss_inputs:
            e = json.loads(path.read_text())['encounter']
            encounters[e['npc_id']] = e
        data = prepare(data, snapshot['tables'], encounters)
        data['snapshot_sha256'] = manifest['snapshot_sha256']
        data['gear_inputs_sha256'] = hashlib.sha256(args.inputs.read_bytes()).hexdigest()
        args.output.write_bytes((json.dumps(data, indent=2) + '\n').encode())
        print(f'Prepared {len(data["cases"])} native encounter cases')


if __name__ == '__main__':
    main()

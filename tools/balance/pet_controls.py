"""Native pet ownership controls; expose engine failures without certifying balance."""
import argparse
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('/tmp/nightcap-balance-20260912')


def assess_ownership(state, owner_id, expected_spells):
    pets = state['pets']
    ids = [p['entity_id'] for p in pets]
    refs = [r['entity_id'] for r in state['class_pets'] if r['entity_id']]
    if state['primary_pet']:
        refs.append(state['primary_pet'])
    dangling = sorted(set(refs) - set(ids))
    untracked = sorted(set(ids) - set(refs))
    wrong_owner = sorted(p['entity_id'] for p in pets if p['owner_id'] != owner_id)
    depopping = sorted(p['entity_id'] for p in pets if p['depop'])
    spells = sorted(p['spell'] for p in pets)
    ready = (not dangling and not untracked and not wrong_owner and not depopping
             and len(ids) == len(set(ids)) and len(refs) == len(set(refs))
             and spells == sorted(expected_spells))
    return {'ready': ready, 'pet_spells': spells, 'expected_spells': sorted(expected_spells),
            'dangling_references': dangling, 'untracked_pets': untracked,
            'wrong_owner_pets': wrong_owner, 'depopping_pets': depopping}


def prepare(gear, aa_inputs, binary_sha256):
    base = next(b for b in gear['builds'] if b['profile'] == 'mag-nec-shm'
                and b['tier'] == 'captured_drops/balanced/shield/unforced')
    allocations = {b['aa_stage']: b for b in aa_inputs['builds']
                   if b['profile'] == 'mag-nec-shm'
                   and b['aa_policy'] in ('common_free', 'balanced', 'purchase_closure')}
    cases = []

    def add(identity, stage, spells, expected, *, naked=False, reagents=True, buff=False):
        build = copy.deepcopy(base)
        for key in ('aa_budget', 'aa_rank_ids', 'aa_stage', 'aa_policy'):
            build[key] = allocations[stage][key]
        if naked:
            build['equipment'] = []
            build['tier'] = 'isolated/no-equipment'
        actions = [{'spell': s} for s in spells]
        if buff:
            actions.append({'spell': 107, 'target_class': 13})
        supplies = [{'id': 10015, 'count': 10}, {'id': 13073, 'count': 10}] if reagents else []
        cases.append({'id': identity, 'seed': 1729, 'expected_spells': expected,
                      'input': {'builds': [build], 'export_equipment': True,
                                'pet_probe': {'reagents': supplies, 'actions': actions}}})

    add('mage-missing-reagent', '0', [633], [], naked=True, reagents=False)
    add('mage-with-reagent', '0', [633], [633], naked=True)
    add('necro-only', '0', [443], [443])
    add('shaman-only', '0', [166], [166])
    add('mage-repeat', '0', [633, 633], [633])
    add('mage-shaman', '0', [633, 166], [633, 166])
    add('shaman-mage', '0', [166, 633], [633, 166])
    add('necro-mage-shaman', '0', [443, 633, 166], [633, 443, 166])
    for stage in ('0', '100', '200', '500', 'all'):
        add('triple-' + stage, stage, [633, 443, 166], [633, 443, 166], buff=True)
    for method in ('owner', 'owner_or_self'):
        add('unregistered-' + method, '0', [633, 443, 166], [633, 166])
        cases[-1]['input']['pet_probe']['owner_lookup_control'] = method
    return {'scope': 'Summon/ownership/reagent/buff controls with matched gear; open-pool AA sensitivity only, not release balance.',
            'binary_sha256': binary_sha256, 'cases': cases}


def summarize(case, report):
    from augment_controls import verify_equipment
    build = case['input']['builds'][0]
    if len(report['builds']) != 1 or report['native_rng_seed'] != case['seed']:
        raise ValueError('Pet control actor/seed mismatch')
    player = report['builds'][0]
    verify_equipment(case['input'], report)
    if ([p['rank_id'] for p in player['aa_purchases']] != build['aa_rank_ids']
            or player['profile'] != build['profile'] or player['tier'] != build['tier']
            or player['aa_budget'] != build['aa_budget']
            or player['aa_spent'] != sum(p['cost'] for p in player['aa_purchases'])
            or player['aa_remaining'] != build['aa_budget'] - player['aa_spent']):
        raise ValueError('Pet control build/purchase mismatch')
    probe = report['pet_probe']
    if probe['input'] != case['input']['pet_probe'] or [a['input'] for a in probe['actions']] != probe['input']['actions']:
        raise ValueError('Pet control action mismatch')
    if probe['initial']['pets'] or probe['final']['ms'] < 12000:
        raise ValueError('Pet control did not start empty and process its settling period')
    if 'owner_lookup_control' in probe['input']:
        control = probe['owner_lookup_control']
        expected = 0 if control['method'] == 'owner' else control['pet_id']
        if (not control['registered_owner'] or not control['registered_owner_or_self']
                or control['unregistered_result'] != expected or control['unregistered_owner_id']
                or not control['unregistered_depop']):
            raise ValueError('Native owner lookup changed registered/orphan semantics')
    return {'id': case['id'], 'aa_spent': player['aa_spent'],
            'assessment': assess_ownership(probe['final'], probe['player_entity_id'], case['expected_spells']),
            'pets': probe['final']['pets']}


def run(matrix, output):
    if Path.cwd().resolve() != ROOT or output.resolve().parent != ROOT or output.exists():
        raise ValueError('Use a new output in the isolated runtime')
    binary = ROOT/'balance-zone'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != matrix['binary_sha256']:
        raise ValueError('Native pet binary provenance differs')
    runs = []
    for case in matrix['cases']:
        source, result = ROOT/'pet-case-input.json', ROOT/'pet-case-output.json'
        source.write_text(json.dumps(case['input']), encoding='utf-8')
        completed = subprocess.run([str(binary), 'tests:balance', str(source), str(result)],
                                   env=os.environ | {'NIGHTCAP_BALANCE_RNG_SEED': str(case['seed'])},
                                   capture_output=True, text=True, timeout=120)
        if completed.returncode:
            raise RuntimeError(f"Native pet case {case['id']} failed: {completed.stderr[-2000:]}")
        raw = result.read_bytes()
        report = json.loads(raw)
        summary = summarize(case, report)
        runs.append({'id': case['id'], 'native_raw_sha256': hashlib.sha256(raw).hexdigest(),
                     'summary': summary, 'report': report})
        output.write_bytes(gzip.compress(json.dumps({'runs': runs}, separators=(',', ':')).encode(), mtime=0))
        print(json.dumps({k: v for k, v in summary.items() if k != 'pets'}), flush=True)


def verify(matrix, evidence):
    cases = {c['id']: c for c in matrix['cases']}
    runs = {r['id']: r for r in evidence['runs']}
    if len(cases) != len(matrix['cases']) or len(runs) != len(evidence['runs']) or cases.keys() != runs.keys():
        raise ValueError('Incomplete, duplicate or unexpected pet controls')
    for identity, case in cases.items():
        if summarize(case, runs[identity]['report']) != runs[identity]['summary']:
            raise ValueError('Pet summary differs from native report')
    return [r['summary'] for r in evidence['runs']]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    matrix = json.loads(args.inputs.read_text(encoding='utf-8'))
    if args.run:
        run(matrix, args.output)
    else:
        summaries = verify(matrix, json.loads(gzip.decompress(args.verify.read_bytes())))
        args.output.write_bytes((json.dumps({'cases': summaries}, indent=2)+'\n').encode())
        print(f'Verified {len(summaries)} reports; {sum(s["assessment"]["ready"] for s in summaries)} have the expected owned pet roster')

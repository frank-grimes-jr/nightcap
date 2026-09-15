"""Native socket-loading controls in the isolated balance runtime."""
import argparse
import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path

from gear_haste_controls import recommended_bonus

ROOT = Path('/tmp/nightcap-balance-20260912')


def prepare(templates):
    template = next(b for b in templates['builds'] if b['profile'] == 'war-clr-wiz' and b['aa_budget'] == 0)
    builds = []
    for name, entries in (
        ('helmet', [{'slot': 2, 'id': 601549}]),
        ('helmet_hp', [{'slot': 2, 'id': 601549, 'augments': [{'socket': 0, 'id': 651903}]}]),
        ('helmet_mana', [{'slot': 2, 'id': 601549, 'augments': [{'socket': 0, 'id': 679626}]}]),
        ('ring', [{'slot': 15, 'id': 609959}]),
        ('ring_hp', [{'slot': 15, 'id': 609959, 'augments': [{'socket': 0, 'id': 651903}]}]),
        ('ring_mana', [{'slot': 15, 'id': 609959, 'augments': [{'socket': 0, 'id': 679626}]}]),
    ):
        build = copy.deepcopy(template)
        build['equipment'] = entries
        build['tier'] = name
        build.pop('spell_probes', None)
        builds.append(build)
    return {'export_equipment': True, 'builds': builds}


def verify_equipment(inputs, report):
    if len(inputs['builds']) != len(report['builds']):
        raise ValueError('Native build count changed')
    for wanted, observed in zip(inputs['builds'], report['builds']):
        if (wanted['profile'], wanted['tier']) != (observed['profile'], observed['tier']):
            raise ValueError('Native build identity changed')
        normalize = lambda entries: sorted(
            [(e['slot'], e['id'], sorted((a['socket'], a['id']) for a in e.get('augments', [])))
             for e in entries])
        if normalize(wanted['equipment']) != normalize(observed['equipped_items']):
            raise ValueError('Native equipment/socket state differs from requested loadout')


def verify(inputs, report):
    verify_equipment(inputs, report)
    rows = {b['tier']: b for b in report['builds']}
    checks = []
    for parent, rec in (('helmet', 0), ('ring', 62)):
        for suffix, stat, raw, req in (('hp', 'item_hp', 12, 20), ('mana', 'item_mana', 24, 25)):
            augmented = rows[parent+'_'+suffix]
            delta = augmented[stat] - rows[parent][stat]
            expected = recommended_bonus(raw, 50, rec)
            if delta != expected:
                raise ValueError('Augment stats did not use native parent recommended level')
            item = augmented['equipped_items'][0]
            if item['recommended_level'] != rec or item['required_level'] != req:
                raise ValueError('Augmented item native level metadata changed')
            checks.append({'case': parent+'_'+suffix, 'stat': stat, 'delta': delta, 'expected': expected})
    return checks


def run(inputs, output):
    if Path.cwd().resolve() != ROOT or output.resolve().parent != ROOT or output.exists():
        raise ValueError('Use an isolated runtime and a new output path')
    source, target = ROOT/'augment-case-input.json', ROOT/'augment-case-output.json'

    def invoke(value):
        source.write_text(json.dumps(value))
        if target.exists():
            target.unlink()
        completed = subprocess.run([str(ROOT/'balance-zone'), 'tests:balance', str(source), str(target)],
                                   capture_output=True, text=True, timeout=120,
                                   env=os.environ | {'NIGHTCAP_BALANCE_RNG_SEED': '12345'})
        return completed, json.loads(target.read_text()) if target.exists() else None

    completed, report = invoke(inputs)
    if completed.returncode:
        raise RuntimeError(completed.stderr[-2000:])
    checks = verify(inputs, report)
    invalid = []
    failures = {
        'wrong_socket_type': [{'slot': 13, 'id': 608079, 'augments': [{'socket': 0, 'id': 651903}]}],
        'negative_socket': [{'slot': 2, 'id': 601549, 'augments': [{'socket': -1, 'id': 651903}]}],
        'out_of_bounds_socket': [{'slot': 2, 'id': 601549, 'augments': [{'socket': 6, 'id': 651903}]}],
        'missing_augment': [{'slot': 2, 'id': 601549, 'augments': [{'socket': 0, 'id': 4294967295}]}],
        'duplicate_socket': [{'slot': 2, 'id': 601549, 'augments': [{'socket': 0, 'id': 651903}, {'socket': 0, 'id': 679626}]}],
        'duplicate_augment_lore': [{'slot': 2, 'id': 601549, 'augments': [{'socket': 0, 'id': 651903}]},
                                   {'slot': 15, 'id': 609959, 'augments': [{'socket': 0, 'id': 651903}]}],
        'duplicate_worn_slot': [{'slot': 2, 'id': 601549}, {'slot': 2, 'id': 601549}],
        'augment_as_equipment': [{'slot': 2, 'id': 651903}],
        'above_required_level': [{'slot': 3, 'id': 609488}],
    }
    for name, entries in failures.items():
        value = copy.deepcopy(inputs)
        value['builds'] = [value['builds'][0]]
        value['builds'][0]['equipment'] = entries
        completed, unexpected = invoke(value)
        error = completed.stderr
        if completed.returncode == 0 or unexpected is not None or not any(
                message in error for message in ('Invalid equipped', 'Equipped item/augment lore conflict')):
            raise ValueError(f'Native invalid loadout did not fail as expected: {name}: {error[-500:]}')
        invalid.append({'case': name, 'exit_code': completed.returncode, 'rejected': True})
    result = {'binary_sha256': hashlib.sha256((ROOT/'balance-zone').read_bytes()).hexdigest(),
              'checks': checks, 'invalid_controls': invalid, 'report': report}
    output.write_bytes((json.dumps(result, indent=2)+'\n').encode())
    print(json.dumps({'stat_controls': len(checks), 'invalid_controls': len(invalid)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    inputs = json.loads(args.inputs.read_text())
    if args.run:
        run(inputs, args.output)
    else:
        args.output.write_bytes((json.dumps(prepare(inputs), indent=2)+'\n').encode())


if __name__ == '__main__':
    main()

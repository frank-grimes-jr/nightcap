"""Legal combined-system stress, separate from stock progression coverage."""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def main():
    source = json.loads((HERE / 'input.json').read_text())
    prior = json.loads((HERE.parent / 'classic-augment-stacking/fixture.json').read_text())
    full = next(c for c in prior['cases'] if c['name'] == 'full_healer')
    # Preserve the established full-healer hosts and legal augment combinations.
    # Use the same new healing shoulders as the stock raid test. Eye/wrist/ring
    # targets already occur here; Valorium legs also exercise the 2-second lane.
    slots = copy.deepcopy([r for r in full['slots'] if r[0] <= 21])
    next(r for r in slots if r[0] == 6)[1] = 601557
    result = {'rules': source['rules'], 'policy': source['policy'], 'cases': [],
              'scope': 'Existing full-healer fixture with focus target shoulders; separate eight-Dodging-scale variant. Legal acquired rewards, no item edits beyond focus policy. Not a stock leveling fixture.'}
    for variant in ('full_healer', 'full_dodging'):
        gear = copy.deepcopy(slots)
        if variant == 'full_dodging':
            for r in gear:
                r[2] = [609602 if a == 609607 else a for a in r[2]]
        for case in source['cases']:
            if not case['id'].startswith('raid-'):
                continue
            c = copy.deepcopy(case)
            c['id'] = variant + '-' + case['id']
            c['slots'] = gear
            c['exact_sockets'] = False
            result['cases'].append(c)
    (HERE / 'stress-input.json').write_text(json.dumps(result, indent=2) + '\n')
    pressure = {'rules': source['rules'], 'policy': source['policy'], 'cases': [],
                'scope': 'Three simultaneous primary-hand attackers using identical native NPC templates; controlled pressure breakpoint, no NPC AI/extra attack rounds.'}
    for case in source['cases']:
        if case['id'].split('-aa', 1)[0] not in ('early', 'mid_pal', 'pre_raid', 'raid'):
            continue
        c = copy.deepcopy(case)
        c['id'] = 'three-' + c['id']
        c['attackers'] = 3
        pressure['cases'].append(c)
    (HERE / 'pressure-input.json').write_text(json.dumps(pressure, indent=2) + '\n')

if __name__ == '__main__':
    main()

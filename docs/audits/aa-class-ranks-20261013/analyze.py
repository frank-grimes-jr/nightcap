"""Offline class-rank audit. Writes this audit directory only; never edits policy or PEQ."""
import collections
import copy
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from aa_tbs_policy import compile_policy, digest

spec = importlib.util.spec_from_file_location('catalog_audit', HERE.parent / 'aa-tbs-20261013/analyze.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
CLASSES = module.CLASSES

# Recommendations for a measured QA candidate, not a declaration of balanced gameplay.
CAPS = {
    75: 9, 206: 5, 557: 6, 281: 9, 605: 5,
    90: 4, 118: 4, 103: 4, 227: 6, 262: 5, 504: 5,
    186: 10, 187: 10, 248: 10, 266: 10, 278: 5, 665: 5,
    114: 11, 215: 9, 259: 6, 526: 3, 740: 3, 628: 3,
    18: 9, 19: 12, 89: 6,
}
# These currently have no legal ranks. Preserve that state while examining their
# triggered spells / short burns separately instead of silently unlocking them.
GUARDS = {359: 0, 541: 0, 516: 0}
FOLLOW_UP = {
    218: 'Retune fixed-damage Headshot before admission; not equivalent to Slay.',
    555: 'Retune fixed-damage Assassinate before admission; not equivalent to Slay.',
    249: 'Pet flurry stacks across held classes: audit combined cap/routing first.',
    267: 'Pet flurry stacks across held classes: audit combined cap/routing first.',
    279: 'Pet flurry stacks across held classes: audit combined cap/routing first.',
    274: 'Flat kick damage multiplies the benefit of Master Wu; tune together.',
    368: 'Flat Frenzy damage is very large for early content; tune rather than blind unlock.',
    299: 'Flat HP can replace gear progression; measure early-level survival first.',
    97: 'Critical Mend jumps from 30 to 68 at rank 4; inspect sustain before increasing.',
    173: 'Eldritch Rune 1500 to 3000 absorption; test duration and effective AA buff behavior.',
    545: 'Deep Sleep adds stronger triggered debuffs; inspect stacking against bosses.',
    442: 'Touch of the Cursed higher proc spells: measure lifetap and Soul Abrasion together.',
    214: 'Theft of Life adds heal crit and stacks with Healing Gift; audit sustain.',
    38: 'Celestial Regeneration: measure triggered healing, uptime and mana-free sustain.',
    185: 'Spirit of the Wood: measure regen, damage shield and AA buff lifetime.',
    257: 'Nature\'s Boon: requires ward NPC/pet data, not only the AA spell record.',
    447: 'Ancestral Aid: heal procs plus melee modifiers; verify actual AA buff lifetime.',
    254: 'Divine Avatar: large melee modifiers, test held-WAR/MNK combinations and uptime.',
    128: 'Paragon: resource refill/regen can erase attrition; measure full recovery cycle.',
    177: 'Spirit Call: requires swarm NPC data and owner-pet bonus routing.',
    174: 'Servant of Ro: requires swarm NPC data and spell behavior.',
    207: 'Host of the Elements: requires swarm NPC data and spell behavior.',
    558: 'Turn Undead: inspect linked damage spell and actual cooldown before expansion.',
    559: 'Turn Summoned: inspect linked damage spell and actual cooldown before expansion.',
    6000: 'Harm Touch: first ten ranks free, formula-based damage; needs explicit redesign audit.',
    6001: 'Lay on Hands: first ten ranks free; cap blocks Hand of Piety/Fervent Blessing.',
    6002: 'Hunter\'s Attack Power: all 26 in-era ranks free; earned-point scarcity cannot balance it.',
    397: 'Destructive Fury: keep explicit deferral while testing increased crit frequency.',
    398: 'Destructive Fury: keep explicit deferral while testing increased crit frequency.',
    338: 'Veteran\'s Wrath: crit damage multiplies attack-frequency gains; separate campaign.',
    697: 'Mortal Coil: kill-trigger sustain risks runaway camp clearing; separate campaign.',
}


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def write_csv(name, rows):
    with (HERE / name).open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def caps(rows):
    result = collections.Counter()
    for row in rows:
        result[row['ability_id']] = max(result[row['ability_id']], row['ordinal'])
    return result


def closed(rows, mask):
    candidates = {(r['ability_id'], r['ordinal']): r for r in rows if r['classes'] & mask}
    retained = set()
    while True:
        previous = len(retained)
        for key, row in candidates.items():
            deps = list(row['prereqs'].items())
            if row['ordinal'] > 1:
                deps.append((row['ability_id'], row['ordinal'] - 1))
            if all(dep in retained for dep in deps):
                retained.add(key)
        if len(retained) == previous:
            break
    return [candidates[key] for key in sorted(retained)]


def main():
    config = json.loads((HERE / 'baseline-policy.json').read_text())
    catalog = json.loads(gzip.decompress((ROOT / config['catalog']).read_bytes()))
    snap_path = HERE.parent / 'aa-tbs-20261013/production-snapshot.json.gz'
    snapshot = json.loads(gzip.decompress(snap_path.read_bytes()))
    c = module.Catalog(snapshot['tables'])
    for table in catalog:
        assert catalog[table] == snapshot['tables'][table], f'Catalog drift: {table}'
    baseline = compile_policy(catalog, config)
    proposal = copy.deepcopy(config)
    proposal['id'] = 'AUDIT-ONLY-class-ranks-20261013'
    proposal['notes'] = 'Undeployed target-catalog hypothesis. All allowed ranks remain level 1. Triple Backstab also needs a native activation repair; this config alone is insufficient. See this audit README.'
    proposal['rank_caps'].update({str(k): v for k, v in CAPS.items()})
    unguarded = compile_policy(catalog, proposal)
    proposal['rank_caps'].update({str(k): v for k, v in GUARDS.items()})
    candidate = compile_policy(catalog, proposal)
    before, after, raw = caps(baseline), caps(candidate), caps(unguarded)
    effect_rows = list(csv.DictReader((HERE.parent / 'aa-tbs-20261013/ranks.csv').open(encoding='utf-8-sig')))
    labels = {(int(r['ability_id']), int(r['ordinal'])): r['effects'] for r in effect_rows}
    inventory = []
    for aid, a in sorted(c.abilities.items()):
        if not a['enabled'] or aid <= 0 or a['category'] in (3, 4) or a['charges'] or a['grant_only']:
            continue
        chain = c.chains[aid]
        natural = []
        for rank in chain:
            if rank['expansion'] > 13:
                break
            natural.append(rank)
        if not natural or len(natural) <= before[aid]:
            continue
        status = 'retain; no specific higher-cap recommendation'
        if aid in CAPS:
            status = 'recommend higher rank depth for measured QA'
        elif aid in GUARDS:
            status = 'preserve current blocked state; review incidental unlock separately'
        elif aid in FOLLOW_UP:
            status = FOLLOW_UP[aid]
        inventory.append({
            'ability_id': aid, 'name': a['name'].strip(),
            'classes': '/'.join(n for i, n in enumerate(CLASSES) if a['classes'] & (1 << i)),
            'current_legal_cap': before[aid], 'proposed_legal_cap': after[aid],
            'tbs_contiguous_prefix': len(natural), 'all_catalog_ranks': len(chain),
            'current_points': sum(r['cost'] for r in chain[:before[aid]]),
            'proposed_points': sum(r['cost'] for r in chain[:after[aid]]),
            'tbs_zero_cost_ranks': sum(r['cost'] == 0 for r in natural),
            'current_effects': labels.get((aid, before[aid]), ''),
            'proposed_effects': labels.get((aid, after[aid]), ''),
            'tbs_top_effects': labels.get((aid, len(natural)), ''),
            'next_rank_prereqs': json.dumps(chain[before[aid]]['prereqs'], sort_keys=True),
            'explicitly_deferred': aid in config['deferred_abilities'],
            'recommendation': status,
        })
    write_csv('rank-inventory.csv', inventory)
    write_csv('recommended-caps.csv', [r for r in inventory if r['ability_id'] in CAPS])
    deps = [{'ability_id': aid, 'name': c.abilities[aid]['name'].strip(),
             'current_cap': before[aid], 'unguarded_cap': raw[aid], 'proposed_cap': after[aid],
             'first_rank_prereqs': json.dumps(c.chains[aid][0]['prereqs'], sort_keys=True)}
            for aid in sorted(raw) if raw[aid] and not before[aid]]
    write_csv('dependency-unlocks.csv', deps)
    profiles = {name: 1 << i for i, name in enumerate(CLASSES)}
    for names in ['WAR/CLR/WIZ', 'WAR/CLR/MNK', 'MAG/NEC/SHM', 'PAL/WAR/MNK',
                  'SHD/SHM/BRD', 'RNG/DRU/ENC', 'MAG/BST/NEC', 'BRD/BST/PAL']:
        profiles[names] = sum(1 << CLASSES.index(n) for n in names.split('/'))
    coverage = []
    for name, mask in profiles.items():
        row = {'classes': name}
        for prefix, policy in [('current', baseline), ('proposed', candidate)]:
            rr = closed(policy, mask)
            row.update({prefix + '_families': len({r['ability_id'] for r in rr}),
                        prefix + '_ranks': len(rr),
                        prefix + '_points': sum(c.ranks[r['rank_id']]['cost'] for r in rr)})
        coverage.append(row)
    write_csv('coverage.csv', coverage)
    slay = []
    for r in c.chains[75][:10]:
        effect = next(e for e in c.effects[r['id']] if e['effect_id'] == 219)
        slay.append({'ordinal': r['ordinal'], 'rank_id': r['id'], 'expansion': r['expansion'],
                     'rank_cost': r['cost'], 'cumulative_cost': sum(x['cost'] for x in c.chains[75][:r['ordinal']]),
                     'aa_only_proc_percent_at_rate_rule_1': effect['base2'] / 100,
                     'native_damage_factor_at_damage_rule_1': effect['base1'] / 100})
    write_csv('slay-undead.csv', slay)
    assert len(baseline) == 941 and len(before) == 390
    assert all(r['level'] == 1 for r in candidate)
    assert {r['rank_id'] for r in baseline} <= {r['rank_id'] for r in candidate}
    assert all(after[aid] == count for aid, count in CAPS.items())
    assert all(after[aid] == 0 and before[aid] == 0 for aid in GUARDS)
    assert all(after[aid] == 0 for aid in config['deferred_abilities'])
    assert all(r['expansion'] <= 13 or r['ability_id'] in config['later_exceptions'] for r in candidate)
    assert slay[8]['rank_id'] == 5040 and slay[9]['expansion'] == 19
    assert all((dep, count) in {(x['ability_id'], x['ordinal']) for x in candidate}
               for r in candidate for dep, count in r['prereqs'].items())
    write_json('candidate-policy.json', proposal)
    write_json('summary.json', {
        'status': 'audit_only_not_deployed_not_encounter_validated',
        'source_policy_sha256': digest(config), 'catalog_sha256': digest(catalog),
        'snapshot_file_sha256': hashlib.sha256(snap_path.read_bytes()).hexdigest(),
        'current': {'families': len(before), 'ranks': len(baseline)},
        'candidate': {'families': len(after), 'ranks': len(candidate)},
        'recommended_families': len(CAPS), 'current_blocked_guards': sorted(GUARDS),
        'truncated_or_blocked_in_era_families': len(inventory),
        'implementation_blockers': ['Triple Backstab native activation requires live DoubleBackstabLevelRequirement 55, above global MaxLevel 50; repair and test before inclusion.'],
        'checks': 'baseline reproduced; identities preserved; all level 1; prerequisite closed; no deferred family admitted; no new later exception',
    })
    print((HERE / 'summary.json').read_text())


if __name__ == '__main__':
    main()

"""Generate auditable candidate builds; scores are explicit, not combat outcomes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from gear import optimize_gear


PROFILES = {
    'war-clr-wiz': ((1, 2, 12), 'int', False),
    'war-clr-mnk': ((1, 2, 7), 'wis', True),
    'mag-nec-shm': ((13, 11, 10), 'int', False),
}
STATS = ('hp', 'mana', 'ac', 'astr', 'asta', 'aagi', 'adex', 'aint', 'awis',
         'heroic_str', 'heroic_sta', 'heroic_agi', 'heroic_dex', 'heroic_int', 'heroic_wis',
         'spelldmg', 'healamt', 'attack', 'accuracy', 'avoidance', 'regen', 'manaregen',
         'fr', 'cr', 'mr', 'pr', 'dr', 'shielding', 'spellshield', 'dotshielding')


def load_snapshot(path):
    raw = path.read_bytes()
    manifest = json.loads(path.with_suffix('.manifest.json').read_text(encoding='utf-8'))
    if hashlib.sha256(raw).hexdigest() != manifest['snapshot_sha256']:
        raise ValueError('Snapshot does not match its reviewed manifest')
    snapshot = json.loads(gzip.decompress(raw))
    if snapshot['metadata']['schema_version'] != 1:
        raise ValueError('Unsupported snapshot schema')
    snapshot['tables']['items'] = [{k.lower(): v for k, v in row.items()} for row in snapshot['tables']['items']]
    return snapshot, manifest


def score_item(item, casting_stat, melee):
    score = (item['hp'] + item['mana'] + 4*item['ac'] + 10*item['heroic_sta']
             + 10*item['heroic_' + casting_stat] + 2*item['a' + casting_stat]
             + item['asta'] + 2*item['spelldmg'] + 2*item['healamt'])
    if melee and item['damage'] > 0 and item['delay'] > 0:
        score += item['damage'] * 1000 // item['delay']
    return score


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    snapshot, manifest = load_snapshot(args.snapshot)
    sources = {}
    for row in snapshot['tables']['drop_sources']:
        sources.setdefault(row['item_id'], []).append(row)
    builds = []
    for profile, (classes, casting_stat, melee) in PROFILES.items():
        for tier, tier_name in enumerate(('Base', 'Polished', 'Exalted', 'Ascended')):
            items = [i for i in snapshot['tables']['items'] if i['id']//200000 == tier]
            score = lambda item: score_item(item, casting_stat, melee)
            gear = optimize_gear(items, tuple(range(1, 21)), score, classes, 50)
            equipped = []
            for slot, item in gear.items():
                base_id = item['id'] % 200000
                if base_id not in sources:
                    raise ValueError(f'Item {item["id"]} has no captured source')
                equipped.append({'slot': slot, 'id': item['id'], 'name': item['name'],
                                 'base_id': base_id, 'score': score(item),
                                 'source_count': len(sources[base_id]), 'source_examples': sources[base_id][:3]})
            totals = {stat: sum(item[stat] for item in gear.values()) for stat in STATS}
            builds.append({'profile': profile, 'classes': classes, 'level': 50,
                           'race': 'Human', 'deity': 'Agnostic', 'tier': tier_name,
                           'casting_stat_scored': casting_stat, 'melee_ratio_scored': melee,
                           'total_score': sum(score(i) for i in gear.values()),
                           'equipment': equipped, 'raw_item_totals': totals,
                           'capped_spell_damage': min(250, totals['spelldmg']),
                           'capped_heal_amount': min(250, totals['healamt'])})
    report = {'snapshot_sha256': manifest['snapshot_sha256'],
              'status': 'Candidate builds, not yet certified full BiS or simulated combat results',
              'objective': 'hp + mana + 4*ac + 10*heroic_sta + 10*heroic_casting_stat + 2*casting_stat + sta + 2*spelldmg + 2*healamt; melee additionally damage*1000//delay',
              'constraints': 'Twenty standard worn slots (1-20), no two-handed primary weapons (non-weapon caster items allowed), shield, native class/race/deity/lore gates, required/recommended level <=50. Exact optimal additive score within the captured drop-only tier pool. Quest/global-loot/merchant paths, haste/procs/focus, AAs, and cross-stat caps remain outside this optimization.',
              'builds': builds}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for build in builds:
        raw = build['raw_item_totals']
        print(f'{build["profile"]:12} {build["tier"]:8} HP={raw["hp"]:5} mana={raw["mana"]:5} AC={raw["ac"]:4} spell={raw["spelldmg"]:3} heal={raw["healamt"]:3}')


if __name__ == '__main__':
    main()

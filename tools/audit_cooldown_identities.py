"""Build a complete timer-membership inventory from a SELECT-only catalog."""
import argparse
import csv
import gzip
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

from aa_tbs_policy import compile_policy

ROOT = Path(__file__).resolve().parents[1]


def audit(path, output):
    raw = gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()
    current = json.loads(raw)
    config = json.loads((ROOT/'config/aa-policy.json').read_text())
    with gzip.open(ROOT/config['catalog'], 'rt', encoding='utf-8') as stream:
        data = json.load(stream)
    for table, key in [('aa_ability', 'abilities'), ('aa_ranks', 'ranks')]:
        updates = {int(r['id']): r for r in current[key]}
        for row in data[table]:
            for k, v in updates.get(row['id'], {}).items():
                if k in row and isinstance(row[k], int):
                    row[k] = int(v)
    policy = compile_policy(data, config)
    effects = {int(r['rank_id']) for r in current['aa_effect_counts']}
    ranks = {int(r['id']): r for r in current['ranks']}
    abilities = {int(a['id']): a for a in current['abilities']}
    groups, families = defaultdict(dict), {}
    inventory = []
    for entry in policy:
        rid, aid = entry['rank_id'], entry['ability_id']
        rank = ranks[rid]
        if rid in effects or not 0 < int(rank['spell']) < 65536 or int(rank['recast_time']) <= 0:
            continue
        a = abilities[aid]
        group = int(rank['spell_type'])
        groups[group][aid] = a['name']
        families[aid] = int(a['classes'])
        inventory.append(dict(kind='allowed_activated_aa', id=rid, family=aid, name=a['name'],
                              group=group, seconds=int(rank['recast_time']),
                              legacy_key=1000+group, candidate_key=0x100000+aid,
                              disposition='independent AA family'))
    for spell in current['spells']:
        sid, group = int(spell['id']), int(spell['timer_id'])
        disc = int(spell['IsDiscipline']) != 0
        legacy = ((14+group) if disc else (28+group if group>0 else 5000+sid)) & 0xffff
        new = (0x400000+sid if group == -1 else 0x300000+group) if disc else (28+group if group>0 else 5000+sid)
        inventory.append(dict(kind='discipline' if disc else 'spell', id=sid, family='', name=spell['name'],
                              group=group, seconds=int(spell['recast_time'])/1000,
                              legacy_key=legacy, candidate_key=new,
                              disposition=('unsupported native spell ID; catalog only' if sid>65535 else
                                           'shared content group remains' if (group>=0 if disc else group>0) else 'individual reuse')))
        if not disc:
            inventory[-1]['per_spell_legacy_key'] = (5000+sid)&0xffff
            inventory[-1]['per_spell_candidate_key'] = 5000+sid
    for item in current['items']:
        iid, group = int(item['id']), int(item['recasttype'])
        inventory.append(dict(kind='item', id=iid, family='', name=item['Name'], group=group,
                              seconds=int(item['recastdelay']), legacy_key=(-iid)&0xffff if group == -1 else 100+group,
                              candidate_key=0x200000+iid if group == -1 else 100+group,
                              disposition='independent item' if group == -1 else 'shared content group remains'))
    max_slots = max(sum(bool(mask & sum(1<<c for c in combo)) for mask in families.values())
                    for combo in itertools.combinations(range(16), 3))
    result = dict(captured_at=current['captured_at'], capture_sha256=hashlib.sha256(raw).hexdigest(),
                  policy_sha256=hashlib.sha256((ROOT/'config/aa-policy.json').read_bytes()).hexdigest(),
                  definitions={k:len(current[k]) for k in ['abilities','ranks','spells','items']},
                  allowed_activated_families=len(families), maximum_three_class_slots=max_slots,
                  aa_shared_groups={g:v for g,v in groups.items() if len(v)>1},
                  ordered_aliases=sum(len(v)*(len(v)-1) for v in groups.values()),
                  saved_active_timer_aggregates=current['active_timer_groups'],
                  limitations=['Catalog membership is not proof of item ownership or learned spell access.',
                               'AA policy count excludes passive effect-bearing and zero-reuse ranks; runtime also handles toggles.',
                               'Shared spell/discipline/item content groups are inventoried, not declared intentional or independent.'])
    output.mkdir(parents=True, exist_ok=True)
    (output/'catalog-summary.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    with (output/'timer-membership.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(inventory[0])+['per_spell_legacy_key','per_spell_candidate_key'])
        writer.writeheader()
        writer.writerows(inventory)
    lines = ['# Shared activated AA groups in the live catalog', '',
             'Candidate isolates each family; ranks of the same family remain linked.', '',
             '| Legacy group | Families |', '|---|---|']
    for g, members in sorted(groups.items()):
        if len(members)>1:
            lines.append(f'| {g} | '+ '; '.join(f'{name} ({aid})' for aid,name in sorted(members.items()))+' |')
    (output/'aa-shared-groups.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['aa_shared_groups','saved_active_timer_aggregates']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    audit(args.capture, args.output)

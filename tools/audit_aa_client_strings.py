"""Read-only AA title/ownership audit for #16; never emits or executes updates."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def title_ids(text):
    """RoF2 dbstr records are SID^type^text^...; only type 1 names AAs."""
    titles = set()
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split('^')
        if len(fields) < 3 or not fields[0].isdigit() or not fields[1].isdigit():
            raise ValueError('Malformed client string record')
        if int(fields[1]) == 1 and fields[2].strip():
            titles.add(int(fields[0]))
    if not titles:
        raise ValueError('No nonempty type-1 client titles found')
    return titles


def indexed(rows, key, fields):
    result = {}
    for row in rows:
        if any(type(row.get(field)) is not int for field in fields):
            raise ValueError('Missing or noninteger fields in ' + key)
        if row[key] <= 0 or row[key] in result:
            raise ValueError('Invalid or duplicate ' + key)
        result[row[key]] = row
    return result


def audit(snapshot, titles):
    abilities = indexed(snapshot['abilities'], 'id', ('id', 'first_rank_id', 'enabled'))
    ranks = indexed(snapshot['ranks'], 'id', ('id', 'title_sid', 'next_id'))
    ownership = indexed(snapshot['ownership'], 'aa_id', ('aa_id', 'saved_rows'))
    if not abilities or not ranks or not titles:
        raise ValueError('Empty catalog or client titles')
    first_ids = [a['first_rank_id'] for a in abilities.values()]
    if len(first_ids) != len(set(first_ids)):
        raise ValueError('Shared first rank: ownership attribution is ambiguous')
    if ownership.keys() - set(first_ids):
        raise ValueError('Unmapped saved ownership; review before any disablement')
    if any(row['saved_rows'] <= 0 for row in ownership.values()):
        raise ValueError('Invalid saved ownership row count')
    affected = []
    rank_owners = {}
    for aid, ability in sorted(abilities.items()):
        if ability['enabled'] not in (0, 1) or ability['first_rank_id'] <= 0:
            raise ValueError('Invalid ability flags or first rank')
        rid, seen, missing = ability['first_rank_id'], set(), set()
        while rid > 0:
            if rid in seen or rid not in ranks:
                raise ValueError('Cyclic or missing rank in ability ' + str(aid))
            if rid in rank_owners and rank_owners[rid] != aid:
                raise ValueError('Rank shared by multiple abilities: ' + str(rid))
            rank_owners[rid] = aid
            seen.add(rid)
            rank = ranks[rid]
            if rank['title_sid'] not in titles:
                missing.add(rank['title_sid'])
            rid = rank['next_id']
            if rid < -1:
                raise ValueError('Invalid rank terminator')
        if missing:
            affected.append({
                'ability_id': aid, 'first_rank_id': ability['first_rank_id'],
                'enabled': ability['enabled'], 'missing_title_sids': sorted(missing),
                'saved_rows': ownership.get(ability['first_rank_id'], {}).get('saved_rows', 0),
            })
    enabled = [row for row in affected if row['enabled']]
    return {
        'abilities_checked': len(abilities), 'ranks_checked': len(rank_owners),
        'client_title_count': len(titles),
        'enabled_affected_abilities': len(enabled),
        'enabled_affected_saved_rows': sum(row['saved_rows'] for row in enabled),
        'missing_title_abilities': affected,
        'status': 'audit_only_not_authorization_to_disable',
    }


def load_snapshot(text):
    """Read tab-separated group + JSON records from the companion SELECT script."""
    groups = defaultdict(list)
    for line in text.splitlines():
        group, row = line.split('\t', 1)
        if group not in ('abilities', 'ranks', 'ownership', 'summary'):
            raise ValueError('Unknown snapshot group: ' + group)
        groups[group].append(json.loads(row))
    if len(groups['summary']) != 1:
        raise ValueError('Missing or duplicate snapshot completion summary')
    summary = groups['summary'][0]
    for group in ('abilities', 'ranks', 'ownership'):
        if type(summary.get(group)) is not int or summary[group] != len(groups[group]):
            raise ValueError('Incomplete snapshot group: ' + group)
    return {key: groups[key] for key in ('abilities', 'ranks', 'ownership')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--dbstr', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in (args.snapshot.resolve(), args.dbstr.resolve()):
        parser.error('Output must not overwrite either input')
    snapshot_bytes, client_bytes = args.snapshot.read_bytes(), args.dbstr.read_bytes()
    report = audit(load_snapshot(snapshot_bytes.decode('utf-8-sig')),
                   title_ids(client_bytes.decode('cp1252')))
    report.update(audited_at=datetime.now(timezone.utc).isoformat(),
                  snapshot_sha256=hashlib.sha256(snapshot_bytes).hexdigest(),
                  dbstr_sha256=hashlib.sha256(client_bytes).hexdigest())
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

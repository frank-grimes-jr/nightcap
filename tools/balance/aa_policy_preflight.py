"""Compile candidate AA rank caps and report owned-rank conflicts without writes.

This is a preflight, not a live policy installer, refund calculator, or replacement
for native class/level/race/deity/purchase checks. Saved aa_id is a first-rank ID;
aa_value counts ranks, despite GetRankByPointsSpent's native method name.
"""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path


SNAPSHOT_SQL = """START TRANSACTION READ ONLY;
SELECT 'abilities', JSON_OBJECT('id',id,'name',name,'enabled',enabled,
 'first_rank_id',first_rank_id,'classes',classes,'grant_only',grant_only,
 'charges',charges) FROM aa_ability ORDER BY id;
SELECT 'ranks', JSON_OBJECT('id',id,'cost',cost,'next_id',next_id,
 'level_req',level_req,'expansion',expansion) FROM aa_ranks ORDER BY id;
SELECT 'prerequisites', JSON_OBJECT('rank_id',rank_id,'aa_id',aa_id,
 'points',points) FROM aa_rank_prereqs ORDER BY rank_id,aa_id;
SELECT 'purchases', JSON_OBJECT('id',id,'aa_id',aa_id,'aa_value',aa_value,
 'charges',charges) FROM character_alternate_abilities ORDER BY id,aa_id;
COMMIT;
"""


def unique(rows, key, label):
    result = {key(row): row for row in rows}
    if len(result) != len(rows):
        raise ValueError('Duplicate ' + label)
    return result


def integer(value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('Expected an integer >= ' + str(minimum))
    return value


def parse_caps(values):
    caps = {}
    for key, value in values.items():
        if type(key) is not str or str(int(key)) != key or int(key) <= 0:
            raise ValueError('AA cap keys must be canonical positive ability IDs')
        caps[int(key)] = integer(value, 1)
    return caps


def build_preflight(snapshot, specification):
    abilities = unique(snapshot['abilities'], lambda r: r['id'], 'ability')
    ranks = unique(snapshot['ranks'], lambda r: r['id'], 'rank')
    unique(snapshot['purchases'], lambda r: (r['id'], r['aa_id']), 'purchase')
    unique(snapshot['prerequisites'], lambda r: (r['rank_id'], r['aa_id']), 'prerequisite')
    unique(specification['policies'], lambda r: r['id'], 'policy')
    chains, owners, chain_issues = {}, defaultdict(set), defaultdict(list)
    malformed = set()
    for aid, ability in sorted(abilities.items()):
        chain, seen, rid = [], set(), ability['first_rank_id']
        while rid >= 0:
            if rid in seen:
                chain_issues[aid].append('cyclic rank: ' + str(rid))
                malformed.add(aid)
                break
            if rid not in ranks:
                # Zone::LoadAlternateAdvancement truncates a missing next row.
                # A valid retained prefix need not contain unreleased tail data.
                chain_issues[aid].append('missing rank; native chain ends here: ' + str(rid))
                break
            seen.add(rid)
            if ability['enabled'] == 1:
                owners[rid].add(aid)
            chain.append(ranks[rid])
            rid = ranks[rid]['next_id']
        if not chain:
            chain_issues[aid].append('empty rank chain')
            malformed.add(aid)
        chains[aid] = chain
    for rid, aids in owners.items():
        if len(aids) > 1:
            for aid in aids:
                chain_issues[aid].append('shared rank: ' + str(rid))
                malformed.add(aid)
    prerequisites = defaultdict(dict)
    for row in snapshot['prerequisites']:
        # These are the same invalid-row exclusions used by the native loader.
        if row['aa_id'] > 0 and row['points'] > 0:
            prerequisites[row['rank_id']][row['aa_id']] = row['points']

    free = parse_caps(specification['free_caps'])
    policies = []
    for policy in specification['policies']:
        paid = parse_caps(policy['caps'])
        if free.keys() & paid.keys():
            raise ValueError('Free and paid AA caps overlap')
        caps = paid | free
        compiled = []
        for aid, cap in sorted(caps.items()):
            ability = abilities.get(aid)
            if (not ability or ability['enabled'] != 1 or aid in malformed
                    or cap > len(chains[aid])):
                raise ValueError('Unknown, disabled, malformed or oversized AA cap: ' + str(aid))
            inherited = {}
            for ordinal, rank in enumerate(chains[aid][:cap], 1):
                cost = integer(rank['cost'])
                if aid in free and cost != 0:
                    raise ValueError('Free AA cap contains a paid rank')
                for dependency, count in prerequisites[rank['id']].items():
                    inherited[dependency] = max(inherited.get(dependency, 0), count)
                compiled.append({'ability_id': aid, 'name': ability['name'], 'rank': ordinal,
                                 'rank_id': rank['id'], 'cost': cost,
                                 'native_expansion': rank['expansion'], 'level_req': rank['level_req'],
                                 'prerequisites': [{'ability_id': a, 'ranks': n}
                                                   for a, n in sorted(inherited.items())]})

        by_position = {(r['ability_id'], r['rank']): r['rank_id'] for r in compiled}
        edges, issues = defaultdict(list), []
        for row in compiled:
            rid = row['rank_id']
            if row['rank'] > 1:
                edges[rid].append(by_position[row['ability_id'], row['rank'] - 1])
            for prerequisite in row['prerequisites']:
                aid, count = prerequisite['ability_id'], prerequisite['ranks']
                target = by_position.get((aid, count))
                if target is None:
                    issues.append({'rank_id': rid, 'ability_id': aid, 'required_ranks': count,
                                   'reason': 'missing_or_disabled_ability' if aid not in abilities
                                   or abilities[aid]['enabled'] != 1 else 'outside_rank_caps'})
                else:
                    edges[rid].append(target)
        visiting, visited = set(), set()

        def visit(rid):
            if rid in visiting:
                issue = {'rank_id': rid, 'reason': 'cyclic_prerequisite'}
                if issue not in issues:
                    issues.append(issue)
                return
            if rid in visited:
                return
            visiting.add(rid)
            for dependency in edges[rid]:
                visit(dependency)
            visiting.remove(rid)
            visited.add(rid)

        for row in compiled:
            visit(row['rank_id'])

        impact = []
        for purchase in sorted(snapshot['purchases'], key=lambda r: (r['id'], r['aa_id'])):
            saved, count = purchase['aa_id'], purchase['aa_value']
            integer(purchase['charges'])
            row = {'character_id': purchase['id'], 'saved_first_rank_id': saved,
                   'owned_rank_count': count, 'charges': purchase['charges'],
                   'has_unspent_charges': purchase['charges'] > 0,
                   'ability_id': None, 'candidate_rank_count': None,
                   'nominal_removed_rank_cost': None, 'status': 'unresolved'}
            aids = owners.get(saved, set())
            if len(aids) != 1:
                row['reason'] = 'Missing or ambiguous saved rank'
            else:
                aid = next(iter(aids))
                row['ability_id'] = aid
                if aid in malformed or abilities[aid]['enabled'] != 1:
                    row['reason'] = 'Malformed or disabled owned ability'
                elif saved != abilities[aid]['first_rank_id']:
                    row['reason'] = 'Saved aa_id is not the canonical first rank'
                elif type(count) is not int or not 1 <= count <= len(chains[aid]):
                    row['reason'] = 'Owned rank count is outside the rank chain'
                elif any(type(r['cost']) is not int or r['cost'] < 0 for r in chains[aid][:count]):
                    row['reason'] = 'Owned ranks have invalid nominal costs'
                else:
                    retained = min(count, caps.get(aid, 0))
                    row.update(candidate_rank_count=retained,
                               nominal_removed_rank_cost=sum(r['cost'] for r in chains[aid][retained:count]),
                               status='outside_pool' if retained == 0 else 'above_cap' if retained < count else 'retained')
                    if retained == 0:
                        row['exclusion_note'] = specification.get('deferred_examples', {}).get(str(aid),
                            'Outside this diagnostic combat core; not a permanent-removal decision.')
            impact.append(row)
        policies.append({'id': policy['id'], 'caps': {str(a): n for a, n in sorted(caps.items())},
                         'allowed_rank_ids': sorted(r['rank_id'] for r in compiled),
                         'ranks': compiled, 'prerequisites_closed': not issues, 'prerequisite_issues': issues,
                         'purchase_counts': dict(sorted(Counter(r['status'] for r in impact).items())),
                         'affected_character_ids': sorted({r['character_id'] for r in impact if r['status'] != 'retained'}),
                         'purchase_impact': impact})
    return {'scope': 'Read-only rank-policy preflight. No access enforcement or refund authorization. '
                     'Nominal rank cost does not establish how a character acquired the AA. '
                     'Native per-character eligibility and complete release offerings require separate validation.',
            'source_sha256': hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
            'source_counts': {k: len(snapshot[k]) for k in ('abilities', 'ranks', 'prerequisites', 'purchases')},
            'source_chain_issues': {str(a): reasons for a, reasons in sorted(chain_issues.items()) if reasons},
            'policies': policies}


def read_json(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--specification', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build_preflight(read_json(args.snapshot), read_json(args.specification))
    args.output.write_bytes((json.dumps(result, indent=2) + '\n').encode())
    for policy in result['policies']:
        print(policy['id'], len(policy['allowed_rank_ids']), 'ranks;', policy['purchase_counts'],
              'prerequisite issues:', len(policy['prerequisite_issues']))

"""Read-only production catalog and anonymous ownership preflight."""
import collections
import gzip
import hashlib
import json
from pathlib import Path

import aa_tbs_policy as policy

STAGE = Path(__file__).resolve().parent


def canonical(tables):
    return {name: sorted(rows, key=lambda row: json.dumps(row, sort_keys=True))
            for name, rows in tables.items()}


def check(sql):
    config = json.loads((STAGE / 'aa-policy.json').read_text())
    captured = json.loads(gzip.decompress((STAGE / 'aa-catalog.json.gz').read_bytes()))
    queries = []
    for table, rows in sorted(captured.items()):
        assert table in ('aa_ability', 'aa_ranks', 'aa_rank_effects', 'aa_rank_prereqs')
        cols = sorted(rows[0])
        assert all(c.replace('_', '').isalnum() for c in cols)
        pairs = ','.join("'%s',`%s`" % (c, c) for c in cols)
        queries.append("SELECT '%s',JSON_OBJECT(%s) FROM `%s`;" % (table, pairs, table))
    queries.append("""SELECT 'owned',JSON_OBJECT('level',c.level,'class',c.class,
        'class2',COALESCE(m.class2,0),'class3',COALESCE(m.class3,0),
        'aa_id',a.aa_id,'aa_value',a.aa_value,'charges',a.charges)
        FROM character_alternate_abilities a JOIN character_data c ON c.id=a.id
        LEFT JOIN character_multiclass m ON m.character_id=c.id ORDER BY a.id,a.aa_id;""")
    response = sql('SET SESSION max_statement_time=30; START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;\n'
                   + '\n'.join(queries) + '\nROLLBACK;')
    actual = {table: [] for table in captured}
    owned = []
    for line in response.splitlines():
        table, row = line.split('\t', 1)
        (owned if table == 'owned' else actual[table]).append(json.loads(row))
    assert canonical(actual) == canonical(captured), 'AA catalog drift: rebuild/review the policy before deployment'
    legal = policy.compile_policy(actual, config)
    by_ability = collections.defaultdict(list)
    for row in legal:
        by_ability[row['ability_id']].append(row)
    ranks = {r['id']: r for r in actual['aa_ranks']}
    abilities = {a['first_rank_id']: a for a in actual['aa_ability'] if a['enabled']}
    result = collections.Counter()
    dormant = collections.Counter()
    for row in owned:
        ability = abilities.get(row['aa_id'])
        assert ability is not None, 'Unresolvable earned AA: no data will be changed'
        rid, count, seen = ability['first_rank_id'], 0, set()
        while rid in ranks:
            assert rid not in seen, 'Cyclic earned rank chain'
            seen.add(rid)
            count += 1
            rid = ranks[rid]['next_id']
        assert 1 <= row['aa_value'] <= count, 'Unresolvable earned AA count: no data will be changed'
        mask = sum(1 << (c - 1) for c in set((row['class'], row['class2'], row['class3'])) if 1 <= c <= 16)
        usable = max((r['ordinal'] for r in by_ability[ability['id']]
                      if r['level'] <= row['level'] and r['classes'] & mask), default=0)
        usable = min(usable, row['aa_value'])
        result['ownership_rows'] += 1
        result['earned_rank_count'] += row['aa_value']
        result['saved_charges'] += row['charges']
        result['fully_usable' if usable == row['aa_value'] else 'partially_usable' if usable else 'dormant'] += 1
        if usable != row['aa_value']:
            dormant[str(ability['id']) + ' ' + ability['name']] += 1
    return {'catalog_sha256': policy.digest(canonical(actual)), 'policy_sha256': policy.digest(config),
            'ownership': dict(result), 'affected_families': dict(sorted(dormant.items())),
            'database_modified': False}

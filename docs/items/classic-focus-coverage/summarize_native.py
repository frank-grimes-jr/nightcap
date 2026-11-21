"""Summarize guarded paired native measurements; never accept discarded dry runs."""
import collections
import gzip
import json
import statistics
import sys
from pathlib import Path

def summarize(path):
    data = json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes())
    pairs = collections.defaultdict(dict)
    assert sum(r['landed_casts'] for r in data['cases']) > 0, 'No observed native cast completions'
    for row in data['cases']:
        assert row['damage'] > 0 and row['swings'] > 0 and row['attempts'] > 0
        assert row['metrics']['hp'] + row['healing'] - row['damage'] == row['hp_end']
        assert row['stage'] not in pairs[row['id']]
        pairs[row['id']][row['stage']] = row
    assert pairs and all(set(p) == {'before', 'after'} for p in pairs.values())
    grouped = collections.defaultdict(list)
    for key, pair in pairs.items():
        before, after = pair['before'], pair['after']
        a, b = before['metrics'], after['metrics']
        for field in ('hp', 'mana', 'heal_amount', 'spell_damage', 'channeling'):
            assert a[field] == b[field], (key, field)
        assert b['cast_ms'] <= a['cast_ms'] and b['mana_cost_sample'] <= a['mana_cost_sample']
        assert b['healing_sample'] >= a['healing_sample']
        assert before['spent_points'] == after['spent_points']
        grouped[key.rsplit('-seed', 1)[0]].append(pair)
    out = {'pairs': len(pairs), 'scope': data['scope'], 'groups': {}}
    for key, group in grouped.items():
        result = {}
        for stage in ('before', 'after'):
            rows = [p[stage] for p in group]
            result[stage] = {
                'n': len(rows), 'results': dict(collections.Counter(r['result'] for r in rows)),
                'mean_survival_ms': statistics.mean(r['elapsed_ms'] for r in rows),
                'mean_healing': statistics.mean(r['healing'] for r in rows),
                'mean_mana_end': statistics.mean(r['mana_end'] for r in rows),
                'cast_starts': sum(r['starts'] for r in rows),
                'landed_casts': sum(r['landed_casts'] for r in rows),
                'failed_started_casts': sum(r['failed_started_casts'] for r in rows),
                'stunned_ms': sum(r['stunned_ms'] for r in rows),
                'metrics': rows[0]['metrics'], 'spent_points': rows[0]['spent_points']}
        out['groups'][key] = result
    return out

if __name__ == '__main__':
    src = Path(sys.argv[1])
    out = summarize(src)
    stem = src.name.removesuffix('.gz').removesuffix('.json')
    src.with_name(stem + '-summary.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({'pairs': out['pairs'], 'groups': len(out['groups'])}))

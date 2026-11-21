"""Prove the mana-only correction preserves healing and evaluate corrected pressure."""
from pathlib import Path
import gzip
import json

HERE = Path(__file__).resolve().parent

def load(name):
    p = HERE / name
    if not p.exists():
        p = p.with_suffix(p.suffix + '.gz')
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes())

def matrix():
    old, new = load('correction-matrix-before.json'), load('correction-matrix-after.json')
    key = lambda r: tuple(r[k] for k in ('classic', 'worn_mode', 'heal_endpoint', 'mana_endpoint', 'placement'))
    a, b = ({key(r): r for r in d['category_matrix']} for d in (old, new))
    assert set(a) == set(b) and len(a) == 144
    for k, row in b.items():
        for field in ('direct_heal', 'selected_heal', 'healing'):
            assert row[field] == a[k][field], (k, field, a[k][field], row[field])
        assert row['direct_mana'] == (row['mana_endpoint'] if row['placement'].startswith('multi_') else 0), k
        assert 0 <= row['selected_mana'] <= row['mana_endpoint'], k
    controls = {r['id']: r for r in new['focus_controls']}
    assert controls['healing_only']['selected_heal'] == controls['both']['selected_heal'] == 20
    assert controls['mana_only']['selected_mana'] == controls['both']['selected_mana'] == 10
    assert all(r['direct_heal_as_mana'] == 0 and r['direct_mana_as_heal'] == 10 for r in controls.values())
    return {'cases_per_engine': 144, 'healing_exactly_preserved': True,
            'mana_ignores_healing_slots': True,
            'reverse_mana_to_healing_behavior': 'Intentionally unchanged to preserve existing healing strength',
            'stock_controls': controls}

def totals(rows):
    return {'runs': len(rows), 'deaths': sum(r['result'] == 'player_death' for r in rows),
            'survived_duration': sum(r['result'] == 'duration' for r in rows),
            'landed_casts': sum(r['landed_casts'] for r in rows),
            'mean_duration_ms': sum(r['elapsed_ms'] for r in rows) / len(rows),
            'mana_end': sum(r['mana_end'] for r in rows)}

def pressure(stem):
    old, new = load(stem + '.json')['cases'], load('correction-' + stem + '.json')['cases']
    a = {(r['id'], r['stage']): r for r in old}
    b = {(r['id'], r['stage']): r for r in new}
    assert set(a) == set(b)
    for k, r in b.items():
        assert r['damage'] > 0 and r['attempts'] > 0
        assert r['metrics']['hp'] + r['healing'] - r['damage'] == r['hp_end']
        for field in ('hp', 'mana', 'heal_amount', 'spell_damage', 'channeling', 'cast_ms', 'healing_sample'):
            assert a[k]['metrics'][field] == r['metrics'][field], (stem, k, field)
        assert a[k]['spent_points'] == r['spent_points']
    return {'pairs': len(new) // 2, 'same_gear_healing_exactly_preserved': True,
            'original_baseline': totals([r for r in old if r['stage'] == 'before']),
            'uncorrected_content_candidate': totals([r for r in old if r['stage'] == 'after']),
            'corrected_baseline': totals([r for r in new if r['stage'] == 'before']),
            'corrected_content_candidate': totals([r for r in new if r['stage'] == 'after'])}

def main():
    result = {'matrix': matrix(), 'pressure': {s: pressure(s) for s in ('results', 'pressure-results', 'stress-results')},
              'limits': 'Controlled primary-hand attacks, finite HP/mana, no NPC AI or special attacks; no stuns observed in original fixtures. Per-cast healing strength preserved; mana efficiency intentionally corrected.'}
    assert sum(r['pairs'] for r in result['pressure'].values()) == 260
    (HERE / 'correction-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS 144 paired category scenarios and 260 paired pressure scenarios; healing strength unchanged')

if __name__ == '__main__':
    main()

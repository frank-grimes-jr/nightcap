"""Verify the one-file candidate against private captures and read-only sources."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import client_gameplay_assets as assets
from client_spell_cast_times import repair_cast_times


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rows(raw):
    result = {}
    for line in raw.splitlines():
        fields = line.split(b'^')
        spell_id = int(fields[0])
        assert spell_id not in result
        result[spell_id] = fields
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('before', 'after', 'original', 'generation-source', 'production', 'channel', 'output'):
        p.add_argument('--' + name, required=True, type=Path)
    a = p.parse_args()
    before, after, original = (v.read_bytes() for v in (a.before, a.after, a.original))
    capture = json.loads(a.production.read_bytes())
    channel = json.loads(a.channel.read_bytes())
    db = {s['id']: s for s in capture['spells']}
    old, new, native = rows(before), rows(after), rows(original)
    assert sha(original) == assets.SOURCE_SHA256
    assert sha(before) == channel['spell_asset']['sha256']
    assert len(before) == channel['spell_asset']['size']
    expected, changed = repair_cast_times(before)
    assert after == expected and len(changed) == 638
    assert repair_cast_times(after) == (after, [])
    assert old.keys() == new.keys()
    for spell_id in old:
        differences = [i for i, (x, y) in enumerate(zip(old[spell_id], new[spell_id])) if x != y]
        assert differences == ([13] if spell_id in changed else [])
        if spell_id in changed:
            assert len(old[spell_id]) == len(new[spell_id]) == 237
            assert int(old[spell_id][13]) == 50
            assert int(new[spell_id][13]) == db[spell_id]['cast_time'] == int(native[spell_id][13])
            assert new[spell_id][1].decode('latin1') == db[spell_id]['name'] == native[spell_id][1].decode('latin1')
    _, dots = assets.instant_dots(before)
    assert not set(changed).intersection(dots)
    # The normal generator starts with its preserved reference client, not a
    # later signed release containing additions made by separate content tools.
    generation_source = a.generation_source.read_bytes()
    generated, _ = assets.restore_spell_classes(generation_source, original)
    generated, _ = repair_cast_times(generated)
    generated, _ = assets.instant_dots(generated)
    for transform in (assets.rabid_bear_spells, assets.pet_support_spells,
                      assets.pet_fragment_spells, assets.wpm_spells):
        generated = transform(generated)
    arrival = json.loads((ROOT / 'docs/ecommons-hub/plan.json').read_bytes())['arrival']
    generated = assets.recall_spell(generated, arrival)
    generated_rows = rows(generated)
    assert all(generated_rows[i][13] == new[i][13] for i in changed)
    result = dict(status='verified_candidate_not_published',
        production_captured_utc=capture['captured_utc'],
        production_capture_sha256=sha(a.production.read_bytes()),
        production_query=capture['query'], production_rows=len(db),
        published_release=channel['release'], published_inventory=channel['files'],
        channel_sha256=channel['channel_sha256'], original_sha256=sha(original),
        before_sha256=sha(before), after_sha256=sha(after), output_size=len(after),
        catalog_sha256=sha((ROOT / 'assets/spell-cast-times.csv').read_bytes()),
        spell_rows=len(old), changed_rows=len(changed), changed_fields=[13],
        native_instant_definitions=sum(db[i]['cast_time'] == 0 for i in changed),
        generation_source_sha256=sha(generation_source),
        normal_spell_generation='All 638 repaired durations survive full spell composition from the preserved generator input',
        generation_limit='Existing class-restoration stage rejects later published custom spell 43220; do not regenerate the whole signed file from the old reference',
        preserved='All other fields, rows and line endings; all other client files untouched')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

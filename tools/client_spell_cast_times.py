"""Repair the reviewed stale 50-ms client definitions without changing server timing.

The catalog is the October 30 production/original-source intersection, not a
blanket reset to stock: Bard songs, instant DoTs and custom spells keep their
separate policies. Only field 13 of these exact spell identities may change.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / 'assets/spell-cast-times.csv'


def repair_cast_times(raw):
    with CATALOG.open(encoding='utf-8', newline='') as stream:
        entries = list(csv.DictReader(stream))
    reviewed = {int(r['id']): (r['name'], int(r['cast_time'])) for r in entries}
    if len(entries) != 638 or len(reviewed) != len(entries):
        raise ValueError('Unexpected reviewed cast-time catalog')
    output, seen, changed = [], set(), []
    for line in raw.splitlines(keepends=True):
        ending = b'\r\n' if line.endswith(b'\r\n') else b'\n' if line.endswith(b'\n') else b''
        fields = (line[:-len(ending)] if ending else line).split(b'^')
        if len(fields) != 237:
            raise ValueError('Expected 237 RoF2 spell fields')
        spell_id, cast_time = int(fields[0]), int(fields[13])
        if spell_id < 0 or spell_id in seen or cast_time < 0:
            raise ValueError('Invalid or duplicate spell')
        seen.add(spell_id)
        if spell_id in reviewed:
            name, expected = reviewed[spell_id]
            if fields[1].decode('latin1') != name or cast_time not in (50, expected):
                raise ValueError(f'Unreviewed spell identity/timing drift: {spell_id}')
            if cast_time != expected:
                fields[13] = str(expected).encode('ascii')
                changed.append(spell_id)
        output.append(b'^'.join(fields) + ending)
    if reviewed.keys() - seen:
        raise ValueError('Missing reviewed cast-time spells')
    return b''.join(output), changed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    source, destination = args.input.resolve(strict=True), args.output.resolve()
    if destination == source or source.parent in destination.parents:
        raise ValueError('Stage outside the source client tree')
    raw = source.read_bytes()
    fixed, changed = repair_cast_times(raw)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(fixed)
    print(json.dumps({'status': 'staged_not_installed', 'changed_spells': len(changed),
                      'input_sha256': hashlib.sha256(raw).hexdigest(),
                      'output_sha256': hashlib.sha256(fixed).hexdigest()}))


if __name__ == '__main__':
    main()

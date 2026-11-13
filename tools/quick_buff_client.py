"""Scoped dbstr delta for the Quick Buff hotkey; never edit a reference client.

Apply to the authenticated current signed release when preparing a new release.
No spell assets or DLL change are required. This does not sign or publish files.
"""
import argparse
import hashlib
import json
from pathlib import Path

DESCRIPTION = ('Instantly casts the eligible beneficial buff spells memorized on your spell bar '
               'on yourself. Group and pet buffs use normal targeting. Costs 50 percent of maximum '
               'mana once per activation; requires the full cost. No reuse time. Normal spell '
               'eligibility, reagents and stacking apply. Does not cast direct heals, attacks, '
               'summons or travel spells. Replaces the passive buff casting-time reduction; '
               'all three existing ranks activate the same hotkey.')


def strings(raw):
    updates = {2: 'Quick Buff', 3: 'Quick Buff', 4: DESCRIPTION}
    seen = set()
    title = False
    out = []
    for line in raw.splitlines(keepends=True):
        fields = line.rstrip(b'\r\n').split(b'^', 2)
        if len(fields) == 3 and fields[:2] == [b'147', b'1']:
            if title or fields[2].removesuffix(b'^0') != b'Quick Buff':
                raise ValueError('Unexpected or duplicate Quick Buff title')
            title = True
        if len(fields) < 3 or fields[0] != b'147' or fields[1] not in (b'2', b'3', b'4'):
            out.append(line)
            continue
        kind = int(fields[1])
        if kind in seen:
            raise ValueError('Duplicate Quick Buff client string')
        seen.add(kind)
        ending = line[len(line.rstrip(b'\r\n')):]
        suffix = b'^0' if fields[2].endswith(b'^0') else b''
        out.append(f'147^{kind}^{updates[kind]}'.encode('ascii') + suffix + ending)
    if not title:
        raise ValueError('Expected current Quick Buff title is missing')
    if 4 not in seen:
        raise ValueError('Expected Quick Buff description is missing')
    # Passive AA data may omit hotkey labels entirely. Add only these two keys.
    for kind in sorted(updates.keys() - seen):
        if out and not out[-1].endswith(b'\n'):
            out[-1] += b'\r\n'
        out.append(f'147^{kind}^{updates[kind]}\r\n'.encode('ascii'))
    return b''.join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    raw = args.base.read_bytes()
    updated = strings(raw)
    with args.out.open('xb') as handle:
        handle.write(updated)
    print(json.dumps(dict(status='unsigned_not_published',
        base_sha256=hashlib.sha256(raw).hexdigest(), sha256=hashlib.sha256(updated).hexdigest())))


if __name__ == '__main__':
    main()

"""Remove content door locks using exact captured preimages; never auto-apply."""
import argparse
import copy
import json
from pathlib import Path

from content_patch import patch_sql


def plan(capture):
    result = copy.deepcopy(capture)
    seen = set()
    for row in result['doors']:
        for field in ('id', 'keyitem', 'lockpick'):
            value = row[field]
            minimum = -32768 if field == 'lockpick' else 0
            maximum = 32767 if field == 'lockpick' else 2147483647
            if type(value) is not int or not minimum <= value <= maximum:
                raise ValueError(f'Invalid door {field}: {value!r}')
        if row['id'] in seen:
            raise ValueError(f'Duplicate door id: {row["id"]}')
        seen.add(row['id'])
        row.update(keyitem=0, lockpick=0)
    return result


def generate(capture):
    after = plan(capture)
    locked = [row for row in capture['doors'] if row['keyitem'] or row['lockpick']]
    if not locked:
        return ('-- No locked doors.\n',) * 2
    ids = {row['id'] for row in locked}
    unlocked = [row for row in after['doors'] if row['id'] in ids]
    # Keep captured IDs in the inverse scope and detect newly introduced locks.
    scope = '`keyitem` <> 0 OR `lockpick` <> 0 OR `id` IN (' + ','.join(map(str, sorted(ids))) + ')'
    before = {'rows': {'doors': locked}}
    after = {'rows': {'doors': unlocked}}
    return tuple(patch_sql(a, b, {'doors': ['id']}, {'doors': scope}).replace(
        '-- Stop the target zone, back up and capture fresh preimages before applying.',
        '-- Back up first; hold door use and compare a fresh complete door capture.\n'
        '-- Refresh affected loaded zones using supported static-data reloads after applying.\n'
        '-- Never kill a production zone worker; follow the keyless-doors runbook.'
    ) for a, b in ((before, after), (after, before)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    capture = json.loads(args.capture.read_text(encoding='utf-8-sig'))
    forward, rollback = generate(capture)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, sql in (('forward.sql', forward), ('rollback.sql', rollback)):
        (args.output / name).write_text(sql, encoding='utf-8')

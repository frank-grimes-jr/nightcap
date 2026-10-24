"""Generate a guarded two-field entrance patch; never apply it automatically."""
import argparse
import copy
import json
from pathlib import Path

from content_patch import patch_sql

IDENTITY = dict(id=10599, zone='paineel', version=0, doorid=3,
                name='PAROCK105', guild=0, keyitem=6379, lockpick=60)
SCOPE = "id=10599 OR (zone='paineel' AND doorid=3)"


def plan(capture):
    result = copy.deepcopy(capture)
    targets = [d for d in result['doors']
               if d['id'] == 10599 or (d['zone'] == 'paineel' and d['doorid'] == 3)]
    if len(targets) != 1 or any(targets[0].get(k) != v for k, v in IDENTITY.items()):
        raise ValueError('Paineel entrance identity or lock preimage drift')
    targets[0].update(keyitem=0, lockpick=0)
    return result


def generate(capture):
    after = plan(capture)
    before_rows = [d for d in capture['doors'] if d['id'] == 10599]
    after_rows = [d for d in after['doors'] if d['id'] == 10599]
    before = {'rows': {'doors': before_rows}}
    after = {'rows': {'doors': after_rows}}
    keys = {'doors': ['id']}
    scopes = {'doors': SCOPE}
    return tuple(patch_sql(a, b, keys, scopes).replace(
        '-- Stop the target zone, back up and capture fresh preimages before applying.',
        '-- Back up first; hold entrance use and capture fresh preimages.\n'
        '-- Reload Paineel static data through the supported runtime API after applying.\n'
        '-- Do not kill a production zone process; see the release runbook.'
    ) for a, b in ((before, after), (after, before)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    forward, rollback = generate(json.loads(args.capture.read_text(encoding='utf-8-sig')))
    args.output.mkdir(parents=True, exist_ok=True)
    for name, sql in [('forward.sql', forward), ('rollback.sql', rollback)]:
        (args.output / name).write_text(sql, encoding='utf-8')

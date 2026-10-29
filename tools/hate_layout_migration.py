"""Compile the additive private Hate layout; never apply SQL from this tool.

Only private zone186 placement rows and its reserved patrols are owned here.
The inverse is for the isolated rehearsal only. After activation, retain these
rows until all successor runs/checkpoints/corpses expire; never restore players.
"""
import copy
import json
from pathlib import Path

import content_patch
from dungeon_contract import predicate

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/dungeons/hate-layout-20261029'
KEYS = {'nightcap_dungeon_spawns': ['zone_id', 'spawn_id'],
        'grid': ['zoneid', 'id'], 'grid_entries': ['zoneid', 'gridid', 'number']}
SCOPES = {'nightcap_dungeon_spawns': 'zone_id=186',
          'grid': 'zoneid=186 AND id BETWEEN 9001 AND 9047',
          'grid_entries': 'zoneid=186 AND gridid BETWEEN 9001 AND 9047'}


def capture(query):
    return content_patch.capture(query, SCOPES)


def rows():
    data = json.loads((HERE / 'population.json').read_text())
    result = dict(nightcap_dungeon_spawns=data['rows'], grid=data['grid'],
                  grid_entries=data['grid_entries'])
    if len(result['nightcap_dungeon_spawns']) != 176:
        raise ValueError('Private population cardinality drift')
    grid_ids = {r['id'] for r in result['grid']}
    if grid_ids != set(range(9001, 9048)):
        raise ValueError('Reserved patrol identity drift')
    for table, values in result.items():
        keys = [tuple(r[k] for k in KEYS[table]) for r in values]
        if len(set(keys)) != len(keys):
            raise ValueError('Duplicate identity: ' + table)
        zone_key = 'zone_id' if table == 'nightcap_dungeon_spawns' else 'zoneid'
        if any(r[zone_key] != 186 for r in values):
            raise ValueError('Unowned zone: ' + table)
    if any(r['gridid'] not in grid_ids for r in result['grid_entries']):
        raise ValueError('Unowned patrol waypoint')
    if any(r['grid_id'] and r['grid_id'] not in grid_ids for r in result['nightcap_dungeon_spawns']):
        raise ValueError('Missing patrol')
    for grid in grid_ids:
        numbers = sorted(r['number'] for r in result['grid_entries'] if r['gridid'] == grid)
        if len(numbers) < 2 or numbers != list(range(1, len(numbers) + 1)):
            raise ValueError('Noncontiguous patrol')
    return result


def desired(before):
    if before['scopes'] != SCOPES or set(before['rows']) != set(KEYS):
        raise ValueError('Capture scope drift')
    if any(before['rows'].values()):
        raise ValueError('Reserved Hate layout already occupied')
    after = copy.deepcopy(before)
    after['rows'] = rows()
    return after


def patch_sql(before, after):
    if before['scopes'] != SCOPES or after['scopes'] != SCOPES:
        raise ValueError('Capture scope drift')
    for state in (before, after):
        if set(state['rows']) != set(KEYS):
            raise ValueError('Capture table drift')
        for table, values in state['rows'].items():
            zone_key = 'zone_id' if table == 'nightcap_dungeon_spawns' else 'zoneid'
            if any(int(r[zone_key]) != 186 for r in values):
                raise ValueError('Unowned zone: ' + table)
            grid_key = {'grid': 'id', 'grid_entries': 'gridid'}.get(table)
            if grid_key and any(not 9001 <= int(r[grid_key]) <= 9047 for r in values):
                raise ValueError('Unowned patrol: ' + table)
    return content_patch.patch_sql(before, after, KEYS, SCOPES).replace('Court ', 'Hate layout ')


def source_policy():
    policies = json.loads((HERE / 'spawn-policy.json').read_text())
    private = {r['spawn_id']: r for r in rows()['nightcap_dungeon_spawns'] if r['npc_id'] != 998812}
    if len(policies) != len(private) or {r['id'] for r in policies} != set(private):
        raise ValueError('Original spawn policy identity drift')
    source = {r['id']: r for r in json.loads((HERE / 'public-source.json').read_text())['spawn']
              if r['zone'] == 'hateplane'}
    return [dict(r, zone='hateplane', version=source[r['id']]['version'],
                 spawngroupID=private[r['id']]['group_id'],
                 respawntime=private[r['id']]['respawn']) for r in policies]


def runtime_checks():
    checks = []
    for table, values in rows().items():
        checks.append(dict(label=f'hate-layout/{table}/count',
                           sql=f'SELECT COUNT(*) FROM `{table}` WHERE {SCOPES[table]}',
                           expected=str(len(values))))
        for start in range(0, len(values), 8):
            batch = values[start:start + 8]
            checks.append(dict(label=f'hate-layout/{table}/{start}',
                               sql=f'SELECT COUNT(*) FROM `{table}` WHERE ' + ' OR '.join(predicate(r) for r in batch),
                               expected=str(len(batch))))
    policies = source_policy()
    for start in range(0, len(policies), 8):
        batch = policies[start:start + 8]
        checks.append(dict(label=f'hate-layout/original-spawn-policy/{start}',
                           sql='SELECT COUNT(*) FROM `spawn2` WHERE ' + ' OR '.join(predicate(r) for r in batch),
                           expected=str(len(batch))))
    return checks


def main():
    # Empty scope is the reviewed install contract, not a claimed production
    # capture. SQL guards every target count/engine/trigger before inserting.
    before = dict(scopes=SCOPES, rows={t: [] for t in KEYS})
    after = desired(before)
    (HERE / 'install-rows.json').write_text(json.dumps(after['rows'], indent=2) + '\n')
    (HERE / 'forward.sql').write_text(patch_sql(before, after), encoding='utf-8', newline='\n')
    (HERE / 'runtime-checks.json').write_text(json.dumps(runtime_checks(), indent=2) + '\n')
    print('Compiled additive Hate layout and runtime checks; no database writes.')


if __name__ == '__main__':
    main()

"""Plan scoped travel retention and reject unsafe capacity rollout budgets.

This module never connects to a server or applies its generated SQL.
"""
import argparse
import copy
import datetime
import json
from pathlib import Path

from content_patch import patch_sql

WORKERS = 20
TRAVEL_ZONES = {'ecommons':22, 'rivervale':19,
                'feerrott':47, 'commons':21, 'eastkarana':15}
# Milliseconds. Preserve script cleanup windows; highpasshold, all dungeons,
# Fear/Sky, and exceptional long-lived zones are deliberately absent.
DELAYS = {'ecommons':300000, 'rivervale':300000,
          'feerrott':600000, 'commons':900000, 'eastkarana':1800000}
MIB = 1024**2
DISK_BEFORE_BACKUP = 3 * 1024**3
DISK_AFTER_BACKUP = 2 * 1024**3
MEMORY_RESERVE = 512 * MIB
PER_ADDITIONAL_WORKER = 256 * MIB


def selected(capture):
    rows = capture['rows']['zone']
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate zone row ID')
    result = []
    for name, zone_id in TRAVEL_ZONES.items():
        matches = [row for row in rows if row['short_name'] == name and str(row['version']) == '0']
        if len(matches) != 1 or str(matches[0]['zoneidnumber']) != str(zone_id):
            raise ValueError(f'Zone identity drift: {name}')
        if str(matches[0]['shutdowndelay']) != '3600000':
            raise ValueError(f'Expected original one-hour timer: {name}')
        result.append(matches[0])
    return result


def plan(capture):
    ids = {row['id'] for row in selected(capture)}
    after = copy.deepcopy(capture)
    for row in after['rows']['zone']:
        if row['id'] in ids:
            row['shutdowndelay'] = str(DELAYS[row['short_name']])
    return after


def generate(capture):
    before_rows = selected(capture)
    ids = {row['id'] for row in before_rows}
    after_rows = [row for row in plan(capture)['rows']['zone'] if row['id'] in ids]
    before = {'rows': {'zone':before_rows}}
    after = {'rows': {'zone':after_rows}}
    # Identity + version scope catches extra/missing records as well as exact
    # captured row drift. Raw captures use the native CAST-to-CHAR representation.
    names = ','.join("'" + name + "'" for name in sorted(TRAVEL_ZONES))
    scope = {'zone':f'`version`=0 AND `short_name` IN ({names})'}
    return tuple(patch_sql(a, b, {'zone':['id']}, scope).replace(
        '-- Stop the target zone, back up and capture fresh preimages before applying.',
        '-- Requires the reviewed whole-runtime maintenance procedure and fresh backup.\n'
        '-- Restart the complete supervised game to refresh every ZoneStore and timer.\n'
        '-- Never kill an individual zone worker or restore player/checkpoint snapshots.'
    ) for a, b in ((before,after),(after,before)))


def resource_blockers(resources, *, after_backup=False):
    problems = []
    if resources['worker_env'] != ['NIGHTCAP_ZONE_WORKERS=12']:
        problems.append('worker baseline changed; recapture and reassess')
    required_disk = DISK_AFTER_BACKUP if after_backup else DISK_BEFORE_BACKUP
    if resources['disk_free'] < required_disk:
        problems.append(f'disk free must be at least {required_disk} bytes')
    native = resources['native']
    additional = (WORKERS - 12) * PER_ADDITIONAL_WORKER
    if max(native['memory_peak'],native['memory_current']) + additional + MEMORY_RESERVE > native['memory_limit']:
        problems.append('game memory budget leaves less than 512 MiB reserve')
    if resources['host_memory']['MemAvailable'] < additional + MEMORY_RESERVE:
        problems.append('host memory budget leaves less than 512 MiB reserve')
    return problems


def activation_blockers(capture, now=None, *, after_backup=False):
    """A necessary preflight, not deployment authorization or a stop/backup check."""
    problems = resource_blockers(capture['resources'], after_backup=after_backup)
    now = now or datetime.datetime.now(datetime.timezone.utc)
    captured = datetime.datetime.fromisoformat(capture['captured_at'])
    if captured.tzinfo is None or not 0 <= (now-captured).total_seconds() <= 3600:
        problems.append('capture must be no more than one hour old and timezone-aware')
    required = {'Zone:StateSavingOnShutdown':'true', 'Zone:KillProcessOnDynamicShutdown':'false'}
    rules = [line.split('\t') for line in capture['rules'].splitlines()]
    for name, value in required.items():
        matches = [row for row in rules if len(row)==3 and row[1]==name]
        if not any(row[0]=='1' and row[2]==value for row in matches) or any(row[2]!=value for row in matches):
            problems.append('required default/override rule drift: '+name)
    resources = capture['resources']
    if any(not s['running'] or s['oom'] for s in resources['services'].values()):
        problems.append('service stopped or OOM evidence requires review')
    events = dict(line.split() for line in resources['native']['memory_events'].splitlines())
    if any(int(events.get(key,0)) for key in ('oom','oom_kill','oom_group_kill')):
        problems.append('game OOM events require review')
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--require-safe-resources',action='store_true',
                        help='Reject stale/unsafe resource/rule captures before writing a plan')
    args = parser.parse_args()
    before = json.loads(args.capture.read_text(encoding='utf-8'))
    if args.require_safe_resources:
        problems = activation_blockers(before)
        if problems:
            parser.exit(1,'Rollout preflight refused: '+'; '.join(problems)+'\n')
    forward, inverse = generate(before)
    args.output.mkdir(parents=True,exist_ok=True)
    for name, text in [('forward.sql',forward),('rollback.sql',inverse)]:
        (args.output/name).write_text(text,encoding='utf-8')
    report = {'workers_before':12,'workers_after':WORKERS,
              'timers_minutes':{name:ms//60000 for name,ms in DELAYS.items()},
              'unchanged_zone_rows':len(before['rows']['zone'])-len(TRAVEL_ZONES),
              'resource_blockers':resource_blockers(before['resources']),
              'production_changed':False}
    (args.output/'plan.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()

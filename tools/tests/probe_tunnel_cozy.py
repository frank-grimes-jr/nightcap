"""Check proposed poses against the fresh entire EC scene and native terrain."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tunnel_cozy_layout import placements, STATIONS, ORNAMENTS
from probe_tunnel_courts import distance, patrol_segments

def scene(rows):
    npcs = {n['id']: n for n in rows['npc_types']}
    entries = {}
    for entry in rows['spawnentry']:
        entries.setdefault(entry['spawngroupID'], []).append(entry['npcID'])
    actors = []
    for spawn in rows['spawn2']:
        if spawn['zone'] != 'ecommons' or spawn['version'] != '0':
            continue
        for ident in entries.get(spawn['spawngroupID'], []):
            actor = dict(id=int(ident), name=npcs[ident]['name'],
                         pathgrid=int(spawn['pathgrid']), gap=12,
                         **{k: float(spawn[k]) for k in ('x', 'y', 'z', 'heading')})
            actor.update(placements().get(int(ident), {}))
            actors.append(actor)
    objects = []
    for obj in rows['object']:
        if obj['zoneid'] != '22':
            continue
        ident = int(obj['id'])
        name, x, y, heading = STATIONS.get(ident, (obj['display_name'] or obj['objectname'],
            float(obj['xpos']), float(obj['ypos']), float(obj['heading'])))
        objects.append(dict(id=ident, name=name, x=x, y=y, heading=heading, gap=12))
    furniture = []
    for door in rows['doors']:
        if door['zone'] == 'ecommons' and door['version'] in ('0', '-1'):
            furniture.append(dict(id=int(door['id']), name=door['name'],
                x=float(door['pos_x']), y=float(door['pos_y']),
                gap=15 if door['name'].startswith(('CART', 'WAGON', 'LEANTO')) else 10))
    furniture += [dict(id=i, name=v[2], x=v[3], y=v[4], gap=10) for i, v in ORNAMENTS.items()]
    return actors, objects, furniture

def preserved_frontage_issues(obstacles, changed):
    issues = []
    changed_keys = {key for key, _ in changed}
    for key, obj in obstacles:
        if key in changed_keys or not key.startswith(('npc-', 'object-')):
            continue
        heading = obj['heading'] * math.tau / 512
        front = dict(x=obj['x']+math.sin(heading)*12, y=obj['y']+math.cos(heading)*12)
        for other_key, other in changed:
            if distance(other, obj, front) < max(6, other['gap']-4):
                issues.append(f'Preserved {key} frontage blocked by {other_key}')
    return issues

def run(snapshot, evidence):
    rows = json.loads(snapshot.read_bytes())['rows']
    actors, objects, furniture = scene(rows)
    obstacles = [(f'npc-{a["id"]}', a) for a in actors if not a['pathgrid']]
    obstacles += [(f'object-{o["id"]}', o) for o in objects]
    obstacles += [(f'door-{d["id"]}', d) for d in furniture]
    changed = [(key, value) for key, value in obstacles if
        (key.startswith('npc-') and value['id'] in placements()) or
        (key.startswith('object-') and value['id'] in STATIONS) or
        (key.startswith('door-') and value['id'] in ORNAMENTS)]
    issues, points, rays, clearances = [], [], [], []
    routes = patrol_segments(rows)
    # A moved actor must not obstruct an untouched service's existing approach.
    # Existing unrelated crowding is not attributed to this revision.
    issues += preserved_frontage_issues(obstacles, changed)
    for key, obj in changed:
        for other_key, other in obstacles:
            if key == other_key:
                continue
            sep = math.hypot(obj['x']-other['x'], obj['y']-other['y'])
            gap = max(obj['gap'], other['gap'])
            clearances.append(sep)
            if sep < gap:
                issues.append(f'{key}/{other_key} overlap: {sep:.1f} < {gap}')
        for index, (a, b) in enumerate(routes):
            sep = distance(obj, a, b)
            if sep < obj['gap']:
                issues.append(f'{key}/walker-{index}: {sep:.1f} < {obj["gap"]}')
        points.append(dict(label=key, x=obj['x'], y=obj['y'], z=3.75))
        if key.startswith(('npc-', 'object-')):
            heading = obj['heading'] * math.tau / 512
            front = dict(x=obj['x']+math.sin(heading)*12, y=obj['y']+math.cos(heading)*12, z=3.75)
            for other_key, other in obstacles:
                if key != other_key and distance(other, obj, front) < max(6, other['gap']-4):
                    issues.append(f'{key} frontage blocked by {other_key}')
            points.append(dict(label=key+'-approach', **front))
            rays.append(dict(label=key+'-approach', **{'from': [obj['x'], obj['y'], 6.75]}, to=[front['x'], front['y'], 6.75]))
    # Explicit open walking links between workshop bays and the service nook.
    aisles = [((-350,-1769),(-301,-1762)), ((-301,-1762),(-301,-1797)),
              ((-301,-1797),(-323,-1808)), ((-323,-1808),(-314,-1820)),
              ((-314,-1820),(-323,-1830)), ((-323,-1830),(-313,-1861)),
              ((-313,-1861),(-279,-1859)), ((-279,-1859),(-268,-1824)),
              ((-263,-1785),(-195,-1758)),
              ((-195,-1758),(-145,-1736)), ((-211,-1617),(-181,-1601)),
              ((-181,-1601),(-162,-1596))]
    for index, (a, b) in enumerate(aisles):
        length = math.dist(a,b)
        for key, obj in obstacles:
            if distance(obj, dict(x=a[0],y=a[1]), dict(x=b[0],y=b[1])) < max(7,obj['gap']-4):
                issues.append(f'aisle-{index} blocked by {key}')
        for side in (-4,0,4):
            dx=(b[1]-a[1])/length*side;dy=-(b[0]-a[0])/length*side
            rays.append(dict(label=f'aisle-{index}-{side}', **{'from':[a[0]+dx,a[1]+dy,6.75]}, to=[b[0]+dx,b[1]+dy,6.75]))
        for step in range(math.ceil(length/4)+1):
            ratio=step/math.ceil(length/4)
            points.append(dict(label=f'aisle-{index}-{step}',x=a[0]+(b[0]-a[0])*ratio,y=a[1]+(b[1]-a[1])*ratio,z=3.75))
    request=dict(map='/home/eqemu/server/maps/base/ecommons.map', points=points, segments=rays)
    result=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1',
        '/tmp/nightcap-map-probe-20260920/map-probe'],input=json.dumps(request),text=True,capture_output=True,check=True)
    terrain=json.loads(result.stdout)
    for point in terrain['points']:
        if not all(s['ground_hit'] and abs(s['ground_z'])<.1 and s['headroom']>=12 for s in point['samples']):
            issues.append('Terrain '+point['label'])
    issues += ['Blocked ray '+ray['label'] for ray in terrain['segments'] if ray['blocked']]
    summary=dict(moved_npcs=len(placements()),stations=len(STATIONS),ornaments=len(ORNAMENTS),
        ground_samples=sum(len(p['samples']) for p in terrain['points']),rays=len(rays),
        minimum_static_separation=min(clearances),issues=issues,
        snapshot_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest())
    evidence.mkdir(parents=True,exist_ok=True)
    for name,data in [('scene',dict(actors=actors,objects=objects,furniture=furniture,aisles=aisles)),
                      ('geometry-input',request),('geometry',terrain),('geometry-summary',summary)]:
        (evidence/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    return summary

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args()
    result=run(args.snapshot,args.evidence)
    print(json.dumps(result,indent=2))
    sys.exit(bool(result['issues']))

"""Select bounded campaign placements using the retained native map raycaster."""
import hashlib
import itertools
import json
from pathlib import Path
import subprocess

from last_lantern_content import ROOT, SCENES

OUT = ROOT / 'docs/adventure-journal/release-20261107'
CONTAINER = 'akk-stack-eqemu-server-1'
PROBE = '/tmp/nightcap-map-probe-20260920/map-probe'


def probe(name, points, segments=()):
    # The retained probe casts from input Z+8. Start at NPC Z+1 instead, below
    # low tunnel ceilings, so a ceiling's upper face cannot masquerade as floor.
    native_points = [dict(p, z=p['z'] - 7) for p in points]
    request = dict(map='/home/eqemu/server/maps/base/' + name + '.map',
                   points=native_points, segments=list(segments))
    p = subprocess.run(['docker', 'exec', '-i', CONTAINER, PROBE],
                       input=json.dumps(request), text=True, capture_output=True, timeout=90)
    if p.returncode:
        raise RuntimeError(p.stderr[-1000:])
    result = json.loads(p.stdout)
    for point in result['points']:
        point['z'] += 7
    return result


def walkable(point):
    samples = point['samples']
    return (all(s['ground_hit'] and s['headroom'] >= 9 for s in samples)
            and max(s['ground_z'] for s in samples) - min(s['ground_z'] for s in samples) < 2
            and abs(samples[0]['ground_z'] - point['z']) < 7)


def distance(a, b):
    return sum((a[k] - b[k]) ** 2 for k in ('x', 'y', 'z')) ** .5


def floor_point(point):
    return dict(x=point['x'], y=point['y'], z=point['samples'][0]['ground_z'] + 3.75, heading=128)


def main():
    source = json.loads((OUT / 'production-content.json').read_text())
    entrance_spawns = json.loads((OUT / 'entrance-spawns.json').read_text())
    zones = {z['zone']: z for z in source['zones']}
    result = dict(scope='Native map geometry only; no client visibility or gameplay acceptance',
                  floor_ray_origin='NPC Z + 1; below low ceilings',
                  scenes={}, public=[], maps={})
    scene_zones = sorted({s['zone'] for s in SCENES})
    for identity in scene_zones:
        z = zones[identity]
        catalog = json.loads((ROOT / 'docs/dungeons/catalog.json').read_text())
        dungeon = next((d for d in catalog['dungeons'] if d['zone_id'] == identity), None)
        anchors = [z] + ([b['spawn'] for b in dungeon['bosses']] if dungeon else [])
        grid = [dict(label=f'{anchor_index}:{dx}:{dy}', x=a['x'] + dx, y=a['y'] + dy, z=a['z'])
                for anchor_index, a in enumerate(anchors)
                for dx, dy in itertools.product(range(-60, 61, 12), repeat=2)]
        captured = probe(z['name'], grid)
        good = sorted([p for p in captured['points'] if walkable(p)], key=lambda p: distance(p, z))
        assert good, 'No usable scene landing: ' + z['name']
        candidates = good
        selected = None
        for origin in candidates[:150]:
            near = [p for p in candidates if 18 <= distance(p, origin) <= 40]
            pairs = [(a, b) for a, b in itertools.combinations(near[:16], 2) if 18 <= distance(a, b) <= 40]
            for a, b in pairs[:30]:
                poses = [floor_point(p) for p in (origin, a, b)]
                arrival = next((floor_point(p) for p in good
                                if 10 <= distance(floor_point(p), poses[0]) <= 25
                                and all(distance(floor_point(p), actor) >= 10 for actor in poses)), None)
                if not arrival:
                    continue
                segments = [dict(label=str(i), **{'from': [poses[i][k] for k in ('x', 'y', 'z')],
                                                 'to': [poses[i + 1][k] for k in ('x', 'y', 'z')]})
                            for i in range(2)]
                segments.append(dict(label='arrival', **{'from': [arrival[k] for k in ('x', 'y', 'z')],
                                                        'to': [poses[0][k] for k in ('x', 'y', 'z')]}))
                path_points = []
                for segment in segments:
                    for sample in range(9):
                        xyz = [a + (b - a) * sample / 8 for a, b in zip(segment['from'], segment['to'])]
                        path_points.append(dict(label=f"{segment['label']}:{sample}", x=xyz[0], y=xyz[1], z=xyz[2]))
                lines = probe(z['name'], path_points, segments)
                if not any(s['blocked'] for s in lines['segments']) and all(walkable(p) for p in lines['points']):
                    selected = dict(zone=identity, name=z['name'], poses=poses,
                                    arrival=arrival, points=[origin, a, b],
                                    segments=lines['segments'], path_points=lines['points'])
                    break
            if selected:
                break
        assert selected, 'No connected three-position scene: ' + z['name']
        result['scenes'][str(identity)] = selected
        result['maps'][z['name']] = subprocess.check_output(
            ['docker', 'exec', CONTAINER, 'sha256sum', '/home/eqemu/server/maps/base/' + z['name'] + '.map'],
            text=True).split()[0]
        print(z['name'], 'selected 3 connected positions from', len(good), 'walkable candidates', flush=True)
    (OUT / 'geometry-scenes-candidate.json').write_text(json.dumps(result, indent=2) + '\n')
    public = [(22, 998900, -225, -1612, 3.75), (22, 998901, -245, -1612, 3.75),
              (22, 998902, -207, -1634, 3.75)]
    for index, identity in enumerate((65, 63, 11)):
        z = zones[identity]
        options = [dict(label=f'{dx}:{dy}', x=z['x'] + dx, y=z['y'] + dy, z=z['z'])
                   for dx, dy in itertools.product(range(-36, 37, 6), repeat=2)
                   if 14 <= (dx * dx + dy * dy) ** .5 <= 36]
        checked = probe(z['name'], options)
        actors = [a for a in entrance_spawns if a['zone'] == identity]
        choices = [p for p in checked['points'] if walkable(p)
                   and all(distance(floor_point(p), actor) >= 14 for actor in actors)]
        assert choices, 'No clear courier position: ' + z['name']
        chosen = min(choices, key=lambda p: distance(p, z))
        pose = floor_point(chosen)
        public.append((identity, 998903 + index, pose['x'], pose['y'], pose['z']))
    for identity, group in itertools.groupby(sorted(public), key=lambda p: p[0]):
        rows = list(group)
        points = [dict(label=str(npc), x=x, y=y, z=z) for _, npc, x, y, z in rows]
        checked = probe(zones[identity]['name'], points)
        assert all(walkable(p) for p in checked['points']), 'Public placement needs review: ' + zones[identity]['name']
        for p, row in zip(checked['points'], rows):
            pose = floor_point(p)
            if identity == 22:
                nearest = min(distance(pose, actor) for actor in source['hub_spawns'])
                assert nearest >= 14, 'Crowded company placement: ' + p['label']
                p['nearest_static_npc'] = nearest
            result['public'].append(dict(zone=identity, npc=row[1], **pose, evidence=p))
    (OUT / 'geometry.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Wrote verified native geometry for eight scenes and six public services.')


if __name__ == '__main__':
    main()

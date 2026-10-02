"""Audit the complete tunnel scene and raycast the revised actors and walk routes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tunnel_social_layout import placements, paths, STATIONS
from probe_tunnel_courts import distance

def scene(source):
    npcs={int(n['id']):n for n in source['npc_types']}
    entries={}
    for e in source['spawnentry']:
        entries.setdefault(e['spawngroupID'],[]).append(int(e['npcID']))
    if not {i for values in entries.values() for i in values}<=npcs.keys():
        raise ValueError('Incomplete native NPC capture')
    actors={}
    for s in source['spawn2']:
        for ident in entries.get(s['spawngroupID'],[]):
            if -500<=float(s['x'])<=50 and -1900<=float(s['y'])<=-1450 or ident in placements():
                if ident in actors:raise ValueError('Ambiguous tunnel spawn: '+str(ident))
                actors[ident]=dict(id=ident,name=npcs[ident]['name'],spawn_id=s['id'],
                    pathgrid=int(s['pathgrid']),**{k:float(s[k]) for k in ('x','y','z','heading')})
    for ident,p in placements().items():actors[ident].update(p)
    for ident,route in paths().items():actors[ident].update({k:route[0][k] for k in ('x','y','z','heading')})
    objects=[]
    for row in source['object']:
        ident=int(row['id']);name=row['display_name'] or row['objectname']
        x,y,z,h=(float(row[k]) for k in ('xpos','ypos','zpos','heading'))
        if ident in STATIONS:name,x,y,h=STATIONS[ident];z=0
        objects.append(dict(id=ident,name=name,x=x,y=y,z=z,heading=h,gap=12))
    furniture=[dict(id=d['id'],name=d['name'],x=float(d['pos_x']),y=float(d['pos_y']),
                    gap=15 if d['name'].startswith(('CART','WAGON','LEANTO')) else 10)
               for d in source['doors']]
    return actors,objects,furniture

def run(snapshot,evidence):
    source=json.loads(snapshot.read_bytes())['rows']
    actors,objects,furniture=scene(source)
    stationary=[a for a in actors.values() if not a['pathgrid']]
    obstacles=stationary+objects+furniture
    issues=[];points=[];segments=[];clearances=[]
    for ident,p in placements().items():
        for other in obstacles:
            if other in stationary and other['id']==ident:continue
            gap=other.get('gap',12);sep=math.hypot(p['x']-other['x'],p['y']-other['y'])
            clearances.append(sep)
            if sep<gap:issues.append(f"NPC overlap {ident}/{other['name']}: {sep:.1f} < {gap}")
        h=p['heading']*math.tau/512
        front=dict(x=p['x']+math.sin(h)*12,y=p['y']+math.cos(h)*12,z=p['z'])
        for other in obstacles:
            if other in stationary and other['id']==ident:continue
            sep=distance(other,p,front);gap=max(6,other.get('gap',12)-4)
            if sep<gap:issues.append(f"Frontage {ident}/{other['name']}: {sep:.1f} < {gap}")
        points.append(dict(label=f'front-{ident}',**front))
        segments.append(dict(label=f'front-{ident}',**{'from':[p['x'],p['y'],p['z']+3]},to=[front['x'],front['y'],front['z']+3]))
    # Existing native stations/NPCs are included in terrain coverage. Existing
    # native overlaps are recorded separately, never silently treated as new work.
    for p in actors.values():points.append(dict(label=f"actor-{p['id']}",**{k:p[k] for k in ('x','y','z')}))
    for p in objects:
        if p['id'] in STATIONS:
            for other in obstacles:
                if other is p:continue
                sep=math.hypot(p['x']-other['x'],p['y']-other['y'])
                if sep<other.get('gap',12):issues.append(f"Station {p['name']}/{other['name']}: {sep:.1f}")
            points.append(dict(label=f"station-{p['id']}",x=p['x'],y=p['y'],z=3.75))
    for ident,route in paths().items():
        for index,(a,b) in enumerate(zip(route,route[1:])):
            for other in obstacles:
                sep=distance(other,a,b);gap=other.get('gap',12)
                if sep<gap:issues.append(f"Route {ident}/{index}/{other['name']}: {sep:.1f} < {gap}")
            length=math.hypot(a['x']-b['x'],a['y']-b['y']);steps=math.ceil(length/4)
            for j in range(steps+1):
                points.append(dict(label=f'walk-{ident}-{index}-{j}',x=a['x']+(b['x']-a['x'])*j/steps,
                                   y=a['y']+(b['y']-a['y'])*j/steps,z=3.75))
            # Test the whole path plus shoulder-width rays, not just waypoints.
            dx=(b['y']-a['y'])/length*4;dy=-(b['x']-a['x'])/length*4
            for side in (-1,0,1):
                segments.append(dict(label=f'walk-{ident}-{index}-{side}',
                    **{'from':[a['x']+side*dx,a['y']+side*dy,6.75]},
                    to=[b['x']+side*dx,b['y']+side*dy,6.75]))
    request=dict(map='/home/eqemu/server/maps/base/ecommons.map',points=points,segments=segments)
    result=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1',
        '/tmp/nightcap-map-probe-20260920/map-probe'],input=json.dumps(request),text=True,capture_output=True,check=True)
    terrain=json.loads(result.stdout)
    for p in terrain['points']:
        if not all(s['ground_hit'] and abs(s['ground_z'])<.1 and s['headroom']>=12 for s in p['samples']):
            issues.append('Terrain '+p['label'])
    issues.extend('Blocked ray '+s['label'] for s in terrain['segments'] if s['blocked'])
    summary=dict(actors=len(actors),repositioned=len(placements()),walkers=len(paths()),
                 stations=len(STATIONS),ground_samples=len(points)*5,rays=len(segments),issues=issues,
                 snapshot_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest())
    evidence.mkdir(parents=True,exist_ok=True)
    for name,data in [('scene',dict(actors=actors,objects=objects,furniture=furniture)),
                      ('geometry-input',request),('geometry',terrain),('summary',summary)]:
        (evidence/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();r=run(a.snapshot,a.evidence);print(json.dumps(r,indent=2));sys.exit(bool(r['issues']))

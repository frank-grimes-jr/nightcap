"""Check compact residents, outside access, fire clearance and all eight walking routes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tunnel_campfire import positions, RING_CENTER
from probe_tunnel_social import scene, paths, distance

def run(snapshot,evidence):
    source=json.loads(snapshot.read_bytes())['rows'];actors,objects,furniture=scene(source)
    positions_now=positions()
    for ident,p in positions_now.items():actors[ident].update(p)
    stationary=[a for a in actors.values() if not a['pathgrid']]
    fire=dict(id=999606,name='Resident campfire',x=RING_CENTER[0],y=RING_CENTER[1],z=0,gap=9)
    obstacles=stationary+objects+furniture+[fire];issues=[];points=[];segments=[];clearances=[]
    for ident,p in positions_now.items():
        for other in obstacles:
            if other in stationary and other['id']==ident:continue
            sep=math.hypot(p['x']-other['x'],p['y']-other['y']);gap=other.get('gap',12)
            clearances.append(sep)
            if sep<gap:issues.append(f"Resident overlap {ident}/{other['name']}: {sep:.1f} < {gap}")
        # Players approach these social residents from outside the ring. The
        # existing merchant frontage policy remains unchanged in its own probe.
        h=p['heading']*math.tau/512
        approach=dict(x=p['x']-math.sin(h)*12,y=p['y']-math.cos(h)*12,z=p['z'])
        for other in obstacles:
            if other in stationary and other['id']==ident:continue
            if distance(other,p,approach)<max(6,other.get('gap',12)-4):issues.append(f"Access {ident}/{other['name']}")
        points.extend([dict(label=f'resident-{ident}',**p),dict(label=f'access-{ident}',**approach)])
        segments.append(dict(label=f'access-{ident}',**{'from':[p['x'],p['y'],6.75]},to=[approach['x'],approach['y'],6.75]))
    points.append(dict(label='campfire',x=fire['x'],y=fire['y'],z=3.75))
    for ident,route in paths().items():
        for index,(a,b) in enumerate(zip(route,route[1:])):
            for other in [actors[i] for i in positions_now]+[fire]:
                if distance(other,a,b)<other.get('gap',12):issues.append(f"Route {ident}/{index}/{other['name']}")
    request=dict(map='/home/eqemu/server/maps/base/ecommons.map',points=points,segments=segments)
    result=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','/tmp/nightcap-map-probe-20260920/map-probe'],input=json.dumps(request),text=True,capture_output=True,check=True)
    terrain=json.loads(result.stdout)
    for p in terrain['points']:
        if not all(s['ground_hit'] and abs(s['ground_z'])<.1 and s['headroom']>=12 for s in p['samples']):issues.append('Terrain '+p['label'])
    issues.extend('Blocked ray '+s['label'] for s in terrain['segments'] if s['blocked'])
    report=dict(actors=len(actors),changed_residents=6,fire=dict(model='CAMPFIRE',size=65,x=fire['x'],y=fire['y']),
                ground_samples=len(points)*5,rays=len(segments),walking_routes=len(paths()),minimum_resident_clearance=min(clearances),
                issues=issues,snapshot_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest())
    evidence.mkdir(parents=True,exist_ok=True)
    for name,value in [('summary',report),('geometry-input',request),('geometry',terrain)]:
        (evidence/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();r=run(a.snapshot,a.evidence);print(json.dumps(r,indent=2));sys.exit(bool(r['issues']))

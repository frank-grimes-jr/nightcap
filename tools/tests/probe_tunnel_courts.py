"""Check native terrain, service frontages and retained furniture/patrol clearance."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tunnel_courts import placements, ROOT

def run(snapshot,zones,container,probe,evidence):
    evidence.mkdir(parents=True,exist_ok=True)
    source=json.loads(snapshot.read_bytes())['rows'];positions=placements()
    npcs={n['id']:n for n in source['npc_types']}
    entries={r['spawngroupID']:r['npcID'] for r in source['spawnentry'] if r['npcID'] in npcs}
    obstacles=[]
    for s in source['spawn2']:
        ident=int(entries.get(s['spawngroupID'],0))
        if ident and ident not in positions and s['pathgrid']=='0':
            obstacles.append((str(ident),float(s['x']),float(s['y']),12))
    obstacles += [(o['display_name'],float(o['xpos']),float(o['ypos']),12) for o in source['object'] if o['display_name']]
    obstacles += [(d['name']+d['id'],float(d['pos_x']),float(d['pos_y']),
                   15 if d['name'].startswith(('CART','LEANTO')) else 10) for d in source['doors']]
    neighbors=[]
    for ident,p in positions.items():
        compare=obstacles+[(str(i),q['x'],q['y'],12) for i,q in positions.items() if i>ident]
        for name,x,y,gap in compare:
            distance=math.hypot(p['x']-x,p['y']-y)
            if distance<gap:raise ValueError(f'Overlap: {ident} / {name}: {distance}')
            neighbors.append(distance)
    def distance(p,a,b):
        ax,ay=float(a['x']),float(a['y']);dx=float(b['x'])-ax;dy=float(b['y'])-ay
        t=max(0,min(1,((p['x']-ax)*dx+(p['y']-ay)*dy)/(dx*dx+dy*dy)))
        return math.hypot(p['x']-ax-t*dx,p['y']-ay-t*dy)
    patrol=[]
    for gid in range(999700,999708):
        route=sorted((r for r in source['grid_entries'] if int(r['gridid'])==gid),key=lambda r:int(r['number']))
        if len(route)!=4:raise ValueError('Patrol route drift')
        for p in positions.values():patrol.extend(distance(p,a,b) for a,b in zip(route,route[1:]))
    if min(patrol)<12:raise ValueError('Patrol overlaps a court')
    points=[];segments=[]
    for ident,p in positions.items():
        h=p['heading']*2*math.pi/512
        a=dict(x=p['x']+math.sin(h)*12,y=p['y']+math.cos(h)*12,z=p['z'])
        points += [dict(label=str(ident),**p),dict(label=str(ident)+'-approach',**a)]
        segments.append(dict(**{'from':[p['x'],p['y'],p['z']+3]},to=[a['x'],a['y'],a['z']+3]))
    def native(request):
        result=subprocess.run(['docker','exec','-i',container,probe],input=json.dumps(request),
                              text=True,capture_output=True,check=True)
        return json.loads(result.stdout)
    request=dict(map='/home/eqemu/server/maps/base/ecommons.map',points=points,segments=segments)
    terrain=native(request)
    for p in terrain['points']:
        if not all(s['ground_hit'] and abs(s['ground_z'])<.1 and s['headroom']>=12 for s in p['samples']):
            raise ValueError('Unsafe terrain: '+p['label'])
    if any(s['blocked'] for s in terrain['segments']):raise ValueError('Blocked service approach')
    catalog=ROOT/'server-mods/plugins/tunnel_spire_data.pl'
    code='package plugin; do $ARGV[0] or die $@ || $!; print JSON::PP::encode_json(tunnel_spire_catalog());'
    routes=json.loads(subprocess.check_output(['perl','-MJSON::PP','-e',code,str(catalog)],text=True))
    metadata=json.loads(zones.read_bytes());landings=[]
    for r in routes:
        z=metadata[r['zone']]
        if int(z[1])!=r['zone_id'] or int(z[3])>r['era'] or int(z[4]) or int(z[5])>r['min_level']:
            raise ValueError('Destination gate drift: '+r['zone'])
        report=native(dict(map='/home/eqemu/server/maps/base/'+z[2]+'.map',points=[dict(label=r['zone'],**{k:r[k] for k in ('x','y','z')})]))
        if not all(s['ground_hit'] and 0<r['z']-s['ground_z']<8 and s['headroom']>=12 for s in report['points'][0]['samples']):
            raise ValueError('Unsafe spire landing: '+r['zone'])
        landings.append(report)
    summary=dict(npc_positions=len(positions),court_ground_samples=len(points)*5,approach_rays=len(segments),
        spire_destinations=len(routes),spire_ground_samples=len(routes)*5,
        minimum_patrol_clearance=round(min(patrol),3),minimum_furniture_or_npc_clearance=round(min(neighbors),3),
        status='geometry_passed_visual_QA_pending',snapshot_sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest())
    for name,data in [('geometry-input',request),('geometry',terrain),('spire-geometry',landings),('geometry-summary',summary)]:
        (evidence/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--zone-metadata',type=Path,required=True)
    p.add_argument('--container',default='akk-stack-eqemu-server-1')
    p.add_argument('--probe',default='/tmp/nightcap-map-probe-20260920/map-probe')
    p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    print(json.dumps(run(a.snapshot,a.zone_metadata,a.container,a.probe,a.evidence)))

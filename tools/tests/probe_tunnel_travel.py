"""Verify alcove ground/approach using the existing native EQEmu map probe."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tunnel_travel import ROOT, POSITION, PROPS


def run(probe,container,evidence):
    points=[dict(label='Merrin',**POSITION)]
    points += [dict(label=name,x=x,y=y,z=3.75) for name,x,y,size in PROPS]
    points += [dict(label='Approach',x=-335,y=y,z=3.75) for y in (-1565,-1555,-1545)]
    request=dict(map='/home/eqemu/server/maps/base/ecommons.map',points=points,
        segments=[{'from':[-335,-1565,6],'to':[-335,-1537,6]},
                  {'from':[-315,-1550,6],'to':[-335,-1545,6]}])
    response=subprocess.run(['docker','exec','-i',container,probe],input=json.dumps(request),
                            text=True,capture_output=True,check=True)
    result=json.loads(response.stdout)
    for point in result['points']:
        if not all(s['ground_hit'] and abs(s['ground_z'])<0.1 and s['headroom']>=12 for s in point['samples']):
            raise ValueError('Unsafe ground/headroom: '+point['label'])
    if any(s['blocked'] for s in result['segments']):raise ValueError('Blocked approach')
    # Native geometry excludes these new DB props. Verify the known newer layout
    # and each patrol segment separately; graphical/collision QA remains manual.
    layout=json.loads((ROOT/'docs/releases/tunnel-services-starters/layout.json').read_bytes())
    existing=list(layout['relocations'].values())+[n['position'] for n in layout['npcs']]
    nearest=min(math.hypot(p['x']-n['x'],p['y']-n['y']) for p in points[:4] for n in existing)
    if nearest<12:raise ValueError('Alcove overlaps newer NPC layout')
    def distance(p,a,b):
        dx=b['x']-a['x'];dy=b['y']-a['y']
        t=max(0,min(1,((p['x']-a['x'])*dx+(p['y']-a['y'])*dy)/(dx*dx+dy*dy)))
        return math.hypot(p['x']-a['x']-t*dx,p['y']-a['y']-t*dy)
    patrol=min(distance(p,a,b) for p in points[:4] for path in layout['paths'].values() for a,b in zip(path,path[1:]))
    if patrol<12:raise ValueError('Alcove overlaps newer patrol routes')
    result.update(newer_npc_clearance=round(nearest,2),newer_patrol_clearance=round(patrol,2),
                  status='geometry_passed_visual_QA_pending')
    evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'geometry-input.json').write_text(json.dumps(request,indent=2)+'\n')
    (evidence/'geometry.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(points=len(points),samples=5*len(points),segments=2,
                         npc_clearance=result['newer_npc_clearance'],patrol_clearance=result['newer_patrol_clearance'])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--probe',required=True)
    p.add_argument('--container',default='akk-stack-eqemu-server-1');p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();run(a.probe,a.container,a.evidence)

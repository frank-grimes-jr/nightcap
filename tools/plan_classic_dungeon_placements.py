"""Choose separated entrance Keeper poses using the native map raycaster."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
from classic_dungeon_catalog import ADDED_DUNGEONS

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args(); data=json.loads(a.capture.read_text()); result={}
    groups={e['spawngroupID'] for e in data['spawnentry'] if e['npcID']==999240}
    for short,zone,keeper,band,roster in ADDED_DUNGEONS:
        row=next(z for z in data['zone'] if z['short_name']==short)
        x,y,z=(row['safe_'+axis] for axis in 'xyz')
        points=[dict(label='arrival',x=x,y=y,z=z)]
        for radius in (16,24,32):
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(.707,.707),(-.707,.707),(.707,-.707),(-.707,-.707)):
                points.append(dict(label=str(len(points)),x=round(x+radius*dx,3),y=round(y+radius*dy,3),z=z))
        request={'map':'/home/eqemu/server/maps/base/'+short+'.map','points':points}
        command=['docker','exec','-i','akk-stack-eqemu-server-1','/tmp/nightcap-map-probe-20260920/map-probe']
        probe=json.loads(subprocess.run(command,input=json.dumps(request),text=True,capture_output=True,check=True).stdout)
        waypoints=[s for s in data['spawn2'] if s['zone']==short and s['spawngroupID'] in groups]
        viable=[]
        for point in probe['points'][1:]:
            samples=point['samples']
            if not all(s['ground_hit'] and s['headroom']>=8 for s in samples):continue
            floor=samples[0]['ground_z']
            # Sky's native safe point is intentionally above the island floor.
            if abs(floor-z)>(25 if short=='airplane' else 10) or max(abs(s['ground_z']-floor) for s in samples)>2:continue
            pose={k:point[k] for k in ('x','y')};pose['z']=round(floor+2,3)
            if any(math.dist([pose[k] for k in 'xyz'],[w[k] for k in 'xyz'])<12 for w in waypoints):continue
            nearby=[s for s in data['spawn2'] if s['zone']==short and math.dist([pose[k] for k in 'xyz'],[s[k] for k in 'xyz'])<8]
            if nearby:continue
            viable.append(dict(pose=pose,samples=samples))
        arrival_floor=probe['points'][0]['samples'][0]
        assert arrival_floor['ground_hit'],short+' arrival has no ground'
        rays=[{'from':[x,y,arrival_floor['ground_z']+5],'to':[v['pose']['x'],v['pose']['y'],v['pose']['z']+3]} for v in viable]
        rayprobe=json.loads(subprocess.run(command,input=json.dumps({'map':request['map'],'points':[],'segments':rays}),text=True,capture_output=True,check=True).stdout)
        selected=next((v for v,r in zip(viable,rayprobe['segments']) if not r['blocked']),None)
        digest=subprocess.check_output(['docker','exec','akk-stack-eqemu-server-1','sha256sum',request['map']],text=True).split()[0]
        result[short]={'zone_id':zone,'keeper_id':keeper,'arrival':points[0],'selected':selected,
            'map_sha256':digest,'probe':probe,'rays':rayprobe['segments']}
        print(short,selected['pose'] if selected else 'NO VERIFIED POSE',flush=True)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    assert all(r['selected'] for r in result.values()),'Resolve rejected entrance poses before compiling content'

if __name__=='__main__':main()

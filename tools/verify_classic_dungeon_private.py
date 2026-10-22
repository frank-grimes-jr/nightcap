"""Read-only local native map verification for canonical Sky actors."""
import hashlib
import json
from pathlib import Path
import subprocess
from classic_dungeon_catalog import SKY_PRIVATE, SKY_SERVICES

ROOT=Path(__file__).resolve().parents[1]
def main():
    rows=SKY_PRIVATE+SKY_SERVICES
    request={'map':'/home/eqemu/server/maps/base/airplane.map',
        'points':[dict(label=str(s),x=x,y=y,z=z) for s,g,n,x,y,z,h in rows]}
    result=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1',
        '/tmp/nightcap-map-probe-20260920/map-probe'],input=json.dumps(request),text=True,capture_output=True,check=True)
    evidence=json.loads(result.stdout)
    for point in evidence['points']:
        assert all(s['ground_hit'] and s['headroom']>=8 for s in point['samples']),point['label']
        assert 0<=point['z']-point['samples'][0]['ground_z']<=8,point['label']
    evidence['input_sha256']=hashlib.sha256(json.dumps(rows).encode()).hexdigest()
    evidence['status']='12 poses / 60 ground and headroom samples passed; visible/pathing QA pending'
    (ROOT/'docs/dungeons/classic-expansion-20261022/sky-geometry.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(evidence['status'])
if __name__=='__main__':main()

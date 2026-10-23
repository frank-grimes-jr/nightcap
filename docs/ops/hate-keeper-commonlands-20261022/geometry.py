"""Read-only native map proof, authenticated against production map bytes."""
import json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
docker=['docker','exec','-i','akk-stack-eqemu-server-1']
map_path='/home/eqemu/server/maps/base/ecommons.map'
payload={'map':map_path,'points':[dict(x=-346,y=-1570,z=3),dict(x=-346,y=-1582,z=3)],
         'segments':[{'from':[-346,-1582,6],'to':[-346,-1570,6]}]}
result=json.loads(subprocess.check_output(docker+['/tmp/nightcap-map-probe-20260920/map-probe'],input=json.dumps(payload),text=True))
local=subprocess.check_output(docker+['sha256sum',map_path],text=True).split()[0]
remote="from pathlib import Path;import hashlib;print(hashlib.sha256(Path('/opt/nightcap/deploy/production/data/server/maps/base/ecommons.map').read_bytes()).hexdigest())"
ssh=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
live=subprocess.check_output(ssh,input=remote,text=True).strip()
assert local==live,'Map mismatch'
assert all(s['ground_hit'] and abs(s['ground_z'])<0.01 and s['headroom']>=20 for p in result['points'] for s in p['samples'])
assert all(not s['blocked'] for s in result['segments'])
result.update(map_sha256=local,production_map_equal=True,native_appearance_accepted=False)
(HERE/'geometry.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'samples':10,'ground_z':0,'minimum_headroom':min(s['headroom'] for p in result['points'] for s in p['samples']),'approach_clear':True,'production_map_equal':True}))

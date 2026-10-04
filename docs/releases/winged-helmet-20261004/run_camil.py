"""Run the scoped Camil deployment; keep private backups on the server."""
import ast, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0,str(ROOT.parent/'tunnel-class-courts'))
from capture import SSH

tree = ast.parse((ROOT/'refresh_remote.py').read_text())
probe = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROBE' for t in n.targets))
payload = {name:(ROOT/'camil-plan'/(name+'.sql')).read_text() for name in ('forward','rollback')}
payload['probe'] = probe
payload['expected_npc'] = json.loads((ROOT/'item-before.json').read_text())['rows']['npc_types']
payload['binary_hashes'] = json.loads((ROOT/'refresh.json').read_text())['after']['hashes']
source = 'import io,sys\nsys.stdin=io.StringIO('+repr(json.dumps(payload))+')\n'+(ROOT/'deploy_camil_remote.py').read_text()
result = subprocess.run(SSH+['sudo -n python3 -'],input=source,text=True,capture_output=True,timeout=400)
if result.returncode:
    print(result.stdout)
    raise RuntimeError(result.stderr)
with (ROOT/'camil-deployment.json').open('x') as out:
    out.write(result.stdout)
data = json.loads(result.stdout)
print(json.dumps({k:v for k,v in data.items() if k not in ('before_runtime','after_runtime')}))

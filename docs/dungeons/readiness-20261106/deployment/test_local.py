"""Run Linux release-unit tests in an isolated local build-container directory."""
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
payload={n:(HERE/n).read_text(encoding='utf-8') for n in ('rollout.py','test_rollout.py')}
code='''from pathlib import Path
import json,subprocess,tempfile
with tempfile.TemporaryDirectory(prefix='nightcap-keeper-ops-') as tmp:
 root=Path(tmp)
 for name,text in payload.items():(root/name).write_text(text)
 result=subprocess.run(['python3','-B','-m','unittest','-v','test_rollout'],cwd=root,text=True,capture_output=True)
 assert result.returncode==0,result.stderr
 print(json.dumps({'status':'PASS','tests':6,'output':result.stderr}))
'''
result=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input='payload='+repr(payload)+'\n'+code,text=True,encoding='utf-8',capture_output=True,timeout=90)
if result.returncode:raise RuntimeError(result.stderr[-3500:])
report=json.loads(result.stdout);(HERE/'linux-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(result.stdout)

"""Execute the production-method checks against the preserved hardened candidate."""
import hashlib,json,shutil,subprocess
from pathlib import Path
source=Path('/tmp/nightcap-passive-aa-build-20261004-r2/source')
root=Path('/tmp/nightcap-passive-aa-release-tests')
root.mkdir(exist_ok=False)
for name in ('zone/exp.cpp','zone/client.cpp','zone/client_packet.cpp','zone/zonedb.cpp','zone/gm_commands/aa_exp.cpp'):
    p=root/'server-mods/code'/name;p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(source/name)
test=root/'tools/tests/test_passive_aa.py';test.parent.mkdir(parents=True)
shutil.copyfile('/tmp/nightcap-passive-aa-release-input-20261004/test_passive_aa.py',test)
result=subprocess.run(['python3',str(test)],text=True,capture_output=True)
(root/'test.log').write_text(result.stdout+result.stderr)
assert result.returncode==0,result.stdout+result.stderr
assert '71 checks, 0 failures' in result.stdout
(root/'tests.json').write_text(json.dumps({'native_checks':71,'failures':0,'test_sha256':hashlib.sha256(test.read_bytes()).hexdigest(),'source':'fresh hardened production candidate','output':result.stdout.strip()},indent=2)+'\n')
print(result.stdout)

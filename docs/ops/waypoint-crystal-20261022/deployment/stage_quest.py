"""Run quest recovery regressions on Linux in an isolated private stage."""
import hashlib
import json
import subprocess
from deploy import SSH,HERE,STAGE,run

files=[HERE/name for name in ('quest_remote.py','world_control.py','test_quest.py')]
pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
upload='/home/ubuntu/waypoint-quest-20261022'
subprocess.run(SSH+['mkdir -p -m 700 '+upload],check=True,timeout=30)
subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],*map(str,files),SSH[-1]+':'+upload+'/'],check=True,timeout=60)
source=f'''
import hashlib,json,os,subprocess
from pathlib import Path
upload=Path({upload!r});stage=Path({(STAGE+'/quest-activation')!r});pins={pins!r}
assert not upload.is_symlink() and {{p.name for p in upload.iterdir()}}==set(pins)
assert not stage.is_symlink();stage.mkdir(mode=0o700)
for name,digest in pins.items():
 p=upload/name;assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==digest
 with (stage/name).open('xb') as f:f.write(p.read_bytes());f.flush();os.fsync(f.fileno())
tests=subprocess.run(['python3','-B','test_quest.py'],cwd=stage,capture_output=True,text=True,timeout=40)
assert tests.returncode==0,tests.stderr
print(json.dumps({{'stage':str(stage),'pins':pins,'linux_tests':tests.stderr,'production_quest_unchanged':True}}))
'''
report=json.loads(run(source))
(HERE/'quest-stage.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report))

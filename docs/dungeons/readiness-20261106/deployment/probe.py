"""Read-only current OVH baseline and retained operator API inspection."""
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
CODE='''from pathlib import Path
import importlib.util,json,inspect,shutil
prior=Path('/opt/nightcap/releases/character-stats-window-20261106-v1')
spec=importlib.util.spec_from_file_location('current_stats',prior/'rollout.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);p.initialize()
report={'services':{s:p.r.compact(s) for s in ('game','gateway','db','web','tunnel')},'binaries':p.binaries(),'free_bytes':shutil.disk_usage(p.ROOT).free,'functions':{k:inspect.getsource(fn) for k,fn in [('startup_guards',p.startup.startup_guards),('health',p.base.health),('hold',p.h.hold)]}}
print(json.dumps(report))
'''
if __name__=='__main__':
    result=subprocess.run(SSH+['sudo -n python3 -'],input=CODE,text=True,encoding='utf-8',capture_output=True,timeout=180)
    if result.returncode:raise RuntimeError(result.stderr[-2200:])
    data=json.loads(result.stdout)
    (HERE/'baseline-probe.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))

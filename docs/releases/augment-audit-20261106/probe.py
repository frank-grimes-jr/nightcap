"""Read-only live baseline probe; no secrets, player rows or service changes."""
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
SSH = ['C:/Windows/System32/OpenSSH/ssh.exe', '-i', 'C:/Users/verre/.ssh/nightcap_ovh',
       '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=yes',
       'ubuntu@135.148.47.202']
CODE = '''import importlib.util,json,shutil,hashlib,inspect
from pathlib import Path
prior=Path('/opt/nightcap/releases/power-source-xp-display-20261103-v1')
spec=importlib.util.spec_from_file_location('prior_display',prior/'rollout.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p);p.initialize()
r,h=p.r,p.h
game=r.compact('game')
cache=h.caches()
report={'free_bytes':shutil.disk_usage(p.ROOT).free,'services':{s:r.compact(s) for s in ('game','gateway','db','web','tunnel')},'image_hashes':r.image_hashes(game['image_id']),'expected_binaries':p.binaries(),'cache_summary':cache,'helper_paths':{n:inspect.getsourcefile(m) for n,m in [('release',r),('content',h),('base',p.base)]},'functions':{n:inspect.getsource(getattr(m,n)) for m,n in [(h,'caches'),(h,'content'),(h,'contract'),(r,'database_backup')]}}
print(json.dumps(report))
'''

if __name__ == '__main__':
    p = subprocess.run(SSH + ['sudo -n python3 -'], input=CODE, text=True, encoding='utf-8', capture_output=True, timeout=180)
    if p.returncode:
        raise RuntimeError(p.stderr[-2500:])
    data = json.loads(p.stdout)
    artifact = HERE / 'probe-private.json'
    artifact.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'free_bytes': data['free_bytes'], 'services': data['services'],
                      'image_hashes': data['image_hashes'], 'cache_summary': data['cache_summary'],
                      'helper_paths': data['helper_paths']}))

"""Read-only post-activation evidence; execute on the production host via SSH."""
import datetime
import json
from pathlib import Path
import subprocess

root=Path('/opt/nightcap/deploy/production')
out=Path('/opt/nightcap/backups/commonlands-services-20261016')
result={name:json.loads((out/name).read_text()) for name in
        ('result.json','rehearsal.json','placement.json','cache-verification.json','backup.json')}
services=json.loads(subprocess.run(['docker','inspect','nightcap-production-game-1',
    'nightcap-production-gateway-1','nightcap-production-db-1'],text=True,capture_output=True,check=True).stdout)
result['services']=[dict(name=s['Name'],running=s['State']['Running'],
    health=s['State'].get('Health',{}).get('Status'),restarts=s['RestartCount'],
    started=s['State']['StartedAt']) for s in services]
code='''import hashlib,json,pathlib
rows=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  exe=(p/'exe').resolve();name=exe.name
  if str(exe).startswith('/opt/nightcap/bin/') and name in ('world','zone','loginserver','ucs'):
   rows.append(dict(pid=int(p.name),name=name,sha256=hashlib.sha256((p/'exe').read_bytes()).hexdigest()))
 except (FileNotFoundError,PermissionError):pass
print(json.dumps(rows))'''
result['processes']=json.loads(subprocess.run(['docker','compose','exec','-T','game',
    'python3','-c',code],cwd=root,text=True,capture_output=True,check=True).stdout)
logs=subprocess.run(['docker','logs','--since',result['result.json']['runtime_started_at'],
    'nightcap-production-game-1'],text=True,capture_output=True,check=True)
lines=(logs.stdout+logs.stderr).splitlines()
result['error_matches']=[s for s in lines if any(x in s.lower() for x in
    ('segmentation fault','query failed','mysql error','runtimeerror','error compiling','failed to load npc'))]
result['ecommons_log_lines']=sum('ecommons' in s for s in lines)
result['utc_checked']=datetime.datetime.now(datetime.timezone.utc).isoformat()
assert all(s['running'] and s['health'] in ('healthy',None) for s in result['services'])
assert all(s['health']=='healthy' for s in result['services'] if s['name'].endswith(('game-1','db-1')))
assert len([p for p in result['processes'] if p['name']=='zone'])==12
assert not result['error_matches']
print(json.dumps(result,indent=2))

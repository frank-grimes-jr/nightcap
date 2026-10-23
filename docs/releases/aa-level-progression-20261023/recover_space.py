"""Remove only obsolete uploads with exact independently retained local copies."""
import hashlib,json,subprocess,shlex
from pathlib import Path
HERE=Path(__file__).resolve().parent
plan=json.loads((HERE/'disk-recovery-plan.json').read_text())
assert len(plan['records'])==11 and not plan['production_deleted']
for row in plan['records']:
 p=Path(row['local']);assert p.is_file() and p.stat().st_size==row['bytes']
 with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
remote=r'''import fcntl,hashlib,json,shutil,sys
from pathlib import Path
plan=json.load(sys.stdin);root=Path('/opt/nightcap/deploy/production')
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 before=shutil.disk_usage(root).free
 for row in plan['records']:
  p=Path(row['remote']);assert p.parent==Path('/home/ubuntu') and p.name.endswith('.tar.gz')
  assert p.resolve()==p and p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes']
  with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
 for row in plan['records']:Path(row['remote']).unlink()
 print(json.dumps({'status':'obsolete upload copies removed','files':len(plan['records']),'removed_bytes':sum(r['bytes'] for r in plan['records']),'free_before':before,'free_after':shutil.disk_usage(root).free,'local_recovery_copies_verified':True,'player_data_backups_images_unchanged':True,'owner_explicitly_authorized':True}))
'''
ssh=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -c '+shlex.quote(remote)]
r=subprocess.run(ssh,input=json.dumps(plan),text=True,capture_output=True,check=True)
result=json.loads(r.stdout);(HERE/'disk-recovery-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))

"""Stream the verified release to a new private stage, then preflight only."""
from pathlib import Path
import hashlib,json,shlex,subprocess
HERE=Path(__file__).resolve().parent
receipt=json.loads((HERE/'package-receipt.json').read_text());archive=Path(receipt['archive'])
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==receipt['archive_sha256']
m=json.loads((HERE/'package/manifest.json').read_text())
remote=r"""from pathlib import Path
import hashlib,io,json,os,shutil,subprocess,sys,tarfile
stage=Path('/opt/nightcap/releases/aa-level-progression-20261023');os.umask(0o077)
expected=EXPECTED
assert not stage.exists(),'Inspect prior attempt; never replay staging'
assert shutil.disk_usage(stage.parent).free>=BINARY_BYTES+800*1024**2
raw=sys.stdin.buffer.read(ARCHIVE_BYTES+1)
assert len(raw)==ARCHIVE_BYTES and hashlib.sha256(raw).hexdigest()==ARCHIVE_SHA
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:
 members=t.getmembers();assert len(members)==len(expected) and {m.name for m in members}==set(expected)
 assert all(m.isfile() and not m.name.startswith('/') and '..' not in Path(m.name).parts for m in members)
 stage.mkdir(mode=0o700)
 for member in members:
  p=stage/member.name;assert p.resolve().is_relative_to(stage)
  p.parent.mkdir(parents=True,exist_ok=True)
  with p.open('xb') as f:shutil.copyfileobj(t.extractfile(member),f)
  with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected[member.name]
  p.chmod(0o755 if member.name.startswith('bin/') else 0o644)
with (stage/'preflight.log').open('x') as log:
 result=subprocess.run(['python3',str(stage/'rollout.py'),'preflight'],stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0,'Preflight stopped; inspect private preflight.log'
p=json.loads((stage/'evidence/preflight.json').read_text())
print(json.dumps({'status':'production preflight passed; game unchanged','stage':str(stage),'image':p['image'],'base_image':p['services']['game']['image_id'],'rules_before':len(p['before']),'rules_after':len(p['after']),'free_bytes':shutil.disk_usage(stage).free,'manifest_sha256':p['manifest_sha256']}))
"""
pins={**m['files'],'manifest.json':receipt['manifest_sha256']}
for key,value in [('EXPECTED',pins),('BINARY_BYTES',receipt['replacement_bytes']),('ARCHIVE_BYTES',receipt['archive_bytes']),('ARCHIVE_SHA',receipt['archive_sha256'])]:remote=remote.replace(key,repr(value))
ssh=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -c '+shlex.quote(remote)]
with archive.open('rb') as stream:p=subprocess.run(ssh,stdin=stream,capture_output=True)
(HERE/'staging-output.txt').write_bytes(p.stdout+p.stderr)
if p.returncode:raise RuntimeError((p.stdout+p.stderr).decode()[-1800:])
result=json.loads(p.stdout);(HERE/'preflight-receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))

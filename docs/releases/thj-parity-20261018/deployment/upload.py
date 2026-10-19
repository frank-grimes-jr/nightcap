"""Upload only the authenticated release archive; do not change running services."""
import json
import subprocess
from pathlib import Path
from remote import run

HERE=Path(__file__).resolve().parent
record=json.loads((HERE/'upload.json').read_text())
remote_path='/home/ubuntu/thj-parity-production-20261018.tar.gz'
assert run("from pathlib import Path\nassert not Path("+repr(remote_path)+").exists()\nassert not Path('/opt/nightcap/releases/thj-parity-20261018').exists()\n")==b''
subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe','-i','C:/Users/verre/.ssh/nightcap_ovh',
    '-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',record['path'],
    'ubuntu@135.148.47.202:'+remote_path],check=True)
source='''
import hashlib,json,os,tarfile
from pathlib import Path
os.umask(0o077)
archive=Path(ARCHIVE)
with archive.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest()==DIGEST
stage=Path('/opt/nightcap/releases/thj-parity-20261018')
assert not stage.exists();stage.mkdir(mode=0o700)
with tarfile.open(archive) as t:
 for member in t.getmembers():
  assert member.isfile() and not member.issym() and not member.islnk()
  assert (stage/member.name).resolve().is_relative_to(stage)
 t.extractall(stage,filter='data')
for p in (stage/'bin').iterdir():p.chmod(0o755)
print(json.dumps({'staged':str(stage),'archive_sha256':DIGEST,'services_unchanged':True}))
'''.replace('ARCHIVE',repr(remote_path)).replace('DIGEST',repr(record['sha256']))
print(run(source).decode())

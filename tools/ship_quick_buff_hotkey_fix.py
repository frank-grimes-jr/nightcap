"""Package and privately stage reviewed Quick Buff bytes; no runtime activation."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
from capture_lantern_content import SSH
from quick_buff_remote import ART,run
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/quick-buff-20261112/hotkey-fix'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
    proof=json.loads((OUT/'native-build.json').read_text(encoding='utf-8'))
    probe=json.loads((ART/'production-probe.json').read_text(encoding='utf-8'))
    assert proof['status']=='PASS' and proof['shipping']['baseline-zone']==probe['image_files']['bin/zone']
    names=('common/quick_buff.h','zone/aa_quick_buff.inc','zone/aa.cpp','zone/client.h','zone/spells.cpp')
    pins={n:hashlib.sha256((ROOT/'server-mods/code'/n).read_text(encoding='utf-8').encode()).hexdigest() for n in names}
    assert all(proof['source_sha256'][n]==h for n,h in pins.items()),'Built source differs from reviewed worktree'
    payload=ART/'payload-v2';payload.mkdir(exist_ok=False);(payload/'bin').mkdir()
    subprocess.run(['docker','cp','akk-stack-eqemu-server-1:'+proof['binary'],str(payload/'bin/zone')],check=True,capture_output=True)
    assert sha(payload/'bin/zone')==proof['shipping']['candidate-zone']
    for name in ('rollout.py','native-build.json','release-checks.json','review.json'):(payload/name).write_bytes((OUT/name).read_bytes())
    files={p.relative_to(payload).as_posix():sha(p) for p in payload.rglob('*') if p.is_file()}
    manifest=dict(owner_authorization='Build it and deploy it to the live server so I can test the Quick Buff hotkey in game.',
        source_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip(),
        source_hashes=pins,base_image_id=probe['services']['game']['image_id'],base_hashes=probe['image_files'],
        prior_operator_sha256=probe['operator_sha256'],client_channel_sha256=probe['publication']['channels']['channel.json'],files=files,binaries={'zone':proof['shipping']['candidate-zone']})
    (payload/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    archive=ART/'release-v2.tar.gz'
    with tarfile.open(archive,'x:gz') as handle:
        for path in sorted(payload.rglob('*')):
            if path.is_file():
                info=handle.gettarinfo(str(path),path.relative_to(payload).as_posix());info.mode=0o755 if path.parent.name=='bin' else 0o600
                with path.open('rb') as source:handle.addfile(info,source)
    upload='/home/ubuntu/quick-buff-20261112-v2.tar.gz';ssh=SSH[:-1]
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*ssh[1:-1],str(archive),ssh[-1]+':'+upload],check=True,timeout=600)
    code=r'''
from pathlib import Path
import hashlib,json,os,tarfile
os.umask(0o077);stage=Path('/opt/nightcap/releases/quick-buff-20261112-v2');upload=Path('/home/ubuntu/quick-buff-20261112-v2.tar.gz')
assert hashlib.sha256(upload.read_bytes()).hexdigest()==ARCHIVE_PIN
assert not stage.exists(),'Staging already exists: inspect, never overwrite'
stage.mkdir(mode=0o700)
with tarfile.open(upload) as archive:
 entries=archive.getmembers();assert {e.name for e in entries}==set(FILES)|{'manifest.json'}
 for member in entries:
  target=stage/member.name
  assert member.isfile() and not member.issym() and not member.islnk() and target.resolve().is_relative_to(stage) and not target.exists()
  target.parent.mkdir(mode=0o700,exist_ok=True)
  with target.open('xb') as output:
   data=archive.extractfile(member).read();output.write(data);output.flush();os.fsync(output.fileno())
  if member.name in FILES:assert hashlib.sha256(data).hexdigest()==FILES[member.name]
  os.chmod(target,0o755 if member.name.startswith('bin/') else 0o600)
print(json.dumps(dict(status='STAGED',manifest_sha256=hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest(),runtime_changed=False)))
'''
    result=run('ARCHIVE_PIN='+repr(sha(archive))+'\nFILES='+repr(files)+'\n'+code)
    (OUT/'staged.json').write_text(result,encoding='utf-8');print(result,end='')

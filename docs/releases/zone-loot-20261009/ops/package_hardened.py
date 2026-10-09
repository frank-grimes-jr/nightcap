"""Package only the verified production-source build; preserve the rejected bundle."""
import hashlib,json,shutil,tarfile
from pathlib import Path
ROOT=Path(__file__).parent
PACKAGE=ROOT/'hardened-package'
RELEASE=Path(r'C:/Users/verre/.codex/worktrees/zone-loot-hunt-forge/EQ_Local_Dev/docs/releases/zone-loot-20261009')
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
build=json.loads((ROOT/'production-build-manifest.json').read_text())
assert build['private_login_crypto_self_test']=='passed'
assert build['source_commit']=='77f5d63'
for name,h in build['binaries'].items():assert sha(PACKAGE/'bin'/name)==h,name
for name in ('rollout.py','runtime_ops.py','test_rollout.py'):
    shutil.copyfile(ROOT/name,PACKAGE/name)
shutil.copytree(RELEASE/'generated',PACKAGE/'generated')
shutil.copyfile(ROOT/'production-build-manifest.json',PACKAGE/'production-build-manifest.json')
live=json.loads((ROOT/'live-before.json').read_text())
old_id=live['services']['game']['image_id'];old='nightcap-game:throw-stone-20261009'
(PACKAGE/'Dockerfile').write_bytes(('FROM '+old+'\nCOPY --chmod=755 bin/ /opt/nightcap/bin/\n').encode())
m={'release':'zone-hunt-20261009','source_commit':'77f5d63','build_provenance':'production-build-manifest.json','old_image':old,'old_image_id':old_id,'new_image':'nightcap-game:zone-hunt-20261009','binaries':build['binaries'],'files':{p.relative_to(PACKAGE).as_posix():sha(p) for p in PACKAGE.rglob('*') if p.is_file() and p.name!='manifest.json'}}
(PACKAGE/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',newline='\n')
archive=ROOT/'zone-hunt-hardened-20261009.tar.gz'
assert not archive.exists()
with tarfile.open(archive,'w:gz',compresslevel=1) as t:
    for p in PACKAGE.rglob('*'):
        if not p.is_file():continue
        info=t.gettarinfo(str(p),arcname=p.relative_to(PACKAGE).as_posix());info.uid=info.gid=0;info.uname=info.gname='root';info.mode=0o755 if p.parent.name=='bin' else 0o600
        with p.open('rb') as f:t.addfile(info,f)
result={'file':archive.name,'sha256':sha(archive),'bytes':archive.stat().st_size}
(ROOT/'hardened-package-sha256.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))

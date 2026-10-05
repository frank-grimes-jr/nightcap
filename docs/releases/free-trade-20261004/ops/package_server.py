"""Package the verified binaries and the current, reviewed rollout scripts."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
r=Path(__file__).parent
repo=Path('C:/Users/verre/.codex/worktrees/all-items-tradable/EQ_Local_Dev')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((r/'build-summary.json').read_text())
old=json.loads((r/'server-before-approval.json').read_text())
baseline=json.loads((r/'production-before-approval.json').read_text())
prior=json.loads((r/'base-manifest.json').read_text())
assert sha(r/'base-manifest.json')==build['base_manifest_sha256']
assert old['image_id']==baseline['services']['game']['image_id'] and old['id']==baseline['services']['game']['id']
assert old['image']=='nightcap-game:blessing-lifetime-20261004'
for n,h in prior['binaries'].items():assert old['hashes']['bin/'+n]==h,n
assert subprocess.check_output(['git','diff','79de660','HEAD','--','server-mods/code'],cwd=repo)==b''
stage=r/'server-stage';stage.mkdir(exist_ok=True);(stage/'native-bin').mkdir(exist_ok=True)
for n,h in build['binaries'].items():
    assert sha(r/'native-bin'/n)==h,n
    shutil.copyfile(r/'native-bin'/n,stage/'native-bin'/n)
for n in ('build-summary.json','rollout.py','test_rollout.py'):
    shutil.copyfile(r/n,stage/n)
(stage/'Dockerfile').write_text('FROM '+old['image']+'\nCOPY --chmod=0555 native-bin/ /opt/nightcap/bin/\n')
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
m={'source_commit':commit,'feature_commit':'79de660c01b6cf6bad4b892f6ca5108013f63df1','old_image':old['image'],'old_image_id':old['image_id'],'old_hashes':old['hashes'],
   'new_image':'nightcap-game:free-trade-20261004','binaries':build['binaries'],'baseline':baseline,
   'client_release':baseline['public']['channel.json']['signed']['release'],
   'client_channel_sha256':baseline['public']['channel.json']['sha256'],'hardening_sha256':build['hardening_sha256'],
   'files':{p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*') if p.is_file() and p.name!='manifest.json'}}
(stage/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
archive=r/'free-trade-server-20261004.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=1) as tar:
    for p in sorted(stage.rglob('*')):
        if p.is_file():tar.add(p,arcname=p.relative_to(stage).as_posix(),recursive=False)
digest=sha(archive)
(r/'server-package.json').write_text(json.dumps({'sha256':digest,'bytes':archive.stat().st_size,'source_commit':commit},indent=2)+'\n')
script='''from pathlib import Path,PurePosixPath
import hashlib,json,tarfile
archive=Path('/home/ubuntu/free-trade-server-20261004.tar.gz')
stage=Path('/opt/nightcap/releases/free-trade-20261004')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(archive)==DIGEST and not stage.exists()
with tarfile.open(archive) as tar:
    seen=set()
    for m in tar.getmembers():
        p=PurePosixPath(m.name)
        assert m.isfile() and not p.is_absolute() and '..' not in p.parts and p.as_posix()==m.name and m.name not in seen and chr(92) not in m.name
        seen.add(m.name)
    stage.mkdir(mode=0o700);tar.extractall(stage,filter='data')
    for p in stage.rglob('*'):p.chmod(0o700 if p.is_dir() else 0o600)
m=json.loads((stage/'manifest.json').read_text())
for name,h in m['files'].items():
    p=stage/name;assert not p.is_symlink() and p.resolve().is_relative_to(stage) and sha(p)==h
print(json.dumps({'staged':True,'archive_sha256':DIGEST,'client_release':m['client_release']}))
'''.replace('DIGEST',repr(digest))
(r/'stage-server.py').write_text(script)
print(json.dumps({'sha256':digest,'bytes':archive.stat().st_size,'source_commit':commit,'unchanged_client_release':m['client_release']}))

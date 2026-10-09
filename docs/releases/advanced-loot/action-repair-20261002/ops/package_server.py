import hashlib,json,shutil,tarfile
from pathlib import Path
r=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((r/'native-build-manifest.json').read_bytes())
old=json.loads((r/'server-before.json').read_bytes())
baseline=json.loads((r/'production-before.json').read_bytes())
assert old['image_id']==baseline['services']['game']['image_id'] and old['id']==baseline['services']['game']['id']
assert old['image']=='nightcap-game:advanced-loot-20260930'
assert set(build['changed_source_files'])=={'zone/advanced_loot.cpp','zone/corpse_advanced_loot.cpp'}
assert build['built_targets']==['world','zone'] and build['patch_sha256']==sha(r/'production-source.patch')
for n,h in build['binaries'].items():
    if n in ('world','zone'):assert sha(r/n)==h
    else:assert old['hashes']['bin/'+n]==h
stage=r/'server-stage';stage.mkdir();(stage/'native-bin').mkdir()
for n in ('world','zone'):shutil.copyfile(r/n,stage/'native-bin'/n)
for n in ('native-build-manifest.json','production-source.patch','build.py','resume_build.py','rollout.py','test_rollout.py'):shutil.copyfile(r/n,stage/n)
(stage/'Dockerfile').write_text('FROM '+old['image']+'\nCOPY --chmod=0555 native-bin/ /opt/nightcap/bin/\n')
client=json.loads((r/'production-publish/release-audit.json').read_bytes())
m={'source_commit':build['source_commit'],'old_image':old['image'],'old_image_id':old['image_id'],'old_hashes':old['hashes'],'new_image':'nightcap-game:advanced-loot-actions-20261002','binaries':build['binaries'],'baseline':baseline,'client_release':2026100203,'client_channel_sha256':client['channel_sha256'],'hardening_sha256':build['hardening_sha256'],'files':{p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*') if p.is_file()}}
(stage/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
archive=r/'advanced-loot-actions-server-20261002.tar.gz'
with tarfile.open(archive,'x:gz',compresslevel=1) as tar:
    for p in sorted(stage.rglob('*')):
        if p.is_file():tar.add(p,arcname=p.relative_to(stage),recursive=False)
digest=sha(archive)
(r/'server-package.json').write_text(json.dumps({'sha256':digest,'bytes':archive.stat().st_size,'source_commit':build['source_commit']},indent=2)+'\n')
extract='''from pathlib import Path,PurePosixPath
import hashlib,json,tarfile
archive=Path('/home/ubuntu/advanced-loot-actions-server-20261002.tar.gz')
stage=Path('/opt/nightcap/releases/advanced-loot-actions-server-20261002')
assert hashlib.sha256(archive.read_bytes()).hexdigest()==HASH and not stage.exists()
with tarfile.open(archive) as tar:
    seen=set()
    for m in tar.getmembers():
        p=PurePosixPath(m.name)
        assert m.isfile() and not p.is_absolute() and '..' not in p.parts and p.as_posix()==m.name and m.name not in seen and chr(92) not in m.name
        seen.add(m.name)
    stage.mkdir(mode=0o700);tar.extractall(stage,filter='data')
    for p in stage.rglob('*'):p.chmod(0o700 if p.is_dir() else 0o600)
print(json.dumps({'staged':True,'archive_sha256':HASH}))
'''.replace('HASH',repr(digest))
(r/'stage-server.py').write_text(extract)
print(json.dumps({'sha256':digest,'bytes':archive.stat().st_size}))

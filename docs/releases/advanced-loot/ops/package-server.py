from pathlib import Path
import hashlib,json,shutil,tarfile

ROOT=Path(__file__).resolve().parent
REPO=Path('C:/Users/verre/.codex/worktrees/advanced-loot/EQ_Local_Dev')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((ROOT/'native-build-manifest.json').read_text())
old=json.loads((ROOT/'server-before.json').read_text(encoding='utf-8-sig'))
assert old['image_id']=='sha256:5a2263643ce4660b632cc033558e9108473fb551fa1436767e2e4aee26622964'
assert len(build['changed_source_files'])==24 and build['built_targets']==['world','zone']
assert build['patch_sha256']==sha(ROOT/'production-source.patch')
assert all(old['hashes']['bin/'+n]==h for n,h in build['binaries'].items() if n not in ('world','zone'))
stage=ROOT/'server-stage';stage.mkdir(exist_ok=False)
(stage/'native-bin').mkdir()
previous=Path('E:/EQ_Local_Dev/artifacts/pet-management-20260922/production-ops/server-stage/native-bin')
for name,digest in build['binaries'].items():
    path=ROOT/name if name in ('world','zone') else previous/name
    assert sha(path)==digest,name
    shutil.copyfile(path,stage/'native-bin'/name)
for name in ('native-build-manifest.json','production-source.patch','rollout.py','appdb_probe.py','build.py','test_rollout.py','rollout-tests.log'):
    shutil.copyfile(ROOT/name,stage/name)
shutil.copyfile(REPO/'server-mods/sql/20260930_advanced_loot.sql',stage/'20260930_advanced_loot.sql')
(stage/'Dockerfile').write_text('FROM '+old['image']+'\nCOPY --chmod=0555 native-bin/ /opt/nightcap/bin/\nRUN /opt/nightcap/bin/loginserver --nightcap-crypto-self-test\nRUN python3 -c "import sys;sys.path.insert(0,\'/opt/nightcap\');import start;start.validate_native()"\n')
manifest={
    'source_commit':'0f7d089610a1a3e33ff7324e187f04c19079a846',
    'build_source_commit':build['source_commit'],
    'old_image':old['image'],'old_image_id':old['image_id'],
    'old_restart_count':old['restarts'],'old_started_at':old['started_at'],
    'old_hashes':old['hashes'],'new_image':'nightcap-game:advanced-loot-20260930',
    'client_release':2026093006,
    'client_channel_sha256':'4698296da56f328241c96ab7051f7458585da603c6c8307f623ee838a807fa99',
    'binaries':build['binaries'],'hardening_sha256':build['hardening_sha256'],
    'files':{p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*') if p.is_file() and 'native-bin' not in p.parts}
}
(stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=ROOT/'advanced-loot-server-20260930.tar.gz'
with tarfile.open(archive,'x:gz',compresslevel=3) as tar:
    for p in sorted(stage.rglob('*')):
        if p.is_file():tar.add(p,arcname=p.relative_to(stage),recursive=False)
report={'archive':archive.name,'sha256':sha(archive),'bytes':archive.stat().st_size,'manifest_sha256':sha(stage/'manifest.json')}
(ROOT/'server-package.json').write_text(json.dumps(report,indent=2)+'\n')
code='''from pathlib import Path
import hashlib,json,tarfile
archive=Path('/home/ubuntu/advanced-loot-server-20260930.tar.gz')
stage=Path('/opt/nightcap/releases/advanced-loot-20260930')
assert hashlib.sha256(archive.read_bytes()).hexdigest()==HASH
assert not stage.exists()
with tarfile.open(archive) as tar:
    for m in tar.getmembers():assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
    stage.mkdir(mode=0o700)
    tar.extractall(stage,filter='data')
    for p in stage.rglob('*'):p.chmod(0o700 if p.is_dir() else 0o600)
print(json.dumps({'staged':True,'archive_sha256':HASH}))
'''.replace('HASH',repr(report['sha256']))
(ROOT/'stage-server.py').write_text(code)
print(json.dumps(report))

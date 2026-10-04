"""Package the fingerprinted full build and reviewed rollout, retaining current client."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
r=Path(__file__).parent
repo=Path('C:/Users/verre/.codex/worktrees/passive-aa-experience/EQ_Local_Dev')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((r/'native-manifest.json').read_text())
prior=json.loads((r/'base-manifest.json').read_text())
old=json.loads((r/'hosted-before.json').read_text())
assert build['base_manifest_sha256']==sha(r/'base-manifest.json')
assert build['hardening_sha256']==prior['hardening_sha256']
assert old['image']=='nightcap-game:free-trade-20261004'
reviewed_patch=subprocess.check_output(['git','diff','--relative=server-mods/code','f8037ab^','f8037ab','--','server-mods/code'],cwd=repo)
assert build['patch_sha256']==hashlib.sha256(reviewed_patch).hexdigest(),'Compiled patch is not the reviewed feature'
reviewed_files=subprocess.check_output(['git','diff','--name-only','f8037ab^','f8037ab','--','server-mods/code'],cwd=repo,text=True).splitlines()
assert set(build['changed_source_files'])=={n.removeprefix('server-mods/code/') for n in reviewed_files}
for n,h in prior['binaries'].items():assert old['hashes']['bin/'+n]==h,n
assert subprocess.check_output(['git','diff','f8037ab','HEAD','--','server-mods/code'],cwd=repo)==b''
assert set(build['binaries'])=={'world','zone','shared_memory','ucs','loginserver'}
for n,h in build['binaries'].items():
    p=r/'native-bin'/n;assert sha(p)==h,n;assert p.read_bytes()[:4]==b'\x7fELF'
world=(r/'native-bin/world').read_bytes();zone=(r/'native-bin/zone').read_bytes()
assert b'CALL nightcap_market_rotate({},{},{})\x00' in world
assert b'CALL nightcap_market_rotate({})\x00' not in world
assert b'INSERT INTO character_currency(id,platinum) VALUES({},100)' in world
for marker in (b'LivingEconomy\x00',b'MarketAnnouncement\x00',b'TunnelChatter\x00',b'_Z9Perl__oocPKc',
               b'Your selected classes cannot cast this spell at your current level.',
               b'Former NO DROP items sell for exactly 1 platinum each',b'Use #aaexp on (100%) or #aaexp off (0%).'):
    assert marker in zone,marker
for n in ('world','zone','shared_memory'):
    raw=(r/'native-bin'/n).read_bytes()
    assert b'FreeTrade\x00' in raw and b'PassiveExpPercent\x00' in raw and b'AAExpMinLevel\x00' in raw,n
summary={k:v for k,v in build.items() if k!='source_files'}
summary.update(full_manifest_sha256=sha(r/'native-manifest.json'),native_contract_checks='passed',
               changed_source_sha256={n:build['source_files'][n] for n in build['changed_source_files']})
(r/'build-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
stage=r/'server-stage';stage.mkdir(exist_ok=False);(stage/'native-bin').mkdir()
for n in build['binaries']:shutil.copyfile(r/'native-bin'/n,stage/'native-bin'/n)
for n in ('build-summary.json','rollout.py','test_rollout.py'):shutil.copyfile(r/n,stage/n)
(stage/'Dockerfile').write_text('FROM '+old['image']+'\nCOPY --chmod=0555 native-bin/ /opt/nightcap/bin/\n')
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
m={'source_commit':commit,'feature_commit':'f8037ab','old_image':old['image'],
   'old_image_id':old['services']['game']['image_id'],'old_hashes':old['hashes'],
   'new_image':'nightcap-game:passive-aa-20261004','binaries':build['binaries'],'baseline':old,
   'client_release':old['public']['channel.json']['signed']['release'],
   'client_channel_sha256':old['public']['channel.json']['sha256'],'hardening_sha256':build['hardening_sha256'],
   'files':{p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*') if p.is_file()}}
(stage/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
archive=r/'passive-aa-server-20261004.tar.gz'
with tarfile.open(archive,'w:gz',compresslevel=1) as tar:
    for p in sorted(stage.rglob('*')):
        if p.is_file():tar.add(p,arcname=p.relative_to(stage).as_posix(),recursive=False)
digest=sha(archive)
(r/'server-package.json').write_text(json.dumps({'sha256':digest,'bytes':archive.stat().st_size,'source_commit':commit},indent=2)+'\n')
script='''from pathlib import Path,PurePosixPath
import hashlib,json,tarfile
archive=Path('/home/ubuntu/passive-aa-server-20261004.tar.gz')
stage=Path('/opt/nightcap/releases/passive-aa-20261004')
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

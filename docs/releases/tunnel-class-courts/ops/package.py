from pathlib import Path
import hashlib,json,subprocess,sys,tarfile
BASE=Path(__file__).parent
REPO=Path('C:/Users/verre/.codex/worktrees/tunnel-class-courts/EQ_Local_Dev')
COMMIT='453e61bf150fcabc75ef34ef8ada199c2f15fd15'
sys.path.insert(0,str(BASE.parent));from capture import query
paths=['tools/'+n+'.py' for n in ['tunnel_courts','tunnel_services','pok_hub_migration','pok_hub','generate_living_economy','living_economy']]
paths+=['tools/tests/rehearse_tunnel_courts.py','tools/tests/rehearse_living_economy.py','tools/tests/tunnel_spires_quests.t','docs/ecommons-hub/plan.json','server-mods/plugins/tunnel_spires.pl','server-mods/plugins/tunnel_spire_data.pl','server-mods/quests/ecommons/999527.pl']
stage=BASE/'stage';stage.mkdir()
for name in paths:
 p=stage/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_bytes(subprocess.check_output(['git','show',COMMIT+':'+name],cwd=REPO))
(stage/'rollout.py').write_bytes((BASE/'rollout.py').read_bytes().replace(b'\r\n',b'\n'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((BASE/'baseline.json').read_bytes())
zones=json.loads((BASE.parent/'spire-zone-metadata.json').read_bytes())
row=query("SELECT short_name,zoneidnumber,COALESCE(NULLIF(map_file_name,''),short_name),expansion,min_status,min_level FROM zone WHERE version=0 AND short_name='ecommons';").strip().split('\t');assert row[2]=='ecommons';zones['ecommons']=row
runtime=[dict(source=s,target=t,sha256=sha(stage/s)) for s,t in [('server-mods/plugins/tunnel_spires.pl','plugins/tunnel_spires.pl'),('server-mods/plugins/tunnel_spire_data.pl','plugins/tunnel_spire_data.pl'),('server-mods/quests/ecommons/999527.pl','quests/ecommons/999527.pl')]]
manifest=dict(source_commit=COMMIT,image=baseline['image'],image_id=baseline['image_id'],binaries=baseline['hashes'],scene_sha256=baseline['scene_sha256'],runtime=runtime,maps=json.loads((BASE.parent/'map-hashes.json').read_bytes())['maps'],zones=zones,files={p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*') if p.is_file()})
(stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
archive=BASE/'nightcap-tunnel-courts-20260930.tar.gz'
with tarfile.open(archive,'x:gz') as tar:
 for p in sorted(stage.rglob('*')):
  if p.is_file():tar.add(p,arcname=p.relative_to(stage).as_posix())
record=dict(source_commit=COMMIT,archive_sha256=sha(archive),manifest_sha256=sha(stage/'manifest.json'),files=len(manifest['files']))
(BASE/'package.json').write_text(json.dumps(record,indent=2)+'\n')
bootstrap="""from pathlib import Path
import hashlib,json,tarfile
archive=Path('/home/ubuntu/nightcap-tunnel-courts-20260930.tar.gz')
stage=Path('/opt/nightcap/releases/tunnel-courts-20260930')
assert hashlib.sha256(archive.read_bytes()).hexdigest()==ARCHIVE_SHA
assert not stage.exists()
with tarfile.open(archive,'r:gz') as tar:
 for m in tar.getmembers():assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts
 stage.mkdir(mode=0o700)
 tar.extractall(stage,filter='data')
 for p in stage.rglob('*'):p.chmod(0o700 if p.is_dir() else 0o600)
print(json.dumps(dict(staged=True,archive_sha256=ARCHIVE_SHA)))
""".replace('ARCHIVE_SHA',repr(record['archive_sha256']))
(BASE/'stage-remote.py').write_text(bootstrap)
print(json.dumps(record))

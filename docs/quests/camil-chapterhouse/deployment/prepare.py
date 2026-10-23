"""Package the reviewed build using fresh production preimages and source pins."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
ARTIFACTS=Path('E:/EQ_Local_Dev/artifacts/camil-chapterhouse-20261023')
STAGE=ARTIFACTS/'package'
CONTAINER='akk-stack-eqemu-server-1'
BUILD='/tmp/nightcap-chapterhouse-v1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=json.loads((HERE/'production-preimage.json').read_text())
 native=json.loads((HERE.parent/'native-build-manifest.json').read_text())
 old=json.loads((ROOT/'docs/releases/aa-level-progression-20261023/native-build-manifest.json').read_text())
 assert all(p['base_hashes']['bin/'+n]==h for n,h in old['binaries'].items())
 touched={'common/chapterhouse_policy.h','common/dungeon_policy.h','common/dungeon_catalog.h',
  'common/dungeon_contract.h','common/zone_hunt_catalog.h','zone/dungeon_service.cpp',
  'zone/dungeon_service.h','zone/zone.cpp','zone/chapterhouse_vigil.inc'}
 assert set(native['source_files'])-set(old['source_files'])==touched-set(old['source_files'])
 assert all(native['source_files'][n]==h for n,h in old['source_files'].items() if n not in touched)
 for n in touched:assert hashlib.sha256((ROOT/'server-mods/code'/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==native['source_files'][n],n
 local=json.loads((HERE.parent/'local-content.json').read_text())
 for n in ('zone','spawn2','spawnentry','npc_types','doors','templates'):assert local[n]==p['content'][n],n
 assert json.loads((HERE.parent/'secondary-content.json').read_text())==p['secondary_content']
 assert not any(p['content']['reservations'].values()) and not p['saved_chapterhouse_counts'] and not p['existing_vigil_tables']
 assert not (STAGE/'manifest.json').exists(),'Never replace a completed package'
 STAGE.mkdir(parents=True,exist_ok=True)
 def copy(source,name):
  dest=STAGE/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
 copy(HERE/'rollout.py','rollout.py')
 copy(ROOT/'docs/dungeons/runtime-contract.json','runtime-contract.json')
 for n,h in native['binaries'].items():
  dest=STAGE/'bin'/n;dest.parent.mkdir(exist_ok=True)
  subprocess.run(['docker','cp',CONTAINER+':'+BUILD+'/build/bin/'+n,str(dest)],check=True)
  assert sha(dest)==h,n
 subprocess.run(['docker','cp',str(HERE/'cache_check.cpp'),CONTAINER+':'+BUILD+'/cache_check.cpp'],check=True)
 subprocess.run(['docker','exec',CONTAINER,'g++','-std=c++17','-O0','-I'+BUILD+'/source',
  '-I/home/eqemu/code/build/vcpkg_installed/x64-linux/include',BUILD+'/cache_check.cpp',
  BUILD+'/source/common/eqemu_exception.cpp','-o',BUILD+'/cache_check'],check=True)
 subprocess.run(['docker','cp',CONTAINER+':'+BUILD+'/cache_check',str(STAGE/'cache_check')],check=True)
 components=['sql/20261023_chapterhouse_schema.sql','sql/20261023_chapterhouse_content.sql']
 for name in components:copy(ROOT/'server-mods'/name,name)
 content=STAGE/components[1]
 text=content.read_text();assert text.startswith('-- Candidate based on LOCAL content.')
 content.write_text(text.replace('-- Candidate based on LOCAL content. Re-capture/review production before deployment.',
  '-- Production preimages captured '+p['captured_at']+' and proven identical to reviewed guarded inputs.'))
 scripts={}
 names=subprocess.check_output(['git','diff','--name-only','5d0a0d31','8f4f7f1f','--','server-mods/quests'],cwd=ROOT,text=True).splitlines()
 for name in names:
  relative=name.removeprefix('server-mods/');copy(ROOT/name,relative);scripts[relative]=p['runtime'].get(relative)
 assert len(scripts)==13
 shadows=['quests/chapterhouse/'+n for n in ('default.pl','default.lua')]
 shadows+=['quests/chapterhouse_version1/'+n for n in ('default.pl','default.lua')]
 shadows+=['quests/global/'+Path(n).stem+suffix for n in scripts if '/chapterhouse/' in n for suffix in ('.pl','.lua')]
 assert all(n not in p['runtime'] for n in shadows)
 files={f.relative_to(STAGE).as_posix():sha(f) for f in STAGE.rglob('*') if f.is_file()}
 manifest={'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  'files':files,'base_hashes':p['base_hashes'],'base_image_id':p['services']['game']['image_id'],
  'prior_operator_sha256':p['prior_operator_sha256'],'runtime_helper_sha256':p['helper_sha256'],
  'client_channel_sha256':p['channel_sha256'],'binaries':{**{n:p['base_hashes']['bin/'+n] for n in ('world','zone','shared_memory','ucs','loginserver')},**native['binaries']},
  'components':components,'scripts':list(scripts),'script_preimages':scripts,'absent_quest_shadows':shadows,
  'production_preimage_sha256':sha(HERE/'production-preimage.json'),'owner_live_testing_authorized':True}
 (STAGE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 def mode(info):
  info.mode=0o755 if info.name.startswith('bin/') or info.name=='cache_check' else 0o600
  info.uid=info.gid=0;info.uname=info.gname='root';return info
 archive=ARTIFACTS/'release.tar.gz'
 with tarfile.open(archive,'x:gz',compresslevel=1) as out:
  for f in STAGE.rglob('*'):
   if f.is_file():out.add(f,arcname=f.relative_to(STAGE).as_posix(),filter=mode)
 (HERE/'package-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 receipt={'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'files':len(files),'source_base_matches_production':True,'fresh_preimages_match_reviewed_inputs':True}
 (HERE/'package-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

if __name__=='__main__':main()

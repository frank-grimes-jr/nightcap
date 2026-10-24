"""Package the reviewed build using fresh production preimages and source pins."""
import hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ARTIFACTS=HERE/'private'
STAGE=ARTIFACTS/'package'
CONTAINER='akk-stack-eqemu-server-1'
BUILD='/tmp/nightcap-october24-integrated-v1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=json.loads((HERE/'private/production-before.json').read_text())
 native=json.loads((HERE/'native-build-manifest.json').read_text())
 old=json.loads(Path('C:/Users/verre/.codex/worktrees/rogue-tome-learning/EQ_Local_Dev/docs/releases/rogue-tomes-20261024/native-build-manifest.json').read_text())
 assert p['base_hashes']['bin/zone']==old['zone_sha256']==native['base_zone_sha256']
 touched={n.removeprefix('server-mods/code/') for n in subprocess.check_output(['git','diff','--name-only','origin/main','HEAD','--','server-mods/code'],cwd=ROOT,text=True).splitlines()}
 changes={n for n,h in native['source_files'].items() if old['source_files'].get(n)!=h}
 assert changes==touched,('Unexpected native source delta',sorted(changes-touched),sorted(touched-changes))
 for n in touched:assert hashlib.sha256((ROOT/'server-mods/code'/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==native['source_files'][n],n
 local=json.loads((ROOT/'docs/quests/warhelm/local-content.json').read_text())
 normalize=lambda x:sorted(json.dumps(row,sort_keys=True) for row in x)
 for n in ('zone','spawn2','spawnentry','npc_types','doors','helmet'):assert normalize(local[n])==normalize(p['content'][n]),n
 assert local['templates']==p['content']['templates']
 assert json.loads((ROOT/'docs/quests/warhelm/secondary-content.json').read_text())==p['secondary_content']
 assert not any(p['content']['reservations'].values()) and not p['saved_kael'] and p['kael_instances']=='0' and not p['existing_tables']
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
 components=['sql/20261024_highkeep_rescue.sql','sql/20261024_warhelm_schema.sql','sql/20261024_warhelm_content.sql']
 for name in components:copy(ROOT/'server-mods'/name,name)
 content=STAGE/components[2]
 text=content.read_text();assert text.startswith('-- Candidate based on LOCAL content.')
 content.write_text(text.replace('-- Candidate based on LOCAL content. Re-capture/review production before deployment.',
  '-- Production preimages captured '+'2026-10-24'+' and proven identical to reviewed guarded inputs.'))
 scripts={}
 names=sorted((ROOT/'server-mods/quests/everfrost').glob('9988*.pl'))+sorted((ROOT/'server-mods/quests/kael').glob('9988*.pl'))
 assert len(names)==16
 for path in names:
  relative=path.relative_to(ROOT/'server-mods').as_posix();copy(path,relative);scripts[relative]=p['runtime_files'].get(relative)
 shadows=[]
 for n in scripts:
  folder=Path(n).parent.as_posix();stem=Path(n).stem
  shadows += [folder+'/default.lua',folder+'/default.pl',folder+'/'+stem+'.lua',folder+'_version1/'+stem+'.pl',folder+'_version1/'+stem+'.lua','quests/global/'+stem+'.pl','quests/global/'+stem+'.lua']
 assert all(n not in p['runtime_files'] for n in shadows)
 files={f.relative_to(STAGE).as_posix():sha(f) for f in STAGE.rglob('*') if f.is_file()}
 manifest={'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  'files':files,'base_hashes':p['base_hashes'],'base_image_id':p['base_image_id'],
  'prior_operator_sha256':p['prior_operator_sha256'],'runtime_helper_sha256':p['runtime_helper_sha256'],
  'client_channel_sha256':p['client_channel_sha256'],'binaries':{**{n:p['base_hashes']['bin/'+n] for n in ('world','zone','shared_memory','ucs','loginserver')},**native['binaries']},
  'components':components,'scripts':list(scripts),'script_preimages':scripts,'absent_quest_shadows':shadows,
  'production_preimage_sha256':sha(HERE/'private/production-before.json'),'owner_live_testing_authorized':True}
 (STAGE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 def mode(info):
  info.mode=0o755 if info.name.startswith('bin/') or info.name=='cache_check' else 0o600
  info.uid=info.gid=0;info.uname=info.gname='root';return info
 archive=ARTIFACTS/'release.tar.gz'
 with tarfile.open(archive,'x:gz',compresslevel=1) as out:
  for f in STAGE.rglob('*'):
   if f.is_file():out.add(f,arcname=f.relative_to(STAGE).as_posix(),filter=mode)
 (HERE/'private/package-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 receipt={'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'files':len(files),'source_base_matches_production':True,'fresh_preimages_match_reviewed_inputs':True}
 (HERE/'package-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))

if __name__=='__main__':main()

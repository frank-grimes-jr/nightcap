"""Package exact reviewed binaries, migrations and plane quest changes."""
import argparse,ast,hashlib,json,shutil,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
ARTIFACTS=Path('E:/EQ_Local_Dev/artifacts/classic-dungeon-options-20261022')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def tar_mode(info):
    info.mode=0o755 if info.name.startswith('bin/') or info.name=='cache_check' else 0o600
    info.uid=info.gid=0;info.uname=info.gname='root'
    return info
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--name',default='deployment-package');args=parser.parse_args()
    assert args.name.replace('-','').isalnum()
    stage=ARTIFACTS/args.name;stage.mkdir(exist_ok=False)
    probe=json.loads((ARTIFACTS/'live-probe.json').read_text())
    build=json.loads((HERE.parent/'build-manifest.json').read_text())
    for name,digest in build['candidate_sources'].items():
        assert sha(ROOT/'server-mods/code'/name)==digest,name
    assert build['baseline_zone_sha256']==probe['base_hashes']['bin/zone']
    for name,pins in build['other_binaries'].items():assert pins['baseline']==probe['base_hashes']['bin/'+name]
    base=(ROOT/'docs/releases/aa-pacing-million-20261021/rollout.py').read_text()
    tree=ast.parse(base)
    market='\n\n'.join(ast.get_source_segment(base,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('market','verify_market'))
    operator=(HERE/'rollout.py').read_text()
    marker="# market()/verify_market() are copied exactly from the reviewed October21\n# operator by prepare_local.py and pin the native once-per-startup rotation."
    assert marker in operator
    (stage/'rollout.py').write_text(operator.replace(marker,market),encoding='utf-8')
    def copy(source,name):
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    binaries={n:probe['base_hashes']['bin/'+n] for n in ('world','zone','shared_memory','ucs','loginserver')}
    expected={'zone':build['zone_sha256'],**{n:v['candidate'] for n,v in build['other_binaries'].items()}}
    for name,digest in expected.items():
        source=ARTIFACTS/('reward-'+name);assert sha(source)==digest
        copy(source,'bin/'+name);binaries[name]=digest
    verification=json.loads((HERE.parent/'cache-verification.json').read_text())
    assert sha(HERE.parent/'cache_check.cpp')==verification['harness_sha256']
    harness_hash=subprocess.check_output(['docker','exec','akk-stack-eqemu-server-1','sha256sum',
        '/tmp/nightcap-classic-reward-cache-ea8b5159b70b/cache_check'],text=True).split()[0]
    assert sha(ARTIFACTS/'cache_check')==harness_hash
    copy(ARTIFACTS/'cache_check','cache_check')
    copy(ROOT/'docs/dungeons/runtime-contract.json','runtime-contract.json')
    scripts={};preimages=json.loads((HERE.parent.parent/'classic-expansion-20261022/quest-preimages.json').read_text())
    for name,pins in preimages.items():
        relative='quests/'+name;source=ROOT/'server-mods'/relative
        assert sha(source)==pins['candidate_sha256']
        assert probe['runtime'][relative]==pins['deployed_preimage_sha256']
        copy(source,relative);scripts[relative]=pins['deployed_preimage_sha256']
    module='lua_modules/nightcap_dungeons.lua';assert module not in probe['runtime']
    copy(ROOT/'server-mods'/module,module);scripts[module]=None
    content=json.loads((HERE.parent.parent/'classic-expansion-20261022/content.json').read_text())
    shadows=[]
    for name in preimages:
        zone,npc=Path(name).parent.name,Path(name).stem
        for row in content['npc_types']:
            if row['name']==npc:
                shadows.extend('quests/'+folder+'/'+str(row['id'])+suffix for folder in (zone,'global') for suffix in ('.lua','.pl'))
    additions=json.loads((HERE.parent.parent/'classic-expansion-20261022/install-rows.json').read_text())
    for row in additions['npc_types']:
        zone=row['lastname'] if row['name']=='Instance_Keeper' else 'airplane'
        shadows.extend('quests/'+folder+'/'+str(row['id'])+suffix for folder in (zone,'global') for suffix in ('.lua','.pl'))
        if row['name']=='Instance_Keeper':
            shadows.extend('quests/'+zone+'/Instance_Keeper'+suffix for suffix in ('.lua','.pl'))
    components=['sql/20261022_classic_dungeons.sql','sql/20261022_classic_dungeon_rewards.sql']
    for name in components:copy(ROOT/'server-mods'/name,name)
    audit=json.loads((HERE.parent/'preimages.json').read_text())
    magic=[row['id'] for row in audit['items'] if row['magic']==0];assert len(magic)==220
    (stage/'magic-only-ids.json').write_text(json.dumps(magic))
    files={p.relative_to(stage).as_posix():sha(p) for p in stage.rglob('*') if p.is_file()}
    manifest={'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'files':files,'base_hashes':probe['base_hashes'],'base_image_id':probe['services']['game']['image_id'],
        'runtime_helper_sha256':probe['helper_sha256'],'client_channel_sha256':probe['channel_sha256'],
        'binaries':binaries,'components':components,'scripts':list(scripts),'script_preimages':scripts,
        'absent_quest_shadows':sorted(set(shadows)),'owner_live_testing_authorized':True}
    (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    package=ARTIFACTS/(args.name+'.tar.gz')
    with tarfile.open(package,'x:gz',compresslevel=1) as archive:
        for path in stage.rglob('*'):
            if path.is_file():archive.add(path,arcname=path.relative_to(stage).as_posix(),filter=tar_mode)
    with tarfile.open(package) as archive:
        for member in archive:
            assert member.mode==(0o755 if member.name.startswith('bin/') or member.name=='cache_check' else 0o600)
    (HERE/'package-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'files':len(files),'archive_bytes':package.stat().st_size,'archive_sha256':sha(package)}))
if __name__=='__main__':main()

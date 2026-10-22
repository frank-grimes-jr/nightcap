"""Reproduce live quest-tier zone, then combine only verified dungeon objects."""
import hashlib,json,shlex,subprocess
from pathlib import Path
BASE=Path('/tmp/nightcap-thj-behaviors-v1')
AA=Path('/tmp/nightcap-aa-pacing-million-v2')
QUEST=Path('/tmp/nightcap-quest-handins-build-v1')
DUNGEON=Path('/tmp/nightcap-classic-rewards-build-v2')
OUT=Path('/tmp/nightcap-classic-rewards-with-handins-v1')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    quest=json.loads((QUEST/'manifest.json').read_text());dungeon=json.loads((DUNGEON/'manifest.json').read_text())
    assert quest['zone_sha256']=='6da991b688a5b25819b24274506f2d7a427cd7990ff8ca1992d2beabca75c2f0'
    assert sha(QUEST/'zone')==quest['zone_sha256']
    assert sha(DUNGEON/'zone')==dungeon['zone_sha256']=='948e0fd03523e9469e9829e78d6be24052433114541fb8b8eed53443d3274332'
    assert quest['baseline_zone_sha256']==dungeon['baseline_zone_sha256']
    for name,digest in quest['candidate_sources'].items():assert sha(QUEST/'source'/name)==digest
    for name,digest in dungeon['candidate_sources'].items():assert sha(Path('/tmp/nightcap-classic-rewards-input')/name)==digest
    for name,digest in quest['retained_inputs'].items():assert sha(Path(name))==digest
    cwd=BASE/'build/zone';link=shlex.split((cwd/'CMakeFiles/zone.dir/link.txt').read_text())
    replace={'CMakeFiles/zone.dir/spells.cpp.o':AA/'spells.cpp.o',
             'CMakeFiles/zone.dir/npc.cpp.o':QUEST/'npc.cpp.o',
             'CMakeFiles/zone.dir/task_client_state.cpp.o':QUEST/'task_client_state.cpp.o'}
    for name,path in replace.items():link[link.index(name)]=str(path)
    OUT.mkdir(exist_ok=True);output=link.index('-o')+1
    assert not (OUT/'zone').exists() and not (OUT/'manifest.json').exists()
    def run(name):
        link[output]=str(OUT/name)
        with (OUT/(name+'.log')).open('w') as log:
            subprocess.run(link,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,check=True)
    if not (OUT/'live-baseline').exists():run('live-baseline')
    assert sha(OUT/'live-baseline')==quest['zone_sha256']
    for name,path in {'CMakeFiles/zone.dir/dungeon_service.cpp.o':DUNGEON/'dungeon_service.cpp.o',
                      next(v for v in link if v.endswith('liblua_zone.a')):DUNGEON/'liblua_zone.a',
                      '../bin/libcommon.a':DUNGEON/'libcommon.a'}.items():
        link[link.index(name)]=str(path);replace[name]=path
    pins={str(p):sha(p) for p in replace.values()}
    assert sha(DUNGEON/'libcommon.a')==dungeon['common_archive_sha256']
    assert sha(DUNGEON/'liblua_zone.a')==dungeon['lua_archive_sha256']
    run('zone')
    ldd=subprocess.check_output(['ldd',str(OUT/'zone')],text=True);assert 'not found' not in ldd
    assert all(sha(Path(p))==h for p,h in pins.items())
    evidence={**dungeon,'baseline_zone_sha256':quest['zone_sha256'],'zone_sha256':sha(OUT/'zone'),
        'candidate_sources':{**dungeon['candidate_sources'],**quest['candidate_sources']},
        'combined_inputs':pins,'baseline_reproduced':True,'quest_tier_behavior_retained':True,
        'prior_dungeon_zone_sha256':dungeon['zone_sha256'],'status':'built_not_installed'}
    (OUT/'manifest.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({'zone_sha256':evidence['zone_sha256'],'baseline_reproduced':True}),flush=True)
if __name__=='__main__':main()

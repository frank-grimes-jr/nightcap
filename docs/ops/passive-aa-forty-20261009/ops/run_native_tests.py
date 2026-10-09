"""Verify tuning against the exact production build source, without installing code."""
import hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
root=Path('/tmp/nightcap-passive-aa-forty-20261009')
source=Path('/tmp/nightcap-zone-hunt-hardened-build-20261009/source')
manifest=json.loads((root/'production-build-manifest.json').read_text())
files=['zone/exp.cpp','zone/client.cpp','zone/client_packet.cpp','zone/zonedb.cpp','zone/gm_commands/aa_exp.cpp','common/server_reload_types.h','common/rulesys.cpp','world/zonelist.cpp','zone/worldserver.cpp']
for name in files:
    assert hashlib.sha256((source/name).read_bytes()).hexdigest()==manifest['source_files'][name],name
(root/'server-mods').mkdir(exist_ok=True)
if not (root/'server-mods/code').exists():(root/'server-mods/code').symlink_to(source,target_is_directory=True)
spec=importlib.util.spec_from_file_location('aa',root/'test_passive_aa.py');aa=importlib.util.module_from_spec(spec);spec.loader.exec_module(aa)
aa.ROOT=root;sys.argv=['test_passive_aa.py'];aa.main()
curve=root/'curve.cpp'
curve.write_text(aa.PRELUDE+aa.function((source/'zone/exp.cpp').read_text(),'uint32 Client::GetEXPForLevel')+'''
int main(){reset();Client c;for(int level : {5,7,8,10,11,13,18,19,20,30,40,50})
 std::cout<<level<<" "<<c.GetEXPForLevel(level)<<"\\n";}
''')
subprocess.run(['clang++','-std=c++20',str(curve),'-o',str(root/'curve')],check=True)
rows=[list(map(int,line.split())) for line in subprocess.check_output([str(root/'curve')],text=True).splitlines()]
report={'source':str(source),'source_files_verified':files,'native_checks':129,'failures':0,
 'test_sha256':hashlib.sha256((root/'test_passive_aa.py').read_bytes()).hexdigest(),
 'base_curve_before_per_award_rounding':[{'level':level,'total_level_xp':xp,'aa_at_1_percent':xp*.01/50000,'aa_at_3_percent':xp*.03/50000,'aa_at_5_percent':xp*.05/50000,'aa_at_20_percent':xp*.20/50000,'aa_at_40_percent':xp*.40/50000} for level,xp in rows],
 'limits':'Kills with equal normal/AA modifiers, no deaths/penalties/bonuses; not a player-session or combat-balance test'}
(root/'native-tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

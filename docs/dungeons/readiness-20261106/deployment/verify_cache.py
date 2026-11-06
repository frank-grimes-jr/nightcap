"""Run the repaired native CacheMatches against the actual live shared cache; no player writes."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from probe import SSH

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
header=(ROOT/'server-mods/code/common/dungeon_contract.h').read_text()
ids=[int(v) for v in re.findall(r'case (\d+): return ',header)]
assert len(ids)==len(set(ids))==441
source=r'''#include "common/dungeon_contract.h"
#include <cassert>
#include <cstdint>
#include <fstream>
#include <iostream>
int main(int argc,char**argv){
 assert(argc==2);static_assert(sizeof(EQ::ItemData)==1332);
 std::ifstream file(argv[1],std::ios::binary);assert(file);
 uint32_t header[4]{};file.read(reinterpret_cast<char*>(header),sizeof(header));assert(file);
 auto count=header[1],maximum=header[2],current=header[3];assert(maximum==current);
 unsigned verified=0;
 for(uint32_t id: {IDS}){
  assert(id<count);uint32_t index=0;
  file.seekg(16ull+4ull*id);file.read(reinterpret_cast<char*>(&index),4);assert(file&&index<current);
  EQ::ItemData item{};file.seekg(16ull+4ull*count+uint64_t(index)*sizeof(item));
  file.read(reinterpret_cast<char*>(&item),sizeof(item));assert(file&&item.ID==id);
  if(!NightcapDungeon::CacheMatches(item)){std::cerr<<"Cache guard mismatch: "<<id<<"\n";return 1;}
  ++verified;
 }
 assert(verified==441);std::cout<<"{\"status\":\"PASS\",\"cache_definitions\":"<<verified<<",\"item_bytes\":"<<sizeof(EQ::ItemData)<<"}\n";
}
'''.replace('{IDS}','{'+','.join(map(str,ids))+'}')
code='''from pathlib import Path
import hashlib,json,subprocess
root=Path('/tmp/nightcap-dungeon-readiness-stats-20261106-v1');source=root/'live-cache-check.cpp';binary=root/'live-cache-check'
if source.exists() or binary.exists():
 assert source.is_file() and binary.is_file() and source.read_text()==SOURCE,'Unowned checker build'
else:
 source.write_text(SOURCE)
 command=['clang++','-O0','-UNDEBUG','-std=c++20','-I/tmp/nightcap-dungeon-readiness-20261106-v2/source','-I/tmp/nightcap-augment-audit-20261106-v2/source','-isystem','/home/eqemu/code/build/vcpkg_installed/x64-linux/include',str(source),'-o',str(binary)]
 result=subprocess.run(command,capture_output=True,text=True);assert result.returncode==0,result.stderr[-3000:]
print(json.dumps({'binary':str(binary),'sha256':hashlib.sha256(binary.read_bytes()).hexdigest()}))
'''
result=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input='SOURCE='+repr(source)+'\n'+code,text=True,encoding='utf-8',capture_output=True,timeout=120)
if result.returncode:raise RuntimeError(result.stderr[-3500:])
build=json.loads(result.stdout);local=HERE.parent/'bin/live-cache-check'
subprocess.run(['docker','cp','akk-stack-eqemu-server-1:'+build['binary'],str(local)],check=True,capture_output=True)
assert hashlib.sha256(local.read_bytes()).hexdigest()==build['sha256']
upload='/home/ubuntu/dungeon-readiness-live-cache-check-20261106'
check=f"from pathlib import Path;import hashlib,json;p=Path({upload!r});assert not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()=={build['sha256']!r};print(json.dumps(p.exists()))"
existing=subprocess.run(SSH+['sudo -n python3 -'],input=check,text=True,capture_output=True,check=True,timeout=30)
if not json.loads(existing.stdout):
 subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],str(local),SSH[-1]+':'+upload],check=True,timeout=120)
remote=f'''from pathlib import Path
import fcntl,hashlib,json,subprocess
root=Path('/opt/nightcap/deploy/production');stage=Path('/opt/nightcap/releases/dungeon-readiness-20261106-v1');binary=Path({upload!r})
assert hashlib.sha256(binary.read_bytes()).hexdigest()=={build['sha256']!r};binary.chmod(0o700)
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 deployed=json.loads((stage/'evidence/activation/deployed.json').read_text());assert deployed['gateway_open']
 cid=subprocess.check_output(['docker','compose','ps','-q','game'],cwd=root,text=True).strip()
 state=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
 assert state['Image']==deployed['runtime']['image_id'] and state['State']['StartedAt']==deployed['runtime']['started_at']
 target=Path('/srv/nightcap/shared/items');cache=root/'data/server/shared/items'
 mounts=[v for v in state['Mounts'] if target.is_relative_to(v['Destination'])]
 mount=max(mounts,key=lambda v:len(v['Destination']))
 assert (Path(mount['Source'])/target.relative_to(mount['Destination'])).resolve()==cache.resolve()
 before=cache.stat();result=subprocess.run([str(binary),str(cache)],text=True,capture_output=True)
 assert result.returncode==0,result.stderr[-1500:]
 after=cache.stat();assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
 report=json.loads(result.stdout);assert report['status']=='PASS' and report['cache_definitions']==441
 report.update(runtime_image=state['Image'],checker_sha256={build['sha256']!r},execution='Native checker on host; exact active game bind mount authenticated',scope='Actual live shared item cache with repaired native CacheMatches; read-only, no player/run mutation')
 print(json.dumps(report))
'''
result=subprocess.run(SSH+['sudo -n python3 -'],input=remote,text=True,encoding='utf-8',capture_output=True,timeout=120)
if result.returncode:raise RuntimeError(result.stderr[-3500:])
report=json.loads(result.stdout);(HERE/'native-live-cache.json').write_text(json.dumps(report,indent=2)+'\n');print(result.stdout)

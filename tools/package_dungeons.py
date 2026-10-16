"""Build a paired local-content cache/package; never install or restart a server.

Requires the completed isolated build manifest. Uses only a disposable content
database and a scoped temporary account; configuration/credentials are excluded.
The resulting cache is a local test artifact, not a production-content cache.
"""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import uuid
from dungeon_migration import insert

ROOT=Path(__file__).resolve().parents[1]
CONTAINER='akk-stack-eqemu-server-1'
BUILD='/tmp/nightcap-dungeon-build-20261016'
DB='nightcap_dungeon_cache_'+uuid.uuid4().hex[:12]
USER='nd_'+uuid.uuid4().hex[:12]
PASSWORD=secrets.token_hex(24)
RUNTIME='/tmp/'+DB

def sql(statement):
    result=subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
        'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot -N -B --raw'],
        input=statement,text=True,capture_output=True,timeout=240)
    if result.returncode:raise RuntimeError('Isolated cache database operation failed; credentials withheld')
    return result.stdout

def remote(script):
    result=subprocess.run(['docker','exec','-i',CONTAINER,'python3','-'],input=script,text=True,capture_output=True,timeout=600)
    if result.returncode:raise RuntimeError('Isolated package operation failed: '+result.stderr[-2000:])
    return result.stdout

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    catalog=json.loads((ROOT/'docs/dungeons/catalog.json').read_text())
    overlay={str(p.relative_to(ROOT/'server-mods/code')).replace('\\','/'):
             hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
             for p in (ROOT/'server-mods/code').rglob('*') if p.is_file()}
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    remote('BUILD='+repr(BUILD)+'\nEXPECTED='+repr(overlay)+'\nREVISION='+repr(revision)+'''\nimport hashlib,json
from pathlib import Path
b=Path(BUILD);manifest=json.loads((b/'manifest.json').read_text())
for path,digest in EXPECTED.items():
 assert hashlib.sha256((b/'source'/path).read_bytes().replace(b'\\r\\n',b'\\n')).hexdigest()==digest,'Build overlay mismatch: '+path
manifest.update(overlay_revision=REVISION,overlay_normalized_sha256=EXPECTED)
(b/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\\n')
''')
    created=user_created=False
    prelude=f'BUILD={BUILD!r}\nRUNTIME={RUNTIME!r}\nDB={DB!r}\nUSER={USER!r}\nPASSWORD={PASSWORD!r}\n'
    try:
        sql('CREATE DATABASE '+DB+';');created=True
        for table in ('items','rule_sets','rule_values','variables','logsys_categories','content_flags','zone'):
            sql(f'CREATE TABLE {DB}.{table} LIKE peq.{table}; INSERT INTO {DB}.{table} SELECT * FROM peq.{table};')
        sql(f'CREATE TABLE {DB}.instance_list LIKE peq.instance_list;')
        assert sql(f'SELECT COUNT(*) FROM {DB}.items WHERE id BETWEEN 960000 AND 960329;').strip()=='0'
        sql(f"CREATE USER '{USER}'@'%' IDENTIFIED BY '{PASSWORD}';");user_created=True
        sql(f"GRANT ALL ON {DB}.* TO '{USER}'@'%';")
        # The local test policy matches current effective trading/race/LORE.
        sql(f"DELETE FROM {DB}.variables WHERE varname='RuleSet';")
        for rule in ('Items:FreeTrade','Items:DisableLore'):
            sql(f"REPLACE INTO {DB}.rule_values(ruleset_id,rule_name,rule_value) VALUES(1,'{rule}','true');")
        remote(prelude+r'''
import hashlib,json,subprocess
from pathlib import Path
r=Path(RUNTIME);r.mkdir(mode=0o700);(r/'shared').mkdir();(r/'logs').mkdir()
build=Path(BUILD);manifest=json.loads((build/'manifest.json').read_text())
for name,digest in manifest['binaries'].items():
 assert hashlib.sha256((build/'build/bin'/name).read_bytes()).hexdigest()==digest
cfg=json.loads(Path('/home/eqemu/server/eqemu_config.json').read_text())
db=cfg['server']['database'];db.update(db=DB,username=USER,password=PASSWORD)
cfg['server']['content_database']=dict(db)
cfg['server'].setdefault('directories',{}).update(shared_memory=str(r/'shared')+'/',logs=str(r/'logs')+'/')
p=r/'eqemu_config.json';p.write_text(json.dumps(cfg));p.chmod(0o600)
source=r/'cache_check.cpp'
source.write_text(r"""
#include "common/dungeon_contract.h"
#include <fstream>
#include <vector>
#include <cstdint>
#include <cstring>
#include <iostream>
int main(int argc,char **argv) {
 if(argc!=2)return 2;
 std::ifstream f(argv[1],std::ios::binary);
 std::vector<char> data((std::istreambuf_iterator<char>(f)),{});
 auto read=[&](size_t offset){uint32_t value=0;if(offset+4>data.size())throw 1;std::memcpy(&value,data.data()+offset,4);return value;};
 auto count=read(4),current=read(12);size_t start=16+4ull*count;
 unsigned checked=0;
 for(uint32_t id=960000;id<960330;++id) {
  auto index=read(16+4ull*id);if(index>=current)return 3;
  size_t offset=start+index*sizeof(EQ::ItemData);if(offset+sizeof(EQ::ItemData)>data.size())return 4;
  EQ::ItemData item;std::memcpy(&item,data.data()+offset,sizeof(item));
  if(item.ID!=id || !NightcapDungeon::CacheMatches(item) || !item.NoRent || !item.NoDrop || item.LoreFlag || item.Attuneable || item.Price || item.FixedSellPrice)return 5;
  ++checked;
 }
 std::cout<<sizeof(EQ::ItemData)<<" "<<checked<<"\n";
}
""")
subprocess.run(['clang++','-std=c++20','-I'+BUILD+'/source',str(source),'-o',str(r/'cache_check')],check=True)
''')
        loader=r'''
import hashlib,json,mmap,struct,subprocess
from pathlib import Path
r=Path(RUNTIME)
with (r/('loader-'+str(STEP)+'.log')).open('w') as log:
 result=subprocess.run([BUILD+'/build/bin/shared_memory','items'],cwd=r,stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0,'Native loader failed; private log retained'
log=(r/('loader-'+str(STEP)+'.log')).read_text()
assert not any(x in log for x in ('Unknown column','SQL syntax','Unable to connect',"doesn't exist")),'Native loader dependency failed'
if STEP==0:
 # Keep one baseline cache for the per-record comparison after adding items.
 (r/'shared/items').rename(r/'before-items')
else:
 layout=subprocess.check_output([str(r/'cache_check'),str(r/'shared/items')],text=True).split()
 size,checked=map(int,layout);assert checked==330
 def records(path):
  result={}
  with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
   count,maximum,current=struct.unpack_from('<III',data,4);assert maximum==current
   base=16+4*count
   for id in range(count):
    index=struct.unpack_from('<I',data,16+id*4)[0]
    if index<current:
     result[id]=hashlib.sha256(data[base+index*size:base+(index+1)*size]).hexdigest()
  return result
 before=records(r/'before-items');after=records(r/'shared/items')
 assert set(after)-set(before)==set(range(960000,960330))
 assert all(after[id]==digest for id,digest in before.items()),'Existing cache item changed'
 result=dict(status='passed',scope='Local public content only; not a production cache or gameplay acceptance',
  database=DB,custom_items_checked=checked,existing_items_preserved=len(before),item_struct_bytes=size,
  item_cache_sha256=hashlib.sha256((r/'shared/items').read_bytes()).hexdigest())
 (r/'cache-verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
'''
        remote(prelude+'STEP=0\n'+loader)
        sql('USE '+DB+';\n'+'\n'.join(insert('items',i['values']) for i in catalog['items']))
        report=json.loads(remote(prelude+'STEP=1\n'+loader))
        (ROOT/'docs/dungeons/cache-verification.json').write_text(json.dumps(report,indent=2)+'\n')
        staging=RUNTIME+'/release'
        remote(prelude+"from pathlib import Path\n(Path(RUNTIME)/'release/sql').mkdir(parents=True)\n(Path(RUNTIME)/'release/quests/global').mkdir(parents=True)\n(Path(RUNTIME)/'release/docs').mkdir(parents=True)\n")
        for path in sorted((ROOT/'server-mods/sql').glob('20261016_dungeon*.sql')):
            subprocess.run(['docker','cp',str(path),CONTAINER+':'+staging+'/sql/'+path.name],check=True)
        subprocess.run(['docker','cp',str(ROOT/'server-mods/quests/global/Instance_Keeper.pl'),CONTAINER+':'+staging+'/quests/global/Instance_Keeper.pl'],check=True)
        for name in ('README.md','QA.md','SPEC.md','catalog.json','activation-verification.json','concurrency-verification.json'):
            subprocess.run(['docker','cp',str(ROOT/'docs/dungeons'/name),CONTAINER+':'+staging+'/docs/'+name],check=True)
        remote(prelude+r'''
import hashlib,json,shutil,tarfile
from pathlib import Path
r=Path(RUNTIME);release=r/'release';build=Path(BUILD)
(release/'bin').mkdir();(release/'shared').mkdir()
for name in ('zone','world','shared_memory'):
 shutil.copyfile(build/'build/bin'/name,release/'bin'/name)
 (release/'bin'/name).chmod(0o755)
shutil.copyfile(r/'shared/items',release/'shared/items')
shutil.copyfile(build/'manifest.json',release/'native-build-manifest.json')
shutil.copyfile(r/'cache-verification.json',release/'cache-verification.json')
manifest=dict(status='packaged_for_local_test_not_installed',manual_gameplay_accepted=False,
 cache_scope='Local public content snapshot; regenerate against a fresh target-content clone before any production release',
 files={str(p.relative_to(release)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(release.rglob('*')) if p.is_file()})
(release/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with tarfile.open(r/'nightcap-dungeons-20261016.tar.gz','w:gz',compresslevel=5) as archive:
 archive.add(release,arcname='nightcap-dungeons-20261016')
print('Paired package created.')
''')
        for source,destination in [(BUILD+'/manifest.json',ROOT/'docs/dungeons/native-build-manifest.json'),
            (staging+'/manifest.json',ROOT/'docs/dungeons/package-manifest.json'),
            (RUNTIME+'/nightcap-dungeons-20261016.tar.gz',args.output/'nightcap-dungeons-20261016.tar.gz')]:
            subprocess.run(['docker','cp',CONTAINER+':'+source,str(destination)],check=True)
        package=args.output/'nightcap-dungeons-20261016.tar.gz'
        digest=hashlib.sha256(package.read_bytes()).hexdigest()
        (args.output/(package.name+'.sha256')).write_text(digest+'  '+package.name+'\n')
        print(json.dumps(dict(package=str(package),sha256=digest,cache=report)))
    finally:
        if user_created:sql(f"DROP USER '{USER}'@'%';")
        if created:sql('DROP DATABASE '+DB+';')
        remote(f'from pathlib import Path\np=Path({RUNTIME!r})/"eqemu_config.json"\np.unlink(missing_ok=True)\n')

if __name__=='__main__':main()

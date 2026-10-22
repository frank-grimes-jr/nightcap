"""Build/load the isolated reward DB's actual native item cache. Never install."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/tests'))
from rehearse_dungeons import query

def main():
    folder=ROOT/'docs/dungeons/classic-rewards-20261022'
    rehearsal=json.loads((folder/'rehearsal.json').read_text())
    assert rehearsal['status']=='passed_local_isolated_SQL'
    db=rehearsal['database'];assert re.fullmatch('nightcap_dungeon_rehearsal_[0-9a-f]{12}',db)
    tables=('logsys_categories','variables','rule_sets','rule_values','content_flags','zone')
    for table in tables:
        query(f'CREATE TABLE IF NOT EXISTS `{table}` LIKE peq.`{table}`; INSERT IGNORE INTO `{table}` SELECT * FROM peq.`{table}`;',db)
    # Mirror the required trade/ownership policy explicitly in the clone only.
    query("UPDATE rule_values SET rule_value='true' WHERE rule_name IN ('Items:FreeTrade','Items:DisableLore','Items:DisableAttuneable'); UPDATE variables SET value='' WHERE varname='hotfix_name';",db)
    password=subprocess.check_output(['docker','exec','akk-stack-mariadb-1','printenv','MYSQL_ROOT_PASSWORD'],text=True).strip()
    assert password
    native='/tmp/nightcap-classic-rewards-build-v2'
    source='/tmp/nightcap-classic-rewards-input/cache_check.cpp'
    subprocess.run(['docker','cp',str(folder/'cache_check.cpp'),'akk-stack-eqemu-server-1:'+source],check=True,capture_output=True)
    remote=r'''
import hashlib,json,os,shlex,subprocess
from pathlib import Path
base=Path('/tmp/nightcap-thj-behaviors-v1');candidate=Path(native)
out=Path('/tmp/nightcap-classic-reward-cache-'+db.rsplit('_',1)[-1]);out.mkdir(exist_ok=False)
cfg={'server':{'database':{'host':'mariadb','port':'3306','username':'root','password':password,'db':db}}}
config=out/'eqemu_config.json';config.write_text(json.dumps(cfg));config.chmod(0o600)
try:
    result=subprocess.run([str(candidate/'shared_memory'),'items'],cwd=out,text=True,capture_output=True)
    (out/'loader.log').write_text(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError('Candidate cache loader failed; inspect private local loader.log')
finally:
    config.unlink()
link=shlex.split((base/'build/shared_memory/CMakeFiles/shared_memory.dir/link.txt').read_text())
link=[v for v in link if not v.endswith('.o') and v not in ('-DNDEBUG','-O2')]
pos=link.index('-o')+1;link[pos]=str(out/'cache_check')
link[link.index('../bin/libcommon.a')]=str(candidate/'libcommon.a')
link[1:1]=['-O0','-UNDEBUG','-std=c++20','-I/tmp/nightcap-classic-rewards-input','-I'+str(base/'source'),'-isystem','/home/eqemu/code/build/vcpkg_installed/x64-linux/include',source]
r=subprocess.run(link,cwd=base/'build/shared_memory',text=True,capture_output=True)
if r.returncode:raise RuntimeError(r.stderr[-6000:])
cache=out/'shared/items';assert cache.is_file()
r=subprocess.run([str(out/'cache_check'),str(cache)],text=True,capture_output=True)
if r.returncode:raise RuntimeError(r.stdout+r.stderr)
evidence=json.loads(r.stdout)
evidence.update(status='passed_actual_native_cache',database=db,cache_sha256=hashlib.sha256(cache.read_bytes()).hexdigest(),
                loader_sha256=hashlib.sha256((candidate/'shared_memory').read_bytes()).hexdigest(),
                harness_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),compiler_command=link,assertions_enabled=True,production_changed=False,
                scope='414 custom definitions from isolated DB; no production or whole-stock cache claim')
print(json.dumps(evidence))
'''
    p=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],
        input='db='+repr(db)+'\npassword='+repr(password)+'\nnative='+repr(native)+'\nsource='+repr(source)+'\n'+remote,
        text=True,capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr[-6500:])
    evidence=json.loads(p.stdout)
    (folder/'cache-verification.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence))

if __name__=='__main__':main()

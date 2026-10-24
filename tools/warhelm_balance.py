"""Reproducible native stat calibration in a clone of an existing synthetic fixture.

No PEQ player data or production writes. The diagnostic arena excludes quest Perl
and Chapterhouse pathing; those require the separate encounter tests and player QA.
"""
import argparse,copy,hashlib,io,json,os,subprocess,sys,tarfile
from pathlib import Path
from warhelm_content import ROOT,OUT,compile_rows
from dungeon_migration import insert

DB='nightcap_warhelm_balance_20261024'
BASE_DB='nightcap_chapterhouse_balance_20261023'
RUNTIME='/tmp/nightcap-balance-warhelm-20261024'
BASE='/tmp/nightcap-balance-chapterhouse-20261023'
CONTAINER='akk-stack-eqemu-server-1'

def sql(statement,database=DB):
    assert database in (DB,'information_schema')
    return subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','sh','-lc',
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb -uroot -N -B --raw '+database],
        input=statement,text=True,capture_output=True,check=True).stdout

def remote(script):
    return subprocess.run(['docker','exec','-i',CONTAINER,'python3','-c',script],text=True,capture_output=True,check=True).stdout

def upload(name,data):
    assert '/' not in name
    blob=io.BytesIO()
    with tarfile.open(fileobj=blob,mode='w') as tar:
        info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
    subprocess.run(['docker','exec','-i',CONTAINER,'tar','xf','-','-C',RUNTIME],input=blob.getvalue(),check=True,capture_output=True)

def prepare():
    if sql(f"SELECT SCHEMA_NAME FROM SCHEMATA WHERE SCHEMA_NAME='{DB}'",'information_schema').strip():
        raise RuntimeError('Synthetic target already exists; never replace it')
    sql(f"CREATE DATABASE {DB}; GRANT ALL ON {DB}.* TO 'nightcap_balance'@'%';",'information_schema')
    dump=subprocess.Popen(['docker','exec','akk-stack-mariadb-1','sh','-lc',
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb-dump -uroot --single-transaction --skip-triggers '+BASE_DB],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    restore=subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','sh','-lc',
        'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb -uroot '+DB],stdin=dump.stdout,capture_output=True)
    dump.stdout.close();error=dump.stderr.read();code=dump.wait()
    if code or restore.returncode:raise RuntimeError('Synthetic clone failed: '+error.decode()+restore.stderr.decode())
    remote(f"""import json,shutil
from pathlib import Path
r=Path({RUNTIME!r});b=Path({BASE!r});r.mkdir(exist_ok=False)
c=json.loads((b/'eqemu_config.json').read_text());assert c['server']['database']['db']=={BASE_DB!r}
c['server']['database']['db']={DB!r};c['server']['auto_database_updates']='false'
(r/'eqemu_config.json').write_text(json.dumps(c))
for n in ('quests','plugins','lua_modules','logs','shared'):(r/n).mkdir()
(r/'maps').symlink_to(b/'maps',target_is_directory=True)
shutil.copyfile(b/'base-input.json',r/'base-input.json')
""")
    for name in ('build_native.py','native_harness.cpp','native_runtime.cpp','native_runtime.h'):
        data=(ROOT/'tools/balance'/name).read_text()
        if name=='native_harness.cpp':
            old='db.at("db") != "nightcap_thj_parity_20261018"'
            assert data.count(old)==1
            data=data.replace(old,'db.at("db") != "'+DB+'"')
        upload(name,data.encode())
    (OUT/'balance-setup.json').write_text(json.dumps(dict(database=DB,source_database=BASE_DB,runtime=RUNTIME,scope='Synthetic fixture clone only; October23 captured public definitions and strong gear; current candidate formulas',production_changed=False),indent=2)+'\n')
    print('Prepared separate synthetic calibration runtime',flush=True)

def diagnostics():
    # The only combat override is the dungeon-mode predicate, allowing the
    # unmodified CommonDamage path to apply its real post-calculation Raid scale.
    # No production object/source is changed.
    for name in ('build_native.py','native_harness.cpp','native_runtime.cpp','native_runtime.h'):
        data=(ROOT/'tools/balance'/name).read_text()
        if name=='native_harness.cpp':
            old='db.at("db") != "nightcap_thj_parity_20261018"'
            assert data.count(old)==1
            data=data.replace(old,'db.at("db") != "'+DB+'"')
        if name=='build_native.py':
            old="    link.insert(1, '-Wl,--wrap=gettimeofday,--wrap=time')"
            assert data.count(old)==1
            data=data.replace(old,old+"\n    link.insert(1, '-Wl,--wrap=_ZN15NightcapDungeon7RaidNPCEP3Mob')")
            # Adapters may compile alongside the final native build, but never
            # link against a mixture of old and newly compiled engine objects.
            old='    subprocess.run(link, cwd=build, check=True)'
            assert data.count(old)==1
            data=data.replace(old,'''    import time
    root = args.build_dir.resolve().parent
    expected = json.loads((root/'source-manifest.json').read_text())
    deadline = time.monotonic()+3600
    while True:
        try:
            ready = json.loads((root/'manifest.json').read_text()) if (root/'manifest.json').exists() else {}
        except json.JSONDecodeError:
            ready = {} # The builder may be completing its manifest write.
        if ready.get('source_files') == expected: break
        if time.monotonic()>deadline: raise RuntimeError('Matching full native build did not finish')
        time.sleep(1)
    assert all(digest(source/name)==sha for name,sha in expected.items()), 'Native source changed during diagnostic compilation'
'''+old)
        if name=='native_runtime.cpp':
            key='json NightcapBalanceEncounter(Client *c, const json &input)'
            assert data.count(key)==1
            data=data.replace(key,'''static bool chapterhouse_raid = false;
extern "C" bool __real__ZN15NightcapDungeon7RaidNPCEP3Mob(Mob *);
extern "C" bool __wrap__ZN15NightcapDungeon7RaidNPCEP3Mob(Mob *mob)
{
    if (chapterhouse_raid && mob && mob->IsNPC() && mob->GetNPCTypeID()==32040) { return true; }
    return __real__ZN15NightcapDungeon7RaidNPCEP3Mob(mob);
}
'''+key)
            data=data.replace('const int npc_id = input.at("npc_id").get<int>();', 'chapterhouse_raid = input.value("chapterhouse_raid",false);\n\tconst int npc_id = input.at("npc_id").get<int>();')
        if name=='native_harness.cpp':
            old='|| (policy == "wpm" && c->IsMulticlassMember(1)'
            assert data.count(old)==1
            data=data.replace(old,'|| (policy == "skm" && build.at("classes") == json::array({5,2,7})) '+old)
            # The inherited arena assumed an agnostic Warrior. Use an actual
            # Classic Human Shadow Knight combination for this isolated probe.
            assert data.count('deity = 396;')==1
            data=data.replace('deity = 396;','deity = 201;')
        if name=='native_runtime.cpp':
            data=data.replace('const bool wpm = combat_policy == "wpm";', 'const bool skm = combat_policy == "skm";\n\tconst bool wpm = combat_policy == "wpm";')
            data=data.replace('combat_policy == "melee_heal" || wpm','combat_policy == "melee_heal" || wpm || skm')
            data=data.replace('nuke = wpm ? 216 :','nuke = skm ? 445 : wpm ? 216 :')
            data=data.replace('const bool request_mend = wpm &&','const bool request_mend = (wpm || skm) &&')
            data=data.replace('const uint16 spell = c->GetHPRatio() < 55 ? heal : nuke;',
                'const uint16 spell = c->GetHPRatio() < 55 ? heal : (skm && c->GetHPRatio() >= 85 ? 0 : nuke);')
            data=data.replace('c->GetPP().mem_spells[0] = nuke;', 'if (skm && c->GetSpellMinLevel(nuke)>c->GetLevel()) { throw std::runtime_error("Ineligible Shadow Knight lifetap"); }\n\tc->GetPP().mem_spells[0] = nuke;')
        upload(name,data.encode())
    print('Prepared isolated exact Raid-damage predicate control' ,flush=True)


def build():
    with (OUT/'balance-build.log').open('w') as log:
        r=subprocess.run(['docker','exec',CONTAINER,'python3',RUNTIME+'/build_native.py','--source','/tmp/nightcap-warhelm-v1/source','--build-dir','/tmp/nightcap-warhelm-v1/build'],stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Diagnostic build failed; inspect balance-build.log')
    cache()
    subprocess.run(['docker','cp',CONTAINER+':'+RUNTIME+'/native-build-manifest.json',str(OUT/'balance-build-manifest.json')],check=True,capture_output=True)
    print('Native diagnostic linked; not installed',flush=True)

def cache():
    # This executable reads the isolated runtime's config and writes only its shared/ directory.
    with (OUT/'balance-cache.log').open('w') as log:
        r=subprocess.run(['docker','exec','-w',RUNTIME,CONTAINER,'/tmp/nightcap-warhelm-v1/build/bin/shared_memory'],stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Isolated shared-memory generation failed')

def execute(name,data,seed=101):
    upload(name+'-input.json',json.dumps(data,indent=2).encode())
    command=['docker','exec','-w',RUNTIME,'-e','NIGHTCAP_BALANCE_RNG_SEED='+str(seed),CONTAINER,
        RUNTIME+'/balance-zone','tests:balance',RUNTIME+'/'+name+'-input.json',RUNTIME+'/'+name+'-result.json']
    with (OUT/(name+'.log')).open('w') as log:
        r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=240)
    if r.returncode:raise RuntimeError(name+' native diagnostic failed; inspect its log')
    for suffix in ('-input.json','-result.json'):
        subprocess.run(['docker','cp',CONTAINER+':'+RUNTIME+'/'+name+suffix,str(OUT/(name+suffix))],check=True,capture_output=True)
    return json.loads((OUT/(name+'-result.json')).read_text())

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=('prepare','diagnostics','build','cache'));args=parser.parse_args()
    globals()[args.stage]()

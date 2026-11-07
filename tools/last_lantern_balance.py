"""Isolated native combat calibration; never write PEQ or production."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from last_lantern_content import ROOT, compile_items, compile_npcs
from dungeon_catalog import existing_items
from dungeon_migration import insert
from capture_lantern_content import SSH

OUT=ROOT/'docs/adventure-journal/release-20261107/balance'
OUT.mkdir(parents=True,exist_ok=True)
DB='nightcap_lantern_balance_20261107'
BASE_DB='nightcap_warhelm_balance_20261024'
RUNTIME='/tmp/nightcap-balance-last-lantern-20261107'
BASE='/tmp/nightcap-balance-warhelm-20261024'
CONTAINER='akk-stack-eqemu-server-1'
SEED=1107
TABLES=('rule_sets','rule_values','aa_ability','aa_ranks','aa_rank_effects','aa_rank_prereqs','spells_new','skill_caps')


def remote(code,timeout=300):
    r=subprocess.run(['docker','exec','-i',CONTAINER,'python3','-'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    if r.returncode:raise RuntimeError(r.stderr[-2500:]+r.stdout[-800:])
    return r.stdout


def sql(body,database=DB):
    assert database in (DB,'information_schema')
    r=subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
        'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --quick --skip-column-names '+database],
        input=body,text=True,encoding='utf-8',capture_output=True,timeout=300)
    if r.returncode:raise RuntimeError(r.stderr[-1800:])
    return r.stdout


def prepare():
    assert not sql("SELECT SCHEMA_NAME FROM SCHEMATA WHERE SCHEMA_NAME='"+DB+"'",'information_schema').strip(),'Synthetic target exists; never overwrite'
    sql('CREATE DATABASE '+DB+"; GRANT ALL ON "+DB+".* TO 'nightcap_balance'@'%';",'information_schema')
    dump=subprocess.Popen(['docker','exec','akk-stack-mariadb-1','sh','-c',
        'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb-dump -uroot --single-transaction --quick --skip-triggers '+BASE_DB],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    restore=subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
        'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot '+DB],stdin=dump.stdout,capture_output=True)
    dump.stdout.close();error=dump.stderr.read();code=dump.wait()
    if code or restore.returncode:raise RuntimeError('Synthetic clone failed: '+error.decode()[-800:]+restore.stderr.decode()[-800:])
    print(remote(f'''from pathlib import Path
import json,shutil
p=Path({RUNTIME!r});b=Path({BASE!r});p.mkdir(exist_ok=False)
c=json.loads((b/'eqemu_config.json').read_text());assert c['server']['database']['db']=={BASE_DB!r}
c['server']['database']['db']={DB!r};c['server']['auto_database_updates']='false'
(p/'eqemu_config.json').write_text(json.dumps(c))
for n in ('quests','plugins','lua_modules','logs','shared'):(p/n).mkdir()
(p/'maps').symlink_to(b/'maps',target_is_directory=True)
shutil.copyfile(b/'base-input.json',p/'base-input.json')
print('Created isolated synthetic database and runtime; no production writes.')
''').strip())
    OUT.mkdir(exist_ok=True,parents=True)
    (OUT/'setup.json').write_text(json.dumps(dict(database=DB,source_database=BASE_DB,runtime=RUNTIME,production_changed=False),indent=2)+'\n')


def capture():
    ids={r['values']['id'] for r in existing_items()}
    base=json.loads((ROOT/'artifacts/last-lantern-20261107/balance-inspect.json').read_text())['input']
    for item in base['builds'][0]['equipment']:
        ids.update((item['id'],item['id']%200000))
        ids.update(a['id'] for a in item.get('augments',[]))
    code=r'''
import base64,datetime,gzip,json,subprocess
root='/opt/nightcap/deploy/production'
def q(statement):
 args=['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--quick','--skip-column-names','--default-character-set=utf8mb4','peq']
 text='SET SESSION max_session_mem_used=134217728; SET TRANSACTION READ ONLY; START TRANSACTION WITH CONSISTENT SNAPSHOT; '+statement+'; COMMIT;'
 r=subprocess.run(args,cwd=root,input=text,text=True,capture_output=True,timeout=900)
 assert r.returncode==0,'Read-only public capture failed'
 return r.stdout.splitlines()
result={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'production read-only public combat definitions','tables':{}}
for table in TABLES+('items',):
 columns=[r.split('\t')[0] for r in q('SHOW COLUMNS FROM `'+table+'`')]
 where=' WHERE id IN ('+','.join(map(str,IDS))+')' if table=='items' else ''
 rows=[json.loads(r) for r in q('SELECT JSON_ARRAY('+','.join('`'+c+'`' for c in columns)+') FROM `'+table+'`'+where)]
 result['tables'][table]={'columns':columns,'rows':rows}
result['selected_ruleset']=q("SELECT value FROM variables WHERE varname='RuleSet'")
payload=gzip.compress(json.dumps(result,separators=(',',':')).encode(),mtime=0);assert len(payload)<50000000
print(base64.b64encode(payload).decode())
'''
    r=subprocess.run(SSH,input='TABLES='+repr(TABLES)+'\nIDS='+repr(sorted(ids))+'\n'+code,text=True,encoding='utf-8',capture_output=True,timeout=1200)
    if r.returncode:raise RuntimeError(r.stderr[-1500:])
    raw=base64.b64decode(r.stdout);v=json.loads(gzip.decompress(raw))
    (OUT/'public-content.json.gz').write_bytes(raw)
    receipt=dict(captured_at=v['captured_at'],sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),tables={t:len(d['rows']) for t,d in v['tables'].items()},selected_ruleset=v['selected_ruleset'],production_changed=False)
    (OUT/'public-capture.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


def restore():
    v=json.loads(gzip.decompress((OUT/'public-content.json.gz').read_bytes()))
    assert v['selected_ruleset'] in ([],['default'])
    for table,data in v['tables'].items():
        assert table in TABLES+('items',)
        if table!='items':sql('DELETE FROM `'+table+'`;')
        for start in range(0,len(data['rows']),200):
            sql('\n'.join(insert(table,dict(zip(data['columns'],r))).replace('INSERT INTO','REPLACE INTO',1) for r in data['rows'][start:start+200]))
        print('Refreshed synthetic',table,len(data['rows']),flush=True)
    from epic05 import migration_sql,load_catalog
    # The unchanged charm/spell definitions are additional staged content.
    old=migration_sql(load_catalog())
    definitions=[line for line in old.splitlines() if line.startswith('INSERT INTO `items`') or line.startswith('INSERT INTO `spells_new`')]
    sql('\n'.join(line.replace('INSERT INTO','REPLACE INTO',1) for line in definitions))
    sql('\n'.join(insert('items',r).replace('INSERT INTO','REPLACE INTO',1) for r in compile_items()))
    for character,classes in ((94025,(1,3,7)),(94026,(1,2,12)),(94027,(1,2,7)),(94028,(1,2,13))):
        sql(f"INSERT INTO character_multiclass(character_id,class2,class3) VALUES({character},{classes[1]},{classes[2]}) ON DUPLICATE KEY UPDATE class2=VALUES(class2),class3=VALUES(class3);")
    print('Refreshed current public definitions and candidate equipment only in '+DB)


def build():
    files={n:(ROOT/'tools/balance'/n).read_text(encoding='utf-8') for n in ('build_native.py','native_harness.cpp','native_runtime.cpp','native_runtime.h')}
    old='db.at("db") != "nightcap_thj_parity_20261018"'
    assert files['native_harness.cpp'].count(old)==1
    files['native_harness.cpp']=files['native_harness.cpp'].replace(old,'db.at("db") != "'+DB+'"')
    r=files['native_runtime.cpp']
    old='const uint16 nuke = wpm ? 216 : melee_heal ? 0 : npc_id == 32040 ? 732 : 659;'
    assert r.count(old)==1
    r=r.replace(old,'const uint16 nuke = input.value("nuke_spell", uint16(wpm ? 216 : melee_heal ? 0 : npc_id == 32040 ? 732 : 659));')
    old='const uint16 heal = c->GetSpellMinLevel(9) <= c->GetLevel() ? 9 : 15;'
    assert r.count(old)==1
    r=r.replace(old,'const uint16 heal = input.value("heal_spell", uint16(c->GetSpellMinLevel(9) <= c->GetLevel() ? 9 : 15));')
    r=r.replace('if (wpm && (c->GetSpellMinLevel(nuke)>c->GetLevel()', 'if (nuke && (!IsValidSpell(nuke) || c->GetSpellMinLevel(nuke)>c->GetLevel())) { throw std::runtime_error("Ineligible diagnostic nuke"); }\n\tif (wpm && nuke && (c->GetSpellMinLevel(nuke)>c->GetLevel()')
    # Diagnostic-only two-enemy pressure. Production actor code is unchanged.
    begin=r.index('json NightcapBalanceEncounter(Client *c, const json &input)')
    a,runtime=r[:begin],r[begin:]
    runtime=runtime.replace('const uint32 combat_start = Timer::GetCurrentTime();', 'const unsigned enemy_count=input.value("enemy_count",1u);\n\tif (!enemy_count || enemy_count>2) { throw std::runtime_error("Invalid diagnostic enemy count"); }\n\tstd::vector<BalanceNPC*> foes{npc};\n\tfor(unsigned i=1;i<enemy_count;++i) { auto add=new BalanceNPC(type,nullptr,glm::vec4(p[0],p[1],p[2],p[3]),GravityBehavior::Water);add->capture_damage=true;entity_list.AddNPC(add,false);add->AddToHateList(c,1);foes.push_back(add); }\n\tconst uint32 combat_start = Timer::GetCurrentTime();')
    runtime=runtime.replace('&& terminal.empty(); ms += 50)', '&& !terminal.count(c) && std::any_of(foes.begin(),foes.end(),[](auto f){return !terminal.count(f);}); ms += 50)')
    runtime=runtime.replace('\t\tAdvance(50);', '\t\tif (terminal.count(npc)) { for(auto f:foes) if(!terminal.count(f)) {npc=f;c->SetTarget(npc);break;} }\n\t\tAdvance(50);')
    runtime=runtime.replace('if (!terminal.empty()) { sample(); break; }', 'if (terminal.count(c)) { sample(); break; }')
    runtime=runtime.replace('if (!npc->Process()) { throw std::runtime_error("NPC processing stopped before terminal combat result"); }', 'for(auto f:foes) { if (!terminal.count(f) && !f->Process()) { throw std::runtime_error("NPC processing stopped before terminal combat result"); } }')
    runtime=runtime.replace('return result;\n}', 'result["enemy_count"]=enemy_count;\n\treturn result;\n}',1)
    runtime=runtime.replace('const uint32 combat_start = Timer::GetCurrentTime();','unsigned waves_left=input.value("waves",1u);if(!waves_left || waves_left>3){throw std::runtime_error("Invalid waves");}--waves_left;\n\tconst uint32 combat_start = Timer::GetCurrentTime();')
    runtime=runtime.replace('&& std::any_of(foes.begin(),foes.end(),[](auto f){return !terminal.count(f);});', '&& (waves_left || std::any_of(foes.begin(),foes.end(),[](auto f){return !terminal.count(f);}));')
    runtime=runtime.replace('\t\tif (terminal.count(npc))', '\t\tif (waves_left && std::all_of(foes.begin(),foes.end(),[](auto f){return terminal.count(f);})) { --waves_left;for(unsigned i=0;i<enemy_count;++i){auto add=new BalanceNPC(type,nullptr,glm::vec4(p[0],p[1],p[2],p[3]),GravityBehavior::Water);add->capture_damage=true;entity_list.AddNPC(add,false);add->AddToHateList(c,1);foes.push_back(add);} }\n\t\tif (terminal.count(npc))')
    runtime=runtime.replace('terminal.count(npc) ? "npc_death"', '!waves_left && std::all_of(foes.begin(),foes.end(),[](auto f){return terminal.count(f);}) ? "npc_death"')
    runtime=runtime.replace('result["enemy_count"]=enemy_count;', 'result["enemy_count"]=enemy_count;result["killed_count"]=std::count_if(foes.begin(),foes.end(),[](auto f){return terminal.count(f);});result["waves"]=input.value("waves",1u);')
    r=a+runtime
    files['native_runtime.cpp']=r
    code=r'''from pathlib import Path
import json,shlex,subprocess
runtime=Path(RUNTIME);source=Path('/tmp/nightcap-last-lantern-20261107-v1/source')
for n,s in FILES.items():(runtime/n).write_text(s)
commands=json.loads(Path('/tmp/nightcap-last-lantern-20261107-v1/link-commands.json').read_text())
cmd=commands['candidate-zone'];cwd=Path(cmd['cwd']);args=cmd['arguments']
args=[a if a in ('CMakeFiles/zone.dir/main.cpp.o','CMakeFiles/zone.dir/client.cpp.o') or a.startswith('-') or not a.endswith(('.a','.o')) else str((cwd/a).resolve()) for a in args]
folder=runtime/'build/zone/CMakeFiles/zone.dir';folder.mkdir(parents=True,exist_ok=True)
(folder/'link.txt').write_text(shlex.join(args))
old=Path('/tmp/nightcap-power-source-xp-display-20261103-v1/build/zone/CMakeFiles/zone.dir/flags.make').read_text()
old=old.replace('CXX_INCLUDES = ','CXX_INCLUDES = -I'+str(source)+' -I'+str(source/'zone')+' ')
old=old.replace('CXX_FLAGS = ','CXX_FLAGS = -include /tmp/nightcap-last-lantern-20261107-v1/cmake_pch.hxx ')
(folder/'flags.make').write_text(old)
# Builder replaces these two references; all other inputs are authenticated candidate inputs.
subprocess.run(['python3',str(runtime/'build_native.py'),'--source',str(source),'--build-dir',str(runtime/'build'),*(['--reuse-adapters'] if (runtime/'native-build-manifest.json').exists() else [])],check=True,cwd=runtime)
'''
    result=remote('FILES='+repr(files)+'\nRUNTIME='+repr(RUNTIME)+'\n'+code,1800)
    (OUT/'build.log').write_text(result,encoding='utf-8')
    print(result[-2500:])


def cache():
    with (OUT/'cache.log').open('w',encoding='utf-8') as log:
        r=subprocess.run(['docker','exec','-w',RUNTIME,CONTAINER,'/tmp/nightcap-last-lantern-20261107-v1/candidate-shared_memory.stripped'],stdout=log,stderr=subprocess.STDOUT,timeout=600)
    assert r.returncode==0,(OUT/'cache.log').read_text()[-1500:]
    print('Generated isolated cache using candidate shared_memory.')


def execute(name,value):
    remote('from pathlib import Path\nPath('+repr(RUNTIME+'/'+name+'-input.json')+').write_text('+repr(json.dumps(value))+')')
    command=['docker','exec','-w',RUNTIME,'-e','NIGHTCAP_BALANCE_RNG_SEED='+str(SEED),CONTAINER,RUNTIME+'/balance-zone','tests:balance',RUNTIME+'/'+name+'-input.json',RUNTIME+'/'+name+'-result.json']
    r=subprocess.run(command,text=True,encoding='utf-8',capture_output=True,timeout=300)
    (OUT/(name+'.log')).write_text((r.stdout+r.stderr)[-10000:],encoding='utf-8')
    assert r.returncode==0,(r.stdout+r.stderr)[-1500:]
    result=json.loads(remote('from pathlib import Path\nprint(Path('+repr(RUNTIME+'/'+name+'-result.json')+').read_text())'))
    (OUT/(name+'-result.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def fixture(level,profile='war-pal-mnk',developed=False):
    import copy
    v=json.loads((ROOT/'artifacts/last-lantern-20261107/balance-inspect.json').read_text())['input']
    b=copy.deepcopy(v['builds'][0]);b.update(level=level,test_character_id={'war-pal-mnk':94025,'war-clr-wiz':94026,'war-clr-mnk':94027}[profile],profile=profile,classes={'war-pal-mnk':[1,3,7],'war-clr-wiz':[1,2,12],'war-clr-mnk':[1,2,7]}[profile],aa_budget=0,aa_rank_ids=[],tier='earned campaign before encounter; Normal dungeon supporting gear')
    band=20 if level<30 else 30 if level<40 else 40
    rows={r['design']:r['values'] for r in existing_items() if r['band']==band and r['quality']=='Normal'}
    slots={0:2,1:17,2:7,3:9,4:12,5:18,6:19,7:6,(12 if profile=='war-clr-wiz' else 8):13,16:1,17:15,18:5,19:3,20:8,21:20}
    equipment=[dict(slot=slot,id=rows[design]['id']) for design,slot in slots.items()]
    equipment += [dict(slot=10,id=rows[3]['id']),dict(slot=4,id=rows[16]['id']),dict(slot=16,id=rows[17]['id'])]
    grade=0 if level<=40 else 1 if level<=46 else 2
    earned=1 if level<=25 else 3 if level<=38 else 4 if level<=40 else 6 if level<=46 else 7
    fit=1 if profile!='war-clr-wiz' else 3
    armor=compile_items()
    for item in armor:
        n=item['id']-964000
        if n//32==fit and (n%32)//8==grade and n%8<earned:
            slot=(19,12,9,10,7,18,2,17)[n%8]
            equipment=[r for r in equipment if r['slot']!=slot]+[dict(slot=slot,id=item['id'])]
    if developed:
        # Stronger item quality remains inside the current normal dungeon family.
        for r in equipment:
            if r['id']<964000:r['id']+=2
    b['equipment']=equipment
    for key in ('gear_control','aa_stage','aa_policy'):b.pop(key,None)
    return {'builds':[b],'export_equipment':True,'export_aa_catalog':True}


def probe():
    v=fixture(25);result=execute('probe25',v)
    print(json.dumps({'build':{k:x for k,x in result['builds'][0].items() if k not in ('aa_catalog','equipped_items','aa_purchases')}}))


def fight(level,index,profile='war-pal-mnk',budget=None,hp=None,damage=None,enemies=1,waves=1,seed=1107):
    global SEED
    SEED=seed
    sys.path.insert(0,str(ROOT/'tools/balance'))
    from aa_allocations import Purchases
    v=fixture(level,profile)
    name=f'{level}-{index}-{profile}-aa{budget if budget is not None else 2*(level-1)}-n{enemies}-w{waves}-seed{seed}'
    catalog=execute(name+'-catalog',v)['builds'][0]['aa_catalog']
    if isinstance(catalog,dict):catalog=catalog['ranks']
    state=Purchases(catalog);state.free_closure()
    budget=2*(level-1) if budget is None else budget
    priority=[28,33,34,20,224,18,19,30,189,108,23,114,215,397,398]
    while True:
        available=[r for r in state.ranks.values() if not state.reasons(r) and state.spent+r['cost']<=budget]
        if not available:break
        row=min(available,key=lambda r:(priority.index(r['ability_id']) if r['ability_id'] in priority else 100,r['cost'],r['rank'],r['rank_id']))
        state.buy(row)
    v['builds'][0].update(aa_budget=budget,aa_rank_ids=state.ids,aa_policy='explicit legal native catalog; defense/sustain first then available purchases')
    npc=compile_npcs()[9+index] if index<8 else next(n for n in compile_npcs() if n['id']==998918)
    assert npc['id']==998910+index if index<8 else npc['id']==998918
    npc=dict(npc,id=32040)
    if hp is not None:npc['hp']=hp
    if damage:npc.update(mindmg=damage[0],maxdmg=damage[1])
    sql(insert('npc_types',npc).replace('INSERT INTO','REPLACE INTO',1))
    heal=(17 if level<27 else 15 if level>=36 else 12) if profile=='war-pal-mnk' else 9 if level>=30 else 15
    nuke=(216 if level>=28 else 0) if profile=='war-pal-mnk' else 0 if profile=='war-clr-mnk' else 732 if level>=49 else 659 if level>=43 else 464
    v.pop('export_aa_catalog',None)
    v['encounter']=dict(npc_id=32040,npc_position=[-871,-1395,104.879997,45],duration_ms=600000,return_to_melee=True,combat_policy={'war-pal-mnk':'wpm','war-clr-mnk':'melee_heal','war-clr-wiz':'caster_heal'}[profile],nuke_spell=nuke,heal_spell=heal,melee_specials=True,enemy_count=enemies,waves=waves)
    r=execute(name,v);b=r['builds'][0];e=r['encounter'];trace=e['trace']
    audit=dict(level=level,npc=998910+index,profile=profile,seed=seed,enemies=enemies,waves=waves,killed_count=e['killed_count'],npc_hp=npc['hp'],npc_damage=[npc['mindmg'],npc['maxdmg']],aa_requested=budget,aa_spent=b['aa_spent'],result=e['result'],elapsed_ms=e['elapsed_ms'],hp=b['hp'],mana=b['mana'],minimum_hp=min(t['player_hp'] for t in trace),final_hp=trace[-1]['player_hp'],final_mana=trace[-1]['player_mana'],final_npc_hp=trace[-1]['npc_hp'],heal_spell=heal,nuke_spell=nuke,gear=v['builds'][0]['equipment'],scope='Native SolB arena, explicit simultaneous opponents and continuous waves; no ally guardian or brand mechanic; native trained skills and purchased AAs, no buffs/pets/augments; full expedition QA remains open')
    (OUT/(name+'-summary.json')).write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:x for k,x in audit.items() if k!='gear'}),flush=True)
    return audit


def calibrate():
    fight(25,0)
    fight(50,8)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('prepare','capture','restore','build','cache','probe','calibrate'))
    globals()[parser.parse_args().stage]()

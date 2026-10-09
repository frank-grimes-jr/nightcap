"""Execute the exact install/verification/inverse SQL in a disposable local schema."""
import hashlib,json,re,secrets,subprocess,sys,types
from pathlib import Path
from unittest.mock import patch
sys.modules.setdefault('fcntl',types.SimpleNamespace(LOCK_EX=1,LOCK_NB=2,flock=lambda *a:None))
import rollout as app
schema='nightcap_hunt_rollout_'+secrets.token_hex(6)
release=Path(r'C:/Users/verre/.codex/worktrees/zone-loot-hunt-forge/EQ_Local_Dev/docs/releases/zone-loot-20261009')
docker=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
def sql(q,use=True):
    cmd=[docker,'exec','-i','akk-stack-mariadb-1','sh','-c','MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names']
    r=subprocess.run(cmd,input=(f'USE `{schema}`;\n' if use else '')+q,text=True,capture_output=True,encoding='utf-8',timeout=180)
    if r.returncode:raise RuntimeError(r.stderr[-1500:])
    return r.stdout
def fingerprint():return hashlib.sha256(sql('SELECT * FROM items ORDER BY id;').encode()).hexdigest()
sql(f'CREATE DATABASE `{schema}`;',False)
try:
    tables=('items','spells_new','npc_types','spawn2','spawnentry','loottable','loottable_entries','lootdrop','lootdrop_entries','merchantlist','zone','variables')
    sql('\n'.join(f'CREATE TABLE `{t}` LIKE peq.`{t}`;' for t in tables))
    pre=json.loads((release/'generated/socket-preimages.json').read_text())
    inserts=[]
    for x in pre:
        v={k:v if k=='Name' else int(v) for k,v in x['before'].items()}
        inserts.append('INSERT INTO items ('+','.join('`'+k+'`' for k in v)+') VALUES ('+','.join(app.literal(a) for a in v.values())+');')
    sql('\n'.join(inserts));before=fingerprint()
    with patch.object(app,'STAGE',release),patch.object(app,'sql',sql),patch.object(app.r,'state',lambda s:{'State':{'Running':False}}),patch.object(app.r,'player_data',lambda:{'unchanged':True}):
        app.socket_check(False);baseline=app.content()
        sql((release/'generated/install.sql').read_text());app.installed_check(0)
        assert app.content()==baseline
        sql((release/'generated/activate.sql').read_text());app.installed_check(1)
        app.early_undo({'unchanged':True},baseline)
        assert fingerprint()==before
        assert sql('SELECT COUNT(*) FROM nightcap_zone_hunt_state; SELECT COUNT(*) FROM nightcap_zone_hunt_sources; SELECT COUNT(*) FROM nightcap_zone_hunt_zones; SELECT COUNT(*) FROM nightcap_zone_hunt_forges;').strip()=='0\n0\n0\n0'
    evidence={'status':'passed','schema':'disposable, dropped after run','checks':['real generated installation','all 448 item value predicates','exact 6056 sources and 56 zone configs','all 2290 socket preimages and installed values','all original item columns preserved after normalization','activation gate','actual guarded initial inverse','byte-identical original item rows restored','all owned state rows empty'],'rollout_sha256':hashlib.sha256(Path(app.__file__).read_bytes()).hexdigest()}
    Path(__file__).with_name('inverse-rehearsal.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence))
finally:
    assert re.fullmatch('nightcap_hunt_rollout_[0-9a-f]{12}',schema)
    sql(f'DROP DATABASE `{schema}`;',False)

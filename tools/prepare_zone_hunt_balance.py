"""Prepare a new content-only database and synthetic loadouts; never touch PEQ players."""
import argparse
import copy
import json
from pathlib import Path
import re
import secrets
import subprocess
import sys

DB='nightcap_zone_hunt_20261009'
USER='nightcap_hunt_qa'
RUNTIME='/tmp/nightcap-balance-zone-hunt-20261009'
SERVER='akk-stack-eqemu-server-1'

def command(args,data=None):
    p=subprocess.run(args,input=data,text=True,encoding='utf-8',capture_output=True,timeout=900)
    if p.returncode: raise RuntimeError(p.stderr[-2000:])
    return p.stdout

def sql(text):
    return command(['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
        'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names'],text)

def main(repo,release,snapshot,resume=False):
    sys.path.insert(0,str(repo/'tools/balance'))
    from prepare_native import content_tables
    if not resume and sql(f"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='{DB}'; SELECT User FROM mysql.user WHERE User='{USER}';").strip():
        raise ValueError('Refusing to overwrite an existing QA database/user')
    schema_source=command(['docker','exec',SERVER,'cat','/tmp/nightcap-market-zone-hunt-dev-20261009/source/common/database_schema.h'])
    tables=content_tables(schema_source)
    available=sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_TYPE='BASE TABLE';").splitlines()
    if not set(tables)<=set(available) or any(not re.fullmatch('[a-zA-Z0-9_]+',x) for x in available):
        raise ValueError('Content table registry/schema mismatch')
    password=secrets.token_hex(32)
    if resume:
        if sql(f'SELECT COUNT(*) FROM {DB}.account; SELECT COUNT(*) FROM {DB}.character_data;').strip()!='0\n0':
            raise ValueError('Resume requires an unused content-only fixture')
        if sql(f"SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='{DB}' AND TABLE_NAME='nightcap_zone_hunt_state';").strip():
            raise ValueError('Resume cannot overwrite an installed feature')
        counts=sql('\n'.join(f"SELECT '{t}',(SELECT COUNT(*) FROM peq.`{t}`),(SELECT COUNT(*) FROM {DB}.`{t}`);" for t in tables)).splitlines()
        missing=[]
        for row in counts:
            table,expected,actual=row.split('\t')
            if expected==actual: continue
            if actual!='0': raise ValueError('Partially copied nonempty content table: '+table)
            missing.append(table)
        sql('\n'.join(f'INSERT INTO {DB}.`{t}` SELECT * FROM peq.`{t}`;' for t in missing))
        sql(f"ALTER USER '{USER}'@'%' IDENTIFIED BY '{password}';")
        print(f'Verified resumed content clone; completed {len(missing)} empty tables',flush=True)
    else:
        sql(f"CREATE DATABASE {DB}; CREATE USER '{USER}'@'%' IDENTIFIED BY '{password}'; GRANT ALL ON {DB}.* TO '{USER}'@'%';")
        sql('\n'.join(f'CREATE TABLE {DB}.`{t}` LIKE peq.`{t}`;' for t in available))
        sql('\n'.join(f'INSERT INTO {DB}.`{t}` SELECT * FROM peq.`{t}`;' for t in tables))
    sql(f"INSERT INTO {DB}.variables SELECT * FROM peq.variables WHERE varname IN ('RuleSet','ServerType');")
    # Apply captured socket preimages to the disposable content fixture only.
    # This is not an assertion that local content otherwise equals production.
    from zone_hunt import sql as literal
    preimages=json.loads((release/'generated/socket-preimages.json').read_text())
    updates=[]
    for entry in preimages:
        r=entry['before']
        updates.append('UPDATE items SET '+','.join('`'+k+'`='+literal(v if k=='Name' else int(v)) for k,v in r.items() if k!='id')+' WHERE id='+str(entry['id'])+';')
    sql(f'USE {DB};\n'+'\n'.join(updates))
    sql(f'USE {DB};\n'+(release/'generated/install.sql').read_text())
    snapshot=json.loads(snapshot.read_text())
    for r in snapshot['rules']+snapshot['percent_rules']:
        sql(f"INSERT INTO {DB}.rule_values(ruleset_id,rule_name,rule_value) VALUES({int(r['ruleset_id'])},{literal(r['name'])},{literal(r['value'])}) ON DUPLICATE KEY UPDATE rule_value=VALUES(rule_value);")
    templates=json.loads(command(['docker','exec',SERVER,'cat','/tmp/nightcap-balance-20260912/inputs.json']))
    items=json.loads((release/'generated/items.json').read_text())
    socket_by_id={p['id']:p['socket']-1 for p in preimages}
    builds=[]
    for base in templates['builds']:
        tier=('Base','Polished','Exalted','Ascended').index(base['tier'])
        aug_zone={'war-clr-wiz':'kedge','war-clr-mnk':'gukbottom','mag-nec-shm':'kedge'}[base['profile']]
        aug=next(i['id'] for i in items if i['kind']=='Augment' and i['zone']==aug_zone and i['tier']==tier)
        for mode in ('baseline','augmented'):
            b=copy.deepcopy(base);b['tier']=base['tier']+' / '+mode;b['test_character_id']=len(builds)+1;b['aa_budget']=0
            if mode=='augmented':
                for e in b['equipment']:
                    if e['slot'] in (2,7,12,17,18,19) and e['id'] in socket_by_id:
                        e['augments']=[dict(socket=socket_by_id[e['id']],id=aug)]
            builds.append(b)
    rows=','.join(f"({b['test_character_id']},{b['classes'][1]},{b['classes'][2]})" for b in builds)
    sql(f'INSERT INTO {DB}.character_multiclass(character_id,class2,class3) VALUES {rows};')
    if sql(f'SELECT COUNT(*) FROM {DB}.account; SELECT COUNT(*) FROM {DB}.character_data;').strip()!='0\n0':
        raise ValueError('QA schema unexpectedly contains player/account rows')
    config={'server':{'auto_database_updates':'false','world':{'shortname':'zone_hunt_qa','longname':'Isolated zone hunt QA','tcp':{'ip':'127.0.0.1','port':'1'}},
        'database':{'host':'mariadb','port':'3306','db':DB,'username':USER,'password':password},
        'directories':{'quests':'quests','plugins':'plugins','lua_modules':'lua_modules','logs':'logs','maps':'maps','shared_memory':'shared/',
                       'patches':'/home/eqemu/server','opcodes':'/home/eqemu/server'}}}
    setup="""import json,os,sys
from pathlib import Path
root=Path('/tmp/nightcap-balance-zone-hunt-20261009');root.mkdir(exist_ok=False)
for name in ('quests','plugins','lua_modules','logs','maps','shared'): (root/name).mkdir()
for name,value in json.load(sys.stdin).items():
 p=root/name;p.write_text(json.dumps(value,indent=2)+'\\n');os.chmod(p,0o600)
"""
    inputs=dict(export_equipment=True,builds=builds)
    command(['docker','exec','-i',SERVER,'python3','-c',setup],json.dumps({'eqemu_config.json':config,'zone-hunt-inputs.json':inputs}))
    (release/'balance-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    (release/'balance-setup.json').write_text(json.dumps(dict(database=DB,runtime=RUNTIME,player_rows=0,account_rows=0,
        builds=len(builds),aa_policy='0 AA control',content_scope='Local PEQ content with captured production socket preimages and captured cap rules; not a production clone.'),indent=2)+'\n')
    print(json.dumps(dict(database=DB,builds=len(builds),player_rows=0)))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--release',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True)
    p.add_argument('--resume-content-clone',action='store_true')
    a=p.parse_args();main(a.repo,a.release,a.snapshot,a.resume_content_clone)

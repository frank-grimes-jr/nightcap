"""Create an isolated content-only PEQ clone for the native diagnostic.

Never updates, drops, or grants new permissions on peq. Refuses an existing
destination or test user. Password is generated and sent via stdin, never logged.
"""
import argparse
import hashlib
import json
import re
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from builds import load_snapshot
from verify_cpp import extract_function


DB = 'nightcap_balance_20260912'
USER = 'nightcap_balance'
RUNTIME = '/tmp/nightcap-balance-20260912'
MYSQL = 'akk-stack-mariadb-1'
SERVER = 'akk-stack-eqemu-server-1'


def command(args, *, data=None):
    result = subprocess.run(args, input=data, capture_output=True, check=False)
    if result.returncode:
        # Do not echo commands or SQL payloads (which may contain test credentials).
        raise RuntimeError(result.stderr.decode(errors='replace')[-3000:])
    return result.stdout


def root_sql(sql):
    return command(['docker','exec','-i',MYSQL,'sh','-c',
                    'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names'],
                   data=sql.encode())


def content_tables(source):
    body = extract_function(source, 'static std::vector<std::string> GetContentTables()')
    tables = re.findall(r'"([a-z_]+)"', body)
    if not {'items','spells_new','aa_ranks','zone'} <= set(tables):
        raise ValueError('Content table declaration changed')
    return sorted(set(tables) | {'rule_sets','rule_values','content_flags','logsys_categories',
                                'command_settings','command_subsettings','perl_event_export_settings'})


def native_inputs(builds, tables):
    allocations = {r['id']:r for r in tables['char_create_point_allocations']}
    result = []
    for i, build in enumerate(builds, 1):
        if build['race'] != 'Human' or build['deity'] != 'Agnostic':
            raise ValueError('This native fixture supports Human agnostic creation only')
        candidates = {r['allocation_id'] for r in tables['char_create_combinations']
                      if r['race']==1 and r['class']==build['classes'][0]
                      and r['deity']==396 and r['expansions_req']==0}
        if len(candidates) != 1:
            raise ValueError('Missing or ambiguous Classic creation allocation')
        row = allocations[candidates.pop()]
        creation = {stat:row['base_'+stat]+row['alloc_'+stat] for stat in ('str','sta','dex','agi','int','wis','cha')}
        result.append(build | {'creation':creation,'test_character_id':i})
    return {'builds':result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--builds',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    snapshot, snapshot_manifest = load_snapshot(args.snapshot)
    inputs = native_inputs(json.loads(args.builds.read_text())['builds'], snapshot['tables'])
    existing = root_sql(f"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='{DB}';"
                        f"SELECT User FROM mysql.user WHERE User='{USER}';")
    if existing.strip():
        raise ValueError('Destination database/user exists; refusing to overwrite it')
    available = root_sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME;").decode().splitlines()
    if not available or any(not re.fullmatch('[A-Za-z0-9_]+', t) for t in available):
        raise ValueError('Unexpected source schema')
    selected = content_tables((args.source/'common/database_schema.h').read_text())
    if set(selected)-set(available):
        raise ValueError('Content tables missing: '+str(set(selected)-set(available)))
    dump = ['docker','exec',MYSQL,'mariadb-dump','-ueqemu','-peqemu','--skip-triggers','--skip-add-locks','--skip-disable-keys']
    schema = command(dump+['--no-data','peq',*available])
    data = command(dump+['--single-transaction','--quick','--no-create-info','peq',*selected])
    # Only an explicitly selected ruleset variable is copied, not server/account secrets.
    variables = command(dump+['--single-transaction','--no-create-info',"--where=varname IN ('RuleSet','ServerType')",'peq','variables'])
    password = secrets.token_hex(32)
    root_sql(f"CREATE DATABASE {DB}; CREATE USER '{USER}'@'%' IDENTIFIED BY '{password}'; GRANT ALL ON {DB}.* TO '{USER}'@'%';")
    root_sql_bytes = b'USE '+DB.encode()+b';\n'+schema+b'\n'+data+b'\n'+variables
    command(['docker','exec','-i',MYSQL,'sh','-c',
             'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot'],data=root_sql_bytes)
    rows = ','.join(f"({b['test_character_id']},{b['classes'][1]},{b['classes'][2]})" for b in inputs['builds'])
    root_sql(f'INSERT INTO {DB}.character_multiclass (character_id,class2,class3) VALUES {rows};')
    check = root_sql(f'SELECT COUNT(*) FROM {DB}.account; SELECT COUNT(*) FROM {DB}.character_data;').decode().splitlines()
    if check != ['0','0']:
        raise ValueError('Clone unexpectedly contains player/account rows')
    config = {'server':{'auto_database_updates':'false',
              'world':{'shortname':'nightcap_balance','longname':'Isolated balance diagnostic',
                       'tcp':{'ip':'127.0.0.1','port':'1'}},
              'database':{'host':'mariadb','port':'3306','db':DB,'username':USER,'password':password},
              'directories':{'quests':'quests','plugins':'plugins','lua_modules':'lua_modules',
                             'logs':'logs','maps':'maps','shared_memory':'shared/',
                             'patches':'/home/eqemu/server','opcodes':'/home/eqemu/server'}}}
    setup = """import json,os,sys
from pathlib import Path
root=Path('/tmp/nightcap-balance-20260912')
root.mkdir(exist_ok=True)
for name in ('quests','plugins','lua_modules','logs','maps','shared'):
    (root/name).mkdir(exist_ok=True)
payload=json.load(sys.stdin)
for name,value in payload.items():
    path=root/name
    path.write_text(json.dumps(value,indent=2)+'\\n')
    os.chmod(path,0o600)
"""
    command(['docker','exec','-i',SERVER,'python3','-c',setup],data=json.dumps({'eqemu_config.json':config,'inputs.json':inputs}).encode())
    report = {'captured_at':datetime.now(timezone.utc).isoformat(), 'database':DB, 'runtime':RUNTIME,
              'schema_tables':len(available),'content_tables':selected,'player_rows':0,'account_rows':0,
              'schema_sha256':hashlib.sha256(schema).hexdigest(),'data_sha256':hashlib.sha256(data).hexdigest(),
              'variables_sha256':hashlib.sha256(variables).hexdigest(),
              'creation_snapshot_sha256':snapshot_manifest['snapshot_sha256'],
              'input_canonical_json_sha256':hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),
              'status':'Isolated content clone prepared; native execution and shared-memory generation pending'}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('database','schema_tables','player_rows','account_rows','status')}))


if __name__ == '__main__':
    main()

"""SQL integration checks restricted to a labeled, network-isolated disposable DB.

python test_database.py --container <new-test-container> --schema <login_schema.sql>
Never points at a live DB and never removes the container/volume itself.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import uuid
import accounts

def main(container,schema):
    info=json.loads(subprocess.check_output(['docker','inspect',container],text=True))[0]
    if info['Config']['Labels'].get('nightcap.purpose')!='production-provisioning-test' or info['HostConfig']['NetworkMode']!='none' or info['HostConfig']['Binds']:
        raise RuntimeError('Refusing a database that is not an isolated test container')
    # MariaDB images declare an anonymous /var/lib/mysql volume. No host binds or
    # additional/named data volumes are accepted by this fixture runner.
    for mount in info['Mounts']:
        if mount['Type']!='volume' or mount['Destination']!='/var/lib/mysql' or not re.fullmatch('[0-9a-f]{64}',mount['Name']):
            raise RuntimeError('Unexpected test database volume')
    def sql(text,ok=True):
        p=subprocess.run(['docker','exec','-i',container,'mariadb','-uroot','-N','-B'],input=text,text=True,capture_output=True)
        if ok and p.returncode:raise RuntimeError(p.stderr)
        return p
    database='nightcap_fixture_'+uuid.uuid4().hex[:8]
    sql(f'CREATE DATABASE {database};')
    sql(f'USE {database};\n'+schema.read_text(encoding='utf-8'))
    def run(action,user,hashed,ok=True):return sql(f'USE {database};\n'+accounts.sql_for(action,user,hashed),ok)
    assert run('create','fixture_friend','$7$fixture').stdout.strip()=='1'
    assert run('create','fixture_friend','$7$duplicate',False).returncode!=0
    assert run('reset','fixture_friend','$7$reset').stdout.strip()=='1'
    assert run('reset','missing_friend','$7$reset').stdout.strip()=='0'
    assert run('world','nightcap-world','$7$world').stdout.strip()=='1'
    assert run('world','nightcap-world','$7$other').stdout.strip()=='0'
    counts=sql(f'USE {database}; SELECT (SELECT COUNT(*) FROM login_accounts),(SELECT COUNT(*) FROM login_server_admins),(SELECT COUNT(*) FROM login_world_servers);').stdout.strip()
    assert counts=='1\t1\t1',counts
    print('SQL integration passed: create/duplicate/reset/missing reset/world/repeated world; row counts 1/1/1.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--container',required=True);parser.add_argument('--schema',required=True,type=Path)
    args=parser.parse_args();main(args.container,args.schema)

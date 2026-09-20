"""Generate private runtime configuration on the Linux host; never prints secrets."""
import argparse
import json
import os
from pathlib import Path
import secrets
import sys

def private_file(path, value):
    with path.open('x', encoding='utf-8') as f:
        os.chmod(path, 0o600)
        f.write(value)
        f.flush()
        os.fsync(f.fileno())

def configure(base, destination):
    if os.name != 'posix':
        raise RuntimeError('Run on Linux so owner-only secret permissions are enforced')
    original = json.loads(base.read_text(encoding='utf-8'))
    destination.mkdir(mode=0o700)  # exclusive; never regenerate over existing secrets
    password, root_password = secrets.token_hex(24), secrets.token_hex(24)
    # Native registered-world password field is less than 30 characters.
    world_password = secrets.token_hex(14)
    server = original['server']
    server['auto_database_updates'] = 'false'
    database = {'host':'db','port':'3306','username':'nightcap','password':password,'db':'peq'}
    server['database'] = database
    server['content_database'] = dict(database)
    if 'qsdatabase' in server:
        server['qsdatabase'] = dict(database)
    world = server['world']
    for key in list(world):
        if key.startswith('loginserver'):
            del world[key]
    world.update(address='127.77.0.1',localaddress='127.77.0.1',shortname='Nightcap',longname='Nightcap')
    world['loginserver'] = {'host':'127.0.0.1','port':'5998','legacy':'0','account':'nightcap-world','password':world_password}
    world['tcp'] = {'ip':'127.0.0.1','port':'9001'}
    world['telnet'] = {'ip':'127.0.0.1','port':'9002','enabled':'false'}
    world['http'] = {'enabled':'false','port':'9080'}
    world['key'] = secrets.token_hex(24)
    server['ucs'] = {'host':'127.77.0.1','port':'7778'}
    server.pop('chatserver',None)
    server.pop('mailserver',None)
    server.setdefault('zones',{})['ports'] = {'low':'7000','high':'7030'}
    server['zones']['defaultstatus'] = '0'
    login = {
        'database': {'host':'db','port':3306,'user':'nightcap','password':password,'db':'peq'},
        'general': {'listen_port':5998,'default_loginserver_name':'local'},
        'client_configuration': {'titanium_port':5998},
        'security': {'mode':14,'allow_token_login':False},
        'account': {'auto_create_accounts':False},
        'worldservers': {'unregistered_allowed':False,'reject_duplicate_servers':True},
        'web_api': {'enabled':False},
    }
    for name,value in [('db_password',password),('db_root_password',root_password),
                       ('eqemu_config.json',json.dumps(original,indent=2)),
                       ('login.json',json.dumps(login,indent=2)),
                       ('db_backup.cnf',f'[client]\nuser=root\npassword={root_password}\n')]:
        private_file(destination/name,value+'\n')
    print('Private configuration created. Keep this directory out of release uploads and source control.')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--base',required=True,type=Path,help='private copy of the accepted server configuration')
    parser.add_argument('--output',default='private',type=Path)
    args=parser.parse_args()
    configure(args.base,args.output)

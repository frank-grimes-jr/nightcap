"""Local owner-only provisioning. Passwords enter through the terminal, never argv."""
import argparse
import ctypes
import ctypes.util
import getpass
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

def password_hash(password):
    raw=password.encode('ascii')
    if not 12 <= len(raw) <= 28 or any(c < 33 or c > 126 for c in raw):
        raise ValueError('Use 12–28 printable ASCII characters without spaces for this legacy client')
    sodium=ctypes.CDLL(ctypes.util.find_library('sodium'))
    if sodium.sodium_init()<0:
        raise RuntimeError('sodium initialization failed')
    make=sodium.crypto_pwhash_scryptsalsa208sha256_str
    make.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_ulonglong,ctypes.c_ulonglong,ctypes.c_size_t]
    verify=sodium.crypto_pwhash_scryptsalsa208sha256_str_verify
    verify.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_ulonglong]
    output=ctypes.create_string_buffer(102)
    if make(output,raw,len(raw),524288,16777216)!=0 or not output.value.startswith(b'$7$'):
        raise RuntimeError('password hashing failed')
    if verify(output.value,raw,len(raw))!=0 or verify(output.value,b'wrong',5)==0:
        raise RuntimeError('password hash self-test failed')
    return output.value.decode('ascii')

def bind(name,value):
    # Data-only hex values bind server-side prepared statements; names are fixed.
    return f"SET @{name}=CONVERT(X'{value.encode('utf-8').hex()}' USING utf8mb4);\n"

def sql_for(action,username,hashed):
    if not re.fullmatch(r'[A-Za-z0-9_-]{3,24}',username):
        raise ValueError('Username must be 3–24 letters, digits, underscores or hyphens')
    prefix=bind('name',username)+bind('hash',hashed)
    if action=='create':
        statement="INSERT INTO login_accounts (id,account_name,account_password,account_email,source_loginserver,last_ip_address,last_login_date,created_at) VALUES (@new_id,?,?,CHAR(0x2d),CHAR(108,111,99,97,108),CHAR(48),NOW(),NOW())"
        return prefix+"LOCK TABLES login_accounts WRITE;\nSELECT COALESCE(MAX(id),0)+1 INTO @new_id FROM login_accounts;\n"+f'PREPARE p FROM "{statement}"; EXECUTE p USING @name,@hash; SELECT ROW_COUNT(); UNLOCK TABLES;\n'
    if action=='reset':
        statement="UPDATE login_accounts SET account_password=? WHERE account_name=? AND source_loginserver=CHAR(108,111,99,97,108)"
        return prefix+f'PREPARE p FROM "{statement}"; EXECUTE p USING @hash,@name; SELECT ROW_COUNT();\n'
    if action=='world':
        # Provision on an isolated restored DB. Existing registered worlds are not replaced.
        return prefix+"""SET autocommit=0;
LOCK TABLES login_server_admins WRITE, login_world_servers WRITE;
SELECT COUNT(*) INTO @admin_exists FROM login_server_admins WHERE account_name=@name;
SELECT COUNT(*) INTO @world_exists FROM login_world_servers WHERE short_name=CHAR(78,105,103,104,116,99,97,112);
PREPARE p FROM 'INSERT INTO login_server_admins (account_name,account_password,first_name,last_name,email,registration_date,registration_ip_address) SELECT ?, ?, CHAR(45),CHAR(45),CHAR(45),NOW(),CHAR(48) FROM DUAL WHERE @admin_exists=0 AND @world_exists=0';
EXECUTE p USING @name,@hash;
SET @created=ROW_COUNT();
SET @admin_id=LAST_INSERT_ID();
INSERT INTO login_world_servers (long_name,short_name,tag_description,login_server_list_type_id,login_server_admin_id,is_server_trusted,note) SELECT 'Nightcap','Nightcap','Private',3,@admin_id,0,'Owner provisioned' FROM DUAL WHERE @created=1;
SELECT ROW_COUNT(); COMMIT; UNLOCK TABLES;
"""
    raise ValueError('unknown operation')

def run_sql(config,sql):
    # A temporary 0600 option file keeps DB credentials off process command lines.
    fd,path=tempfile.mkstemp(prefix='nightcap-db-',suffix='.cnf')
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'w') as file:
            for value in config.values():
                if any(c in str(value) for c in '\r\n"\\'):
                    raise ValueError('unsupported database config character')
            file.write('[client]\n'+''.join(f'{key}="{value}"\n' for key,value in config.items()))
        result=subprocess.run(['mariadb',f'--defaults-extra-file={path}','--batch','--skip-column-names'],input=sql,text=True,capture_output=True)
        if result.returncode:
            raise RuntimeError('Provisioning failed; verify schema and duplicate names. No database details printed.')
        if result.stdout.strip()!='1':
            raise RuntimeError('Expected exactly one account change')
    finally:
        os.unlink(path)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['create','reset','world'])
    parser.add_argument('username',nargs='?')
    args=parser.parse_args()
    cfg=json.loads(Path('eqemu_config.json').read_text())['server']
    subprocess.run(['/opt/nightcap/bin/loginserver','--nightcap-crypto-self-test'],check=True)
    if args.action=='world':
        username=cfg['world']['loginserver']['account']
        password=cfg['world']['loginserver']['password']
    else:
        username=args.username or ''
        password=getpass.getpass('New Nightcap password: ')
        if password!=getpass.getpass('Repeat password: '):
            raise ValueError('Passwords did not match')
    db=cfg['database']
    options={'host':db['host'],'port':db['port'],'user':db['username'],'password':db['password'],'database':db['db']}
    run_sql(options,sql_for(args.action,username,password_hash(password)))
    print('Private account provisioned.')

if __name__=='__main__':
    main()

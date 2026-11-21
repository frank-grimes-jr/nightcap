"""Install the checked Cairnwright candidate on the Nightcap QA world."""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path('/opt/nightcap/deploy/production')
STAGE = Path(__file__).resolve().parent
SERVER = ROOT / 'data/server'
BASE = 'sha256:50bcce347049a928a923e9e7598434c19b671699346e9546eba2e080d4e13238'
TAG = 'nightcap-game:cairnwright-testing-20261121'
SCRIPTS = {
    'plugins/multiclass.pl': 'e3c30f45db984578c0fe6c8179b5a836580927ed8b4dfecaacc33b4aa7c76596',
    'quests/ecommons/The_Ancient_Chronicler.pl': '37603797fd378afc680cfab1d63ee5014681ce25ad63cc8a4f89750df2d1c5be',
    'quests/poknowledge/The_Ancient_Chronicler.pl': '777d57939ab1a813f502e1b389c7665f9da2febdb51a049a22bcd0e25a11413e',
    'plugins/cairnwright.pl': None,
    'quests/global/spells/44381.pl': None,
    'quests/global/spells/44382.pl': None,
}
BINS = {
    'world':'a641bef73c39fcc37192685bb077f1f5e9acf77dd4d79e7998ae899912eff521',
    'zone':'771122fc9f8b208eb9338f82df3c614288582a8ae9f5bd19ed7ed4c1b5665989',
}
COUNTS = """SELECT
 (SELECT COUNT(*) FROM spells_new WHERE id IN (44381,44382,44383)),
 (SELECT COUNT(*) FROM items WHERE id IN (998616,998636)),
 (SELECT COUNT(*) FROM base_data WHERE class=17),
 (SELECT COUNT(*) FROM char_create_combinations WHERE class=17),
 (SELECT COUNT(*) FROM start_zones WHERE player_class=17);"""

def run(*args, data=None, timeout=300):
    return subprocess.check_output(args, input=data, cwd=ROOT, timeout=timeout).decode().strip()

def compose(*args, **kwargs):
    return run('docker','compose',*args,**kwargs)

def sql(statement):
    return compose('exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config',
                   '--batch','--skip-column-names','peq',data=statement.encode())

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def put(path, data, mode):
    import tempfile
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    if path.exists():
        st=path.stat()
        os.chown(tmp,st.st_uid,st.st_gid)
    os.chmod(tmp, mode)
    os.replace(tmp,path)

def inspect(service, fmt):
    return run('docker','inspect','--format',fmt,compose('ps','-aq',service))

def players():
    value=json.loads(compose('exec','-T','game','python3','-',data=(STAGE/'world_count.py').read_bytes()))
    assert type(value) is int and value>=0
    return value

def baseline():
    assert inspect('game','{{.Image}}')==BASE
    assert inspect('gateway','{{.State.Running}}')=='true'
    assert sql(COUNTS).split()==['0']*5
    for name, expected in SCRIPTS.items():
        path=SERVER/name
        assert not path.is_symlink()
        if expected:
            assert hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==expected,name
        else:
            assert not path.exists(),name

def prepare():
    baseline()
    assert sql((STAGE/'rehearsal.sql').read_text()).split()==['3','2','50','1']
    for name, expected in BINS.items():
        assert sha(STAGE/'bin'/name)==expected
    base_tag=TAG+'-base'
    run('docker','tag',BASE,base_tag)
    (STAGE/'Dockerfile').write_text('FROM '+base_tag+'\nCOPY --chmod=0755 bin/ /opt/nightcap/bin/\n')
    (STAGE/'.dockerignore').write_text('*\n!bin\n!bin/world\n!bin/zone\n!Dockerfile\n')
    run('docker','build','--network','none','--pull=false','-t',TAG,str(STAGE))
    image=run('docker','image','inspect','--format','{{.Id}}',TAG)
    for name, expected in BINS.items():
        assert run('docker','run','--rm','--network','none','--entrypoint','sha256sum',image,'/opt/nightcap/bin/'+name).split()[0]==expected
        assert 'not found' not in run('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/'+name)
    run('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c',
        'import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
    receipt={'image':image,'source':'cf536ec5','world':BINS['world'],'zone':BINS['zone'],'counts':[3,2,50,1]}
    put(STAGE/'preflight.json',json.dumps(receipt).encode(),0o600)
    print(json.dumps(receipt),flush=True)

def check_runtime(image):
    assert inspect('game','{{.Image}}')==image
    assert inspect('game','{{.State.Health.Status}}')=='healthy'
    assert inspect('game','{{.RestartCount}}')=='0'
    process_check='''from pathlib import Path
import collections,json
rows=collections.Counter()
for p in Path('/proc').glob('[0-9]*/exe'):
 try: rows[p.readlink().as_posix()]+=1
 except OSError: pass
print(json.dumps({n:rows['/opt/nightcap/bin/'+n] for n in ['world','zone','ucs','loginserver']}))'''
    counts=json.loads(compose('exec','-T','game','python3','-c',process_check))
    assert counts=={'world':1,'zone':12,'ucs':1,'loginserver':1},counts
    assert sql(COUNTS).split()==['3','2','50','1','1']
    for name in SCRIPTS:
        assert sha(SERVER/name)==sha(STAGE/'scripts'/name)
    for name,pin in BINS.items():
        assert compose('exec','-T','game','sha256sum','/opt/nightcap/bin/'+name).split()[0]==pin
    return counts

def backup():
    dest=STAGE/'before-peq.sql.gz'
    with dest.open('xb') as out:
        dump=subprocess.Popen(['docker','compose','exec','-T','db','mariadb-dump',
            '--defaults-extra-file=/run/secrets/db_backup_config','--single-transaction','--quick',
            '--routines','--events','--triggers','--hex-blob','peq'],cwd=ROOT,stdout=subprocess.PIPE)
        with gzip.GzipFile(fileobj=out,mode='wb',compresslevel=2) as compressed:
            shutil.copyfileobj(dump.stdout,compressed)
        assert dump.wait()==0
        out.flush()
        os.fsync(out.fileno())
    run('gzip','-t',str(dest))
    return sha(dest)

def activate():
    pre=json.loads((STAGE/'preflight.json').read_bytes())
    image=pre['image']
    assert run('docker','image','inspect','--format','{{.Id}}',TAG)==image
    baseline()
    assert players()==0,'Players online'
    assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')")=='1'
    assert not (ROOT/'private/gm-maintenance.json').exists()
    assert shutil.disk_usage(ROOT).free>2*1024**3
    envfile=ROOT/'.env'
    original_env=envfile.read_bytes()
    pattern=rb'(?m)^NIGHTCAP_GAME_IMAGE=[^\r\n]+'
    new_env,n=re.subn(pattern,b'NIGHTCAP_GAME_IMAGE='+TAG.encode(),original_env)
    assert n==1
    for name in SCRIPTS:
        src=SERVER/name
        if src.is_file():
            dst=STAGE/'before'/name
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
    (STAGE/'activation-started').touch(exist_ok=False)
    attempted_stop=changed=opening=False
    try:
        compose('stop','gateway')
        time.sleep(125)
        assert players()==0
        attempted_stop=True
        compose('stop','-t','90','game')
        assert inspect('game','{{.State.ExitCode}} {{.State.OOMKilled}}')=='0 false'
        pin=backup()
        sql((STAGE/'content.sql').read_text())
        changed=True
        for name in SCRIPTS:
            p=SERVER/name
            p.parent.mkdir(parents=True,exist_ok=True)
            put(p,(STAGE/'scripts'/name).read_bytes(),0o644)
        assert envfile.read_bytes()==original_env
        put(envfile,new_env,envfile.stat().st_mode & 0o777)
        compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        counts=check_runtime(image)
        opening=True
        compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        assert inspect('gateway','{{.State.Running}}')=='true'
        result=dict(image=image,workers=counts['zone'],backup_sha256=pin,gateway_open=True,client_qa='pending')
        put(STAGE/'deployed.json',json.dumps(result).encode(),0o600)
        print(json.dumps(result),flush=True)
    except BaseException:
        if opening:
            raise
        # No public admission since the preflight count. Only undo the new rows and files.
        if attempted_stop:
            compose('stop','-t','90','game')
        if changed:
            assert sql('SELECT COUNT(*) FROM character_data WHERE class=17')=='0'
            sql('START TRANSACTION; DELETE FROM char_create_combinations WHERE class=17; '
                'DELETE FROM start_zones WHERE player_class=17; DELETE FROM base_data WHERE class=17 AND level BETWEEN 1 AND 50; '
                'DELETE FROM items WHERE id IN (998616,998636); DELETE FROM spells_new WHERE id BETWEEN 44381 AND 44383; COMMIT;')
            for name,old in SCRIPTS.items():
                if old:
                    put(SERVER/name,(STAGE/'before'/name).read_bytes(),0o644)
                elif (SERVER/name).exists():
                    assert sha(SERVER/name)==sha(STAGE/'scripts'/name)
                    (SERVER/name).unlink()
            if envfile.read_bytes()==new_env:
                put(envfile,original_env,envfile.stat().st_mode & 0o777)
        if attempted_stop:
            compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        raise

if __name__=='__main__':
    os.umask(0o077)
    args=argparse.ArgumentParser()
    args.add_argument('action',choices=['prepare','activate','verify'])
    action=args.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock','a') as gm:
        for handle in (lock,gm):
            fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if action=='verify':
            result=json.loads((STAGE/'deployed.json').read_bytes())
            check_runtime(result['image'])
            assert inspect('gateway','{{.State.Running}}')=='true'
            print(json.dumps(result))
        elif action=='prepare': prepare()
        else: activate()

"""Prepare, activate, verify or reverse a pinned Classic QA package on the Docker host."""
import argparse
import base64
import contextlib
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

STAGE = Path(__file__).resolve().parent
LOCAL = os.name == 'nt'
ROOT = Path('E:/EQ_Local_Dev/akk-stack') if LOCAL else Path('/opt/nightcap/deploy/production')
SERVICE = 'eqemu-server' if LOCAL else 'game'
DB = 'mariadb' if LOCAL else 'db'
OPTIONS = '/run/local-secrets/client.cnf' if LOCAL else '/run/secrets/db_backup_config'
TAG = ('nightcap-local' if LOCAL else 'nightcap-game') + ':classic-qa-20261127'
PTR = ROOT/('docker-compose.localdev-parity.yml' if LOCAL else '.env')
NAMES = {'quests/fearplane/Cazic_Thule.lua','quests/global/global_player.lua'}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def run(*args, data=None):
    return subprocess.check_output([str(a) for a in args], input=data, cwd=ROOT, timeout=900)


def compose(*args, data=None):
    return run('docker','compose',*args,data=data)


def db(query):
    return compose('exec','-T',DB,'mariadb','--defaults-extra-file='+OPTIONS,'--batch','-N','peq',
                   data=query if isinstance(query,bytes) else query.encode()).decode().strip()


def state(service):
    cid=compose('ps','-aq',service).decode().strip()
    if not cid or '\n' in cid:
        raise RuntimeError(f'Expected one container for {service}')
    return json.loads(run('docker','inspect',cid))[0]


def world(method):
    code=(STAGE/'world_count.py').read_bytes()
    assert code.count(b"method = 'EQW::GetPlayerCount'")==1
    assert method in ('GetPlayerCount','IsLocked','Lock','Unlock')
    code=code.replace(b"method = 'EQW::GetPlayerCount'",f"method = 'EQW::{method}'".encode())
    return json.loads(compose('exec','-T',SERVICE,'python3','-',data=code))


def evidence(name, value):
    path=STAGE/name
    with path.open('x') as out:
        json.dump(value,out,indent=2)
        out.write('\n')


def atomic_pointer(oldref,newref):
    original=PTR.read_bytes()
    prefix=b'    image: ' if LOCAL else b'NIGHTCAP_GAME_IMAGE='
    pattern=rb'(?m)^'+re.escape(prefix+oldref.encode())+rb'(?=\r?$)'
    updated, count=re.subn(pattern,prefix+newref.encode(),original)
    if count!=1:
        raise RuntimeError('Unexpected configured image selector')
    st=PTR.stat()
    with tempfile.NamedTemporaryFile(dir=PTR.parent,delete=False) as tmp:
        tmp.write(updated)
        tmp.flush()
        os.fsync(tmp.fileno())
        if not LOCAL:
            os.fchown(tmp.fileno(),st.st_uid,st.st_gid)
            os.fchmod(tmp.fileno(),st.st_mode & 0o777)
    try:
        if PTR.read_bytes()!=original:
            raise RuntimeError('Concurrent image-selector change')
        os.replace(tmp.name,PTR)
    finally:
        Path(tmp.name).unlink(missing_ok=True)


def load():
    data=json.loads((STAGE/'manifest.json').read_bytes())
    assert set(data['before'])==set(data['after'])==NAMES
    for name,pin in data['operator'].items():
        assert Path(name).name==name and digest(STAGE/name)==pin
    for side in ('before','after'):
        for name,pin in data[side].items():
            assert digest(STAGE/side/name)==pin
    assert digest(STAGE/'zone')==data['zone']
    assert re.fullmatch('[0-9a-f]{40}',data['source'])
    return data


def check(m,candidate):
    expected=dict(m['binaries'])
    if candidate:
        expected['zone']=m['zone']
    current=state(SERVICE)
    wanted=json.loads((STAGE/'prepared.json').read_bytes())['image'] if candidate else m['base_image']
    assert current['Image']==wanted and current['State']['Health']['Status']=='healthy'
    assert not current['State']['OOMKilled']
    if candidate:
        assert current['RestartCount']==0
    snapshot=json.loads(compose('exec','-T',SERVICE,'python3','-',data=(STAGE/'probe.py').read_bytes()))
    quests={name:hashlib.sha256(base64.b64decode(val)).hexdigest() for name,val in snapshot.pop('quests').items()}
    assert quests==m['after' if candidate else 'before']
    assert snapshot['binaries']==expected and snapshot['cache']==m['cache']
    assert db(content_check(not candidate))=='1\t1'
    return dict(image=wanted,quests=quests,players=world('GetPlayerCount'),source=m['source'],**snapshot)


def backup():
    root = STAGE if LOCAL else Path('/mnt/archive/classic-qa-20261127')
    root.mkdir(mode=0o700,exist_ok=True)
    path=root/(time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-peq.sql.gz')
    with path.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',compresslevel=2) as gz:
            cmd=['docker','compose','exec','-T',DB,'mariadb-dump','--defaults-extra-file='+OPTIONS,
                 '--single-transaction','--quick','--routines','--events','--triggers','--hex-blob','peq']
            with subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE) as proc:
                shutil.copyfileobj(proc.stdout,gz,1024*1024)
                if proc.wait()!=0:
                    raise RuntimeError('Database dump failed')
    with gzip.open(path,'rb') as gz:
        found=False
        for line in gz:
            found |= b'CREATE TABLE `character_data`' in line
    assert found
    return {'path':str(path),'sha256':digest(path)}


def install(m,forward):
    game=state(SERVICE)
    assert not game['State']['Running']
    side='after' if forward else 'before'
    other='before' if forward else 'after'
    data={name:{'from':m[other][name],'want':m[side][name],
                'data':base64.b64encode((STAGE/side/name).read_bytes()).decode()} for name in NAMES}
    volume=next(x for x in game['Mounts'] if x['Destination']=='/srv/nightcap')
    mount=('type=volume,src='+volume['Name'] if volume['Type']=='volume' else 'type=bind,src='+volume['Source'])
    run('docker','run','--rm','-i','--network','none','--user','0:0','--mount',mount+',dst=/srv/nightcap',
        '--entrypoint','python3',m['base_image'],'-c',(STAGE/'install_quests.py').read_text(),
        data=json.dumps(data).encode())


def prepare(m):
    check(m,False)
    rehearse_content()
    backup_volume=STAGE if LOCAL else Path('/mnt/archive')
    needed=int(db("SELECT COALESCE(SUM(data_length),0) FROM information_schema.tables WHERE table_schema='peq'"))
    assert shutil.disk_usage(backup_volume).free>needed+512*1024**2, 'Free backup volume space is too low'
    assert run('docker','image','inspect','--format','{{.Id}}',m['base_tag']).decode().strip()==m['base_image']
    context=STAGE/'image'
    context.mkdir(exist_ok=True)
    base_tag=TAG+'-base-'+m['base_image'][7:19]
    run('docker','tag',m['base_image'],base_tag)
    (context/'Dockerfile').write_text(f"FROM {base_tag}\nCOPY --chmod=0755 zone /opt/nightcap/bin/zone\n")
    if not (context/'zone').exists():
        shutil.copy2(STAGE/'zone',context/'zone')
    assert digest(context/'zone')==m['zone']
    run('docker','build','--network','none','--pull=false','-t',TAG,str(context))
    image=run('docker','image','inspect','--format','{{.Id}}',TAG).decode().strip()
    assert run('docker','run','--rm','--network','none','--entrypoint','sha256sum',image,
               '/opt/nightcap/bin/zone').split()[0].decode()==m['zone']
    missing=run('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/zone')
    assert b'not found' not in missing
    for name in NAMES:
        run('docker','run','--rm','-i','--network','none','--entrypoint','luac',image,'-p','-',
            data=(STAGE/'after'/name).read_bytes())
    receipt={'manifest':digest(STAGE/'manifest.json'),'image':image}
    if (STAGE/'prepared.json').exists():
        assert json.loads((STAGE/'prepared.json').read_bytes())==receipt
    else:
        evidence('prepared.json',receipt)


def stop_game():
    compose('stop','-t','100',SERVICE)
    current=state(SERVICE)['State']
    assert not current['Running'] and current['ExitCode']==0 and not current['OOMKilled']


def start_game():
    compose('up','-d','--no-deps','--wait','--wait-timeout','300',SERVICE)


def content(forward, shadow=False):
    phase='forward' if forward else 'rollback'
    updates=[]
    for area,table in [('recall','aa_ability'),('cazic','npc_types')]:
        sql=(STAGE/f'{area}-{phase}.sql').read_text()
        sql='\n'.join(line for line in sql.splitlines() if not line.lstrip().startswith('--')).strip()
        match=re.fullmatch(r'UPDATE\s+'+table+r'\s+SET\s+([^;]+?)\s+WHERE\s+([^;]+);',sql,re.I|re.S)
        if not match:
            raise ValueError(f'Expected one guarded UPDATE of {table}')
        dest='preview_'+table if shadow else table
        changes,guard=match.groups()
        updates.append((f'UPDATE {dest} SET {changes} WHERE {guard};',f'(SELECT COUNT(*) FROM {dest} WHERE {guard})'))
    return updates


def content_check(forward,shadow=False):
    return 'SELECT '+', '.join(query for _,query in content(forward,shadow))+';'


def transaction(forward,shadow=False):
    commands=['DELIMITER //','BEGIN NOT ATOMIC',
              'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
              'START TRANSACTION;']
    for update,_ in content(forward,shadow):
        commands.extend([update,"IF ROW_COUNT() <> 1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Release row changed concurrently'; END IF;"])
    return '\n'.join([*commands,'COMMIT;','END//','DELIMITER ;',''])


def rehearse_content():
    setup=''
    for table,ids in [('aa_ability','420,2220'),('npc_types','72003,76007')]:
        setup+=f'CREATE TEMPORARY TABLE preview_{table} LIKE {table};\n'
        setup+=f'INSERT INTO preview_{table} SELECT * FROM {table} WHERE id IN ({ids});\n'
    sql=setup+content_check(True,True)+'\n'+transaction(True,True)+content_check(False,True)+'\n'
    sql+=transaction(False,True)+content_check(True,True)+'\n'
    # Reject the second write after the first matched; prove the first rolled back.
    sql+='UPDATE preview_npc_types SET hp=hp+1 WHERE id=72003;\nSET @rejected=0;\n'
    nested=transaction(True,True).removeprefix('DELIMITER //\n').removesuffix('END//\nDELIMITER ;\n')
    sql+=("DELIMITER //\nBEGIN NOT ATOMIC\n"
          "DECLARE CONTINUE HANDLER FOR SQLSTATE '45000' SET @rejected=1;\n"
          +nested+"END;\nEND//\nDELIMITER ;\nSELECT @rejected;\n"+content_check(True,True))
    assert db(sql).splitlines()==['1\t1','1\t1','1\t1','1','1\t0']


def switch_db(m,forward):
    if db(content_check(not forward))=='1\t1':
        return
    assert db(content_check(forward))=='1\t1', 'Unexpected content before switch'
    db(transaction(forward))
    assert db(content_check(not forward))=='1\t1'


def reopen():
    if LOCAL:
        if world('IsLocked'):
            assert world('Unlock')['status']=='complete'
    else:
        compose('up','-d','--no-deps','--wait','--wait-timeout','90','gateway')
        assert state('gateway')['State']['Running']


def activate(m,forward):
    prepared=json.loads((STAGE/'prepared.json').read_bytes())
    assert prepared['manifest']==digest(STAGE/'manifest.json')
    assert run('docker','image','inspect','--format','{{.Id}}',TAG).decode().strip()==prepared['image']
    selector=TAG if LOCAL else prepared['image']
    old,new=(m['base_tag'],selector) if forward else (selector,m['base_tag'])
    assert check(m,not forward)['players']==0, 'Players online; release deferred'
    assert db("SELECT IS_FREE_LOCK('nightcap_gm_writes')")=='1'
    assert LOCAL or not (ROOT/'private/gm-maintenance.json').exists()
    phase='activation' if forward else 'rollback'
    if (STAGE/(phase+'-started.json')).exists():
        raise RuntimeError('Existing operation receipt; reconcile before retry')
    assert not world('IsLocked') and (LOCAL or state('gateway')['State']['Running'])
    evidence(phase+'-started.json',{'source':m['source']})
    stopped=False
    pointer_changed=False
    opening=False
    try:
        if LOCAL:
            assert world('Lock')['status']=='complete' and world('IsLocked')
        else:
            compose('stop','gateway')
            assert not state('gateway')['State']['Running']
            time.sleep(125)
        assert world('GetPlayerCount')==0
        stop_game()
        stopped=True
        evidence(phase+'-backup.json',backup())
        switch_db(m,forward)
        install(m,forward)
        atomic_pointer(old,new)
        pointer_changed=True
        start_game()
        result=check(m,forward)
        assert result['players']==0
        evidence(phase+'-verified.json',result)
        opening=True
        reopen()
        evidence(phase+'-complete.json',dict(result,admission_open=True,player_qa='open'))
    except BaseException:
        if opening:
            raise
        if stopped:
            if state(SERVICE)['State']['Running']:
                assert world('GetPlayerCount')==0, 'Hold: players entered during recovery'
                stop_game()
            if pointer_changed:
                atomic_pointer(new,old)
            install(m,not forward)
            switch_db(m,not forward)
        start_game()
        check(m,not forward)
        reopen()
        raise


@contextlib.contextmanager
def locks():
    if LOCAL:
        import msvcrt
        with (ROOT/'.classic-qa-release.lock').open('a+b') as handle:
            handle.seek(0)
            msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
            yield
    else:
        import fcntl
        with (ROOT/'.deployment.lock').open('a') as deployment, Path('/var/lock/nightcap-gm.lock').open('a') as gm:
            for handle in (deployment,gm):
                fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            yield


if __name__=='__main__':
    if not __debug__:
        raise RuntimeError('Required integrity checks are disabled')
    os.umask(0o077)
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['prepare','activate','rollback','verify'])
    action=p.parse_args().action
    with locks():
        manifest=load()
        if action=='prepare':
            prepare(manifest)
        elif action=='verify':
            print(json.dumps(check(manifest,True)))
        else:
            activate(manifest,action=='activate')


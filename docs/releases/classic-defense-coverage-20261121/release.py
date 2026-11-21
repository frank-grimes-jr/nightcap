"""Content-only Classic coverage release with paired cache verification."""
import argparse
import hashlib
import importlib.util
import json
import mmap
import os
from pathlib import Path
import re
import secrets
import shutil
import struct
import subprocess
import sys
import time
import uuid

STAGE = Path(__file__).resolve().parent
ROOT = Path('/opt/nightcap/deploy/production')
EVIDENCE = STAGE/'evidence'
from catalog import changes, generate


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def initialize():
    global op,p,r,a,h,base,m,stock,ids
    m = read(STAGE/'manifest.json')
    assert re.fullmatch('[0-9a-f]{40}',m['source'])
    assert set(m['files'])=={'release.py','catalog.py','production.json.gz','policy.json','effects.json'}
    for name, pin in m['files'].items():
        assert (Path(name).name==name or name=='bin/zone') and sha(STAGE/name)==pin
    path=STAGE.parent/'stock-worn-atk-20261113-v1/release.py'
    assert sha(path)==m['stock_operator']
    spec=importlib.util.spec_from_file_location('stock_release',path)
    op=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(op)
    op.initialize()
    p,r,a,h,base=op.p,op.r,op.a,op.h,op.base
    allowed={m['image']}
    if (EVIDENCE/'preflight.json').exists():allowed.add(read(EVIDENCE/'preflight.json')['candidate_image'])
    assert r.compact('game')['image_id'] in allowed
    receipt=STAGE.parent/'titles-live-20261114-v1/evidence/activation/deployed.json'
    assert sha(receipt)==m['titles_receipt']
    stock=changes()
    ids=','.join(map(str,sorted(stock)))


def candidate_image():
    assert r.image_hashes(m['image'])==m['base_hashes']
    return m['image']


def candidate_runtime(before):
    return r.running(before['candidate_image'],m['binaries'])


def sql(statement, db='peq'):
    return op.op.sql(statement,db)


def before_rows(db):
    sql(generate('before'),db)


def outside():
    return a.prior.digest('items','id NOT IN ('+ids+')')


def cache_check(old,new):
    layout=m['layout']
    size,ident=layout['size'],layout['ID']
    def info(buf):
        payload,slots,capacity,used=struct.unpack_from('<IIII',buf)
        assert len(buf)==payload+8==20+slots*4+size*capacity
        return slots,used
    def row(buf,slots,used,i):
        if i>=slots:return None
        idx=struct.unpack_from('<I',buf,16+i*4)[0]
        if idx>=used:return None
        pos=16+slots*4+size*idx
        assert struct.unpack_from('<I',buf,pos+ident)[0]==i
        return buf[pos:pos+size]
    with old.open('rb') as f,new.open('rb') as g,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as x,mmap.mmap(g.fileno(),0,access=mmap.ACCESS_READ) as y:
        xs,xc=info(x)
        ys,yc=info(y)
        assert yc==xc and xs==ys
        seen=set()
        for i in range(xs):
            left,right=row(x,xs,xc,i),row(y,ys,yc,i)
            if i in stock:
                _,prior_values,target_values=stock[i]
                expected=bytearray(left)
                for field,k in [('Worn',0),('Focus',4)]:
                    offset=layout[field]
                    if target_values[k]!=prior_values[k]:
                        assert struct.unpack_from('<iB',left,offset)==(prior_values[k],prior_values[k+1])
                        struct.pack_into('<iB',expected,offset,target_values[k],target_values[k+1])
                assert right==expected,i
                seen.add(i)
            else:assert left==right,i
        assert seen==set(stock)
        return dict(records=xc,changed=len(seen),unchanged=xc-len(seen),items_sha256=sha(new))



def rehearsal():
    db='nightcap_dungeon_stage_'+uuid.uuid4().hex[:12]
    user='aug_'+uuid.uuid4().hex[:12]
    work=STAGE/('rehearsal-'+db[-12:])
    work.mkdir(mode=0o700)
    (work/'shared').mkdir()
    (work/'logs').mkdir()
    cfg=work/'eqemu_config.json'
    tables=('items','rule_sets','rule_values','variables','logsys_categories','content_flags','zone','instance_list')
    sql('CREATE DATABASE '+db)
    try:
        for t in tables:sql(f'CREATE TABLE {db}.{t} LIKE peq.{t}')
        sql('START TRANSACTION WITH CONSISTENT SNAPSHOT;\n'+'\n'.join(f'INSERT INTO {db}.{t} SELECT * FROM peq.{t};' for t in tables if t!='instance_list')+'\nCOMMIT;')
        before_rows(db)
        for action in ('forward','verify','forward','rollback'):
            sql(generate(action),db)
        before_rows(db)
        sql(generate('forward'),db)
        sql(generate('verify'),db)
        password=secrets.token_hex(28)
        sql(f"CREATE USER '{user}'@'%' IDENTIFIED BY '{password}'; GRANT SELECT ON {db}.* TO '{user}'@'%';")
        conf=read(ROOT/'private/eqemu_config.json')
        conn=conf['server']['database']
        conn.update(db=db,username=user,password=password)
        conf['server']['content_database']=dict(conn)
        conf['server'].setdefault('directories',{}).update(shared_memory='/runtime/shared/',logs='/runtime/logs/')
        cfg.write_text(json.dumps(conf))
        cfg.chmod(0o600)
        network,=r.state('db')['NetworkSettings']['Networks']
        cmd=['docker','run','--rm','--network',network,'--user','0','-v',str(work)+':/runtime','--workdir','/runtime','--entrypoint','/opt/nightcap/bin/shared_memory',m['image'],'items']
        with (work/'loader.log').open('x') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
        return cache_check(ROOT/'data/server/shared/items',work/'shared/items')
    finally:
        cfg.unlink(missing_ok=True)
        sql(f"DROP USER IF EXISTS '{user}'@'%'; DROP DATABASE {db};")


def verify_content(before):
    assert outside()==before['outside']
    sql(generate('verify'))
    expected=dict(before['caches'],items=before['rehearsal']['items_sha256'])
    assert h.caches()==expected and h.publication()==before['publication']
    assert a.prior.p.rules()==before['rules']
    assert all(r.compact(k)==m['services'][k] for k in ('db','web','tunnel'))


def check_spells():
    from catalog import literal
    for row in read(STAGE/'effects.json')['spells']:
        where=' AND '.join(('BINARY ' if isinstance(v,str) else '')+'`'+k+'` <=> '+literal(v) for k,v in sorted(row.items()))
        assert sql('SELECT COUNT(*) FROM spells_new WHERE '+where).strip()=='1',row['id']


def preflight():
    before_rows('peq')
    check_spells()
    assert r.compact('game')['image_id']==m['image'] and r.compact('gateway')['running']
    assert not any(r.running(m['image'],m['binaries'])['errors'].values())
    assert shutil.disk_usage(ROOT).free>4*1024**3
    EVIDENCE.mkdir(exist_ok=True)
    state=dict(manifest=sha(STAGE/'manifest.json'),outside=outside(),publication=h.publication(),caches=h.caches(),rules=a.prior.p.rules())
    assert state['caches']==m['caches']
    assert sha(ROOT/'data/public/channel.json')==m['channel']
    p.startup.startup_guards()
    p.contract()
    base.health()
    state['rehearsal']=rehearsal()
    state['candidate_image']=candidate_image()
    before_rows('peq')
    p.save(EVIDENCE/'preflight.json',state)


def activate():
    before=read(EVIDENCE/'preflight.json')
    assert before['manifest']==sha(STAGE/'manifest.json')
    assert h.caches()==before['caches'] and outside()==before['outside']
    before_rows('peq')
    assert r.compact('game')['image_id']==m['image'] and r.compact('gateway')['running']
    check_spells()
    assert h.publication()==before['publication'] and a.prior.p.rules()==before['rules']
    connected_before=a.prior.players()
    assert connected_before==0, 'Players online; activation deferred'
    folder=EVIDENCE/'activation'
    folder.mkdir(mode=0o700)
    sql_started=False
    p.save(folder/'started.json',{'source':m['source']})
    try:
        r.compose('stop','gateway')
        assert not r.compact('gateway')['running']
        p.save(folder/'drain.json',{'connected_before':connected_before})
        deadline=time.monotonic()+300
        time.sleep(125)
        while a.prior.players():
            assert time.monotonic()<deadline,'Native disconnect/save still pending'
            time.sleep(5)
        r.compose('stop','-t','90','game')
        st=r.state('game')['State']
        assert not st['Running'] and st['ExitCode']==0 and not st['OOMKilled']
        saved=a.prior.saved()
        market=p.market.market()
        r.STAGE=base.EVIDENCE=folder
        backup=r.database_backup()
        assert backup['gzip_integrity'] and sha(Path(backup['path']))==backup['sha256']
        p.save(folder/'backup.json',backup)
        expected=base.boot_state(saved)
        assert saved==a.prior.saved()
        before_rows('peq')
        sql_started=True
        sql(generate('forward'))
        sql(generate('verify'))
        assert saved==a.prior.saved()
        r.select(before['candidate_image'])
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        runtime=candidate_runtime(before)
        assert not any(runtime['errors'].values()) and runtime['restart_count']==0
        assert sum(row[0]=='zone' for row in runtime['processes'])==12
        assert a.prior.saved()==expected
        rotation=p.market.verify_market(market,runtime['started_at'])
        base.health()
        verify_content(before)
        r.closed_ports()
        p.save(folder/'verified-closed.json',dict(started_at=runtime['started_at'],market=rotation))
        p.contract()
        p.save(folder/'opening.json',{'source':m['source']})
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        result=verify_open(before)
        p.save(folder/'deployed.json',result)
    except BaseException:
        if not sql_started:
            r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
            r.compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        else:
            h.hold(folder)
        raise


def verify_open(before):
    folder=EVIDENCE/'activation'
    runtime=candidate_runtime(before)
    assert runtime['started_at']==read(folder/'verified-closed.json')['started_at']
    assert r.compact('gateway')['running'] and not any(runtime['errors'].values())
    workers=sum(row[0]=='zone' for row in runtime['processes'])
    assert workers==12 and runtime['restart_count']==0
    assert sha(ROOT/'data/public/channel.json')==m['channel']
    verify_content(before)
    base.health()
    return dict(source=m['source'],gateway_open=True,workers=workers,errors=runtime['errors'],restarts=runtime['restart_count'],image=before['candidate_image'],binaries=m['binaries'],client=m['client'],cache=before['rehearsal'],backup_sha256=read(folder/'backup.json')['sha256'],player_qa='open')


if __name__=='__main__':
    import fcntl
    assert __debug__
    os.umask(0o077)
    initialize()
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        for handle in (lock,gm):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists() and sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
        action=sys.argv[1]
        if action=='verify':print(json.dumps(verify_open(read(EVIDENCE/'preflight.json'))))
        else:{'preflight':preflight,'activate':activate}[action]()

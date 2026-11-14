"""Content-only promotion. Reuse the audited stock-item release controls."""
import argparse
import fcntl
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
from catalog import FAMILIES, generate, scales


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def initialize():
    global op,p,r,a,h,base,m,stock,added,ids
    m = read(STAGE/'manifest.json')
    assert re.fullmatch('[0-9a-f]{40}',m['source'])
    for name, pin in m['files'].items():
        assert Path(name).name==name and sha(STAGE/name)==pin
    path=STAGE.parent/'stock-worn-atk-20261113-v1/release.py'
    assert sha(path)==m['stock_operator']
    spec=importlib.util.spec_from_file_location('stock_release',path)
    op=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(op)
    op.initialize()
    p,r,a,h,base=op.p,op.r,op.a,op.h,op.base
    dep=STAGE.parent/'fixed-aa-duration-20261114-v1/evidence/activation/deployed.json'
    assert sha(dep)==m['prior_receipt'] and read(dep)['image']==m['image']
    stock={row['id']:row for row in read(STAGE/'stock.json')}
    added={row['id']:row for row in scales()}
    ids=','.join(map(str,sorted(set(stock)|set(added))))


def sql(statement, db='peq'):
    return op.op.sql(statement,db)


def before_rows(db):
    rows=sql('SELECT id,healamt,spelldmg,hp,mana FROM items WHERE id IN ('+ids+') ORDER BY id',db)
    actual=[list(map(int,row.split())) for row in rows.splitlines()]
    assert actual==[[i,*stock[i]['before']] for i in sorted(stock)]
    for table,col in [('tradeskill_recipe','id'),('tradeskill_recipe_entries','recipe_id')]:
        assert sql(f'SELECT COUNT(*) FROM {table} WHERE {col} BETWEEN 96920 AND 96922',db).strip()=='0'


def outside():
    return {t:a.prior.digest(t,pred) for t,pred in [('items','id NOT IN ('+ids+')'),
        ('tradeskill_recipe','id NOT BETWEEN 96920 AND 96922'),('tradeskill_recipe_entries','recipe_id NOT BETWEEN 96920 AND 96922')]}


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
        assert yc==xc+len(added)
        for i in range(max(xs,ys)):
            left,right=row(x,xs,xc,i),row(y,ys,yc,i)
            if i in added:
                assert left is None and right is not None
                item=added[i]
                for field,key in [('HP','hp'),('Mana','mana'),('HealAmt','healamt'),('SpellDmg','spelldmg'),('DamageShield','damageshield'),('Slots','slots'),('AugType','augtype')]:
                    assert struct.unpack_from('<i',right,layout[field])[0]==item.get(key,0),(i,field)
                for field,key in [('Worn','worneffect'),('Focus','focuseffect')]:
                    if key in item:assert struct.unpack_from('<i',right,layout[field])[0]==item[key]
            elif i in stock:
                expected=bytearray(left)
                for k,field in enumerate(('HealAmt','SpellDmg','HP','Mana')):
                    assert struct.unpack_from('<i',left,layout[field])[0]==stock[i]['before'][k]
                    struct.pack_into('<i',expected,layout[field],stock[i]['after'][k])
                assert right==expected,i
            else:assert left==right,i
        return {'before':xc,'after':yc,'stock_families':9,'scale_definitions':len(added),'items_sha256':sha(new)}


def rehearsal():
    db='nightcap_dungeon_stage_'+uuid.uuid4().hex[:12]
    user='aug_'+uuid.uuid4().hex[:12]
    work=STAGE/('rehearsal-'+db[-12:])
    work.mkdir(mode=0o700)
    (work/'shared').mkdir()
    (work/'logs').mkdir()
    cfg=work/'eqemu_config.json'
    tables=('items','tradeskill_recipe','tradeskill_recipe_entries','rule_sets','rule_values','variables','logsys_categories','content_flags','zone','instance_list')
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
        for idx,(_,_,_,scale,gem) in enumerate(FAMILIES):
            # Native tradeskill lookup first identifies component matches and then
            # checks the full ingredient list and the supplied container.
            query=f"""SELECT e.recipe_id FROM tradeskill_recipe_entries e JOIN tradeskill_recipe r ON r.id=e.recipe_id
                WHERE r.enabled AND e.componentcount>0 GROUP BY e.recipe_id
                HAVING SUM(e.componentcount)=2 AND SUM(IF(e.item_id IN ({scale},{gem}),e.componentcount,0))=2
                AND SUM(e.item_id*e.componentcount)={scale+gem}"""
            assert sql(query,db).split()==[str(96920+idx)]
            assert sql(f'SELECT item_id FROM tradeskill_recipe_entries WHERE recipe_id={96920+idx} AND iscontainer=1',db).strip()=='17912'
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


def preflight():
    before_rows('peq')
    assert sql("SELECT COUNT(*) FROM items WHERE (id=11602 AND name='White Dragon Scales') OR (id=11622 AND name='Red Dragon Scales') OR (id=17912 AND bagtype=20) OR (id=10036 AND name='Black Sapphire') OR (id=10033 AND name='Fire Emerald') OR (id=10032 AND name='Star Ruby')").strip()=='6'
    assert sql("SELECT COUNT(*) FROM spells_new WHERE (id=3501 AND effectid1=125) OR (id=3513 AND effectid1=124) OR (id=3889 AND effectid1=174 AND effect_base_value1=10)").strip()=='3'
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
    before_rows('peq')
    p.save(EVIDENCE/'preflight.json',state)


def activate():
    before=read(EVIDENCE/'preflight.json')
    assert before['manifest']==sha(STAGE/'manifest.json')
    assert h.caches()==before['caches'] and outside()==before['outside']
    before_rows('peq')
    assert r.compact('game')['image_id']==m['image'] and r.compact('gateway')['running']
    assert a.prior.players()==0
    folder=EVIDENCE/'activation'
    folder.mkdir(mode=0o700)
    sql_started=False
    p.save(folder/'started.json',{'source':m['source']})
    try:
        r.compose('stop','gateway')
        time.sleep(125)
        assert a.prior.players()==0
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
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        runtime=r.running(m['image'],m['binaries'])
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
    runtime=r.running(m['image'],m['binaries'])
    assert runtime['started_at']==read(folder/'verified-closed.json')['started_at']
    assert r.compact('gateway')['running'] and not any(runtime['errors'].values())
    workers=sum(row[0]=='zone' for row in runtime['processes'])
    assert workers==12 and runtime['restart_count']==0
    assert sha(ROOT/'data/public/channel.json')==m['channel']
    verify_content(before)
    base.health()
    return dict(source=m['source'],gateway_open=True,workers=workers,errors=runtime['errors'],restarts=runtime['restart_count'],image=m['image'],client=m['client'],cache=before['rehearsal'],backup_sha256=read(folder/'backup.json')['sha256'],player_qa='open')


if __name__=='__main__':
    assert __debug__
    os.umask(0o077)
    initialize()
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        for handle in (lock,gm):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists() and sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
        action=sys.argv[1]
        if action=='verify':print(json.dumps(verify_open(read(EVIDENCE/'preflight.json'))))
        else:{'preflight':preflight,'activate':activate}[action]()

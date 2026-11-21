"""Release the paired ornament content, quest and binaries using the retained production supervisor."""
import fcntl
import gzip
import hashlib
import importlib.util
import json
import mmap
import os
import shutil
import secrets
import uuid
import struct
import subprocess
import sys
import time
from pathlib import Path

stage = Path(__file__).resolve().parent
root = Path('/opt/nightcap/deploy/production')
active = stage/'activation'
quest = root/'data/server/quests/ecommons/998946.pl'

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def sql(statement, db='peq'):
    return stock.op.sql(statement,db)

def apply(db):
    sql(gzip.decompress((stage/'content.sql.gz').read_bytes()).decode('utf8'),db)

def check_content(db='peq'):
    checks=[
        'SELECT COUNT(*) FROM nightcap_ornament_design WHERE active=1',
        'SELECT COUNT(*) FROM nightcap_ornament_source',
        """SELECT COUNT(*) FROM nightcap_ornament_design d JOIN items i ON d.id=i.id
        WHERE d.active=1 AND i.itemtype=54 AND i.lore='Nightcap appearance ornament'
        AND i.augtype IN (524288,1048576) AND i.hp=0 AND i.mana=0 AND i.ac=0 AND i.damage=0
        AND i.clickeffect<=0 AND i.worneffect<=0 AND i.proceffect<=0 AND i.focuseffect<=0""",
        """SELECT COUNT(*) FROM spawn2 s JOIN spawnentry e ON e.spawngroupID=s.spawngroupID
        JOIN npc_types n ON n.id=e.npcID WHERE n.id=998946 AND n.name='Ornament_Artisan'
        AND s.zone='ecommons' AND s.version=0"""]
    counts=[int(sql(q,db).strip()) for q in checks]
    assert counts==[m['designs'],m['donors'],m['designs'],1],counts
    return counts

def cache_check(old,new):
    size,ident=1332,440
    with old.open('rb') as f,new.open('rb') as g,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as x,mmap.mmap(g.fileno(),0,access=mmap.ACCESS_READ) as y:
        def layout(buf):
            payload,slots,cap,used=struct.unpack_from('<IIII',buf)
            assert len(buf)==payload+8==20+slots*4+size*cap
            return slots,used
        xs,xc=layout(x)
        ys,yc=layout(y)
        assert yc==xc+m['designs'] and ys>=xs
        def row(buf,slots,used,index):
            if index>=slots:return None
            idx=struct.unpack_from('<I',buf,16+index*4)[0]
            if idx>=used:return None
            pos=16+slots*4+size*idx
            assert struct.unpack_from('<I',buf,pos+ident)[0]==index
            return buf[pos:pos+size]
        added=0
        for i in range(ys):
            before,after=row(x,xs,xc,i),row(y,ys,yc,i)
            if before is None and after is not None:
                assert 1000000<=i<=1048575 and struct.unpack_from('<i',after,708)[0] in (524288,1048576)
                added+=1
            else: assert before==after,i
        assert added==m['designs']
    return dict(records=yc,original_records=xc,designs=added,items_sha256=sha(new))

def check_base():
    assert r.compact('game')['image_id']==m['image'] and r.compact('gateway')['running']
    assert h.caches()==m['caches'] and sha(root/'data/public/channel.json')==m['channel']
    assert not os.path.lexists(quest)
    assert sql('SELECT COUNT(*) FROM items WHERE id BETWEEN 1000000 AND 1048575').strip()=='0'
    assert sql('SELECT COUNT(*) FROM npc_types WHERE id=998946').strip()=='0'
    assert sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('nightcap_ornament_design','nightcap_ornament_source')").strip()=='0'

def preflight():
    check_base()
    assert shutil.disk_usage(root).free>3*1024**3
    for k,v in m['services'].items():assert r.compact(k)==v
    stock.p.startup.startup_guards()
    db='nightcap_dungeon_stage_'+uuid.uuid4().hex[:12]
    user='aug_'+uuid.uuid4().hex[:12]
    work=stage/('rehearsal-'+db[-12:])
    work.mkdir(mode=0o700)
    (work/'shared').mkdir()
    (work/'logs').mkdir()
    cfg=work/'eqemu_config.json'
    tables=('items','rule_sets','rule_values','variables','logsys_categories','content_flags','zone',
            'instance_list','npc_types','spawngroup','spawnentry','spawn2')
    sql('CREATE DATABASE '+db)
    try:
        for table in tables:
            sql(f'CREATE TABLE {db}.{table} LIKE peq.{table}')
        sql('START TRANSACTION WITH CONSISTENT SNAPSHOT;'+''.join(
            f'INSERT INTO {db}.{table} SELECT * FROM peq.{table};' for table in tables if table!='instance_list')+'COMMIT;')
        for attempt in range(2):
            apply(db)
            check_content(db)
        password=secrets.token_hex(28)
        sql(f"CREATE USER '{user}'@'%' IDENTIFIED BY '{password}'; GRANT SELECT ON {db}.* TO '{user}'@'%';")
        config=read(root/'private/eqemu_config.json')
        conn=config['server']['database']
        conn.update(db=db,username=user,password=password)
        config['server']['content_database']=dict(conn)
        config['server'].setdefault('directories',{}).update(shared_memory='/runtime/shared/',logs='/runtime/logs/')
        cfg.write_text(json.dumps(config))
        network,=r.state('db')['NetworkSettings']['Networks']
        cmd=['docker','run','--rm','--network',network,'--user','0','-v',str(work)+':/runtime',
             '--workdir','/runtime','--entrypoint','/opt/nightcap/bin/shared_memory',m['image'],'items']
        with (work/'loader.log').open('x') as log:
            subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=360,check=True)
        cache=cache_check(root/'data/server/shared/items',work/'shared/items')
    finally:
        cfg.unlink(missing_ok=True)
        sql(f"DROP USER IF EXISTS '{user}'@'%'; DROP DATABASE {db};")
        (work/'shared/items').unlink(missing_ok=True)
    image=aa.image()
    save(stage/'preflight.json',dict(cache=cache,image=image,rules=aa.rules_digest(),
            publication=h.publication(),manifest=sha(stage/'manifest.json')))

def check_running(pre):
    pins={k[4:]:v for k,v in m['base_hashes'].items() if k.startswith('bin/')}
    pins.update(m['binaries'])
    run=r.running(pre['image'],pins)
    assert not any(run['errors'].values()) and run['restart_count']==0
    assert sum(p[0]=='zone' for p in run['processes'])==12
    assert h.caches()==dict(m['caches'],items=pre['cache']['items_sha256'])
    assert sha(quest)==m['files']['998946.pl'] and aa.rules_digest()==pre['rules']
    assert h.publication()==pre['publication']
    for k in ('db','web','tunnel'):assert r.compact(k)==m['services'][k]
    stock.base.health()
    stock.p.contract()
    r.closed_ports()
    return run

def activate(allow_drain=False):
    pre=read(stage/'preflight.json')
    assert pre['manifest']==sha(stage/'manifest.json') and not active.exists()
    check_base()
    assert allow_drain or a.prior.players()==0,'Player online; defer maintenance'
    active.mkdir(mode=0o700)
    save(active/'started.json',dict(source=m['source']))
    game_stopped=False
    opening=False
    try:
        r.compose('stop','gateway')
        assert not r.compact('gateway')['running']
        time.sleep(125)
        deadline=time.monotonic()+180
        while a.prior.players():
            assert time.monotonic()<deadline,'World did not drain'
            time.sleep(3)
        start=time.monotonic()
        r.compose('stop','-t','90','game')
        game_stopped=True
        st=r.state('game')['State']
        assert not st['Running'] and not st['OOMKilled'] and st['ExitCode']==0 and time.monotonic()-start<70
        saved=a.prior.saved()
        market=stock.p.market.market()
        r.STAGE=stock.base.EVIDENCE=active
        backup=r.database_backup()
        assert backup['gzip_integrity'] and sha(Path(backup['path']))==backup['sha256']
        save(active/'backup.json',backup)
        expected=stock.base.boot_state(saved)
        assert a.prior.saved()==saved
        apply('peq')
        counts=check_content()
        with quest.open('xb') as f:
            f.write((stage/'998946.pl').read_bytes());f.flush();os.fsync(f.fileno())
        quest.chmod(0o644)
        assert a.prior.saved()==saved
        r.select(pre['image'])
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        run=check_running(pre)
        assert a.prior.saved()==expected
        rotation=stock.p.market.verify_market(market,run['started_at'])
        save(active/'verified-closed.json',dict(started_at=run['started_at'],market=rotation))
        opening=True
        save(active/'opening.json',dict(image=pre['image']))
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        assert r.compact('gateway')['running'] and check_running(pre)['started_at']==run['started_at']
        save(active/'deployed.json',dict(source=m['source'],workers=12,errors=run['errors'],
            gateway_open=True,image=pre['image'],binaries=m['binaries'],cache=pre['cache'],
            content=counts,backup_sha256=backup['sha256'],manual_qa='open'))
    except BaseException:
        if opening:r.compose('stop','gateway')
        elif game_stopped:h.hold(active)
        elif r.compact('game')['running']:r.compose('up','-d','--no-deps','--wait','gateway')
        raise

if __name__=='__main__':
    os.umask(0o077)
    m=read(stage/'manifest.json')
    assert set(m['files'])=={'activate.py','bin/world','bin/zone','998946.pl','content.sql.gz','build.json'}
    for n,v in m['files'].items():assert sha(stage/n)==v
    aa=module('aa',stage.parent/'aa-purchase-latency-20261121-v1/release.py')
    stock=module('stock',aa.OLD)
    stock.initialize()
    r,h,a,save=stock.r,stock.h,stock.a,stock.p.save
    aa.STAGE,aa.m,aa.r,aa.sql=stage,m,r,sql
    assert sha(aa.OLD)==m['stock_operator']
    with (root/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        for f in (lock,gm):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
        assert not (root/'private/gm-maintenance.json').exists()
        if sys.argv[1]=='verify':
            result=read(active/'deployed.json')
            assert check_running(read(stage/'preflight.json'))['started_at']==read(active/'verified-closed.json')['started_at']
            assert r.compact('gateway')['running']
            check_content()
            print(json.dumps(result))
        else:{'preflight':preflight,'activate':activate,'activate-authorized-drain':lambda:activate(True)}[sys.argv[1]]()

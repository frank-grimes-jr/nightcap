"""Deploy the validated 405-row ATK data patch using the current production image."""
import argparse
import csv
import fcntl
import gzip
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

STAGE=Path(__file__).resolve().parent
EVIDENCE=STAGE/'evidence'
ROOT=Path('/opt/nightcap/deploy/production')
PREVIOUS=Path('/opt/nightcap/releases/classic-raid-augments-20261112-v2')
SOURCE='690d67f376d367d9111a978543b623789d5e0c6f'

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def initialize():
    global op,p,r,a,h,base,m,targets,ids
    m=read(STAGE/'manifest.json')
    assert m['source']==SOURCE and m['authorization']=='Push to prod'
    assert set(m['files'])=={'release.py','forward.sql.gz','rollback.sql.gz','changes.csv','production-items.json.gz'}
    for name,digest in m['files'].items():
        path=STAGE/name
        assert path.is_file() and not path.is_symlink() and sha(path)==digest,name
    assert sha(PREVIOUS/'rollout.py')==m['prior_operator']
    spec=importlib.util.spec_from_file_location('raid',PREVIOUS/'rollout.py')
    op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op);op.initialize()
    p,r,a,h,base=op.p,op.r,op.a,op.h,op.base
    deployed=read(PREVIOUS/'evidence/activation/deployed.json')
    assert deployed['gateway_open'] and m['image']==deployed['image']
    with (STAGE/'changes.csv').open(encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    targets={int(x['item_id']):(int(x['before_atk']),int(x['after_atk'])) for x in rows}
    assert len(rows)==len(targets)==405 and len({x['base_id'] for x in rows})==135
    ids=','.join(str(i) for i in sorted(targets))

def row_check(installed,db='peq'):
    ref=json.loads(gzip.decompress((STAGE/'production-items.json.gz').read_bytes()))
    rows=ref['rows'];cols=ref['columns']
    assert len(rows)==926 and all(re.fullmatch('[A-Za-z0-9_]+',c) for c in cols)
    if installed:
        for row in rows:
            i=int(row['id'])
            if i in targets:
                assert int(row['attack'])==targets[i][0]
                row['attack']=str(targets[i][1])
    fields=','.join('CAST(`'+c+'` AS CHAR)' for c in cols)
    keys=','.join(str(int(x['id'])) for x in rows)
    live=op.sql('SELECT JSON_ARRAY('+fields+') FROM items WHERE id IN ('+keys+') ORDER BY id;',db)
    current=[dict(zip(cols,json.loads(line),strict=True)) for line in live.splitlines()]
    assert current==rows, 'Full stock item or control preimages differ'
    return len(current)

def outside():
    return a.prior.digest('items','id NOT IN ('+ids+')')

def static_content():
    return {k:v for k,v in a.content().items() if k.split('/')[0]!='items'}

def apply(direction,db):
    assert direction in ('forward','rollback')
    assert op.sql("SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE() AND ROUTINE_NAME='nightcap_stock_worn_atk_20261113'",db).strip()=='0'
    op.sql(gzip.decompress((STAGE/(direction+'.sql.gz')).read_bytes()).decode(),db)

def compare(old,new,layout,changes):
    size,ident,attack=layout['size'],layout['ID'],layout['Attack']
    with old.open('rb') as fo,new.open('rb') as fn,mmap.mmap(fo.fileno(),0,access=mmap.ACCESS_READ) as orig,mmap.mmap(fn.fileno(),0,access=mmap.ACCESS_READ) as cand:
        assert orig[:16]==cand[:16]
        payload,slots,capacity,used=struct.unpack_from('<IIII',orig)
        assert len(orig)==len(cand)==20+4*slots+size*capacity==payload+8
        found=set();total=0
        for i in range(slots):
            x,y=(struct.unpack_from('<I',buf,16+4*i)[0] for buf in (orig,cand))
            if x>=used:
                assert y>=used
                continue
            assert y<used
            pos=16+4*slots
            left=orig[pos+x*size:pos+(x+1)*size];right=cand[pos+y*size:pos+(y+1)*size]
            assert struct.unpack_from('<I',left,ident)[0]==struct.unpack_from('<I',right,ident)[0]==i
            total+=1
            if i in changes:
                assert (struct.unpack_from('<i',left,attack)[0],struct.unpack_from('<i',right,attack)[0])==changes[i],i
                assert left[:attack]==right[:attack] and left[attack+4:]==right[attack+4:],i
                found.add(i)
            else: assert left==right,('Unrelated item cache change',i)
        assert found==set(changes) and total==used
        return dict(records=total,changed=len(found),byte_identical=total-len(found))

def rehearsal():
    db='nightcap_dungeon_stage_'+uuid.uuid4().hex[:12]; user='atk_'+uuid.uuid4().hex[:12]
    work=STAGE/'rehearsal';work.mkdir(mode=0o700);(work/'shared').mkdir();(work/'logs').mkdir()
    cfg=work/'eqemu_config.json'
    tables=('items','rule_sets','rule_values','variables','logsys_categories','content_flags','zone','instance_list')
    op.sql('CREATE DATABASE '+db)
    try:
        for t in tables:op.sql(f'CREATE TABLE {db}.{t} LIKE peq.{t}')
        op.sql('START TRANSACTION WITH CONSISTENT SNAPSHOT;\n'+'\n'.join(f'INSERT INTO {db}.{t} SELECT * FROM peq.{t};' for t in tables if t!='instance_list')+'\nCOMMIT;')
        row_check(False,db); apply('forward',db);row_check(True,db)
        apply('forward',db);row_check(True,db)
        apply('rollback',db);row_check(False,db)
        apply('forward',db);row_check(True,db)
        contract=op.read(a.prior.prior.STAGE/'runtime-contract.json')
        pattern=re.compile(r'\b(FROM|JOIN)\s+`?items`?(?=\s|[;,.)]|$)',re.I)
        for checks in contract.values():
            for c in checks:
                query=pattern.sub(lambda match:match[1]+' `'+db+'`.`items`',c['sql'])
                if query!=c['sql']:assert op.sql(query).strip()==c['expected'],c['label']
        pwd=secrets.token_hex(28)
        op.sql(f"CREATE USER '{user}'@'%' IDENTIFIED BY '{pwd}'; GRANT SELECT ON {db}.* TO '{user}'@'%';")
        config=read(ROOT/'private/eqemu_config.json')
        conn=config['server']['database'];conn.update(db=db,username=user,password=pwd)
        config['server']['content_database']=dict(conn)
        config['server'].setdefault('directories',{}).update(shared_memory='/runtime/shared/',logs='/runtime/logs/')
        cfg.write_text(json.dumps(config));cfg.chmod(0o600)
        network,=r.state('db')['NetworkSettings']['Networks']
        cmd=['docker','run','--rm','--network',network,'--user','0','-v',str(work)+':/runtime','--workdir','/runtime','--entrypoint','/opt/nightcap/bin/shared_memory',m['image'],'items']
        with (work/'loader.log').open('x') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
        cache=work/'shared/items'
        return {**compare(ROOT/'data/server/shared/items',cache,m['layout'],targets),'items_sha256':sha(cache),'full_rows_verified':926,'forward_replay_inverse':True}
    finally:
        cfg.unlink(missing_ok=True)
        op.sql(f"DROP USER IF EXISTS '{user}'@'%'; DROP DATABASE {db};")

def verify_preserved(before,installed,opened=False):
    for name in ('db','web','tunnel'):assert r.compact(name)==before['services'][name],name
    assert r.runtime()==before['runtime'] and h.publication()==before['publication']
    assert a.prior.p.rules()==before['rules']
    assert outside()==before['outside']
    content=static_content()
    expected=dict(before['content'])
    if opened:
        for t in a.prior.NEW_TABLES:
            content.pop(t+'/complete-icon-release',None);expected.pop(t+'/complete-icon-release',None)
    assert content==expected
    cache=dict(before['caches'])
    if installed:cache['items']=before['rehearsal']['items_sha256']
    assert h.caches()==cache
    row_check(installed)

def preflight():
    assert not EVIDENCE.exists()
    services={s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
    assert all(v['running'] and not v['oom_killed'] for v in services.values())
    assert services['game']['image_id']==m['image'] and services['game']['health']==services['db']['health']=='healthy'
    assert shutil.disk_usage(ROOT).free>4*1024**3
    r.running(m['image'],op.binaries(),services['game']['restarts']);base.health();p.startup.startup_guards();r.closed_ports();p.contract()
    row_check(False)
    EVIDENCE.mkdir(mode=0o700)
    before=dict(manifest_sha256=sha(STAGE/'manifest.json'),services=services,caches=h.caches(),content=static_content(),outside=outside(),runtime=r.runtime(),rules=a.prior.p.rules(),publication=h.publication())
    p.save(EVIDENCE/'before.json',before)
    before['rehearsal']=rehearsal()
    verify_preserved(before,False)
    assert all(r.compact(n)==s for n,s in services.items())
    p.save(EVIDENCE/'preflight.json',before)
    print('Guarded production rehearsal passed.',flush=True)

def activate():
    before=read(EVIDENCE/'preflight.json');folder=EVIDENCE/'activation'
    assert not folder.exists() and sha(STAGE/'manifest.json')==before['manifest_sha256']
    verify_preserved(before,False);p.startup.startup_guards();p.contract()
    assert all(r.compact(n)==s for n,s in before['services'].items())
    assert a.prior.players()==0,'Players online; leave gateway open'
    dry=EVIDENCE/'boot-rehearsal';dry.mkdir(exist_ok=True)
    old=base.EVIDENCE;base.EVIDENCE=dry
    try:base.boot_state(a.prior.saved())
    finally:base.EVIDENCE=old
    assert a.prior.players()==0
    folder.mkdir(mode=0o700);p.save(folder/'started.json',{'image':m['image']})
    try:
        r.compose('stop','gateway');time.sleep(125)
        assert a.prior.players()==0
        t=time.monotonic();r.compose('stop','-t','90','game')
        state=r.state('game')['State'];assert time.monotonic()-t<70 and not state['Running'] and not state['OOMKilled'] and state['ExitCode']==0
        saved=a.prior.saved();market=p.market.market()
        p.save(folder/'stopped-state.json',saved);p.save(folder/'market-before.json',market)
        r.STAGE=folder;base.EVIDENCE=folder
        backup=r.database_backup()
        assert backup['gzip_integrity'] and backup['compressed_bytes']>0 and sha(Path(backup['path']))==backup['sha256']
        p.save(folder/'backup.json',backup);assert a.prior.saved()==saved
        expected=base.boot_state(saved)
        row_check(False);p.save(folder/'sql-started.json',{'payload':m['files']['forward.sql.gz']});apply('forward','peq')
        row_check(True);assert a.prior.saved()==saved and outside()==before['outside']
        p.save(folder/'sql-installed.json',{'updated':405})
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        first=r.running(m['image'],op.binaries());base.health();time.sleep(8)
        current=r.running(m['image'],op.binaries());assert current['started_at']==first['started_at']
        assert a.prior.saved()==expected
        rotation=p.market.verify_market(market,current['started_at'])
        verify_preserved(before,True);checks=p.contract();base.health();r.closed_ports()
        assert not r.state('gateway')['State']['Running']
        p.save(folder/'verified-closed.json',dict(runtime=current,game=r.compact('game'),market=rotation,checks=checks))
        # Keep the deployment locks from activation through admission verification.
        p.save(folder/'opening.json',{'source':SOURCE})
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        final=r.running(m['image'],op.binaries())
        assert final['started_at']==current['started_at'] and r.compact('gateway')['running']
        base.health();r.closed_ports();verify_preserved(before,True,True)
        p.save(folder/'deployed.json',dict(source=SOURCE,gateway_open=True,runtime=final,rows=405,base_families=135,cache=before['rehearsal'],client_channel_sha256=m['channel'],backup_sha256=backup['sha256'],player_qa='open'))
        print('ATK deployed and public admissions verified.',flush=True)
    except BaseException:
        h.hold(folder)
        raise

if __name__=='__main__':
    assert __debug__
    os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate'));args=parser.parse_args()
    initialize()
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists() and op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
        {'preflight':preflight,'activate':activate}[args.action]()


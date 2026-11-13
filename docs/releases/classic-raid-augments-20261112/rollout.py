"""One-shot OVH deployment for the sixteen Classic raid augments."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import mmap
import os
import re
from pathlib import Path
import secrets
import shutil
import struct
import subprocess
import time
import uuid

STAGE = Path(__file__).resolve().parent
ROOT = Path('/opt/nightcap/deploy/production')
EVIDENCE = STAGE / 'evidence'
TAG = 'nightcap-game:' + STAGE.name
PRIOR = Path('/opt/nightcap/releases/dot-no-initial-damage-20261112-v2/rollout.py')
IDS = set(range(963200, 963216))
FILTER = 'id NOT BETWEEN 963200 AND 963215'
NATIVE = ('world', 'zone', 'shared_memory')

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def initialize():
    global m, p, r, a, h, base
    m = read(STAGE/'manifest.json')
    assert m['authorization'] == 'Merge to test and then to main/production once your tests pass.'
    assert set(m['files']) == {'rollout.py','content.sql','native.json',*('bin/'+n for n in NATIVE)}
    for name, pin in m['files'].items():
        path = STAGE/name
        assert not path.is_symlink() and path.resolve().is_relative_to(STAGE) and sha(path) == pin, name
    assert sha(PRIOR) == m['prior_sha256']
    spec = importlib.util.spec_from_file_location('previous_dot_release', PRIOR)
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    p = prior.initialize()
    r, a, h, base = p.r, p.a, p.h, p.base
    receipt = read(STAGE/'native.json')
    assert receipt['base_zone'] == m['base_hashes']['bin/zone'] and len(receipt['verified_feature_sources']) == 30
    assert m['binaries'] == {n:m['files']['bin/'+n] for n in NATIVE} == receipt['shipping']
    assert r.image_hashes(m['base_image_id']) == m['base_hashes']
    a.STAGE, a.TAG, a.m = STAGE, TAG, m

def binaries(installed=True):
    before = {k[4:]:v for k,v in m['base_hashes'].items() if k.startswith('bin/')}
    return {**before, **m['binaries']} if installed else before

def sql(statement, db='peq'):
    return a.sql(statement, db)

def count(db='peq'):
    return int(sql('SELECT COUNT(*) FROM items WHERE id BETWEEN 963200 AND 963215;',db).strip())

def install(db):
    assert sql("SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA=DATABASE() AND ROUTINE_NAME='nightcap_install_raid_augments';", db).strip() == '0'
    # Stock item 33961 is a pre-existing jewelry item with the same display name.
    # Pin this exact row so a second augment or a different collision still stops.
    query = ('SELECT CONCAT(id,CHAR(9),Name,CHAR(9),itemtype) FROM items WHERE '+FILTER+
             ' AND BINARY Name IN ('+','.join("X'"+v.encode().hex()+"'" for v in m['names'])+') ORDER BY id;')
    assert sql(query,db).splitlines() == ['33961\tDeepwater Pearl\t11'], 'Unexpected existing trophy name'
    sql((STAGE/'content.sql').read_text(), db)
    assert count(db) == 16

def trophy_digest(db='peq'):
    columns=[line.split('\t')[0] for line in sql('SHOW COLUMNS FROM items;',db).splitlines()]
    assert all(re.fullmatch('[A-Za-z0-9_]+',c) for c in columns)
    fields=','.join('`'+c+'`' for c in columns if c not in ('created','updated','verified'))
    result=sql('SELECT SHA2(JSON_ARRAY('+fields+'),256) FROM items WHERE id BETWEEN 963200 AND 963215 ORDER BY id;',db)
    assert len(result.splitlines())==16
    return hashlib.sha256(result.encode()).hexdigest()

def content(opened=False):
    data = {k:v for k,v in a.content().items() if k.split('/')[0] != 'items'}
    data['items/outside-raid'] = a.prior.digest('items', FILTER)
    data['items/schema'] = re.sub(r' AUTO_INCREMENT=[0-9]+','',sql('SHOW CREATE TABLE items'))
    if opened:
        for table in a.prior.NEW_TABLES:
            data.pop(table+'/complete-icon-release', None)
    return data

def cache_compare(old, new, layout):
    with old.open('rb') as fo, new.open('rb') as fn, mmap.mmap(fo.fileno(),0,access=mmap.ACCESS_READ) as x, mmap.mmap(fn.fileno(),0,access=mmap.ACCESS_READ) as y:
        def header(buf):
            payload, slots, capacity, used = struct.unpack_from('<IIII',buf)
            assert 0 < used <= capacity and len(buf) == payload+8 == 20+4*slots+layout['size']*capacity
            return slots, used
        def row(buf, slots, used, item):
            if item >= slots: return None
            idx = struct.unpack_from('<I',buf,16+4*item)[0]
            if idx >= used: return None
            pos = 16 + 4*slots + idx*layout['size']
            assert struct.unpack_from('<I',buf,pos+layout['ID'])[0] == item
            return buf[pos:pos+layout['size']]
        xs,xc = header(x)
        ys,yc = header(y)
        assert yc == xc + len(IDS)
        added = set()
        for item in range(max(xs,ys)):
            left, right = row(x,xs,xc,item), row(y,ys,yc,item)
            if item in IDS:
                assert left is None and right is not None
                fields = ('LoreGroup','LoreFlag','Slots','AugType','ReqLevel','NoPet')
                actual = [struct.unpack_from('<'+fmt,right,layout[n])[0] for n,fmt in zip(fields,('i','B','I','I','B','B'))]
                assert actual == [-1,1,131072,2097152,50,1], (item,actual)
                added.add(item)
            else:
                assert left == right, ('unrelated item cache record changed',item)
        assert added == IDS
        return dict(original_items=xc, new_items=yc, verified_trophies=sorted(added))

def rehearse(image):
    db = 'nightcap_dungeon_stage_'+uuid.uuid4().hex[:12]
    folder = STAGE/'rehearsal'
    folder.mkdir(mode=0o700)
    (folder/'shared').mkdir()
    (folder/'logs').mkdir()
    user = 'ra_'+uuid.uuid4().hex[:12]
    password = secrets.token_hex(28)
    tables = ('items','rule_sets','rule_values','variables','logsys_categories','content_flags','zone','instance_list')
    sql('CREATE DATABASE '+db)
    cfg = folder/'eqemu_config.json'
    try:
        for t in tables:
            sql(f'CREATE TABLE {db}.{t} LIKE peq.{t}')
        sql('START TRANSACTION WITH CONSISTENT SNAPSHOT;\n'+'\n'.join(f'INSERT INTO {db}.{t} SELECT * FROM peq.{t};' for t in tables if t!='instance_list')+'\nCOMMIT;')
        sql(f"CREATE USER '{user}'@'%' IDENTIFIED BY '{password}'; GRANT SELECT ON {db}.* TO '{user}'@'%';")
        conf = read(ROOT/'private/eqemu_config.json')
        conn = conf['server']['database']
        conn.update(db=db,username=user,password=password)
        conf['server']['content_database'] = dict(conn)
        conf['server'].setdefault('directories',{}).update(shared_memory='/runtime/shared/',logs='/runtime/logs/')
        cfg.write_text(json.dumps(conf));cfg.chmod(0o600)
        network, = r.state('db')['NetworkSettings']['Networks']
        assert count(db) == 0
        install(db)
        install(db)
        # Verify every existing dungeon contract query using items against the proposed catalog.
        contract=read(a.prior.prior.STAGE/'runtime-contract.json')
        pattern=re.compile(r'\b(FROM|JOIN)\s+`?items`?(?=\s|[;,.)]|$)',re.I)
        for checks in contract.values():
            for check in checks:
                query=pattern.sub(lambda m:m[1]+' `'+db+'`.`items`',check['sql'])
                if query!=check['sql']:
                    assert sql(query).strip()==check['expected'],check['label']
        args=['docker','run','--rm','--network',network,'--user','0','-v',str(folder)+':/runtime','--workdir','/runtime','--entrypoint','/opt/nightcap/bin/shared_memory',image,'items']
        with (folder/'loader.log').open('x') as log:
            subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=240,check=True)
        artifact = folder/'shared/items'
        result = cache_compare(ROOT/'data/server/shared/items', artifact, read(STAGE/'native.json')['layout'])
        return {**result,'sha256':sha(artifact),'raid_rows':trophy_digest(db)}
    finally:
        cfg.unlink(missing_ok=True)
        sql(f"DROP USER IF EXISTS '{user}'@'%'; DROP DATABASE {db};")

def unchanged(before, installed, opened=False):
    for k in ('db','web','tunnel'):
        assert r.compact(k) == before['services'][k], k
    assert r.runtime() == before['runtime'] and h.publication() == before['publication']
    assert a.prior.p.rules() == before['rules']
    expected = dict(before['content'])
    if opened:
        for t in a.prior.NEW_TABLES: expected.pop(t+'/complete-icon-release',None)
    assert content(opened) == expected, 'Unrelated gameplay content changed'
    cache = dict(before['caches'])
    if installed: cache['items'] = before['rehearsal']['sha256']
    assert h.caches() == cache
    assert count() == (16 if installed else 0)
    if installed:
        assert trophy_digest() == before['rehearsal']['raid_rows']

def preflight():
    assert not EVIDENCE.exists() and a.prior.players()==0
    services = {s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
    assert all(v['running'] and not v['oom_killed'] for v in services.values())
    assert services['game']['image_id'] == m['base_image_id'] and services['game']['health'] == services['db']['health'] == 'healthy'
    assert count()==0 and sha(ROOT/'data/public/channel.json') == m['client_channel_sha256']
    # Complete a dry native state-expiry prediction before closing access.
    dry = STAGE/'boot-rehearsal'
    dry.mkdir(mode=0o700)
    previous=base.EVIDENCE
    try:
        base.EVIDENCE=dry
        base.boot_state(a.prior.saved())
    finally:
        base.EVIDENCE=previous
    assert shutil.disk_usage(ROOT).free > 4*1024**3
    r.running(m['base_image_id'], binaries(False), services['game']['restarts'])
    base.health();p.startup.startup_guards();r.closed_ports();p.contract()
    EVIDENCE.mkdir(mode=0o700)
    before = dict(manifest_sha256=sha(STAGE/'manifest.json'),services=services,runtime=r.runtime(),publication=h.publication(),caches=h.caches(),content=content(),rules=a.prior.p.rules())
    p.save(EVIDENCE/'before.json',before)
    before['image'] = a.image()
    before['rehearsal'] = rehearse(before['image'])
    unchanged(before,False)
    assert all(r.compact(s)==v for s,v in services.items())
    p.save(EVIDENCE/'preflight.json',before)
    print('Full item-cache rehearsal and guarded SQL replay passed.',flush=True)

def activate():
    before=read(EVIDENCE/'preflight.json')
    folder=EVIDENCE/'activation'
    assert not folder.exists() and sha(STAGE/'manifest.json')==before['manifest_sha256']
    assert all(r.compact(s)==v for s,v in before['services'].items()) and a.prior.players()==0
    unchanged(before,False);p.startup.startup_guards()
    folder.mkdir(mode=0o700)
    p.save(folder/'started.json',{'image':before['image']})
    try:
        r.compose('stop','gateway')
        time.sleep(125)
        assert a.prior.players()==0
        started=time.monotonic()
        r.compose('stop','-t','90','game')
        state=r.state('game')['State']
        assert time.monotonic()-started<70 and not state['Running'] and state['ExitCode']==0 and not state['OOMKilled']
        unchanged(before,False);p.startup.startup_guards()
        saved=a.prior.saved(); market=p.market.market()
        p.save(folder/'stopped-state.json',saved);p.save(folder/'market-before.json',market)
        r.STAGE=folder;base.EVIDENCE=folder
        p.save(folder/'backup.json',r.database_backup())
        assert a.prior.saved()==saved
        expected=base.boot_state(saved)
        p.save(folder/'sql-started.json',{'sha256':m['files']['content.sql']})
        install('peq')
        assert a.prior.saved()==saved and content()==before['content']
        assert trophy_digest()==before['rehearsal']['raid_rows']
        p.save(folder/'sql-installed.json',{'items':16})
        r.select(before['image'])
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        first=r.running(before['image'],binaries());base.health();time.sleep(8)
        current=r.running(before['image'],binaries())
        assert first['started_at']==current['started_at'] and a.prior.saved()==expected
        rotation=p.market.verify_market(market,current['started_at'])
        unchanged(before,True);checks=p.contract();base.health();r.closed_ports()
        logs=r.out('docker','compose','logs','--no-color','--since',current['started_at'],'game')
        for msg in ('MySQL Error','Orphaned Rule','Unknown column','Dungeon schema drift','Dungeon content drift','Dungeon item cache drift','Failed to load Alternate Advancement'):
            assert msg not in logs, msg
        assert not r.state('gateway')['State']['Running']
        p.save(folder/'verified-closed.json',dict(runtime=current,game=r.compact('game'),checks=checks,market=rotation))
    except BaseException:
        h.hold(folder)
        raise

def open_access():
    before=read(EVIDENCE/'preflight.json');folder=EVIDENCE/'activation';verified=read(folder/'verified-closed.json')
    assert not list(folder.glob('held-*.json')) and not (folder/'opening.json').exists()
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game')==verified['game']
        assert a.prior.saved()==read(folder/'expected-boot-state.json')
        unchanged(before,True);p.contract();base.health();r.closed_ports()
        p.save(folder/'opening.json',{'owner_authorized':True})
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        current=r.running(before['image'],binaries())
        assert current['started_at']==verified['runtime']['started_at'] and r.state('gateway')['State']['Running']
        unchanged(before,True,True);base.health();r.closed_ports()
        p.save(folder/'deployed.json',dict(source=m['source_revision'],image=before['image'],runtime=current,gateway_open=True,items=16,client_update_required=False,owner_qa='open'))
    except BaseException:
        h.hold(folder)
        raise

if __name__=='__main__':
    assert __debug__
    os.umask(0o077)
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('preflight','activate','open'))
    action=parser.parse_args().action
    initialize()
    with (ROOT/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists() and sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':activate,'open':open_access}[action]()
        print('Verified raid augment action:',action,flush=True)

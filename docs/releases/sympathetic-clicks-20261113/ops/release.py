"""Run one pinned and paired Classic click release on the production host."""
import argparse
import copy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import time
import uuid

from cache import compare, sha

STAGE = Path(__file__).resolve().parent
ROOT = Path('/opt/nightcap/deploy/production')
PREVIOUS = Path('/opt/nightcap/releases/stock-worn-atk-20261113-v1')
EVIDENCE = STAGE/'evidence'
ACTIVE = EVIDENCE/'activation'
SERVICES = ('game','gateway','db','web','tunnel')
CHANGED = {'items':'id IN (610150,610338)', 'spells_new':'id IN (44379,44380)',
           'db_str':'id IN (44379,44380) AND type=6'}
ERRORS = ('MySQL Error','Orphaned Rule','Unknown column','Dungeon schema drift',
          'Dungeon content drift','Dungeon item cache drift','Failed to load Alternate Advancement')

def read(path):
    return json.loads(path.read_bytes())

def module(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def initialize():
    global stock, p, r, a, h, base, sql, save, m
    m = read(STAGE/'manifest.json')
    assert m['authorization']=='Push to main and server'
    assert sha(PREVIOUS/'release.py')==m['prior_operator']
    assert sha(PREVIOUS/'evidence/activation/deployed.json')==m['prior_receipt']
    for name, pin in m['files'].items():
        path = STAGE/name
        assert path.resolve().is_relative_to(STAGE) and not path.is_symlink() and sha(path)==pin, name
    stock = module('stock_before_sympathetic',PREVIOUS/'release.py')
    stock.initialize()
    p,r,a,h,base,sql,save = stock.p,stock.r,stock.a,stock.h,stock.base,stock.op.sql,stock.p.save
    assert m['base_image_id']==stock.m['image'] and r.image_hashes(m['base_image_id'])==m['base_hashes']
    assert m['binaries']=={'zone':m['files']['bin/zone']}
    signed = read(STAGE/'client/verification.json')
    assert signed['release']==m['client_release']==2026111301 and signed['changed_assets']==2
    assert signed['channel_sha256']==m['files']['client/channel.json']
    assert m['client_before']==m['files']['client/previous-channel.json']

def owned(db='peq'):
    return {table:a.prior.digest(table,scope,db) for table,scope in CHANGED.items()}

def content(opened=False):
    values = {k:v for k,v in a.content().items() if k.split('/')[0] not in CHANGED}
    for table, scope in CHANGED.items():
        values[table+'/outside'] = a.prior.digest(table,'NOT ('+scope+')')
    if opened:
        for table in a.prior.NEW_TABLES:
            values.pop(table+'/complete-icon-release',None)
    return values

def apply(name,db):
    assert name in ('forward','disable','remove-unused')
    sql((STAGE/(name+'.sql')).read_text(),db)

def rehearse(image):
    db = 'nightcap_dungeon_stage_'+uuid.uuid4().hex[:12]
    user = 'sym_'+uuid.uuid4().hex[:12]
    password = secrets.token_hex(28)
    folder = STAGE/('rehearsal-'+uuid.uuid4().hex[:8])
    folder.mkdir(mode=0o700)
    (folder/'shared').mkdir()
    (folder/'logs').mkdir()
    config_path = folder/'eqemu_config.json'
    sql('CREATE DATABASE '+db)
    try:
        tables = sorted(set(m['reference_tables']) | {'items','spells_new','db_str','rule_sets','rule_values',
                        'variables','logsys_categories','content_flags','zone','instance_list'})
        assert all(re.fullmatch('[a-z_0-9]+',t) for t in tables)
        for table in tables:
            sql(f'CREATE TABLE {db}.{table} LIKE peq.{table}')
        sql('START TRANSACTION WITH CONSISTENT SNAPSHOT;\n'+'\n'.join(
            f'INSERT INTO {db}.{t} SELECT * FROM peq.{t};' for t in tables)+'\nCOMMIT;')
        before = owned(db)
        assert before['items']['rows']==2 and before['db_str']['rows']==before['spells_new']['rows']==0
        assert before==owned()
        apply('forward',db)
        after = owned(db)
        assert all(v['rows']==2 for v in after.values())
        apply('forward',db)
        assert owned(db)==after
        apply('disable',db)
        disabled = owned(db)
        assert disabled=={**after,'items':before['items']}
        apply('remove-unused',db)
        assert owned(db)==before
        apply('forward',db)
        assert owned(db)==after
        # Validate inherited production content assertions against candidate tables.
        pattern = re.compile(r'\b(FROM|JOIN)\s+`?(items|spells_new|db_str)`?(?=\s|[;,.)]|$)',re.I)
        for checks in read(a.prior.prior.STAGE/'runtime-contract.json').values():
            for check in checks:
                query=pattern.sub(lambda match:match[1]+' `'+db+'`.`'+match[2]+'`',check['sql'])
                if query!=check['sql']:
                    assert sql(query).strip()==check['expected'],check['label']
        sql(f"CREATE USER '{user}'@'%' IDENTIFIED BY '{password}'; GRANT SELECT ON {db}.* TO '{user}'@'%';")
        config = read(ROOT/'private/eqemu_config.json')
        conn = config['server']['database']
        conn.update(db=db,username=user,password=password)
        config['server']['content_database'] = dict(conn)
        config['server'].setdefault('directories',{}).update(shared_memory='/runtime/shared/',logs='/runtime/logs/')
        config_path.write_text(json.dumps(config))
        config_path.chmod(0o600)
        network, = r.state('db')['NetworkSettings']['Networks']
        args = ['docker','run','--rm','--network',network,'--user','0','-v',str(folder)+':/runtime',
                '--workdir','/runtime','--entrypoint','/opt/nightcap/bin/shared_memory',image,'items','spells']
        with (folder/'loader.log').open('x') as log:
            subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
        caches = compare(ROOT/'data/server/shared',folder/'shared',m['layout'])
        return dict(before=before,after=after,disabled=disabled,cache=caches,forward_replay_disable_inverse=True)
    finally:
        config_path.unlink(missing_ok=True)
        sql(f"DROP USER IF EXISTS '{user}'@'%'; DROP DATABASE {db};")

def binaries(installed):
    old = {k[4:]:v for k,v in m['base_hashes'].items() if k.startswith('bin/')}
    return {**old,**(m['binaries'] if installed else {})}

def preserved(before,installed,published=False,opened=False):
    assert all(r.compact(n)==before['services'][n] for n in ('db','web','tunnel'))
    assert r.runtime()==before['runtime'] and a.prior.p.rules()==before['rules']
    expected = copy.deepcopy(before['publication'])
    if published:
        expected['channels']['channel.json']=m['files']['client/channel.json']
    assert h.publication()==expected, 'Public dependencies drifted'
    data = dict(before['content'])
    if opened:
        for table in a.prior.NEW_TABLES:
            data.pop(table+'/complete-icon-release',None)
    assert content(opened)==data,'Unrelated content drifted'
    assert owned()==before['rehearsal']['after' if installed else 'before']
    expected_cache = {n:v['after' if installed else 'before'] for n,v in before['rehearsal']['cache'].items()}
    assert h.caches()==expected_cache,'Runtime caches differ from isolated rehearsal'

def preflight():
    assert not (EVIDENCE/'preflight.json').exists() and not ACTIVE.exists()
    services = {s:r.compact(s) for s in SERVICES}
    assert services==m['baseline_services'] and all(s['running'] for s in services.values())
    assert services['game']['health']==services['db']['health']=='healthy'
    assert services['game']['image_id']==m['base_image_id']
    assert h.publication()['channels']['channel.json']==m['client_before']
    assert shutil.disk_usage(ROOT).free>4*1024**3
    r.running(m['base_image_id'],binaries(False),services['game']['restarts'])
    base.health()
    p.startup.startup_guards()
    p.contract()
    r.closed_ports()
    EVIDENCE.mkdir(mode=0o700,exist_ok=True)
    before=dict(services=services,runtime=r.runtime(),rules=a.prior.p.rules(),content=content(),publication=h.publication(),
                manifest=sha(STAGE/'manifest.json'))
    a.STAGE, a.TAG, a.m = STAGE,'nightcap-game:'+STAGE.name,m
    before['image'] = a.image()
    before['rehearsal'] = rehearse(before['image'])
    preserved(before,False)
    assert all(r.compact(n)==v for n,v in services.items())
    save(EVIDENCE/'preflight.json',before)

def native(before):
    current=r.running(before['image'],binaries(True))
    assert current['restart_count']==0 and sum(row[0]=='zone' for row in current['processes'])==12
    base.health()
    r.closed_ports()
    log=r.out('docker','compose','logs','--no-color','--since',current['started_at'],'game')
    assert not any(msg in log for msg in ERRORS),'Runtime startup error'
    return current

def activate():
    before=read(EVIDENCE/'preflight.json')
    assert not ACTIVE.exists() and sha(STAGE/'manifest.json')==before['manifest']
    preserved(before,False)
    p.startup.startup_guards()
    p.contract()
    assert all(r.compact(n)==v for n,v in before['services'].items())
    dry=EVIDENCE/'boot-rehearsal'
    dry.mkdir(exist_ok=True)
    old=base.EVIDENCE
    try:
        base.EVIDENCE=dry
        base.boot_state(a.prior.saved())
    finally:
        base.EVIDENCE=old
    assert a.prior.players()==0,'Players online'
    ACTIVE.mkdir(mode=0o700)
    save(ACTIVE/'started.json',dict(source=m['source'],image=before['image']))
    try:
        r.compose('stop','gateway')
        time.sleep(125)
        assert a.prior.players()==0
        started=time.monotonic()
        r.compose('stop','-t','90','game')
        state=r.state('game')['State']
        assert time.monotonic()-started<70 and not state['Running'] and state['ExitCode']==0 and not state['OOMKilled']
        saved=a.prior.saved()
        market=p.market.market()
        save(ACTIVE/'stopped-state.json',saved)
        save(ACTIVE/'market-before.json',market)
        r.STAGE=ACTIVE
        base.EVIDENCE=ACTIVE
        backup=r.database_backup()
        assert backup['gzip_integrity'] and backup['compressed_bytes']>0 and sha(Path(backup['path']))==backup['sha256']
        save(ACTIVE/'backup.json',backup)
        assert a.prior.saved()==saved and owned()==before['rehearsal']['before']
        expected=base.boot_state(saved)
        save(ACTIVE/'sql-started.json',{'sha256':m['files']['forward.sql']})
        apply('forward','peq')
        assert owned()==before['rehearsal']['after'] and a.prior.saved()==saved
        save(ACTIVE/'sql-installed.json',{'items':2,'spells':2,'descriptions':2})
        r.select(before['image'])
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
        first=native(before)
        time.sleep(8)
        current=native(before)
        assert current['started_at']==first['started_at'] and a.prior.saved()==expected
        rotation=p.market.verify_market(market,current['started_at'])
        preserved(before,True)
        checks=p.contract()
        assert not r.compact('gateway')['running']
        save(ACTIVE/'verified-closed.json',dict(runtime=current,game=r.compact('game'),market=rotation,checks=checks))
    except BaseException:
        h.hold(ACTIVE)
        raise

def publish():
    before=read(EVIDENCE/'preflight.json')
    verified=read(ACTIVE/'verified-closed.json')
    assert not (STAGE/'client/published.json').exists()
    assert r.compact('game')==verified['game'] and a.prior.players()==0
    def snapshot():
        services={n:r.compact(n) for n in SERVICES}
        assert not services['gateway']['running'] and services['game']['health']==services['db']['health']=='healthy'
        assert all(s['running'] and not s['oom_killed'] for n,s in services.items() if n!='gateway')
        assert services['game']==verified['game'] and a.prior.players()==0
        assert owned()==before['rehearsal']['after']
        assert h.caches()=={n:v['after'] for n,v in before['rehearsal']['cache'].items()}
        return services
    assert not r.compact('gateway')['running']
    preserved(before,True)
    result=module('paired_publisher',STAGE/'client/publish.py').publish(STAGE/'client',ROOT/'data/public',snapshot=snapshot)
    assert result['channel_sha256']==m['files']['client/channel.json']
    save(STAGE/'client/published.json',result)
    preserved(before,True,True)

def open_access():
    before=read(EVIDENCE/'preflight.json')
    verified=read(ACTIVE/'verified-closed.json')
    client=read(STAGE/'public-client-verified.json')
    assert client['release']==m['client_release'] and client['hosted'] and client['signature']=='valid against shipped production key'
    assert client['channel_sha256']==read(STAGE/'client/published.json')['channel_sha256']==m['files']['client/channel.json']
    assert not (ACTIVE/'opening.json').exists() and not list(ACTIVE.glob('held-*.json'))
    assert r.compact('game')==verified['game'] and not r.compact('gateway')['running']
    assert a.prior.saved()==read(ACTIVE/'expected-boot-state.json')
    preserved(before,True,True)
    p.contract()
    native(before)
    save(ACTIVE/'opening.json',dict(source=m['source']))
    try:
        r.compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
        current=native(before)
        assert r.compact('gateway')['running'] and current['started_at']==verified['runtime']['started_at']
        preserved(before,True,True,True)
        save(ACTIVE/'deployed.json',dict(source=m['source'],image=before['image'],runtime=current,gateway_open=True,
             client_release=m['client_release'],client_channel_sha256=client['channel_sha256'],cache=before['rehearsal']['cache'],
             backup_sha256=read(ACTIVE/'backup.json')['sha256'],owner_gameplay_accepted=False))
    except BaseException:
        h.hold(ACTIVE)
        raise

def recover_closed():
    """Reverse only an unreleased candidate while admissions and player state are pinned."""
    before=read(EVIDENCE/'preflight.json')
    assert (ACTIVE/'started.json').exists() and not (ACTIVE/'opening.json').exists()
    assert sha(ROOT/'data/public/channel.json')==m['client_before']
    assert not (STAGE/'client/published.json').exists() and not (ACTIVE/'recovered.json').exists()
    assert not r.compact('gateway')['running'] and a.prior.players()==0
    r.compose('stop','-t','90','game')
    assert not r.state('game')['State']['Running']
    after=before['rehearsal']['after']
    if owned()==after:
        backup=read(ACTIVE/'backup.json')
        assert backup['gzip_integrity'] and sha(Path(backup['path']))==backup['sha256']
        apply('disable','peq')
    if owned()==before['rehearsal']['disabled']:
        apply('remove-unused','peq')
    assert owned()==before['rehearsal']['before']
    # Boot transitions can expire saved state. Predict the current stopped state again.
    folder=ACTIVE/('recovery-'+uuid.uuid4().hex[:8])
    folder.mkdir(mode=0o700)
    base.EVIDENCE=folder
    expected=base.boot_state(a.prior.saved())
    r.select(m['base_image_id'])
    r.compose('up','-d','--no-deps','--wait','--wait-timeout','240','game')
    old=r.running(m['base_image_id'],binaries(False))
    assert a.prior.saved()==expected
    preserved(before,False)
    p.contract()
    base.health()
    r.closed_ports()
    r.compose('up','-d','--no-deps','--wait','--wait-timeout','60','gateway')
    assert r.compact('gateway')['running'] and r.running(m['base_image_id'],binaries(False))['started_at']==old['started_at']
    save(ACTIVE/'recovered.json',dict(image=m['base_image_id'],gateway_open=True,player_snapshot_restored=False))

if __name__=='__main__':
    assert __debug__
    os.umask(0o077)
    parser=argparse.ArgumentParser()
    actions={'preflight':preflight,'activate':activate,'publish':publish,'open':open_access,'recover-closed':recover_closed}
    parser.add_argument('action',choices=actions)
    action=parser.parse_args().action
    initialize()
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists() and sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
        actions[action]()
    print('Verified',action,flush=True)
